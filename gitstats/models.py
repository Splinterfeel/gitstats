from django.db import models


class RepositorySource(models.Model):
    class Meta:
        db_table = 'gitstats_repository_source'

    name = models.CharField(max_length=255, unique=True)


class Repository(models.Model):
    class Meta:
        db_table = 'gitstats_repository'

    name = models.CharField(max_length=300, unique=True)
    source = models.ForeignKey("RepositorySource", on_delete=models.CASCADE, null=True)
    gitlab_project_id = models.IntegerField(null=True, unique=True)

    def __str__(self):
        return f"[{self.source.name}] {self.name}"


class Author(models.Model):
    class Meta:
        db_table = 'gitstats_author'

    name = models.CharField(max_length=300, unique=True)

    def __str__(self):
        return self.name


class Commit(models.Model):
    class Meta:
        db_table = 'gitstats_commit'

    repository = models.ForeignKey("Repository", on_delete=models.CASCADE)
    commit_date = models.DateField()
    commit_hash = models.CharField(max_length=150, unique=True)
    author = models.ForeignKey("Author", on_delete=models.CASCADE)
    stats_parsed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.commit_date}: {self.commit_hash}, {self.author.name}"


class CommitStats(models.Model):
    class Meta:
        db_table = 'gitstats_commit_stats'

    commit = models.ForeignKey("Commit", on_delete=models.CASCADE)
    additions = models.IntegerField()
    deletions = models.IntegerField()
    file = models.CharField(max_length=700, db_index=True)
