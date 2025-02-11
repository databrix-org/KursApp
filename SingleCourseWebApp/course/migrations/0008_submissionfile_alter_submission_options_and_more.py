# Generated by Django 5.1.3 on 2025-01-14 12:47

import course.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0007_alter_exercise_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubmissionFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(help_text='A file submitted by the student', upload_to=course.models.get_submission_file_path, validators=[course.models.validate_file_size])),
                ('description', models.CharField(blank=True, help_text='Optional description of the file', max_length=255)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['uploaded_at'],
            },
        ),
        migrations.AlterModelOptions(
            name='submission',
            options={'ordering': ['-submitted_at']},
        ),
        migrations.RemoveField(
            model_name='submission',
            name='submission_file',
        ),
        migrations.AddField(
            model_name='submission',
            name='feedback',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name='submission',
            index=models.Index(fields=['exercise', 'student'], name='course_subm_exercis_2d9cef_idx'),
        ),
        migrations.AddIndex(
            model_name='submission',
            index=models.Index(fields=['submitted_at'], name='course_subm_submitt_911280_idx'),
        ),
        migrations.AddField(
            model_name='submissionfile',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='course.submission'),
        ),
        migrations.AddIndex(
            model_name='submissionfile',
            index=models.Index(fields=['submission'], name='course_subm_submiss_055dbc_idx'),
        ),
        migrations.AddIndex(
            model_name='submissionfile',
            index=models.Index(fields=['uploaded_at'], name='course_subm_uploade_5458f7_idx'),
        ),
    ]
