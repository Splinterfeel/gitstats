import csv
import subprocess
import zipfile
import os
import gitstats.dtos as dtos
from django_gitstat.settings import BASE_DIR, env
from gitstats.models import Repository, RepositorySource
from gitstats import core


UNPACK_DIR = env("UNPACK_REPOS_DIR")


def unpack_zip(file_name: str) -> tuple[str, str]:
    file_path = os.path.join(BASE_DIR, file_name)
    destination_dir = os.path.join(BASE_DIR, UNPACK_DIR)
    os.makedirs(destination_dir, exist_ok=True)
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(destination_dir)
    path = os.path.join(destination_dir, file_name.replace('.zip', ''))
    folder_name = path.split('\\')[-1]
    return path, folder_name


def parse_commits_from_folder(path: str) -> list[dtos.CommitDTO]:
    cmd_delimiter = get_cmd_delimiter()
    commands = [f"cd {path}", "git log --no-merges --pretty=format:%as,%h,%ae%gd"]
    output = subprocess.check_output(cmd_delimiter.join(commands), shell=True)
    data = []
    csv_data = csv.reader(output.decode().splitlines())
    for line in csv_data:
        data.append(dtos.CommitDTO(
            commit_date=line[0], commit_hash=line[1], commit_author=line[2],
        ))
    print('parsed', len(data), 'commits')
    return data


def get_cmd_delimiter():
    if os.name == 'nt':
        return '&'
    else:
        return ';'


def format_commit_stats_line(commit_hash: str, line: str) -> dtos.CommitStats:
    additions = line[0]
    deletions = line[1]
    file = line[2]
    if '{' in file and '}' in file and '=>' in file:
        # file moved, save only new location
        first = file.split('{')[0]
        last = file.split('}')[-1]
        file = (first + last).replace('\\\\', r'\\')
    return dtos.CommitStats(commit=commit_hash, additions=additions, deletions=deletions, file=file)


def parse_commit_stats_from_folder(project_folder: str, repository: Repository):
    unparsed_commits = core.get_unparsed_commits(repository)
    commands = [f"cd {project_folder}", "git diff {commit_1} {commit_2} --numstat"]
    cmd_delimiter = get_cmd_delimiter()
    cmd_str = cmd_delimiter.join(commands)
    print('reading filestats for', len(unparsed_commits), 'commits')
    for commit in unparsed_commits:
        ready_stats: list[dtos.CommitStats] = []
        prev_hash = commit.prev if commit.prev is not None else ''
        command = cmd_str.format(commit_1=commit.commit_hash, commit_2=prev_hash)
        output = subprocess.check_output(command, shell=True)
        output_lines = [line.split() for line in output.decode().splitlines()]
        for line in output_lines:
            ready_stats.append(format_commit_stats_line(commit.commit_hash, line))
        core.insert_commit_stats(commit, ready_stats)
        commit.stats_parsed = True
        commit.save()


def generate_stats_from_file(zip_name: str):
    project_folder, project_name = unpack_zip(zip_name)
    file_source, _ = RepositorySource.objects.get_or_create(name='file')
    repository, _ = Repository.objects.get_or_create(name=project_name, source=file_source)
    commits: list[dtos.CommitDTO] = parse_commits_from_folder(project_folder)
    core.insert_commits(repository, commits)
    parse_commit_stats_from_folder(project_folder, repository)
