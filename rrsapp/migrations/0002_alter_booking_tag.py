# Generated by Django 4.1.2 on 2024-10-18 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rrsapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='tag',
            field=models.CharField(max_length=32),
        ),
    ]
