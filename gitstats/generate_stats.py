import csv
import subprocess
import zipfile
import os
import gitstats.utils as utils
from django_gitstat.settings import BASE_DIR, env
from django.db.models.expressions import Window
from django.db.models.functions import Lag
from gitstats.models import Repository, Author, Commit, CommitStats

UNPACK_DIR = env("UNPACK_REPOS_DIR")


def unpack_zip(file_name: str) -> str:
    file_path = os.path.join(BASE_DIR, file_name)
    destination_dir = os.path.join(BASE_DIR, UNPACK_DIR)
    os.makedirs(destination_dir, exist_ok=True)
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(destination_dir)
    return os.path.join(destination_dir, file_name.replace('.zip', ''))


def parse_commits(path: str) -> list[utils.StatRow]:
    cmd_delimiter = get_cmd_delimiter()
    commands = [f"cd {path}", "git log --no-merges --pretty=format:%as,%h,%ae%gd"]
    output = subprocess.check_output(cmd_delimiter.join(commands), shell=True)
    data = []
    csv_data = csv.reader(output.decode().splitlines())
    for line in csv_data:
        data.append(utils.StatRow(
            commit_date=line[0], commit_hash=line[1], commit_author=line[2],
        ))
    print('parsed', len(data), 'commits')
    return data


def get_cmd_delimiter():
    if os.name == 'nt':
        return '&'
    else:
        return ';'


def format_commit_stats_line(commit_hash: str, line: str) -> utils.CommitStats:
    additions = line[0]
    deletions = line[1]
    file = line[2]
    if '{' in file and '}' in file and '=>' in file:
        # file moved, save only new location
        first = file.split('{')[0]
        last = file.split('}')[-1]
        file = (first + last).replace('\\\\', r'\\')
    return utils.CommitStats(commit=commit_hash, additions=additions, deletions=deletions, file=file)


def parse_commit_stats(project_folder: str, project_name: str):
    repository = Repository.objects.filter(name=project_name).first()
    unparsed_commits = Commit.objects.filter(
        repository=repository, stats_parsed=False
    ).annotate(prev=Window(expression=Lag('commit_hash'))).order_by('-commit_date')
    commands = [f"cd {project_folder}", "git diff {commit_1} {commit_2} --numstat"]
    cmd_delimiter = get_cmd_delimiter()
    cmd_str = cmd_delimiter.join(commands)
    print('reading filestats for', len(unparsed_commits), 'commits')
    for commit in unparsed_commits:
        ready_stats: list[utils.CommitStats] = []
        prev_hash = commit.prev if commit.prev is not None else ''
        command = cmd_str.format(commit_1=commit.commit_hash, commit_2=prev_hash)
        output = subprocess.check_output(command, shell=True)
        output_lines = [line.split() for line in output.decode().splitlines()]
        for line in output_lines:
            ready_stats.append(format_commit_stats_line(commit.commit_hash, line))
        CommitStats.objects.filter(commit=commit).delete()
        new_stats = [CommitStats(
            commit=commit, additions=s.additions, deletions=s.deletions, file=s.file
            ) for s in ready_stats
        ]
        CommitStats.objects.bulk_create(new_stats)
        commit.stats_parsed = True
        commit.save()


def insert_commits(project_name: str, commits: list[utils.StatRow]):
    repository, _ = Repository.objects.get_or_create(name=project_name)
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


def generate(repo_zip: str):
    project_folder = unpack_zip(repo_zip)
    project_name = project_folder.split('\\')[-1]
    commits: list[utils.StatRow] = parse_commits(project_folder)
    insert_commits(project_name, commits)
    parse_commit_stats(project_folder, project_name)
