from django.conf import settings
from django.core.management.base import BaseCommand

import os
import polib

from django_deepl.utils import PO_FILE_NAME, PO_FILE_EXTENSION, get_apps_name, get_all_languages

class Command(BaseCommand):
    help = (
        "Clean up PO files by removing entries with empty msgid fields. "
        "Operates on specified Django apps and languages. "
        "If no app or language is specified, processes all available."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apps_name = get_apps_name()
        self.all_languages = get_all_languages()

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            choices=self.apps_name,
            default=self.apps_name,
            nargs='*',
            help="Specify which app(s) to clean. If not provided, cleans all apps."
        )
        parser.add_argument(
            '--language',
            choices=self.all_languages,
            default=self.all_languages,
            nargs='*',
            help="Specify which language(s) to clean. If not provided, cleans all languages."
        )

    def handle(self, *args, **kwargs):
        apps_to_clean = kwargs.get('app') or self.apps_name
        langs_to_clean = kwargs.get('language') or get_all_languages()
        base_dir = settings.BASE_DIR

        for app in apps_to_clean:
            try:
                app_path = os.path.join(base_dir, app) if app != 'project_base_directory' else base_dir
                locale_path = os.path.join(app_path, "locale")

                if not os.path.isdir(app_path):
                    self.stdout.write(self.style.WARNING(f"Skipping {app}: app directory not found"))
                    continue

                if not os.path.exists(locale_path):
                    self.stdout.write(self.style.WARNING(f"Skipping {app}: no locale folder found"))
                    continue

                for lang in langs_to_clean:
                    po_file_path = os.path.join(locale_path, lang, "LC_MESSAGES", f"{PO_FILE_NAME}{PO_FILE_EXTENSION}")
                    if os.path.exists(po_file_path):
                        try:
                            po = polib.pofile(po_file_path)
                            entries_to_remove = [entry for entry in po if entry.msgid == ""]
                            if len(entries_to_remove) > 0:
                                for entry in entries_to_remove:
                                    print(entry)
                                    po.remove(entry)
                                po.save(po_file_path)
                                self.stdout.write(self.style.SUCCESS(f"Cleaned empty translation in {po_file_path}"))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Error cleaning {po_file_path}: {e}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"PO file not found: {po_file_path}"))


            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing app {app}: {e}"))

        self.stdout.write(self.style.SUCCESS("\nCleaning completed!"))
