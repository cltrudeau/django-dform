# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-26 12:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dform', '0003_auto_20161026_1250'),
    ]

    operations = [
        migrations.AddField(
            model_name='answergroup',
            name='ip_address',
            field=models.GenericIPAddressField(default='127.0.0.1'),
        ),
    ]