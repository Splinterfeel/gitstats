from django.db.models.expressions import Window
from django.db.models.functions import Lag
from gitstats import dtos
from gitstats.models import Commit, CommitStats, Repository, Author


def insert_commits(repository: Repository, commits: list[dtos.CommitDTO]):
    uq_str_authors = set([c.commit_author for c in commits])
    new_authors = [Author(name=name) for name in uq_str_authors]
    Author.objects.bulk_create(new_authors, ignore_conflicts=True)
    authors = Author.objects.filter(name__in=uq_str_authors).in_bulk(field_name='name')
    commit_objs = [Commit(
            repository=repository, author=authors[c.commit_author],
            commit_date=c.commit_date, commit_hash=c.commit_hash
        ) for c in commits
    ]
    Commit.objects.bulk_create(commit_objs, ignore_conflicts=True)


def get_unparsed_commits(repository: Repository):
    """Get commits which stats are stil not parsed"""
    unparsed_commits = Commit.objects.filter(
        repository=repository, stats_parsed=False
    ).annotate(prev=Window(expression=Lag('commit_hash'))).order_by('-commit_date')
    return unparsed_commits


def insert_commit_stats(commit: Commit, commit_stats: CommitStats):
    CommitStats.objects.filter(commit=commit).delete()
    new_stats = [CommitStats(
            commit=commit, additions=s.additions, deletions=s.deletions, file=s.file
            ) for s in commit_stats
        ]
    CommitStats.objects.bulk_create(new_stats)
