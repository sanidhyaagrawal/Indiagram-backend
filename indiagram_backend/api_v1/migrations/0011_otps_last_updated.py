# Generated by Django 3.0.8 on 2020-08-03 18:50

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api_v1', '0010_auto_20200803_2132'),
    ]

    operations = [
        migrations.AddField(
            model_name='otps',
            name='last_updated',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
