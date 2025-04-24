from django.core.management.base import BaseCommand
from gitstats import core_gitlab


class Command(BaseCommand):
    def handle(self, *args, **options):
        print('updating watched gitlab repositories')
        core_gitlab.update()
