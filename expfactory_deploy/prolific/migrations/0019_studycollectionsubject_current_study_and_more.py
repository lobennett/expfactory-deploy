# Generated by Django 4.1.3 on 2024-03-18 21:25

from django.db import migrations, models
import django.db.models.deletion
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ("prolific", "0018_studycollection_failure_to_start_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="studycollectionsubject",
            name="current_study",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="prolific.study",
            ),
        ),
        migrations.AddField(
            model_name="studycollectionsubject",
            name="ttcc_flagged_at",
            field=model_utils.fields.MonitorField(
                default=None, monitor="status", null=True, when={"flagged"}
            ),
        ),
        migrations.AddField(
            model_name="studycollectionsubject",
            name="ttcc_warned_at",
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="studycollectionsubject",
            name="ttfs_warned_at",
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="studysubject",
            name="failed_at",
            field=model_utils.fields.MonitorField(
                default=None,
                monitor="status",
                null=True,
                when={"failed", "kicked", "flagged"},
            ),
        ),
        migrations.AddField(
            model_name="studysubject",
            name="status",
            field=model_utils.fields.StatusField(
                choices=[
                    ("n/a", "n/a"),
                    ("not-started", "not-started"),
                    ("started", "started"),
                    ("completed", "completed"),
                    ("failed", "failed"),
                    ("redo", "redo"),
                    ("kicked", "kicked"),
                    ("flagged", "flagged"),
                ],
                default="n/a",
                max_length=100,
                no_check_for_status=True,
            ),
        ),
        migrations.AddField(
            model_name="studysubject",
            name="status_reason",
            field=model_utils.fields.StatusField(
                choices=[
                    ("n/a", "n/a"),
                    ("study-timer", "study-timer"),
                    ("initial-timer", "initial-timer"),
                    ("collection-timer", "collection-timer"),
                ],
                default="n/a",
                max_length=100,
                no_check_for_status=True,
            ),
        ),
        migrations.AddField(
            model_name="studysubject",
            name="warned_at",
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name="studycollectionsubject",
            name="failed_at",
            field=model_utils.fields.MonitorField(
                default=None, monitor="status", null=True, when={"failed", "kicked"}
            ),
        ),
        migrations.AlterField(
            model_name="studycollectionsubject",
            name="status",
            field=model_utils.fields.StatusField(
                choices=[
                    ("n/a", "n/a"),
                    ("study-timer", "study-timer"),
                    ("initial-timer", "initial-timer"),
                    ("collection-timer", "collection-timer"),
                ],
                default="n/a",
                max_length=100,
                no_check_for_status=True,
            ),
        ),
    ]