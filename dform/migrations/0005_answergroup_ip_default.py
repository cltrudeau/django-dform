# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-01-15 17:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dform', '0004_answergroup_ip_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answergroup',
            name='ip_address',
            field=models.GenericIPAddressField(default='0.0.0.0', verbose_name='IP Address'),
        ),
    ]
