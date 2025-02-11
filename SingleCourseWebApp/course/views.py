"""
Course management application views.

This module contains all the views for the course management application, organized into
logical groups based on functionality:

1. Authentication and User Management
2. Course Management
3. Module Management
4. Lesson Management
5. Exercise Management
6. Group Management
7. Progress Tracking

Each view is properly documented with docstrings explaining its purpose, parameters,
and return values.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate
from django.conf import settings
from .models import (
    Course, Enrollment, LessonProgress, Lesson, Exercise, Group, Module,
    ExerciseMaterial, JupyterLabImage, CustomUserModel, Submission, SubmissionFile
)
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from functools import wraps
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib import messages
from django.db import models, transaction
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.db.models import Count, Max, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.files.base import ContentFile
from .forms import JupyterExerciseUploadForm, ExerciseMaterialForm
from django.core.cache import cache
import shutil
import os
import logging
import re
import uuid

logger = logging.getLogger(__name__)

# Utility Functions

def ensure_directory_exists(path):
    """Create directory if it doesn't exist.
    
    Args:
        path: The directory path to create.
    """
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Created directory: {path}")

def copy_file_safely(src, dest):
    """Copy file with proper error handling.
    
    Args:
        src: Source file path.
        dest: Destination file path.
        
    Returns:
        bool: True if copy was successful, False otherwise.
    """
    try:
        if os.path.exists(src):
            ensure_directory_exists(os.path.dirname(dest))
            shutil.copy2(src, dest)
            logger.info(f"Copied file from {src} to {dest}")
            return True
        else:
            logger.warning(f"Source file does not exist: {src}")
            return False
    except Exception as e:
        logger.error(f"Error copying file from {src} to {dest}: {str(e)}")
        return False

def copy_exercise_files(group, exercise):
    """Copy exercise files to the group's directory.
    
    Copies the entire exercise directory from exercise_files to user_directories/group_name/
    
    Args:
        group: Group model instance.
        exercise: Exercise model instance.
    """
    if not exercise:
        return

    # Get source and destination paths
    source_dir = os.path.join(settings.EXERCISE_FILES_ROOT, exercise.lesson.title)
    group_dir = os.path.join(settings.USER_FILES_ROOT, f'group_{group.id}')
    
    try:
        # Create group directory if it doesn't exist
        os.makedirs(group_dir, exist_ok=True)
        
        # If source directory exists, copy it to the group directory
        if os.path.exists(source_dir):
            dest_dir = os.path.join(group_dir, exercise.lesson.title)
            
            # Remove destination directory if it exists
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            
            # Copy the entire directory
            shutil.copytree(source_dir, dest_dir)
            logger.info(f"Copied exercise directory from {source_dir} to {dest_dir}")
        else:
            logger.warning(f"Source directory does not exist: {source_dir}")
    
    except Exception as e:
        logger.error(f"Error copying exercise files for group {group.id}: {str(e)}")

def rename_exercise_directories(old_title, new_title, exercise):
    """Rename exercise directories when lesson title changes.
    
    Args:
        old_title: Previous lesson title
        new_title: New lesson title
        exercise: Exercise model instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Rename in exercise files directory
        old_exercise_dir = os.path.join(settings.EXERCISE_FILES_ROOT, old_title)
        new_exercise_dir = os.path.join(settings.EXERCISE_FILES_ROOT, new_title)
        
        if os.path.exists(old_exercise_dir):
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(new_exercise_dir), exist_ok=True)
            # Rename the directory
            shutil.move(old_exercise_dir, new_exercise_dir)
            logger.info(f"Renamed exercise directory from {old_exercise_dir} to {new_exercise_dir}")
        
        # Rename in all group directories
        course = exercise.lesson.module.course
        for group in course.groups.all():
            old_group_dir = os.path.join(settings.USER_FILES_ROOT, f'group_{group.id}', old_title)
            new_group_dir = os.path.join(settings.USER_FILES_ROOT, f'group_{group.id}', new_title)
            
            if os.path.exists(old_group_dir):
                # Create parent directory if it doesn't exist
                os.makedirs(os.path.dirname(new_group_dir), exist_ok=True)
                # Rename the directory
                shutil.move(old_group_dir, new_group_dir)
                logger.info(f"Renamed group directory from {old_group_dir} to {new_group_dir}")
        
        return True
    except Exception as e:
        logger.error(f"Error renaming exercise directories: {str(e)}")
        return False

def course_context_processor(request):
    """Add course to all template contexts.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        dict: A dictionary containing the course object if it exists.
    """
    try:
        course = Course.objects.first()
    except Course.DoesNotExist:
        course = None
    return {'course': course}

def require_enrollment_and_group(view_func):
    """Decorator to check if user is enrolled in course and belongs to a group.
    
    Args:
        view_func: The view function to be decorated.
        
    Returns:
        function: The wrapped view function that checks enrollment and group membership.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Extract course_id from kwargs, or from lesson_id if present
        course_id = kwargs.get('course_id')
        if not course_id and 'lesson_id' in kwargs:
            lesson = get_object_or_404(Lesson, id=kwargs['lesson_id'])
            course_id = lesson.module.course.id
            
        course = get_object_or_404(Course, id=course_id)
        
        # Check enrollment
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return redirect('course:home')
            
        # Check group membership
        if not Group.objects.filter(course=course, members=request.user).exists():
            return redirect('course:home')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Authentication and User Management Views

@login_required
def dev_login(request):
    """Development-only login view.
    
    This view is only available in DEBUG mode and should not be used in production.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        HttpResponse: The rendered login template or redirect to home.
    """
    if not settings.DEBUG:
        return redirect('course:home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('course:home')
    return render(request, 'course/dev_login.html')

# Course Management Views

@login_required
def home(request):
    """Home page view showing course information and enrollment status.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        HttpResponse: The rendered home template with course context.
    """
    course = Course.objects.first()
    if not course:
        return render(request, 'course/course_not_published.html')
    
    is_enrolled = False
    user_group = None
    available_groups = []
    is_instructor = False
    
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        user_group = Group.objects.filter(course=course, members=request.user).first()
        is_instructor = course.instructor == request.user or request.user.is_instructor

        # Get available groups (not full and user not already in them)
        if is_enrolled and not user_group:
            available_groups = Group.objects.filter(course=course)\
                .annotate(member_count=models.Count('members'))\
                .filter(member_count__lt=course.max_members)\
                .exclude(members=request.user)
    
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'user_group': user_group,
        'available_groups': available_groups,
        'is_instructor': is_instructor,
    }
    return render(request, 'course/homepage/home.html', context)

@login_required
def course_enroll(request, course_id):
    """Enroll a student in a course.
    
    Args:
        request: The HTTP request object.
        course_id: The ID of the course to enroll in.
        
    Returns:
        HttpResponse: Redirect to home page.
    """
    course = Course.objects.get(id=course_id)
    if request.method == 'POST':
        Enrollment.objects.get_or_create(
            student=request.user,
            course=course
        )
        return redirect('course:home')
    return redirect('course:home')

@login_required
@require_enrollment_and_group
def course_overview(request, course_id):
    """Display course overview with modules, lessons, and progress.
    
    This view shows the course structure and the student's progress through
    the course content, including completed lessons and next lesson to take.
    
    Args:
        request: The HTTP request object.
        course_id: The ID of the course to display.
        
    Returns:
        HttpResponse: The rendered course overview template.
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Check if course is published or user is instructor
    if not course.is_published and not request.user.is_instructor:
        return render(request, 'course/course_not_published.html')
    
    # Get all modules with their lessons, ordered by their respective order fields
    modules = course.modules.prefetch_related('lessons').all()
    
    # Get the user's progress for all lessons in the course
    lesson_progress = LessonProgress.objects.filter(
        student=request.user,
        lesson__module__course=course
    ).select_related('lesson')
    
    # Create a progress lookup dictionary for quick access
    progress_lookup = {
        progress.lesson_id: progress 
        for progress in lesson_progress
    }
    
    # Prepare module data with lessons and progress
    modules_data = []
    for module in modules:
        lessons_data = [{
            'lesson': lesson,
            'progress': progress_lookup.get(lesson.id)
        } for lesson in module.lessons.all()]
        
        modules_data.append({
            'module': module,
            'lessons': lessons_data
        })

    # Calculate total and completed lessons
    total_lessons = sum(len(module.lessons.all()) for module in modules)
    completed_lessons = len([p for p in lesson_progress if p.is_completed])
    
    # Update debug data to include the counts
    debug_data = {
        'course_title': course.title,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'modules': [{
            'title': module_data['module'].title,
            'lessons': [{
                'title': lesson_data['lesson'].title,
                'id': lesson_data['lesson'].id,
                'order': lesson_data['lesson'].order,
                'duration': lesson_data['lesson'].duration,
                'is_completed': bool(lesson_data['progress'] and lesson_data['progress'].is_completed)
            } for lesson_data in module_data['lessons']]
        } for module_data in modules_data]
    }
    
    # Find the first incomplete lesson
    first_incomplete_lesson = None
    for module in modules:
        for lesson in module.lessons.all():
            if lesson.id not in progress_lookup or not progress_lookup[lesson.id].is_completed:
                first_incomplete_lesson = lesson
                break
        if first_incomplete_lesson:
            break
    
    # If all lessons are complete, use the last lesson
    if not first_incomplete_lesson and modules:
        last_module = modules.last()
        if last_module:
            first_incomplete_lesson = last_module.lessons.last()

    context = {
        'course_title': course.title,
        'modules_data': modules_data,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'debug_data_json': json.dumps(debug_data, cls=DjangoJSONEncoder),
        'continue_lesson': first_incomplete_lesson,
    }
    return render(request, 'course/learningpage/learn.html', context)

