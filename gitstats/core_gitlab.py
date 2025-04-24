from datetime import datetime
import gitlab
from django_gitstat.settings import env
from gitstats.models import Commit, Repository, RepositorySource
from gitstats import dtos, core
from tqdm import tqdm


GITLAB_HOST = env('GITLAB_HOST')
GITLAB_TOKEN = env('GITLAB_TOKEN')


def get_gitlab_client():
    return gitlab.Gitlab(GITLAB_HOST, GITLAB_TOKEN)


def get_project_by_namespace(namespace: str):
    gl = get_gitlab_client()
    namespace = namespace.replace(GITLAB_HOST, '')
    if namespace.startswith('/'):
        namespace = namespace[1:]
    project = gl.projects.get(namespace)
    return project


def get_commits(gitlab_project_id: int):
    gl = get_gitlab_client()
    project = gl.projects.get(gitlab_project_id)
    commits = project.commits.list(get_all=True, all=True, order_by='created_at', sort='desc', with_stats=True)
    return commits


def get_gitlab_commit_stats(commit) -> list[dtos.CommitStats]:
    diff = commit.diff()
    stats: list[dtos.CommitStats] = []
    for row in diff:
        stats.append(dtos.CommitStats(
            commit=commit.short_id,
            additions=len([x for x in row['diff'].splitlines() if x.startswith('+')]),
            deletions=len([x for x in row['diff'].splitlines() if x.startswith('-')]),
            file=row['new_path'],
        ))
    return stats


def add_gitlab_repository(namespace: str):
    project = get_project_by_namespace(namespace)
    print(project.name, project.id)
    gitlab_source, _ = RepositorySource.objects.get_or_create(name='gitlab')
    repository, created = Repository.objects.get_or_create(
        name=project.name, source=gitlab_source, gitlab_project_id=project.id
    )
    if not created:
        print('Repository', repository.name, 'already exists')
    else:
        print('Created repository', repository.name)


def update():
    gitlab_source, _ = RepositorySource.objects.get_or_create(name='gitlab')
    gitlab_repos = Repository.objects.filter(source=gitlab_source)
    if not gitlab_repos:
        print('no gitlab repositories are added')
        return
    for repo in gitlab_repos:
        print(f'[ * ] updating {repo.name} id {repo.gitlab_project_id}')
        update_repository(repo)


def update_repository(repository: Repository):
    api_commits = get_commits(repository.gitlab_project_id)
    print('     ', len(api_commits), 'commits')
    dto_commits: list[dtos.CommitDTO] = []
    for api_commit in api_commits:
        dto_commits.append(dtos.CommitDTO(
            commit_author=api_commit.author_email,
            commit_date=datetime.strptime(api_commit.created_at[:10], '%Y-%m-%d').date(),
            commit_hash=api_commit.short_id,
        ))
    core.insert_commits(repository, dto_commits)
    unparsed_commits: list[Commit] = core.get_unparsed_commits(repository).in_bulk(field_name='commit_hash')
    commits_to_parse = [commit for commit in api_commits if commit.short_id in unparsed_commits]
    if not commits_to_parse:
        print('     ', 'Up to date')
        return
    print('     ', 'parsing', len(unparsed_commits), 'unparsed commits')
    for api_commit in tqdm(commits_to_parse):
        db_commit = unparsed_commits[api_commit.short_id]
        stats = get_gitlab_commit_stats(api_commit)
        core.insert_commit_stats(db_commit, stats)
        db_commit.stats_parsed = True
        db_commit.save()
    print('Done')
