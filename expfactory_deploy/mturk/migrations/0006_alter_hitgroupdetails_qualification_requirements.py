# Generated by Django 4.1.3 on 2023-07-11 22:14

from django.db import migrations, models
import mturk.models


class Migration(migrations.Migration):

    dependencies = [
        ("mturk", "0005_alter_hitgroupdetails_auto_approval_delay"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hitgroupdetails",
            name="qualification_requirements",
            field=models.JSONField(default=mturk.models.default_quals),
        ),
    ]