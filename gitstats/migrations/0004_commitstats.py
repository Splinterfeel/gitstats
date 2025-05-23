# Generated by Django 5.1.5 on 2025-04-21 15:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gitstats", "0003_alter_commit_commit_hash"),
    ]

    operations = [
        migrations.CreateModel(
            name="CommitStats",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("additions", models.IntegerField()),
                ("deletions", models.IntegerField()),
                ("file", models.CharField(db_index=True, max_length=700)),
                (
                    "commit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="gitstats.commit",
                    ),
                ),
            ],
            options={
                "db_table": "gitstats_commit_stats",
            },
        ),
    ]
