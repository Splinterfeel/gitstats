from django.core.management.base import BaseCommand, CommandError
from django_gitstat.settings import env
from gitstats import core_gitlab


GITLAB_HOST = env('GITLAB_HOST')


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--url', help="project URL")

    def handle(self, *args, **options):
        url = options['url']
        if not url:
            raise CommandError("provide --url argument")
        print('querying', GITLAB_HOST, 'for project', options['url'])
        core_gitlab.add_gitlab_repository(url)