@login_required
def manage_course(request, course_id):
    """Manage course settings and configuration.
    
    Args:
        request: The HTTP request object.
        course_id: The ID of the course to manage.
        
    Returns:
        HttpResponse: The rendered course management template.
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is admin for course settings
    is_admin = request.user.is_superuser
    
    if request.method == 'POST' and request.GET.get('action') == 'update_settings':
        # Only allow admins to update course settings
        if not is_admin:
            return JsonResponse({
                'success': False,
                'error': 'Only administrators can modify course settings'
            }, status=403)
            
        try:
            # Update basic course settings
            course.title = request.POST.get('title', course.title)
            course.description = request.POST.get('description', course.description)
            course.max_members = int(request.POST.get('max_members', course.max_members))
            course.difficulty_level = int(request.POST.get('difficulty_level', course.difficulty_level))
            course.is_published = request.POST.get('is_published') == 'true'
            
            # Handle domain name
            domain_name = request.POST.get('domain_name', '').strip()
            if domain_name:
                # Basic domain validation
                if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-_.]+[a-zA-Z0-9]$', domain_name):
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid domain name format'
                    }, status=400)
                course.domain_name = domain_name
            else:
                course.domain_name = None
            
            # Handle JupyterLab image
            jupyterlab_image = request.POST.get('jupyterlab_image', '').strip()
            if jupyterlab_image:
                # Create or update JupyterLab image
                jupyterlab_image_obj, created = JupyterLabImage.objects.get_or_create(
                    course=course,
                    defaults={
                        'image_name': jupyterlab_image,
                    }
                )
                
                if not created:
                    # Update existing image
                    jupyterlab_image_obj.image_name = jupyterlab_image
                    jupyterlab_image_obj.save()
            
            course.save()
            
            response_data = {
                'success': True,
                'message': 'Course settings updated successfully',
                'domain_name': course.domain_name
            }
            
            # Add JupyterLab image info to response if it exists
            if hasattr(course, 'jupyterlab_image'):
                response_data['jupyterlab_image'] = {
                    'name': course.jupyterlab_image.image_name
                }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    if is_admin:
        modules = Module.objects.filter(course=course).order_by('order')
    else:
        modules = Module.objects.filter(course=course, instructor=request.user).order_by('order')
    
    context = {
        'course': course,
        'modules': modules,
        'option': request.GET.get('option', 'overview'),
        'is_admin': is_admin  # Add admin status to context
    }

    if request.GET.get('option') == 'overview' or request.GET.get('option') == None:
        return render(request, 'course/editcourse/manage_settings.html', context)
    elif request.GET.get('option') == 'modules':
        return render(request, 'course/editcourse/manage_modules.html', context)
    elif request.GET.get('option') == 'groups':
        # Add group-specific context
        groups = Group.objects.filter(course=course).prefetch_related('members')
        students = CustomUserModel.objects.filter(
            is_student=True,
            enrollment__course=course
        ).exclude(
            course_groups__course=course
        ).order_by('first_name', 'last_name')
        
        context.update({
            'groups': groups,
            'students': students,
            'max_members': course.max_members
        })
        return render(request, 'course/editcourse/manage_groups.html', context)


# Module Management Views

@login_required
@require_POST
def create_module(request, course_id):
    """Create a new module in the course.
    
    Args:
        request: The HTTP request object.
        course_id: The ID of the course to create the module in.
        
    Returns:
        JsonResponse: The created module data or error message.
    """
    if not request.user.is_instructor:
        raise PermissionDenied("Only instructors can create modules")
    
    try:
        # Get the course
        course = get_object_or_404(Course, id=course_id)
        
        # Parse the JSON data from request
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid JSON data: {str(e)}'
            }, status=400)
        
        # Validate required fields
        title = data.get('title')
        if not title:
            return JsonResponse({
                'success': False,
                'error': 'Title is required'
            }, status=400)
        
        description = data.get('description', '')
        
        # Get the last order number
        last_order = Module.objects.filter(course=course).aggregate(Max('order'))['order__max']
        order = (last_order or 0) + 1
        
        # Create the module with the current instructor
        module = Module.objects.create(
            course=course,
            instructor=request.user,  # Assign current instructor
            title=title,
            description=description,
            order=order
        )
        
        return JsonResponse({
            'success': True,
            'module_id': module.id,
            'module_title': module.title
        })
        
    except Exception as e:
        import traceback
        print(f"Error creating module: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_POST
def delete_module(request, module_id):
    """Delete a module from the course.
    
    Args:
        request: The HTTP request object.
        module_id: The ID of the module to delete.
        
    Returns:
        JsonResponse: Success message or error.
    """
    try:
        module = get_object_or_404(Module, id=module_id)
        
        # Check if user can edit this module
        if not module.can_edit(request.user):
            raise PermissionDenied("You don't have permission to delete this module")
            
        module.delete()
        return JsonResponse({
            'success': True,
            'message': 'Module deleted successfully'
        })
    except PermissionDenied as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=403)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(['GET'])
def get_module(request, module_id):
    """Get module data including its lessons.
    
    Args:
        request: The HTTP request object.
        module_id: The ID of the module to retrieve.
        
    Returns:
        JsonResponse: The module data including lessons.
    """
    if not request.user.is_instructor:
        raise PermissionDenied("Only instructors can view module details")
    
    module = get_object_or_404(Module, id=module_id)
    # Include edit permission in response
    can_edit = module.can_edit(request.user)
    if not can_edit:
        raise PermissionDenied("You are not the instructor of this module")
    
    lessons = module.lessons.all().order_by('order')
    

    
    return JsonResponse({
        'success': True,
        'module': {
            'id': module.id,
            'title': module.title,
            'description': module.description,
            'instructor': {
                'id': module.instructor.id,
                'name': module.instructor.get_full_name()
            },
            'lessons': [{
                'id': lesson.id,
                'title': lesson.title,
                'lesson_type': lesson.lesson_type,
                'lesson_content': lesson.lesson_content,
                'video_file': lesson.video_file.url if lesson.video_file else None,
                'exercise_type': lesson.lesson_exercise.exercise_type if hasattr(lesson, 'lesson_exercise') else None,
            } for lesson in lessons]
        }
    })

@login_required
@require_http_methods(['POST'])
def update_module(request, module_id):
    """Update a module's details.
    
    Args:
        request: The HTTP request object.
        module_id: The ID of the module to update.
        
    Returns:
        JsonResponse: The updated module data or error message.
    """
    module = get_object_or_404(Module, id=module_id)
    
    # Check if user can edit this module
    if not module.can_edit(request.user):
        return JsonResponse({
            'success': False,
            'error': "You don't have permission to edit this module"
        }, status=403)
    
    data = json.loads(request.body)
    title = data.get('title')
    description = data.get('description')
    
    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)
    
    module.title = title
    module.description = description
    module.save()
    
    return JsonResponse({
        'success': True,
        'module': {
            'id': module.id,
            'title': module.title,
            'description': module.description,
            'can_edit': True
        }
    })

@login_required
@require_POST
def update_module_order(request):
    """Update the order of modules in a course.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        JsonResponse: Success message or error.
    """
    if not request.user.is_instructor:
        return JsonResponse({
            'success': False,
            'error': 'Only instructors can reorder modules'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        modules = data.get('modules', [])
        print(modules)
        if request.user.is_superuser:
            with transaction.atomic():
                for module_data in modules:
                    Module.objects.filter(
                        id=module_data['id'],
                    ).update(order=module_data['order'])
        else:
            return JsonResponse({'success': False, 'error': 'You are not authorized to reorder modules, please contact the administrator.'})
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# Lesson Management Views

@login_required
@require_enrollment_and_group
def lesson_detail(request, lesson_id):
    """Display detailed view of a lesson.
    
    Args:
        request: The HTTP request object.
        lesson_id: The ID of the lesson to display.
        
    Returns:
        HttpResponse: The rendered lesson detail template.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    current_module = lesson.module
    
    # Check if course is published or user is instructor
    if not course.is_published and not request.user.is_instructor:
        return render(request, 'course/course_not_published.html')
    
    # Get or create progress for this lesson
    progress, created = LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson
    )
    
    # Get the user's progress for lessons in the current module
    lesson_progress = LessonProgress.objects.filter(
        student=request.user,
        lesson__module=current_module
    ).select_related('lesson')
    
    # Create a progress lookup dictionary for quick access
    progress_lookup = {
        progress.lesson_id: progress 
        for progress in lesson_progress
    }
    
    # Prepare only the current module's data with lessons and progress
    lessons_data = [{
        'lesson_title': lesson.title,
        'lesson_id': lesson.id,
        'progress': progress_lookup.get(lesson.id)
    } for lesson in current_module.lessons.all()]
    
    modules_data = [{
        'module': current_module,
        'lessons': lessons_data
    }]
    
    # Base response data
    response_data = {
        'lesson_id': lesson.id,
        'title': lesson.title,
        'lesson_type': lesson.lesson_type,
        'progress': progress,
        'modules_data': modules_data,
        'current_module': current_module  # Add current module to context
    }
    
    # Add type-specific content
    if lesson.lesson_type == 'reading':
        response_data['lesson_content'] = lesson.lesson_content
    elif lesson.lesson_type == 'video':
        response_data['video_url'] = lesson.video_file.url if lesson.video_file else None
    elif lesson.lesson_type == 'exercise':
        # Get the exercise object
        try:
            exercise = lesson.lesson_exercise
            # Get user's group
            group = Group.objects.filter(course=lesson.module.course, members=request.user).first()
            
            # Get latest submission for the group
            latest_submission = None
            if group:
                latest_submission = Submission.objects.filter(
                    exercise=exercise,
                    student__course_groups=group
                ).order_by('-submitted_at').first()
            
            # Get the notebook file path from exercise
            notebook_name = None
            if exercise.exercise_type == 'jupyter' and exercise.file:
                notebook_name = os.path.basename(exercise.file.name)
                # Clean up the notebook name to remove any path artifacts
                notebook_name = notebook_name.replace('\\', '/').split('/')[-1]
            
            response_data.update({
                'lesson_content': lesson.lesson_content,
                'exercise': exercise,
                'exercise_type': exercise.exercise_type,
                'latest_submission': latest_submission,
                'notebook_name': notebook_name,  # Add cleaned notebook name
                'exercise_name': lesson.title,  # Add exercise name explicitly
            })
        except Exercise.DoesNotExist:
            # Handle case where exercise doesn't exist
            response_data.update({
                'lesson_content': lesson.lesson_content,
                'exercise': None,
                'error_message': 'Exercise content is not available yet.'
            })
    
    # Add MEDIA_URL to the context
    response_data['MEDIA_URL'] = settings.MEDIA_URL
    
    return render(request, 'course/learningpage/lesson_base.html', response_data)

