# Generated by Django 3.2.20 on 2024-10-22 23:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocation', '0006_added_allocation_linkage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='allocationattribute',
            name='value',
            field=models.CharField(max_length=8192),
        ),
        migrations.AlterField(
            model_name='historicalallocationattribute',
            name='value',
            field=models.CharField(max_length=8192),
        ),
    ]
