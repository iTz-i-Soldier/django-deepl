from django.conf import settings
from django.core.management.base import BaseCommand

import os
import polib

from django_deepl.utils import check_translation_status, get_apps_name

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apps_name = get_apps_name()

    help = "Check missing translations and completion percentage for installed Django apps"
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
            help="Specify which app(s) to check (optional). If not provided, checks all apps."
        )
        parser.add_argument(
            '--language',
            choices=[lang[0] for lang in settings.LANGUAGES],
            default=[lang[0] for lang in settings.LANGUAGES],
            nargs='*',
            help="Specify which language(s) to check (optional). If not provided, checks all languages."
        )

    def handle(self, *args, **kwargs):
        check_translation_status(self, *args, **kwargs)

