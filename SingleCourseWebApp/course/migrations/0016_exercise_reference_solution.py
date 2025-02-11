# Generated by Django 5.1.3 on 2025-02-11 09:13

import course.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0015_lesson_course_less_module__3c7196_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='reference_solution',
            field=models.FileField(blank=True, help_text='Reference solution for the exercise (Jupyter Notebook)', null=True, upload_to=course.models.get_reference_solution_path, validators=[course.models.validate_file_size]),
        ),
    ]
