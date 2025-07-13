from django.conf import settings 

import deepl
import os
import polib
import time
from datetime import datetime
import re

TRANSLATION_IGNORE_PATTERNS = getattr(
    settings,
    'TRANSLATION_IGNORE_PATTERNS',
    [
        r'%\(\w+\)',
        r'%\(\w+\)[sd]',
        r'%[dsf]',
        r'(\{\{[^{}]+\}\}|\{[^{}]+\})'
    ]
)
TAG_HANDLING = 'xml'
IGNORE_TAGS_TEXT = getattr(settings, 'IGNORE_TAGS_TEXT', 'ddlit')
IGNORE_TAGS = getattr(settings, 'IGNORE_TAGS', (f'<{IGNORE_TAGS_TEXT}>', f'</{IGNORE_TAGS_TEXT}>'))

BACKUP_FILE_NAME = getattr(settings, 'BACKUP_FILE_NAME', "django_deepl_backup")
PO_FILE_EXTENSION = getattr(settings, 'PO_FILE_EXTENSION', ".po")

PO_FILE_NAME = getattr(settings, 'PO_FILE_NAME', "django")

DEEPL_API_KEY = getattr(settings, 'DEEPL_API_KEY', None)

def extract_timestamp_from_filename(file_name):
    backup_file_pattern = re.compile(f"^{re.escape(BACKUP_FILE_NAME)}_(\\d+){re.escape(PO_FILE_EXTENSION)}$")
    match = backup_file_pattern.fullmatch(file_name)
    if match:
        timestamp_str = match.group(1)
        return timestamp_str
    else:
        return None


def is_today_timestamp(timestamp_str):
    try:
        timestamp = int(timestamp_str)
        file_date = datetime.fromtimestamp(timestamp).date()
        today_date = datetime.today().date()
        return file_date == today_date
    except ValueError:
        return False

def is_valid_timestamp(timestamp_str):
    try:
        timestamp = int(timestamp_str)
        return True
    except ValueError:
        return False

def is_today_timestamp(timestamp_str):
    if is_valid_timestamp(timestamp_str):
        timestamp = int(timestamp_str)
        file_date = datetime.fromtimestamp(timestamp).date()
        today_date = datetime.today().date()
        return file_date == today_date
    return False

def generate_po_backup_filename():
    backup_timestamp = int(time.time())
    backup_file_name = f"{BACKUP_FILE_NAME}_{backup_timestamp}{PO_FILE_EXTENSION}"
    return backup_file_name

def get_apps_name():
    app_list = []
    base_dir = settings.BASE_DIR
    dir_list = list(set(os.listdir(base_dir)) | set(settings.INSTALLED_APPS))
    for directory in dir_list:
        if directory == 'locale' and os.path.isdir(os.path.join(base_dir, directory)):
            app_list.append('project_base_directory')
            continue
        if os.path.isdir(os.path.join(base_dir, directory)) and 'locale' in os.listdir(os.path.join(base_dir, directory)):
            if directory not in app_list:
                app_list.append(directory)
    return app_list

def get_all_languages():
    languages = []
    base_dir = settings.BASE_DIR
    apps = get_apps_name()

    for app in apps:
        app_path = os.path.join(base_dir, app) if app != 'project_base_directory' else base_dir  
        locale_path = os.path.join(app_path, "locale")

        if os.path.exists(locale_path) and os.path.isdir(locale_path):
                for lang in os.listdir(locale_path): 
                    if os.path.isdir(os.path.join(locale_path, lang)) and lang not in languages:
                        languages.append(lang)

        for lang_code in settings.LANGUAGES:
            if lang_code[0] not in languages:
                languages.append(lang_code[0])

    return languages


