# Generated by Django 5.1.4 on 2025-01-18 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='weeklyTimeLimitHours',
            field=models.IntegerField(default=0),
        ),
    ]
