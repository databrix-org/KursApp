from django.core.management.base import BaseCommand
from django.conf import settings
from course.models import CustomUserModel, Course, Enrollment, Module, Lesson, Exercise
from django.db import transaction

class Command(BaseCommand):
    help = 'Sets up development data including users and a course'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        if not settings.DEBUG:
            self.stdout.write(self.style.ERROR('This command can only be run in DEBUG mode'))
            return

        # Create instructor
        instructor, created = CustomUserModel.objects.get_or_create(
            username='instructor',
            defaults={
                'email': 'instructor@example.com',
                'first_name': 'Test',
                'last_name': 'Instructor',
                'is_instructor': True,
                'is_student': False,
            }
        )
        if created:
            instructor.set_password('instructor123')
            instructor.save()
            self.stdout.write(self.style.SUCCESS('Created instructor user'))

        # Create student
        student, created = CustomUserModel.objects.get_or_create(
            username='student',
            defaults={
                'email': 'student@example.com',
                'first_name': 'Test',
                'last_name': 'Student',
                'is_student': True,
            }
        )
        if created:
            student.set_password('student123')
            student.save()
            self.stdout.write(self.style.SUCCESS('Created student user'))

        # Create course
        course, created = Course.objects.get_or_create(
            title='Development Test Course',
            defaults={
                'description': 'This is a test course for development',
                'instructor': instructor,
                'difficulty_level': 1,
                'is_published': True,
                'max_members': 3,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created test course'))

        # Create modules
        module1, created = Module.objects.get_or_create(
            course=course,
            title='Introduction to Programming',
            defaults={
                'description': 'Basic programming concepts',
                'order': 1,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created module 1'))

        module2, created = Module.objects.get_or_create(
            course=course,
            title='Advanced Topics',
            defaults={
                'description': 'Advanced programming concepts',
                'order': 2,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created module 2'))

        # Create lessons for module 1
        lessons_data = [
            {
                'module': module1,
                'title': 'Getting Started',
                'order': 1,
                'lesson_type': 'reading',
                'lesson_content': 'Welcome to the course! In this lesson...',
            },
            {
                'module': module1,
                'title': 'Your First Program',
                'order': 2,
                'lesson_type': 'video',
                'lesson_content': 'Video lesson about writing your first program',
            },
            {
                'module': module2,
                'title': 'Data Structures',
                'order': 1,
                'lesson_type': 'reading',
                'lesson_content': 'Learn about different data structures...',
            },
            {
                'module': module2,
                'title': 'Programming Exercise',
                'order': 2,
                'lesson_type': 'exercise',
                'lesson_content': 'Practice what you learned',
            },
        ]

        for lesson_data in lessons_data:
            lesson, created = Lesson.objects.get_or_create(
                module=lesson_data['module'],
                title=lesson_data['title'],
                defaults={
                    'order': lesson_data['order'],
                    'lesson_type': lesson_data['lesson_type'],
                    'lesson_content': lesson_data['lesson_content'],
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created lesson: {lesson.title}')
                )

                # Create exercise for the exercise-type lesson
                if lesson.lesson_type == 'exercise':
                    exercise, created = Exercise.objects.get_or_create(
                        lesson=lesson,
                        defaults={
                            'exercise_type': 'programming',
                        }
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'Created exercise for: {lesson.title}')
                        )

        # Create enrollment for student
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            course=course,
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Enrolled student in course')) 
