# Generated by Django 3.0.8 on 2020-10-01 04:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_v1', '0018_auto_20201001_1026'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sessiontoken',
            old_name='token',
            new_name='sessionToken',
        ),
    ]
