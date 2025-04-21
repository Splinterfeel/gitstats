from django.core.management.base import BaseCommand, CommandError
from gitstats import generate_stats


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--file', help="ZIP filename to read")

    def handle(self, *args, **options):
        file = options['file']
        if not file:
            raise CommandError("provide --file argument")
        print('reading stats from', options['file'])
        generate_stats.generate(options['file'])
