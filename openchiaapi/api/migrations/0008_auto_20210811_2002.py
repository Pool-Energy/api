# Generated by Django 3.2.6 on 2021-08-11 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_auto_20210809_2035'),
    ]

    operations = [
        migrations.AddField(
            model_name='launcher',
            name='email',
            field=models.EmailField(default=None, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='launcher',
            name='notify_missing_partials_hours',
            field=models.IntegerField(default=1, null=True),
        ),
    ]