def check_translation_status(self, *args, **kwargs):
    app_to_check = kwargs.get('app')
    language_to_check = kwargs.get('language')

    po_files_to_translate = []
    base_language = settings.LANGUAGE_CODE
    base_dir = settings.BASE_DIR

    self.stdout.write(self.style.SUCCESS("\nChecking translations for Django apps...\n"))

    for app in app_to_check:
        try:
            app_path = os.path.join(base_dir, app) if app != 'project_base_directory' else base_dir
            locale_path = os.path.join(app_path, "locale")
            
            if not os.path.isdir(app_path):
                continue

            if not os.path.exists(locale_path):
                self.stdout.write(f"\nApp: {app}")
                self.stdout.write(f" - Exists in project directory: {'✅' if os.path.isdir(app_path) else '❌'}")
                self.stdout.write(self.style.ERROR(" - No translation folder (locale) found!"))
                continue

            missing_languages = []
            all_languages_present = True

            for lang in language_to_check:
                po_file_path = os.path.join(locale_path, lang, "LC_MESSAGES", f"{PO_FILE_NAME}{PO_FILE_EXTENSION}")
                if not os.path.exists(po_file_path):
                    all_languages_present = False
                    missing_languages.append(lang)

            self.stdout.write(f"\nApp: {app}")
            self.stdout.write(f" - Has translation folder: {'✅' if os.path.exists(locale_path) else '❌'}")

            if all_languages_present:
                self.stdout.write(self.style.SUCCESS(" - All required languages are available ✅"))
            else:
                self.stdout.write(self.style.WARNING(f" - Folder not found for: {', '.join(missing_languages)}"))

            completion_rates = {}
            extra_info = {}

            for lang in language_to_check:
                po_file_path = os.path.join(locale_path, lang, "LC_MESSAGES", f"{PO_FILE_NAME}{PO_FILE_EXTENSION}")
                
                if os.path.exists(po_file_path):
                    file_translation_details = {
                        'app': app,
                        'translate_from': base_language,
                        'translate_to': lang,
                        'file_path': po_file_path
                    }
                    po_files_to_translate.append(file_translation_details)

                    try:
                        po_file = polib.pofile(po_file_path)

                        total_entries = len([entry for entry in po_file if entry.msgid.strip() != ""])
                        translated_entries = len([entry for entry in po_file if entry.translated()])

                        fuzzy_active_count = len([entry for entry in po_file if entry.fuzzy and not entry.obsolete and entry.msgid])

                        obsolete_entries = [entry for entry in po_file.obsolete_entries() if entry.msgid.strip() != ""]
                        obsolete_count = len(obsolete_entries)

                        fuzzy_obsolete_count = len([entry for entry in obsolete_entries if entry.fuzzy and entry.msgid])

                        total_fuzzy_count = fuzzy_active_count + fuzzy_obsolete_count

                        completion_rate = (translated_entries / total_entries * 100) if total_entries > 0 else 0
                        completion_rates[lang] = round(completion_rate, 2)
                        extra_info[lang] = {
                            "fuzzy_obsolete_count":fuzzy_obsolete_count,
                            "fuzzy_active_count":fuzzy_active_count,
                            "obsolete_count":obsolete_count,
                        }

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error reading PO file for {lang} in app {app}: {e}"))

            if completion_rates:
                self.stdout.write(" - Translation completion rates:")
                for lang, percentage in completion_rates.items():
                    extra = extra_info.get(lang, {})

                    obsolete_count = extra.get("obsolete_count", 0)
                    fuzzy_active_count = extra.get("fuzzy_active_count", 0)
                    fuzzy_obsolete_count = extra.get("fuzzy_obsolete_count", 0)

                    self.stdout.write(f"   • {lang}: {int(percentage)}%")

                    if obsolete_count > 0:
                        self.stdout.write(self.style.WARNING(f"      • There are {obsolete_count} obsolete translations."))
                        if fuzzy_obsolete_count > 0:
                            self.stdout.write(self.style.WARNING(
                                f"         • Of these, {fuzzy_obsolete_count} are fuzzy obsolete translations."
                            ))

                    if fuzzy_active_count > 0:
                        self.stdout.write(self.style.WARNING(f"      • Fuzzy: {fuzzy_active_count}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking app {app}: {e}"))
            exit(0)

    self.stdout.write(self.style.SUCCESS("\nCheck completed!"))

    return po_files_to_translate



