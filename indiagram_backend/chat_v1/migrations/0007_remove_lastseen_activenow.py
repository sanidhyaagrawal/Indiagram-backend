# Generated by Django 3.0.8 on 2020-09-29 06:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat_v1', '0006_auto_20200929_1040'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lastseen',
            name='activeNow',
        ),
    ]
