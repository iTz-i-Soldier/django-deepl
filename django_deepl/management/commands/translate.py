from django.conf import settings
from django.core.management.base import BaseCommand

import deepl
from deepl.exceptions import AuthorizationException
import os
import polib
import shutil
import re
from datetime import datetime, timezone

from django_deepl.utils import check_translation_status, get_apps_name, PO_FILE_EXTENSION, PO_FILE_NAME, generate_po_backup_filename, TRANSLATION_IGNORE_PATTERNS, IGNORE_TAGS, IGNORE_TAGS_TEXT, TAG_HANDLING, DEEPL_API_KEY

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.initialize()

    help = f"Automatically translates msgid strings in {PO_FILE_EXTENSION} files into the target language by filling in msgstr values."
    suppressed_base_arguments = [
        '--verbosity', 
        '--settings', 
        '--pythonpath', 
        '--traceback', 
        '--no-color', 
        '--force-color', 
        '--skip-checks',
        '--version'
        ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            choices=self.apps_name,
            default=self.apps_name,
            nargs='*',
            help="Specify which app(s) to translate (optional). If not provided, all apps will be processed."
        )
        parser.add_argument(
            '--language',
            choices=[lang[0] for lang in settings.LANGUAGES],
            default=[lang[0] for lang in settings.LANGUAGES],
            nargs='*',
            help="Specify which language(s) {PO_FILE_EXTENSION} file to translate (optional). If not provided, all languages will be processed."
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            default=False,
            help="If set, translates even already translated msgstr values (default: False)."
        )
        parser.add_argument(
            '--split_sentences',
            choices=['1', '0', 'nonewlines'],
            default='nonewlines',
            help="Specify how text should be split into sentences. Options: '1' text will be split into sentences using both newlines and punctuation, '0' text will not be split into sentences. Use this for applications where each text contains only one sentence, 'nonewlines' text will be split into sentences using punctuation but not newlines, (default: 'nonewlines')."
        )
        parser.add_argument(
            '--preserve_formatting',
            action='store_true',
            default=True,  
            help="Controls automatic-formatting-correction. Set to True to prevent automatic-correction of formatting (default: True)."
        )
        parser.add_argument(
            '--formality',
            choices=['less', 'more'],
            default='less', 
            help=f"Controls whether translations should lean toward informal or formal language. Options: 'less' (informal), 'more' (formal) (default: 'less'). Supported languages: {', '.join(lang.lower() for lang in self.languages_with_formality_supported)}."
        )
        parser.add_argument(
            '--context',
            type=str,
            default=None,
            help="Specifies additional context to influence translations, not translated itself. (Characters in the context parameter are not counted toward billing.)."
        )
        parser.add_argument(
            '--model_type',
            choices=['quality_optimized', 'prefer_quality_optimized', 'latency_optimized'],
            default='prefer_quality_optimized', 
            help="Specifies the type of translation model to use. Options: 'quality_optimized'use a translation model that maximizes translation quality, at the cost of response time. This option may be unavailable for some language pairs, 'prefer_quality_optimized' use the highest-quality translation model for the given language pair, 'latency_optimized' use a translation model that minimizes response time, at the cost of translation quality, ......if a language pair that is not supported by next-gen models, it will fail. Consider using prefer_quality_optimized instead....... (default: 'prefer_quality_optimized')."
        )
        parser.add_argument(
            '--translate_base_language',
            action='store_true',
            default=False,
            help=f"If specified, the base language {PO_FILE_EXTENSION} file of the Django app will also be translated."
        )
        parser.add_argument(
            '--no_backup',
            action='store_true',
            default=False,
            help=f"If specified, no backup files will be created for each {PO_FILE_EXTENSION}."
        )
        parser.add_argument(
            '--preferred_variant',
            choices=self.available_variant,
            default=[],
            nargs='*',
            help=(
                "Specify the preferred variant(s) for the target language. "
                "This will be applied only to the corresponding language pair. "
                "For example, if translating to 'en', you can specify 'en-us' to prefer the US English variant."
            )
        )
        parser.add_argument(
            '--usage',
            action='store_true',
            default=False,
            help=f"Remaining usage: {self.usage[0]} characters out of {self.usage[1]} characters."
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            default=False,
            help="Enable interactive mode. Asks for confirmation or reformulation before each translation."
        )

    def initialize(self):
        self.stdout.write(self.style.WARNING(
            "Initializing translation client and preparing necessary data. Please wait..."
        ))
        self.apps_name = get_apps_name()

        self.deepl_client = self.get_deepl_client()
        self.available_source_languages = self.get_available_source_languages()
        self.available_target_languages = self.get_available_target_languages()
        self.languages_with_formality_supported = self.get_languages_with_formality_supported()
        self.usage = self.check_usage()
        self.available_variant = [lang.lower() for lang in self.available_target_languages if '-' in lang]

    def handle(self, *args, **kwargs):
        if kwargs.get('usage'):
            remaining_usage = self.usage
            self.stdout.write(self.style.SUCCESS(f"Remaining usage: {remaining_usage[0]} characters out of {remaining_usage[1]} characters."))
            exit(0)

        app_to_check = kwargs.get('app')
        language_to_check = kwargs.get('language')
        overwrite = kwargs.get('overwrite')
        split_sentences = kwargs.get('split_sentences')
        preserve_formatting = kwargs.get('preserve_formatting')
        formality = kwargs.get('formality')
        context = kwargs.get('context')
        model_type = kwargs.get('model_type')
        translate_base_language = kwargs.get('translate_base_language')
        no_backup = kwargs.get('no_backup')
        preferred_variant = kwargs.get('preferred_variant')

        base_language = settings.LANGUAGE_CODE
        base_dir = settings.BASE_DIR

        self.stdout.write(self.style.WARNING(
            f"\nDetected base translation language: {base_language}.\n"
            f"{'Including' if translate_base_language else 'Ignoring'} base language translation.\n"
        ))

        files_to_translate = check_translation_status(self, *args, **kwargs)

        if len(files_to_translate) <= 0:
            self.stdout.write(self.style.ERROR("\nNo files to translate."))
            exit(0)

        filtered_files_to_translate = [
            file for file in files_to_translate if translate_base_language or file['translate_to'] != base_language
        ]

        available_source_languages_set = set(self.available_source_languages)
        available_target_languages_set = set(self.available_target_languages)

        for file_to_translate in filtered_files_to_translate:

            translate_to = file_to_translate['translate_to']
            translate_from = file_to_translate['translate_from']
            
            source_lang = translate_from.split('-')[0].upper()
            if source_lang not in available_source_languages_set:
                self.stdout.write(self.style.ERROR(f'({translate_from}) is not an available source language.'))

                if len(preferred_variant) > 0:
                    preferred_match = next((lang for lang in preferred_variant if lang in available_source_languages_set), None)
                    if preferred_match:
                        source_lang = preferred_match
                        file_to_translate['translate_from'] = source_lang.lower()
                        self.stdout.write(self.style.WARNING(f'Using preferred variant: {source_lang}'))
                
                possible_match = next((lang for lang in available_source_languages_set if lang.startswith(source_lang)), None)
                if possible_match:
                    source_lang = possible_match
                    preferred_variant.append(possible_match)
                    file_to_translate['translate_from'] = source_lang.lower()
                    self.stdout.write(self.style.WARNING(f'Using closest match: {source_lang}'))
                else:
                    self.stdout.write(self.style.ERROR('No suitable match found for the source language.'))
                    exit(0)

            target_lang = translate_to.upper()
            if target_lang not in available_target_languages_set:
                self.stdout.write(self.style.ERROR(f'({translate_to}) is not an available target language.'))

                if len(preferred_variant) > 0:
                    preferred_match = next((lang for lang in preferred_variant if lang in available_target_languages_set), None)
                    if preferred_match:
                        target_lang = preferred_match
                        file_to_translate['translate_to'] = target_lang.lower()
                        self.stdout.write(self.style.WARNING(f'Using preferred variant: {target_lang}'))
                        continue

                possible_match = next((lang for lang in available_target_languages_set if lang.startswith(target_lang.split('-')[0])), None)
                if possible_match:
                    target_lang = possible_match
                    preferred_variant.append(possible_match)
                    file_to_translate['translate_to'] = target_lang.lower()
                    self.stdout.write(self.style.WARNING(f'Using closest match: {target_lang}'))
                else:
                    self.stdout.write(self.style.ERROR('No suitable match found for the target language.'))
                    exit(0)

            if formality is not None and target_lang not in self.languages_with_formality_supported:
                self.stdout.write(self.style.ERROR(
                    f'({translate_to}) is not an available target language for translation with formality.\n'
                    f'Languages with formality support: {", ".join(self.languages_with_formality_supported).lower()}\n'
                    'Formality will not be used for the translation.\n'
                ))
                kwargs['formality'] = None

            self.translate_po_file(file_to_translate, *args, **kwargs)

        self.stdout.write(self.style.SUCCESS("\nTranslation completed!"))

    def translate_po_file(self, file_to_translate, *args, **kwargs):
        overwrite = kwargs.get('overwrite')
        split_sentences = kwargs.get('split_sentences')
        preserve_formatting = kwargs.get('preserve_formatting')
        formality = kwargs.get('formality')
        context = kwargs.get('context')
        model_type = kwargs.get('model_type')
        no_backup = kwargs.get('no_backup')
        interactive = kwargs.get('interactive')
        
        app = file_to_translate['app']
        translate_from = file_to_translate['translate_from']
        translate_to = file_to_translate['translate_to']
        file_path = file_to_translate['file_path']
        deepl_usage = self.check_usage()

        if not no_backup:
            po_file_name = f'{PO_FILE_NAME}{PO_FILE_EXTENSION}'
            backup_file_name = generate_po_backup_filename()
            backup_file_path = file_path.replace(po_file_name, backup_file_name)
            shutil.copy(file_path, backup_file_path)

        self.stdout.write(self.style.SUCCESS(
            "\n--------------------------------------\n"
            f"Translation started...\n"
            f"Backup file: {f'{backup_file_path}' if not no_backup else 'Not created'}\n"
            f"App: {app}\n"
            f"From language: {translate_from}\n"
            f"To language: {translate_to}\n"
            f"File path: {file_path}\n"
            f"Split sentences: {split_sentences}\n"
            f"Preserve formatting: {preserve_formatting}\n"
            f"Formality: {formality}\n"
            f"Overwrite: {overwrite}\n"
            f"Context: {context}\n"
            f"Model type: {model_type}\n"
            f"Deepl usage: {deepl_usage[0]} characters used of {deepl_usage[1]} total characters.\n"
            "--------------------------------------"
        ))

        characters_consumed, characters_limit = map(int, deepl_usage)
        po = polib.pofile(file_path)
        total_entry = len(po)
        translated_count = 0
        for entry in po:
            remove_fuzzy = False
            remove_previous_msgid = False
            if entry.fuzzy:
                self.stdout.write(self.style.WARNING('\nThis text is marked as fuzzy.'))
                remove_fuzzy = True
                if entry.previous_msgid:
                    self.stdout.write(self.style.WARNING('the new text will be used.'))
                    remove_previous_msgid = True
            msgid = entry.msgid
            msgstr = entry.msgstr
            if not msgid:
                continue
            if msgid and msgstr and not overwrite:
                continue
            text_to_translate = self.add_ignore_tags(msgid)
            estimated_billed_characters = len(text_to_translate)
            
            if estimated_billed_characters + characters_consumed >= characters_limit:
                self.stdout.write(self.style.ERROR(
                    "\nTranslation aborted: the estimated character count would exceed the remaining quota.\n"
                ))
                exit(0)

            try:
                result = self.deepl_client.translate_text(
                    text=text_to_translate,
                    source_lang=translate_from,
                    target_lang=translate_to,
                    context=context,
                    model_type=model_type,
                    split_sentences=split_sentences,
                    preserve_formatting=preserve_formatting,
                    formality=formality,
                    tag_handling=TAG_HANDLING,
                    ignore_tags=IGNORE_TAGS_TEXT
                )
            except KeyboardInterrupt:
                exit(0)
            except Exception as error:
                self.stdout.write(self.style.ERROR(f"\n{error}\n"))
                exit(0)

            translated_text = self.remove_ignore_tags(result.text)
            detected_source_language = result.detected_source_lang
            billed_characters = result.billed_characters
            characters_consumed += int(billed_characters)
            if translated_text and translated_text is not None:
                if interactive:
                    try:
                        while True:
                            self.stdout.write(self.style.WARNING(f'Original text: {msgid}'))
                            self.stdout.write(self.style.WARNING(f'Translated text: {translated_text}'))
                            self.stdout.write(self.style.WARNING("Do you accept the translation?"))
                            self.stdout.write(self.style.WARNING("y: yes, "))
                            self.stdout.write(self.style.WARNING("r: rephrase, "))
                            self.stdout.write(self.style.WARNING("s: skip, "))
                            self.stdout.write(self.style.WARNING("q: deactivate interactive mode\n"))
                            confirm = input(':').strip().lower()
                            if confirm == "y":
                                self.stdout.write(self.style.SUCCESS("\nTranslation accepted.\n"))
                                break
                            elif confirm == "r":
                                self.stdout.write(self.style.ERROR('\nFunction incomplete, do not use.\n'))
                                continue
                                try:
                                    rephrased_result = self.deepl_client.rephrase_text(
                                        text=self.add_ignore_tags(translated_text), 
                                        target_lang=translate_to
                                        # style=
                                        # tone = 
                                    )
                                except AuthorizationException as error:
                                    self.stdout.write(self.style.ERROR(f"\n{error}"))
                                    self.stdout.write(self.style.ERROR("It's possible that this auth key does not have the permissions to use DeepL Write."))
                                    self.stdout.write(self.style.ERROR("(It's not included in DeepL API Free plan.)\n"))
                                    continue
                                except Exception as error:
                                    self.stdout.write(self.style.ERROR(f"\n{error}\n"))
                                    continue
                                rephrased_translation = self.remove_ignore_tags(rephrased_result.text)
                                translated_text = rephrased_translation
                                rephrased_detected_source_language = result.detected_source_lang
                                rephrased_billed_characters = result.billed_characters
                                characters_consumed += int(rephrased_billed_characters)
                                self.stdout.write(self.style.WARNING(f"Rephrased translation: {rephrased_translation}"))
                            elif confirm == "s":
                                translated_text = None
                                self.stdout.write(self.style.WARNING("\nSkipping this entry.\n"))
                                break
                            elif confirm == "q":
                                self.stdout.write(self.style.WARNING("\nThe interactive mode will be disabled from the next translation.\n"))
                                interactive = False
                            else:
                                self.stdout.write(self.style.ERROR("\nInvalid choice. Please enter 'y', 'r', or 's'.\n"))
                    except KeyboardInterrupt:
                        print('\n')
                        exit(0)

                if translated_text and translated_text is not None:
                    entry.msgstr = translated_text
                    if remove_fuzzy:
                        entry.fuzzy = False
                    if remove_previous_msgid:
                        entry.previous_msgid = None
                    translated_count += 1 
                    progress = int((translated_count / total_entry) * 100) if overwrite else po.percent_translated()
                    self.stdout.write(self.style.WARNING(
                        f"Translation progress: {progress}% complete."
                    ))

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M+0000")
        po.metadata["PO-Revision-Date"] = now
        po.metadata["Last-Translator"] = "django-deepl <no-reply@django-deepl.com>"
        po.metadata["X-Translated-Using"] = "django-deepl"
        po.save(file_path)
        exit(0)

    def add_ignore_tags(self, text):
        for pattern in TRANSLATION_IGNORE_PATTERNS:
            text = re.sub(pattern, lambda m: f'{IGNORE_TAGS[0]}{m.group(0)}{IGNORE_TAGS[1]}', text)
        return text

    def remove_ignore_tags(self, text):
        pattern = rf'{IGNORE_TAGS[0]}(.*?){IGNORE_TAGS[1]}'
        return re.sub(pattern, r'\1', text)

    def get_deepl_client(self):
        deepl_api_key = DEEPL_API_KEY
        if deepl_api_key is None or not deepl_api_key:
            self.stdout.write(self.style.ERROR("DEEPL_API_KEY is not defined in the settings."))
            exit(0)
        try:
            deepl_client = deepl.DeepLClient(deepl_api_key, send_platform_info=False)
            return deepl_client
        except Exception as error:
            self.stdout.write(self.style.ERROR(f'{error}'))
            exit(0)

    def check_usage(self):
        try:
            usage = self.deepl_client.get_usage()
            if usage.character.valid:
                return (usage.character.count, usage.character.limit)
            if usage.any_limit_reached:
                self.stdout.write(self.style.ERROR('Translation limit reached.'))
                exit(0)
        except Exception as error:
            self.stdout.write(self.style.ERROR(f'{error}'))
            exit(0)

    def get_available_source_languages(self):
        try:
            available_source_languages = [lang.code for lang in self.deepl_client.get_source_languages()]
        except Exception as error:
            self.stdout.write(self.style.ERROR(f'{error}'))
            exit(0)
        return available_source_languages

    def get_available_target_languages(self):
        try:
            available_target_languages = [lang.code for lang in self.deepl_client.get_target_languages()]
        except Exception as error:
            self.stdout.write(self.style.ERROR(f'{error}'))
            exit(0)
        return available_target_languages

    def get_languages_with_formality_supported(self):
        try:
            languages_with_formality_supported = [lang.code for lang in self.deepl_client.get_target_languages() if lang.supports_formality]
        except Exception as error:
            self.stdout.write(self.style.ERROR(f'{error}'))
            exit(0)
        return languages_with_formality_supported