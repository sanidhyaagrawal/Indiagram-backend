# Generated by Django 3.0.8 on 2020-08-03 09:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v1', '0006_auto_20200729_1025'),
    ]

    operations = [
        migrations.CreateModel(
            name='otps',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=300)),
                ('otp', models.CharField(max_length=300)),
            ],
        ),
    ]
