import os
import polib

from django.conf import settings
from django.core.management.base import BaseCommand
from django_deepl.utils import PO_FILE_NAME, PO_FILE_EXTENSION, get_apps_name, get_all_languages

class Command(BaseCommand):
    help = (
        "Delete obsolete translations from PO files."
        "Operates on specified Django apps and languages. "
        "If no app or language is specified, processes all available."
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apps_name = get_apps_name()
        self.languages = get_all_languages()

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            choices=self.apps_name,
            default=self.apps_name,
            nargs='*',
            help="Specify which app(s) to clean obsolete translations for. Defaults to all apps."
        )
        parser.add_argument(
            '--language',
            choices=self.languages,
            default=self.languages,
            nargs='*',
            help="Specify which language(s) to clean obsolete translations for. Defaults to all languages."
        )

    def handle(self, *args, **kwargs):
        apps_to_check = kwargs.get('app', self.apps_name)
        languages_to_check = kwargs.get('language', self.languages)

        base_dir = settings.BASE_DIR

        self.stdout.write(self.style.SUCCESS("\nStarting to delete obsolete translations...\n"))

        for app in apps_to_check:
            try:
                app_path = os.path.join(base_dir, app) if app != 'project_base_directory' else base_dir
                locale_path = os.path.join(app_path, "locale")

                if not os.path.isdir(app_path):
                    self.stdout.write(self.style.WARNING(f"App directory not found: {app_path}"))
                    continue

                if not os.path.exists(locale_path):
                    self.stdout.write(self.style.WARNING(f"No locale folder found for app: {app}"))
                    continue

                for lang in languages_to_check:
                    po_file_path = os.path.join(locale_path, lang, "LC_MESSAGES", f"{PO_FILE_NAME}{PO_FILE_EXTENSION}")

                    if not os.path.exists(po_file_path):
                        self.stdout.write(self.style.WARNING(f"PO file not found for language '{lang}' in app '{app}'"))
                        continue

                    po_file = polib.pofile(po_file_path)

                    obsolete_entries = po_file.obsolete_entries()

                    if not obsolete_entries:
                        # self.stdout.write(f"No obsolete translations to delete for {app} ({lang})")
                        continue

                    count = len(obsolete_entries)
                    for entry in obsolete_entries:
                        po_file.remove(entry)

                    po_file.save()
                    self.stdout.write(self.style.SUCCESS(f"Deleted {count} obsolete translation(s) from {app} ({lang})"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing app {app}: {e}"))

        self.stdout.write(self.style.SUCCESS("\nObsolete translation deletion completed!\n"))