@login_required
@require_http_methods(['GET'])
def get_lesson(request, lesson_id):
    """Get lesson data for editing.
    
    Args:
        request: The HTTP request object.
        lesson_id: The ID of the lesson to retrieve.
        
    Returns:
        JsonResponse: The lesson data including content and materials.
    """
    if not request.user.is_instructor:
        raise PermissionDenied
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    response_data = {
        'success': True,
        'lesson': {
            'id': lesson.id,
            'title': lesson.title,
            'lesson_type': lesson.lesson_type,
            'lesson_content': lesson.lesson_content,
            'duration': lesson.duration.total_seconds() // 60,  # Convert to minutes
            'video_file': lesson.video_file.url if lesson.video_file else None,
        }
    }
    
    if lesson.lesson_type == 'exercise' and hasattr(lesson, 'lesson_exercise'):
        exercise = lesson.lesson_exercise
        response_data['lesson']['exercise_type'] = exercise.exercise_type
        
        # Add Jupyter notebook specific data
        if exercise.exercise_type == 'jupyter':
            response_data['lesson'].update({
                'jupyter_file': exercise.file.url if exercise.file else None,
                'jupyter_file_name': exercise.file.name if exercise.file else None,
                'materials': [{
                    'id': material.id,
                    'file_url': material.file.url,
                    'file_name': material.file.name.split('/')[-1],
                    'description': material.description
                } for material in exercise.materials.all()] if hasattr(exercise, 'materials') else []
            })
    
    return JsonResponse(response_data)

