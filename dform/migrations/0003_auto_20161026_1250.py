# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-26 12:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dform', '0002_survey_use_recaptcha'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='field_key',
            field=models.CharField(choices=[('tx', 'Text'), ('mt', 'MultiText'), ('em', 'Email'), ('dr', 'Dropdown'), ('rd', 'Radio'), ('ch', 'Checkboxes'), ('rt', 'Rating'), ('in', 'Integer'), ('fl', 'Float')], max_length=2),
        ),
    ]