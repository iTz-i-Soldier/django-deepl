from django.conf import settings
from django.core.management.base import BaseCommand
import os
import re
from django_deepl.utils import get_apps_name, PO_FILE_EXTENSION, BACKUP_FILE_NAME, is_today_timestamp, is_valid_timestamp, extract_timestamp_from_filename

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apps_name = get_apps_name()

    help = "Deletes backups. By default, it removes all backups. If --keep_today is enabled, it keeps backups from today."

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
            '--keep_today',
            action='store_true',
            default=False,  
            help="If enabled, keeps backups from today and deletes others."
        )

    def handle(self, *args, **kwargs):
        keep_today = kwargs.get('keep_today')
        
        base_dir = settings.BASE_DIR
        app_to_check = self.apps_name

        language_to_check = [lang[0] for lang in settings.LANGUAGES]

        self.stdout.write(self.style.SUCCESS("\nChecking backup files for Django apps...\n"))

        for app in app_to_check:
            try:
                app_path = os.path.join(base_dir, app) if app != 'project_base_directory' else base_dir
                if not os.path.isdir(app_path):
                    continue

                locale_path = os.path.join(app_path, "locale")
                if not os.path.exists(locale_path):
                    continue

                for lang in language_to_check:
                    po_file_path = os.path.join(locale_path, lang, "LC_MESSAGES")
                    if not os.path.isdir(po_file_path):
                        continue

                    for file in os.listdir(po_file_path):
                        file = file.strip()
                        backup_file_pattern = f"^{re.escape(BACKUP_FILE_NAME)}_\\d+{re.escape(PO_FILE_EXTENSION)}$"
                        
                        if re.fullmatch(backup_file_pattern, file):
                            file_timestamp = extract_timestamp_from_filename(file)
                            file_path = os.path.join(po_file_path, file)

                            if not file_timestamp or not is_valid_timestamp(file_timestamp):
                                continue

                            if keep_today and is_today_timestamp(file_timestamp):
                                self.stdout.write(self.style.WARNING(f"Skipping file, seems to be from today: {file_path}"))
                                continue

                            try:
                                os.remove(file_path)
                                self.stdout.write(self.style.SUCCESS(f"Deleted: {file_path}"))
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"Failed to delete {file_path}: {e}"))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error checking app {app}: {e}"))
                exit(0)

        self.stdout.write(self.style.SUCCESS("Backups processed"))
