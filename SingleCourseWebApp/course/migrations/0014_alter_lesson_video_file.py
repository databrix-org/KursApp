# Generated by Django 5.1.3 on 2025-02-03 12:36

import course.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0013_alter_lesson_video_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='video_file',
            field=models.FileField(blank=True, help_text='Upload video content for the lesson', null=True, upload_to='media/', validators=[course.models.validate_file_size]),
        ),
    ]
