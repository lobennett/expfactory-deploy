# Generated by Django 4.1.3 on 2024-03-25 18:57

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("prolific", "0022_studycollection_failure_to_start_warning_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="studycollection",
            name="failure_to_strat_grace_interval",
            field=models.DurationField(
                blank=True,
                default=datetime.timedelta(0),
                help_text="hh:mm:ss - Time from previous warning to kick from study. If set to 0 nothing is done instead.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="studycollection",
            name="screener_for",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="prolific.studycollection",
            ),
        ),
        migrations.AddField(
            model_name="studycollection",
            name="screener_rejection_message",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="studysubject",
            name="prolific_session_id",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="studycollection",
            name="time_to_start_first_study",
            field=models.DurationField(
                blank=True,
                help_text="hh:mm:ss - Upon adding participant to a study collection, they have this long to start the first study before being sent a warning message.",
                null=True,
            ),
        ),
    ]