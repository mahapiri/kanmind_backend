# Generated by Django 5.2.1 on 2025-05-14 10:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('task_app', '0007_alter_comment_task_alter_task_priority'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['created_at'], 'verbose_name': 'Comment', 'verbose_name_plural': 'Comments'},
        ),
    ]
