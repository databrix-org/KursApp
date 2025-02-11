from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import (
    CustomUserModel, Course, Module, Lesson, Exercise,
    ExerciseMaterial, JupyterLabImage, Group
)
import os
import shutil
import tempfile

# Create a temporary media root for testing
TEMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class JupyterExerciseTests(TestCase):
    def setUp(self):
        # Create test user
        self.instructor = CustomUserModel.objects.create_user(
            username='testinstructor',
            email='instructor@test.com',
            password='testpass123',
            is_instructor=True
        )
        self.student = CustomUserModel.objects.create_user(
            username='teststudent',
            email='student@test.com',
            password='testpass123',
            is_student=True
        )

        # Create course and module
        self.course = Course.objects.create(
            title='Test Course',
            instructor=self.instructor
        )
        self.module = Module.objects.create(
            course=self.course,
            title='Test Module',
            order=1
        )
        self.lesson = Lesson.objects.create(
            module=self.module,
            title='Test Lesson',
            order=1,
            lesson_type='exercise'
        )

        # Create test files
        self.notebook_content = b'{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 4}'
        self.material_content = b'Test material content'
        self.image_content = b'Test image content'

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(TEMP_MEDIA_ROOT)

    def test_create_jupyter_exercise(self):
        # Test creating a Jupyter notebook exercise
        notebook_file = SimpleUploadedFile('test.ipynb', self.notebook_content)
        exercise = Exercise.objects.create(
            lesson=self.lesson,
            file=notebook_file,
            exercise_type='jupyter'
        )

        self.assertEqual(exercise.exercise_type, 'jupyter')
        self.assertTrue(exercise.file.name.endswith('.ipynb'))

    def test_file_size_validation(self):
        # Create a file larger than 1GB
        large_content = b'x' * (1024 * 1024 * 1024 + 1)  # 1GB + 1 byte
        large_file = SimpleUploadedFile('large.ipynb', large_content)

        with self.assertRaises(ValidationError):
            exercise = Exercise(
                lesson=self.lesson,
                file=large_file,
                exercise_type='jupyter'
            )
            exercise.full_clean()

    def test_exercise_materials(self):
        # Create exercise with materials
        notebook_file = SimpleUploadedFile('test.ipynb', self.notebook_content)
        exercise = Exercise.objects.create(
            lesson=self.lesson,
            file=notebook_file,
            exercise_type='jupyter'
        )

        material_file = SimpleUploadedFile('material.txt', self.material_content)
        material = ExerciseMaterial.objects.create(
            exercise=exercise,
            file=material_file,
            description='Test Material'
        )

        self.assertEqual(material.description, 'Test Material')
        self.assertTrue(os.path.exists(material.file.path))

    def test_jupyterlab_image(self):
        # Create exercise with JupyterLab image
        notebook_file = SimpleUploadedFile('test.ipynb', self.notebook_content)
        exercise = Exercise.objects.create(
            lesson=self.lesson,
            file=notebook_file,
            exercise_type='jupyter'
        )

        image_file = SimpleUploadedFile('jupyter.tar', self.image_content)
        jupyter_image = JupyterLabImage.objects.create(
            exercise=exercise,
            image_file=image_file,
            version='1.0.0'
        )

        self.assertEqual(jupyter_image.version, '1.0.0')
        self.assertTrue(os.path.exists(jupyter_image.image_file.path))

    def test_file_copying_on_group_creation(self):
        # Create exercise with all components
        notebook_file = SimpleUploadedFile('test.ipynb', self.notebook_content)
        exercise = Exercise.objects.create(
            lesson=self.lesson,
            file=notebook_file,
            exercise_type='jupyter'
        )

        material_file = SimpleUploadedFile('material.txt', self.material_content)
        material = ExerciseMaterial.objects.create(
            exercise=exercise,
            file=material_file,
            description='Test Material'
        )

        image_file = SimpleUploadedFile('jupyter.tar', self.image_content)
        jupyter_image = JupyterLabImage.objects.create(
            exercise=exercise,
            image_file=image_file,
            version='1.0.0'
        )

        # Create group and add member
        group = Group.objects.create(course=self.course)
        group.members.add(self.student)

        # Check if files were copied to the group directory
        group_dir = os.path.join(TEMP_MEDIA_ROOT, 'user_directories', f'group_{group.id}', exercise.lesson.title)
        
        # Check main exercise file
        self.assertTrue(os.path.exists(os.path.join(group_dir, 'test.ipynb')))
        
        # Check material file
        self.assertTrue(os.path.exists(os.path.join(group_dir, 'materials', 'material.txt')))
        
        # Check JupyterLab image file
        self.assertTrue(os.path.exists(os.path.join(group_dir, 'jupyterlab', 'jupyter.tar')))

    def test_create_jupyter_exercise_view(self):
        """Test the create jupyter exercise view functionality"""
        # Login as instructor
        self.client.login(username='testinstructor', password='testpass123')

        # Prepare test files
        notebook_file = SimpleUploadedFile('test.ipynb', self.notebook_content)
        material_file = SimpleUploadedFile('material.txt', self.material_content)
        image_file = SimpleUploadedFile('jupyter.tar', self.image_content)

        # Create the POST request data
        data = {
            'notebook': notebook_file,
            'materials': material_file,
            'jupyterlab_image': image_file,
            'image_version': '1.0.0',
            'requirements': 'numpy==1.21.0\npandas==1.3.0'
        }

        # Make the request
        url = f'/course/module/{self.module.id}/lesson/{self.lesson.id}/create-jupyter-exercise/'
        response = self.client.post(url, data, format='multipart')

        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['lesson_id'], self.lesson.id)

        # Verify exercise was created
        exercise = Exercise.objects.get(lesson=self.lesson)
        self.assertEqual(exercise.exercise_type, 'jupyter')
        self.assertTrue(exercise.file.name.endswith('.ipynb'))

        # Verify materials were created
        material = ExerciseMaterial.objects.get(exercise=exercise)
        self.assertTrue(material.file.name.endswith('.txt'))

        # Verify JupyterLab image was created
        image = JupyterLabImage.objects.get(exercise=exercise)
        self.assertEqual(image.version, '1.0.0')
        self.assertTrue(image.image_file.name.endswith('.tar'))

    def test_create_jupyter_exercise_validation(self):
        """Test validation in create jupyter exercise view"""
        # Login as instructor
        self.client.login(username='testinstructor', password='testpass123')

        # Test without required notebook file
        data = {
            'image_version': '1.0.0',
            'requirements': 'numpy==1.21.0'
        }

        url = f'/course/module/{self.module.id}/lesson/{self.lesson.id}/create-jupyter-exercise/'
        response = self.client.post(url, data, format='multipart')

        # Check response indicates error
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)

        # Test with invalid file type
        invalid_file = SimpleUploadedFile('test.txt', b'Not a notebook')
        data['notebook'] = invalid_file

        response = self.client.post(url, data, format='multipart')

        # Check response indicates error
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
