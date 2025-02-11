from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from course.models import Course
import json

class ManageCourseViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            difficulty_level=1,
            instructor=self.user
        )
        self.client.login(username='testuser', password='testpass123')
        self.manage_url = reverse('course:manage', args=[self.course.id])
        self.update_url = reverse('course:update_overview')
        self.publish_url = reverse('course:toggle_publish')

    def test_manage_course_view(self):
        """Test that the manage course view loads correctly"""
        response = self.client.get(self.manage_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'course/ManageCourse.html')
        self.assertContains(response, 'Test Course')
        self.assertContains(response, 'Test Description')

    def test_update_course_title(self):
        """Test updating course title"""
        data = {
            'field': 'title',
            'value': 'Updated Course Title'
        }
        response = self.client.post(
            self.update_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, 'Updated Course Title')

    def test_update_course_description(self):
        """Test updating course description"""
        data = {
            'field': 'description',
            'value': 'Updated course description with more details'
        }
        response = self.client.post(
            self.update_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.course.refresh_from_db()
        self.assertEqual(self.course.description, 'Updated course description with more details')

    def test_update_course_difficulty(self):
        """Test updating course difficulty level"""
        data = {
            'field': 'difficulty_level',
            'value': '2'
        }
        response = self.client.post(
            self.update_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.course.refresh_from_db()
        self.assertEqual(self.course.difficulty_level, 2)

    def test_toggle_course_publish(self):
        """Test toggling course publish state"""
        # Initial state should be unpublished
        self.assertFalse(self.course.is_published)

        # Toggle to published
        response = self.client.post(self.publish_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['is_published'])
        self.course.refresh_from_db()
        self.assertTrue(self.course.is_published)

        # Toggle back to unpublished
        response = self.client.post(self.publish_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['is_published'])
        self.course.refresh_from_db()
        self.assertFalse(self.course.is_published)

    def test_validation_course_title(self):
        """Test course title validation"""
        # Test empty title
        data = {
            'field': 'title',
            'value': ''
        }
        response = self.client.post(
            self.update_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Title is required', response.json()['message'])

        # Test too short title
        data['value'] = 'ab'
        response = self.client.post(
            self.update_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('at least 3 characters', response.json()['message'])

        # Test too long title
        data['value'] = 'a' * 101
        response = self.client.post(
            self.update_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('less than 100 characters', response.json()['message'])

    def test_validation_course_description(self):
        """Test course description validation"""
        # Test empty description
        data = {
            'field': 'description',
            'value': ''
        }
        response = self.client.post(
            self.update_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Description is required', response.json()['message'])

        # Test too short description
        data['value'] = 'short'
        response = self.client.post(
            self.update_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('at least 10 characters', response.json()['message'])

    def test_validation_difficulty_level(self):
        """Test difficulty level validation"""
        # Test invalid difficulty level
        data = {
            'field': 'difficulty_level',
            'value': '5'
        }
        response = self.client.post(
            self.update_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('valid difficulty level', response.json()['message']) 