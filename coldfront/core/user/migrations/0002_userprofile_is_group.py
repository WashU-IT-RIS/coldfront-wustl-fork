# Generated by Django 3.2.20 on 2024-12-12 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="UserProfile",
            name="is_group",
            field=models.BooleanField(default=False),
        ),
    ]