@login_required
@require_POST
def create_lesson(request, module_id):
    """Create a new lesson in a module."""
    if not request.user.is_instructor:
        raise PermissionDenied
    
    module = get_object_or_404(Module, id=module_id)
    
    try:
        # Generate unique lesson name with UUID prefix
        uuid_prefix = str(uuid.uuid4())[:8]  # Get first 8 characters of UUID
        base_name = "New Lesson"
        unique_title = f"{base_name} [{uuid_prefix}]"

        last_order = module.lessons.aggregate(models.Max('order'))['order__max'] or 0
        
        lesson = Lesson.objects.create(
            module=module,
            title=unique_title,
            lesson_type='reading',
            order=last_order + 1,
            duration=timedelta(minutes=10)
        )
        
        return JsonResponse({
            'success': True,
            'lesson_id': lesson.id,
            'lesson_title': lesson.title,
            'lesson_type': lesson.lesson_type
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_POST
def delete_lesson(request, lesson_id):
    """Delete a lesson and clean up associated files.
    
    Args:
        request: The HTTP request object.
        lesson_id: The ID of the lesson to delete.
        
    Returns:
        JsonResponse: Success message or error.
    """
    if not request.user.is_instructor:
        raise PermissionDenied
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    try:
        with transaction.atomic():
            # Get paths to clean up before deleting the lesson
            exercise_files_path = None
            if hasattr(lesson, 'lesson_exercise'):
                exercise = lesson.lesson_exercise
                if exercise.exercise_type == 'jupyter':
                    # Path to exercise files
                    exercise_files_path = os.path.join(settings.EXERCISE_FILES_ROOT, lesson.title)
                    
                    # Get all groups to clean up their directories
                    course = lesson.module.course
                    groups = course.groups.all()
                    
                    # Clean up group directories
                    for group in groups:
                        group_path = os.path.join(settings.USER_FILES_ROOT, f'group_{group.id}', lesson.title)
                        if os.path.exists(group_path):
                            try:
                                shutil.rmtree(group_path)
                                logger.info(f"Deleted group directory: {group_path}")
                            except Exception as e:
                                logger.error(f"Error deleting group directory {group_path}: {str(e)}")
            
            # Delete the lesson (this will cascade delete the exercise and materials)
            lesson.delete()
            
            # Clean up exercise files directory after successful lesson deletion
            if exercise_files_path and os.path.exists(exercise_files_path):
                try:
                    shutil.rmtree(exercise_files_path)
                    logger.info(f"Deleted exercise files directory: {exercise_files_path}")
                except Exception as e:
                    logger.error(f"Error deleting exercise files directory {exercise_files_path}: {str(e)}")
            
            return JsonResponse({'success': True})
            
    except Exception as e:
        logger.error(f"Error deleting lesson: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(['POST'])
def save_lesson(request, lesson_id):
    """Save lesson content and settings.
    
    Args:
        request: The HTTP request object.
        lesson_id: The ID of the lesson to save.
        
    Returns:
        JsonResponse: Success message or error.
    """
    try:
        lesson = get_object_or_404(Lesson, id=lesson_id)
        old_title = lesson.title  # Store old title for directory renaming
        
        # Log request data for debugging
        print(f"Saving lesson {lesson_id}")
        print(f"POST data: {request.POST}")
        print(f"Files: {request.FILES}")
        print(f"Files count: {len(request.FILES)}")
        for key, value in request.FILES.items():
            print(f"File {key}: {value.name} ({value.size} bytes)")
        
        with transaction.atomic():
            # Update basic lesson info
            new_title = request.POST.get('title', lesson.title)
            title_changed = new_title != old_title
            lesson.title = new_title
            lesson.lesson_type = request.POST.get('lesson_type', lesson.lesson_type)
            lesson.duration = timedelta(minutes=int(request.POST.get('duration', 10)))

            # Handle video file upload
            if lesson.lesson_type == 'video' and 'video_file' in request.FILES:
                video_file = request.FILES['video_file']
                print(f"Uploading video file: {video_file.name}")
                
                # Delete old video file if exists
                if lesson.video_file:
                    lesson.video_file.delete(save=False)
                
                # Save new video file
                lesson.video_file = video_file

            # Update lesson content for all lesson types
            content = request.POST.get('content', '')
            lesson.lesson_content = content
            
            if lesson.lesson_type == 'exercise':
                exercise_type = request.POST.get('exercise_type')
                print(f"Exercise type: {exercise_type}")
                
                # Get or create exercise object using the correct related name
                try:
                    exercise = lesson.lesson_exercise
                    print(f"Found existing exercise: {exercise.id}")
                except Exercise.DoesNotExist:
                    exercise = Exercise(lesson=lesson)
                    print("Creating new exercise")
                
                # Update exercise type
                exercise.exercise_type = exercise_type
                exercise.save()
                
                # Handle Jupyter notebook specific files
                if exercise_type == 'jupyter':
                    print("Processing Jupyter exercise files")
                    
                    # If title changed, rename directories
                    if title_changed:
                        logger.info(f"Lesson title changed from '{old_title}' to '{new_title}', renaming directories")
                        if not rename_exercise_directories(old_title, new_title, exercise):
                            raise Exception("Failed to rename exercise directories")
                    
                    # Handle notebook file
                    if 'jupyter_file' in request.FILES:
                        jupyter_file = request.FILES['jupyter_file']
                        print(f"Uploading Jupyter file: {jupyter_file.name}")
                        
                        # Delete old file if exists
                        if exercise.file:
                            exercise.file.delete(save=False)
                        
                        exercise.file = jupyter_file
                        exercise.save()
                        
                        # Get all groups for this course and copy files
                        course = lesson.module.course
                        groups = course.groups.all()
                        for group in groups:
                            copy_exercise_files(group, exercise)
                    
                    # Handle materials
                    if 'materials' in request.FILES:
                        try:
                            # Get list of all material files
                            materials = request.FILES.getlist('materials')
                            print(f"Processing {len(materials)} material files")
                            
                            # Remove old materials if new ones are being uploaded
                            if materials:
                                print("Removing old materials")
                                exercise.materials.all().delete()
                            
                            # Add new materials
                            for material in materials:
                                print(f"Adding material: {material.name} ({material.size} bytes)")
                                try:
                                    material_obj = ExerciseMaterial.objects.create(
                                        exercise=exercise,
                                        file=material,
                                        description=f"Material: {material.name}"
                                    )
                                    print(f"Successfully created material: {material_obj.id}")
                                except Exception as e:
                                    print(f"Error creating material {material.name}: {str(e)}")
                                    raise
                            
                            # Copy all files to group directories after materials are added
                            for group in groups:
                                copy_exercise_files(group, exercise)
                                
                        except Exception as e:
                            print(f"Error processing materials: {str(e)}")
                            raise
            
            lesson.save()
            
            # Prepare response data including file information
            response_data = {
                'success': True,
                'message': 'Lesson saved successfully',
                'files': {}
            }
            
            # Add file information to response if this is an exercise
            if lesson.lesson_type == 'exercise' and hasattr(lesson, 'lesson_exercise'):
                exercise = lesson.lesson_exercise
                if exercise.exercise_type == 'jupyter':
                    response_data['files'] = {
                        'jupyter_file': {
                            'name': exercise.file.name.split('/')[-1] if exercise.file else None,
                            'url': exercise.file.url if exercise.file else None
                        },
                        'materials': [{
                            'id': material.id,
                            'file_name': material.file.name.split('/')[-1],
                            'file_url': material.file.url,
                            'description': material.description
                        } for material in exercise.materials.all()] if exercise.materials.exists() else []
                    }
            
            return JsonResponse(response_data)
            
    except Exception as e:
        import traceback
        print("Error saving lesson:")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_POST
def complete_lesson(request, lesson_id):
    """Mark a lesson as complete or incomplete.
    
    This view handles toggling the completion status of a lesson and
    determines the next lesson in sequence if the lesson is marked as complete.
    
    Args:
        request: The HTTP request object.
        lesson_id: The ID of the lesson to mark.
        
    Returns:
        JsonResponse: The updated completion status and next lesson ID.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    progress = LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson
    )[0]
    
    # Toggle the completion status
    progress.is_completed = not progress.is_completed
    progress.save()
    
    # Only find next lesson if we're marking as complete
    next_lesson_id = None
    if progress.is_completed:
        # Find the next lesson
        current_module = lesson.module
        current_course = current_module.course
        
        # Try to get next lesson in the same module
        next_lesson = Lesson.objects.filter(
            module=current_module,
            order__gt=lesson.order
        ).order_by('order').first()
        
        # If no next lesson in current module, try first lesson of next module
        if not next_lesson:
            next_module = current_course.modules.filter(
                order__gt=current_module.order
            ).order_by('order').first()
            
            if next_module:
                next_lesson = next_module.lessons.order_by('order').first()
            else:
                next_lesson = lesson
        
        next_lesson_id = next_lesson.id if next_lesson else None
    else:
        next_lesson_id = lesson_id
    return JsonResponse({
        'success': True,
        'is_completed': progress.is_completed,
        'next_lesson_id': next_lesson_id
    })

@login_required
@require_http_methods(["POST"])
def reorder_lessons(request, module_id):
    """Update the order of lessons in a module.
    
    Args:
        request: The HTTP request object.
        module_id: The ID of the module containing the lessons.
        
    Returns:
        JsonResponse: Success message or error.
    """
    try:
        data = json.loads(request.body)
        lessons = data.get('lessons', [])
        
        # Get the module
        module = get_object_or_404(Module, id=module_id)
        
        # Update the order of each lesson
        for lesson_data in lessons:
            lesson_id = lesson_data['lesson_id']
            new_order = lesson_data['order']
            
            Lesson.objects.filter(
                id=lesson_id,
                module_id=module_id
            ).update(order=new_order)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Lesson order updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

# Exercise Management Views

@login_required
def create_jupyter_exercise(request, module_id, lesson_id):
    """Create a new Jupyter notebook exercise with associated materials.
    
    Args:
        request: The HTTP request object.
        module_id: The ID of the module containing the lesson.
        lesson_id: The ID of the lesson to create the exercise for.
        
    Returns:
        HttpResponse: The rendered exercise creation template or redirect.
    """
    if not request.user.is_instructor:
        messages.error(request, "Only instructors can create exercises.")
        return redirect('course:home')

    module = get_object_or_404(Module, id=module_id)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    course = module.course  # Get the course from the module

    if request.method == 'POST':
        form = JupyterExerciseUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the exercise
                    exercise = Exercise.objects.create(
                        lesson=lesson,
                        file=form.cleaned_data['notebook'],
                        exercise_type='jupyter'
                    )

                    # Handle multiple material files
                    materials = request.FILES.getlist('materials')
                    for material_file in materials:
                        ExerciseMaterial.objects.create(
                            exercise=exercise,
                            file=material_file,
                            description=f"Material: {material_file.name}"
                        )

                    # Handle JupyterLab image if provided
                    if form.cleaned_data.get('jupyterlab_image'):
                        JupyterLabImage.objects.create(
                            exercise=exercise,
                            image_file=form.cleaned_data['jupyterlab_image'],
                            version=form.cleaned_data['image_version'],
                            requirements=form.cleaned_data.get('requirements', '')
                        )

                messages.success(request, "Exercise created successfully!")
                return redirect('course:manage_lesson', lesson_id=lesson.id)

            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error creating exercise: {str(e)}")
    else:
        form = JupyterExerciseUploadForm()

    context = {
        'form': form,
        'module': module,
        'lesson': lesson,
        'course': course,  # Add course to context
    }
    return render(request, 'course/create_jupyter_exercise.html', context)

@login_required
def edit_jupyter_exercise(request, exercise_id):
    """Edit an existing Jupyter notebook exercise.
    
    Args:
        request: The HTTP request object.
        exercise_id: The ID of the exercise to edit.
        
    Returns:
        HttpResponse: The rendered exercise edit template or redirect.
    """
    if not request.user.is_instructor:
        messages.error(request, "Only instructors can edit exercises.")
        return redirect('course:home')

    exercise = get_object_or_404(Exercise, id=exercise_id, exercise_type='jupyter')
    lesson = exercise.lesson
    course = lesson.module.course  # Get the course from the lesson's module

    # Pre-fill the form with existing data
    initial_data = {
        'notebook': exercise.file,
        'requirements': exercise.jupyterlab_image.requirements if hasattr(exercise, 'jupyterlab_image') else '',
        'image_version': exercise.jupyterlab_image.version if hasattr(exercise, 'jupyterlab_image') else ''
    }

    if request.method == 'POST':
        form = JupyterExerciseUploadForm(request.POST, request.FILES, initial=initial_data)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update exercise file if new one is provided
                    if 'notebook' in request.FILES:
                        exercise.file = form.cleaned_data['notebook']
                        exercise.save()

                    # Handle materials
                    if 'materials' in request.FILES:
                        # Remove old materials
                        exercise.materials.all().delete()
                        # Add new materials
                        materials = request.FILES.getlist('materials')
                        for material_file in materials:
                            ExerciseMaterial.objects.create(
                                exercise=exercise,
                                file=material_file,
                                description=f"Material: {material_file.name}"
                            )

                    # Handle JupyterLab image
                    if form.cleaned_data.get('jupyterlab_image'):
                        if hasattr(exercise, 'jupyterlab_image'):
                            # Update existing image
                            image = exercise.jupyterlab_image
                            image.image_file = form.cleaned_data['jupyterlab_image']
                            image.version = form.cleaned_data['image_version']
                            image.requirements = form.cleaned_data.get('requirements', '')
                            image.save()
                        else:
                            # Create new image
                            JupyterLabImage.objects.create(
                                exercise=exercise,
                                image_file=form.cleaned_data['jupyterlab_image'],
                                version=form.cleaned_data['image_version'],
                                requirements=form.cleaned_data.get('requirements', '')
                            )

                messages.success(request, "Exercise updated successfully!")
                return redirect('course:manage_lesson', lesson_id=lesson.id)

            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error updating exercise: {str(e)}")
    else:
        form = JupyterExerciseUploadForm(initial=initial_data)

    context = {
        'form': form,
        'exercise': exercise,
        'lesson': lesson,
        'course': course,  # Add course to context
    }
    return render(request, 'course/edit_jupyter_exercise.html', context)

@login_required
def check_upload_progress(request):
    """Check the progress of a file upload.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        JsonResponse: The current upload progress or error.
    """
    if request.method == 'GET':
        upload_id = request.GET.get('upload_id')
        if upload_id:
            progress = cache.get(f'upload_progress_{upload_id}')
            if progress:
                return JsonResponse({
                    'total': progress['total'],
                    'uploaded': progress['uploaded'],
                    'progress': (progress['uploaded'] / progress['total']) * 100 if progress['total'] > 0 else 0
                })
    return JsonResponse({'error': 'No upload progress found'}, status=404)

@login_required
def create_jupyter_exercise_ajax(request, module_id, lesson_id):
    """AJAX endpoint for creating a Jupyter notebook exercise.
    
    Args:
        request: The HTTP request object.
        module_id: The ID of the module containing the lesson.
        lesson_id: The ID of the lesson to create the exercise for.
        
    Returns:
        JsonResponse: Success message or error.
    """
    if not request.user.is_instructor:
        return JsonResponse({'success': False, 'error': 'Only instructors can create exercises.'})

    module = get_object_or_404(Module, id=module_id)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)

    if request.method == 'POST':
        form = JupyterExerciseUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the exercise
                    exercise = Exercise.objects.create(
                        lesson=lesson,
                        file=form.cleaned_data['notebook'],
                        exercise_type='jupyter'
                    )

                    # Handle multiple material files
                    materials = request.FILES.getlist('materials')
                    for material_file in materials:
                        ExerciseMaterial.objects.create(
                            exercise=exercise,
                            file=material_file,
                            description=f"Material: {material_file.name}"
                        )

                    # Handle JupyterLab image if provided
                    if form.cleaned_data.get('jupyterlab_image'):
                        JupyterLabImage.objects.create(
                            exercise=exercise,
                            image_file=form.cleaned_data['jupyterlab_image'],
                            version=form.cleaned_data['image_version'],
                            requirements=form.cleaned_data.get('requirements', '')
                        )

                return JsonResponse({'success': True})

            except ValidationError as e:
                return JsonResponse({'success': False, 'error': str(e)})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid form data'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# Group Management Views

@login_required
def manage_groups(request, course_id):
    """Manage course groups and their members.
    
    Args:
        request: The HTTP request object.
        course_id: The ID of the course to manage groups for.
        
    Returns:
        HttpResponse: The rendered group management template.
    """
    course = get_object_or_404(Course, id=course_id)
    if not (request.user.is_instructor or request.user.is_superuser or course.instructor == request.user):
        raise PermissionDenied
    
    groups = Group.objects.filter(course=course).annotate(
        member_count=Count('members'),
        last_active=Max('members__last_login')
    ).order_by('-created_at')
    
    students = CustomUserModel.objects.filter(
        is_student=True,
        enrollment__course=course
    ).exclude(
        groups__course=course
    ).order_by('first_name', 'last_name')
    
    context = {
        'course': course,
        'groups': groups,
        'students': students,
        'active_tab': 'groups',
        'max_members': course.max_members
    }
    return render(request, 'course/editcourse/manage_groups.html', context)

@login_required
def manage_create_group(request, course_id):
    """Create a new group as an instructor.
    
    Args:
        request: The HTTP request object.
        course_id: The ID of the course to create the group in.
        
    Returns:
        JsonResponse: The created group data or error message.
    """
    course = get_object_or_404(Course, id=course_id)
    if not (request.user.is_instructor or request.user.is_superuser or course.instructor == request.user):
        raise PermissionDenied
    
    try:
        with transaction.atomic():
            group = Group.objects.create(course=course)
            
            # Copy exercise files for all exercises in the course
            for module in course.modules.all():
                for lesson in module.lessons.all():
                    try:
                        exercise = lesson.lesson_exercise
                        if exercise and exercise.exercise_type == 'jupyter':
                            logger.info(f"Copying files for Jupyter exercise in lesson {lesson.title}")
                            copy_exercise_files(group, exercise)
                    except Exercise.DoesNotExist:
                        continue
                    except Exception as e:
                        logger.error(f"Error copying files for lesson {lesson.title}: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'id': group.id,
                'member_count': 0,
                'created_at': group.created_at.strftime('%Y-%m-%d %H:%M')
            })
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Failed to create group'}, status=500)

@login_required
@require_POST
def delete_group(request, course_id, group_id):
    """Delete a group.
    
    Args:
        request: The HTTP request object.
        course_id: The ID of the course containing the group.
        group_id: The ID of the group to delete.
        
    Returns:
        JsonResponse: Success message or error.
    """
    course = get_object_or_404(Course, id=course_id)
    if not (request.user.is_instructor or request.user.is_superuser or course.instructor == request.user):
        raise PermissionDenied
    
    group = get_object_or_404(Group, id=group_id, course=course)
    try:
        group.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Failed to delete group'}, status=500)

@login_required
@require_POST
def add_group_member(request, course_id, group_id):
    """Add a student to a group.
    
    Args:
        request: The HTTP request object.
        course_id: The ID of the course containing the group.
        group_id: The ID of the group to add the member to.
        
    Returns:
        JsonResponse: Success message or error.
    """
    course = get_object_or_404(Course, id=course_id)
    if not (request.user.is_instructor or request.user.is_superuser or course.instructor == request.user):
        raise PermissionDenied
    
    group = get_object_or_404(Group, id=group_id, course=course)
    student_id = request.POST.get('student_id')
    
    try:
        with transaction.atomic():
            student = get_object_or_404(CustomUserModel, id=student_id, is_student=True)
            group.add_member(student)
            
            # Copy exercise files for all exercises in the course
            for module in course.modules.all():
                for lesson in module.lessons.all():
                    try:
                        exercise = lesson.lesson_exercise
                        if exercise and exercise.exercise_type == 'jupyter':
                            logger.info(f"Copying files for Jupyter exercise in lesson {lesson.title}")
                            copy_exercise_files(group, exercise)
                    except Exercise.DoesNotExist:
                        continue
                    except Exception as e:
                        logger.error(f"Error copying files for lesson {lesson.title}: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'member_count': group.member_count
            })
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Failed to add member'}, status=500)

@login_required
@require_POST
def remove_group_member(request, course_id, group_id):
    """Remove a student from a group.
    
    Args:
        request: The HTTP request object.
        course_id: The ID of the course containing the group.
        group_id: The ID of the group to remove the member from.
        
    Returns:
        JsonResponse: Success message or error.
    """
    course = get_object_or_404(Course, id=course_id)
    if not (request.user.is_instructor or request.user.is_superuser or course.instructor == request.user):
        raise PermissionDenied
    
    group = get_object_or_404(Group, id=group_id, course=course)
    student_id = request.POST.get('student_id')
    
    try:
        student = get_object_or_404(CustomUserModel, id=student_id)
        group.remove_member(student)
        return JsonResponse({
            'success': True,
            'member_count': group.member_count
        })
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Failed to remove member'}, status=500)

@login_required
def get_group_members(request, group_id):
    """Get the list of members in a group.
    
    Args:
        request: The HTTP request object.
        group_id: The ID of the group to get members for.
        
    Returns:
        JsonResponse: List of group members or error message.
    """
    group = get_object_or_404(Group, id=group_id)
    if not (request.user.is_instructor or request.user.is_superuser or group.course.instructor == request.user):
        raise PermissionDenied
    
    try:
        members = group.members.all().order_by('first_name', 'last_name')
        members_data = [{
            'id': member.id,
            'full_name': member.get_full_name(),
            'email': member.email,  # This is already included
            'last_active': member.last_login.strftime('%Y-%m-%d %H:%M') if member.last_login else 'Never'
        } for member in members]
        
        return JsonResponse(members_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': 'Failed to load members'}, status=500)

@login_required
def list_groups(request, course_id):
    """List all groups in a course with basic information.
    
    Args:
        request: The HTTP request object
        course_id: ID of the course to list groups for
        
    Returns:
        JsonResponse: List of groups with id, member count, and creation date
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Permission check
    #if not (request.user.is_instructor or request.user.is_superuser):
    #    return JsonResponse({
    #        'success': False,
    #        'error': 'Only instructors can view group lists'
    #    }, status=403)


    groups = Group.objects.filter(course=course).order_by('-created_at')

    group_data = [{
        'id': group.id,
        'created_at': group.created_at.strftime('%Y-%m-%d %H:%M'),
        'members': [member.get_full_name() for member in group.members.all()]
    } for group in groups]

    return JsonResponse({
        'success': True,
        'groups': group_data,
        'course_title': course.title,
        'total_groups': len(group_data)
    })


@login_required
def join_group(request, course_id):
    """Join an existing group.
    
    Args:
        request: The HTTP request object.
        course_id: The ID of the course containing the group.
        
    Returns:
        JsonResponse: Success message or error.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    try:
        data = json.loads(request.body)
        group_id = data.get('group_id')
        
        if not group_id:
            return JsonResponse({'success': False, 'error': 'Group ID is required'}, status=400)
        
        course = get_object_or_404(Course, id=course_id)
        group = get_object_or_404(Group, id=group_id, course=course)
        
        # Check if user is already in a group
        if Group.objects.filter(course=course, members=request.user).exists():
            return JsonResponse({'success': False, 'error': 'You are already in a group for this course'}, status=400)
        
        # Check if group is full
        if group.members.count() >= course.max_members:
            return JsonResponse({'success': False, 'error': 'This group is full'}, status=400)
        
        # Add user to group
        group.members.add(request.user)
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def save_exercise_materials(request, exercise_id):
    """Save exercise materials and copy them to group directories.
    
    Args:
        request: The HTTP request object.
        exercise_id: The ID of the exercise to save materials for.
        
    Returns:
        JsonResponse: Success message or error.
    """
    exercise = get_object_or_404(Exercise, id=exercise_id)
    
    if request.method == 'POST':
        form = ExerciseMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    description = form.cleaned_data['description']
                    files = request.FILES.getlist('files')  # Get multiple files
                    
                    for file in files:
                        # Create a new ExerciseMaterial instance for each file
                        material = ExerciseMaterial(
                            exercise=exercise,
                            description=description,
                            file=file
                        )
                        material.save()
                    
                    # Copy exercise files to all group directories
                    course = exercise.lesson.module.course
                    groups = course.groups.all()
                    
                    for group in groups:
                        copy_exercise_files(group, exercise)
                    
                    return JsonResponse({'status': 'success'})
            except Exception as e:
                logger.error(f"Error saving exercise materials: {str(e)}")
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
@require_POST
def delete_jupyter_file(request, lesson_id):
    """Delete the Jupyter notebook file from an exercise.
    
    Args:
        request: The HTTP request object.
        lesson_id: The ID of the lesson containing the exercise to be modified.
        
    Returns:
        JsonResponse: Success message or error.
    """
    if not request.user.is_instructor:
        return JsonResponse({
            'success': False,
            'error': 'Only instructors can delete exercise files'
        }, status=403)
    
    try:
        # Get the lesson and its associated exercise
        lesson = get_object_or_404(Lesson, id=lesson_id)
        try:
            exercise = Exercise.objects.get(lesson=lesson)
            if exercise.file:
                exercise.file.delete(save=False)  # Delete the file from storage
                exercise.file = None
                exercise.save()
                
            return JsonResponse({
                'success': True,
                'message': 'File deleted successfully'
            })
        except Exercise.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No exercise found for this lesson'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_POST
def delete_material(request, lesson_id, material_id):
    """Delete a material file from an exercise.
    
    Args:
        request: The HTTP request object.
        lesson_id: The ID of the lesson containing the exercise.
        material_id: The ID of the material to delete.
        
    Returns:
        JsonResponse: Success message or error.
    """
    if not request.user.is_instructor:
        return JsonResponse({
            'success': False,
            'error': 'Only instructors can delete exercise materials'
        }, status=403)
    
    try:
        # Get the material and verify it belongs to the correct lesson
        material = get_object_or_404(ExerciseMaterial, id=material_id)
        if material.exercise.lesson.id != lesson_id:
            raise PermissionError('Material does not belong to this lesson')
            
        # Delete the actual file from storage
        if material.file:
            material.file.delete(save=False)  # Delete file but don't save model yet
            
        # Delete the material object from database
        material.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Material deleted successfully'
        })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_POST
def submit_exercise(request, lesson_id):
    """Handle exercise submission.
    
    This view handles:
    1. Creating a submission record in the database
    2. Copying the user's work directory to the submissions directory
    3. Creating submission file records for each submitted file
    
    Args:
        request: The HTTP request object.
        lesson_id: The ID of the lesson being submitted.
        
    Returns:
        JsonResponse: Success message or error.
    """
    try:
        # Get the lesson and exercise
        lesson = get_object_or_404(Lesson, id=lesson_id)
        exercise = get_object_or_404(Exercise, lesson=lesson)
        
        # Get the user's group
        group = Group.objects.filter(course=lesson.module.course, members=request.user).first()
        if not group:
            return JsonResponse({
                'success': False,
                'error': 'You must be in a group to submit exercises'
            }, status=400)
            
        # Create submission timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Define source directory
        source_dir = os.path.join(settings.USER_FILES_ROOT, f'group_{group.id}', lesson.title)
        
        # Check if source directory exists
        if not os.path.exists(source_dir):
            return JsonResponse({
                'success': False,
                'error': 'No work found to submit'
            }, status=400)
            
        # Create submission record
        submission = Submission.objects.create(
            exercise=exercise,
            student=request.user
        )
        
        # Define destination directory
        dest_dir = os.path.join(
            settings.DATA_ROOT,
            'exercise_submissions',
            f'group_{group.id}',
            lesson.title
            #timestamp
        )
        
        # Create destination directory
        os.makedirs(dest_dir, exist_ok=True)
        
        # Copy all files from source to destination
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                src_file = os.path.join(root, file)
                # Get relative path from source_dir
                rel_path = os.path.relpath(src_file, source_dir)
                dest_file = os.path.join(dest_dir, rel_path)
                
                # Create subdirectories if needed
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                
                # Copy the file
                shutil.copy2(src_file, dest_file)
                
                # Create submission file record
                rel_path_from_media = os.path.relpath(dest_file, settings.MEDIA_ROOT)
                SubmissionFile.objects.create(
                    submission=submission,
                    file=rel_path_from_media,
                    description=f"Submitted file: {rel_path}"
                )
        
        return JsonResponse({
            'success': True,
            'submission_id': submission.id,
            'submitted_at': submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            'file_count': submission.files.count()
        })
        
    except Exception as e:
        logger.error(f"Error in submit_exercise: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# Submissions Dashboard Views

@login_required
def submissions_dashboard(request):
    """Main view for the submissions dashboard.
    
    This view handles the overview section showing exercise cards.
    Only accessible by instructors, admins, and superusers.
    Instructors can only see their own exercises.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        HttpResponse: The rendered dashboard template or redirect.
    """
    # Check if user has permission to access submissions
    if not (request.user.is_instructor or request.user.is_superuser):
        messages.error(request, "You don't have permission to access the submissions dashboard.")
        return redirect('course:home')
        
    # Get all exercises for the course
    course = Course.objects.first()
    
    # Base query for exercises
    exercises_query = Exercise.objects.filter(
        lesson__module__course=course,
        exercise_type='jupyter'
    ).select_related(
        'lesson',
        'lesson__module'
    ).annotate(
        total_groups_submitted=models.Count(
            'submissions__student__course_groups',
            distinct=True
        ),
        pending_groups=models.Count(
            'submissions__student__course_groups',
            filter=models.Q(submissions__score__isnull=True),
            distinct=True
        )
    )
    
    # Filter exercises based on user role
    if not request.user.is_superuser and not request.user.is_staff:
        # Regular instructors can only see their own exercises
        exercises_query = exercises_query.filter(
            lesson__module__instructor=request.user
        )
    
    exercises = exercises_query.order_by(
        'lesson__module__order',
        'lesson__order'
    )
    
    context = {
        'exercises': exercises,
        'active_section': 'overview',
        'is_admin': request.user.is_superuser or request.user.is_staff
    }
    return render(request, 'course/submissions/dashboard.html', context)

@login_required
def exercise_submissions(request, exercise_id):
    """View for displaying submissions for a specific exercise.
    
    Only accessible by instructors who own the exercise, admins, and superusers.
    
    Args:
        request: The HTTP request object.
        exercise_id: The ID of the exercise to show submissions for.
        
    Returns:
        HttpResponse: The rendered submissions template or JSON response.
    """
    try:
        # Get the exercise and check permissions
        exercise = get_object_or_404(Exercise, id=exercise_id)
        
        # Check if user has permission to view submissions
        if not request.user.is_instructor and not request.user.is_superuser:
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                }, status=403)
            messages.error(request, "You don't have permission to view submissions.")
            return redirect('course:home')
            
        # Check if instructor owns the exercise
        if not request.user.is_superuser and not request.user.is_staff:
            if exercise.lesson.module.instructor != request.user:
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'error': 'You can only view submissions for your own exercises'
                    }, status=403)
                messages.error(request, "You can only view submissions for your own exercises.")
                return redirect('course:submissions_dashboard')
        
        # Get all submissions
        all_submissions = Submission.objects.filter(
            exercise=exercise
        ).select_related(
            'student'
        ).prefetch_related(
            'files',
            'student__course_groups'
        )

        # Create a dictionary to store the latest submission per group
        latest_submissions = {}
        for submission in all_submissions:
            group = submission.student.course_groups.first()
            group_id = group.id if group else 0  # Use 0 for students without a group
            
            if group_id not in latest_submissions or \
               submission.submitted_at > latest_submissions[group_id].submitted_at:
                latest_submissions[group_id] = submission

        # Convert back to a list and sort by submission date
        submissions = sorted(
            latest_submissions.values(),
            key=lambda x: x.submitted_at,
            reverse=True
        )

        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
            try:
                submissions_data = []
                for submission in submissions:
                    # Get the student's group
                    group = Group.objects.filter(
                        course=exercise.lesson.module.course,
                        members=submission.student
                    ).first()
                    
                    files_data = [{
                        'url': file.file.url,
                        'name': os.path.basename(file.file.name)
                    } for file in submission.files.all()]
                    
                    submissions_data.append({
                        'id': submission.id,
                        'group': f'Group {group.id}' if group else 'No Group',
                        'submitted_at': submission.submitted_at.strftime('%Y-%m-%d %H:%M'),
                        'score': submission.score,
                        'passed': submission.passed,
                        'feedback': submission.feedback,
                        'files': files_data
                    })
                
                response_data = {
                    'success': True,
                    'exercise_title': exercise.lesson.title,
                    'submissions': submissions_data
                }
                print(submissions_data)
                return JsonResponse(response_data)
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
        
        # For regular requests, render the template
        context = {
            'exercise': exercise,
            'submissions': submissions,
            'is_admin': request.user.is_superuser or request.user.is_staff
        }
        return render(request, 'course/submissions/exercise_submissions.html', context)
        
    except Exception as e:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        messages.error(request, f"Error loading submissions: {str(e)}")
        return redirect('course:submissions_dashboard')

@login_required
def grade_submission(request, submission_id):
    """View for grading a specific submission.
    
    Args:
        request: The HTTP request object.
        submission_id: The ID of the submission to grade.
        
    Returns:
        HttpResponse: The rendered grading template or JSON response.
    """
    if not request.user.is_instructor:
        raise PermissionDenied
        
    submission = get_object_or_404(Submission, id=submission_id)
    group = submission.student.course_groups.first()
    exercise = submission.exercise
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            submission.score = float(data.get('score'))
            # passed will be auto-calculated in the model's save method
            submission.feedback = data.get('feedback')
            submission.save()
            
            return JsonResponse({
                'success': True,
                'score': submission.score,
                'passed': submission.passed,  # Include passed status in response
                'feedback': submission.feedback
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    # Get reference files if they exist
    reference_files = []
    if hasattr(exercise, 'reference_files'):
        reference_files = [{
            'url': file.file.url,
            'name': os.path.basename(file.file.name)
        } for file in exercise.reference_files.all()]
    
    # Get reference solution if it exists
    reference_solution = None
    if exercise.reference_solution:
        try:
            with exercise.reference_solution.open('r') as f:
                reference_solution = f.read()
        except Exception as e:
            logger.error(f"Error reading reference solution: {e}")
    
    context = {
        'submission': submission,
        'exercise': exercise,
        'reference_files': reference_files,
        'group': group.id if group else None,
        'reference_solution': reference_solution,
        'has_reference_solution': bool(exercise.reference_solution)
    }
    return render(request, 'course/submissions/grade_submission.html', context)

@login_required
def submission_statistics(request):
    """View for displaying submission statistics.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        HttpResponse: The rendered statistics template.
    """
    if not request.user.is_instructor:
        raise PermissionDenied
        
    course = Course.objects.first()

    # Get all groups in the course
    groups = Group.objects.filter(course=course)
    
    # Calculate statistics for each group
    group_stats = []
    for group in groups:
        # Get all submissions from group members
        submissions = Submission.objects.filter(
            exercise__lesson__module__course=course,
            student__in=group.members.all(),
            score__isnull=False  # Only include graded submissions
        )
        
        if submissions.exists():
            avg_score = submissions.aggregate(models.Avg('score'))['score__avg']
            max_score = submissions.aggregate(models.Max('score'))['score__max']
            submission_count = submissions.count()
        else:
            avg_score = 0
            max_score = 0
            submission_count = 0
            
        group_stats.append({
            'group': {
                'id': group.id,
                'members': [
                    {'name': member.get_full_name()} 
                    for member in group.members.all()
                ]
            },
            'avg_score': round(avg_score, 2) if avg_score else 0,
            'max_score': max_score,
            'submission_count': submission_count
        })
    
    context = {
        'group_stats': json.dumps(group_stats),
        'group_stats_raw': group_stats,  # For template rendering
        'active_section': 'statistics'
    }
    return render(request, 'course/submissions/statistics.html', context)



@login_required
def admin_dashboard(request):
    """Admin dashboard view for managing users and role requests.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        HttpResponse: The rendered admin dashboard template.
    """
    if not request.user.is_superuser:
        raise PermissionDenied
    # Get active tab from query parameters, default to 'users'
    active_tab = request.GET.get('tab', 'users')
    
    # Get all users except superuser
    users = CustomUserModel.objects.exclude(
        is_superuser=True
    ).select_related(
        'enrollment'
    ).order_by('date_joined')
    
    context = {
        'active_tab': active_tab,
        'users': users,
    }
    
    return render(request, 'course/adminpage/admin_dashboard.html', context)

@login_required
def admin_change_role(request):
    """Handle user role changes.
    
    Args:
        request: The HTTP request object containing user_id and new_role.
        
    Returns:
        JsonResponse: Success status and any error messages.
    """
    if not request.user.is_superuser:
        raise PermissionDenied
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
        

    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        new_role = data.get('new_role')
        
        user = get_object_or_404(CustomUserModel, id=user_id)
        
        # Update user roles based on new_role
        if new_role == 'instructor':
            user.is_instructor = True
            user.is_student = False
        elif new_role == 'student':
            user.is_instructor = False
            user.is_student = True
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully updated role for {user.get_full_name()}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_POST
def upload_reference_solution(request, exercise_id):
    """Upload a reference solution for an exercise.
    
    Args:
        request: The HTTP request object.
        exercise_id: The ID of the exercise to update.
        
    Returns:
        JsonResponse: Success message or error.
    """
    if not request.user.is_instructor:
        return JsonResponse({
            'success': False,
            'error': 'Only instructors can upload reference solutions'
        }, status=403)
    
    try:
        exercise = get_object_or_404(Exercise, id=exercise_id)
        
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file provided'
            }, status=400)
            
        file = request.FILES['file']
        
        # Validate file type
        if not file.name.endswith('.ipynb'):
            return JsonResponse({
                'success': False,
                'error': 'File must be a Jupyter notebook (.ipynb)'
            }, status=400)
            
        # Delete old reference solution if it exists
        if exercise.reference_solution:
            exercise.reference_solution.delete(save=False)
            
        # Save new reference solution
        exercise.reference_solution = file
        exercise.save()
        
        # Read the newly uploaded file for immediate display
        reference_solution = None
        try:
            with exercise.reference_solution.open('r') as f:
                reference_solution = f.read()
        except Exception as e:
            logger.error(f"Error reading uploaded reference solution: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Reference solution uploaded successfully',
            'reference_solution': reference_solution
        })
        
    except Exception as e:
        logger.error(f"Error uploading reference solution: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

