# Generated by Django 5.1.5 on 2025-04-21 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gitstats", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="commit",
            name="stats_parsed",
            field=models.BooleanField(default=False),
        ),
    ]
