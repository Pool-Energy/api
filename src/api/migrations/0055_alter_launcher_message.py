# Generated by Django 4.2.11 on 2025-01-23 20:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0054_add_globalmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='launcher',
            name='message',
            field=models.CharField(default=None, null=True),
        ),
    ]
