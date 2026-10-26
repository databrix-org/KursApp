from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager
from datetime import timedelta
from django.core.exceptions import ValidationError
import os
import uuid
from django.utils import timezone

def validate_file_size(value):
    filesize = value.size
    if filesize > 2 * 1024 * 1024 * 1024:  # 2GB limit
        raise ValidationError("The maximum file size that can be uploaded is 2GB")
    return value

def get_jupyterlab_image_path(instance, filename):
    return os.path.join('jupyterlab_images', filename)

def get_exercise_file_path(instance, filename):
    """Generate file path for exercise files.
    
    Args:
        instance: Exercise model instance
        filename: Original filename
        
    Returns:
        str: Path where the file should be stored
    """
    return f'course/{instance.lesson.module.course_id}/exercises/{instance.pk}/{uuid.uuid4()}/{os.path.basename(filename)}'

def get_material_file_path(instance, filename):
    """Generate file path for material files.
    
    Args:
        instance: ExerciseMaterial model instance
        filename: Original filename
        
    Returns:
        str: Path where the file should be stored
    """
    return f'course/{instance.exercise.lesson.module.course_id}/materials/{uuid.uuid4()}/{os.path.basename(filename)}'

def get_submission_file_path(instance, filename):
    """Generate file path for submission files.
    
    Args:
        instance: SubmissionFile model instance
        filename: Original filename
        
    Returns:
        str: Path where the file should be stored
    """
    return f'legacy-submissions/{instance.submission_id}/{uuid.uuid4()}/{os.path.basename(filename)}'

def get_reference_solution_path(instance, filename):
    """Generate file path for reference solution files.
    
    Args:
        instance: Exercise model instance
        filename: Original filename
        
    Returns:
        str: Path where the file should be stored
    """
    return f'assessment/{instance.pk}/{uuid.uuid4()}/{os.path.basename(filename)}'

def get_ticket_image_path(instance, filename):
    """Generate file path for ticket images.
    
    Args:
        instance: Ticket model instance
        filename: Original filename
        
    Returns:
        str: Path where the file should be stored
    """
    return os.path.join('ticket_images', f'ticket_{instance.id}_{filename}')



# Create your models here.
class CustomUserModel(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("Email Address"), unique=True, max_length=255)
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    username = models.CharField(_("Username"), max_length=255, unique=True)  # Added for Shibboleth
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_instructor = models.BooleanField(default=False)
    is_student = models.BooleanField(default=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['first_name', 'last_name','is_instructor','is_student','is_staff']),
        ]

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name


# Profile Models (Optional)
class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUserModel, on_delete=models.CASCADE, related_name='student_profile')
    # Additional student-specific fields

class InstructorProfile(models.Model):
    user = models.OneToOneField(CustomUserModel, on_delete=models.CASCADE, related_name='instructor_profile')
    # Additional instructor-specific fields

# Course Model
class Course(models.Model):
    DIFFICULTY_CHOICES = (
        (1, 'Beginner'),
        (2, 'Intermediate'),
        (3, 'Advanced'),
        (4, 'Professional'),
        (5, 'Demo'),
    )
    title = models.CharField(max_length=255, default="Untitled Course")
    description = models.TextField(default="No description")
    instructor = models.ForeignKey(
        CustomUserModel, on_delete=models.PROTECT, related_name='courses',
        limit_choices_to={'is_instructor': True},
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    frontend_enabled = models.BooleanField(default=False)
    lab_url = models.URLField(blank=True)
    
    start_date = models.DateField(null=True, blank=True, help_text="Course start date")
    end_date = models.DateField(null=True, blank=True, help_text="Course end date")
    difficulty_level = models.IntegerField(
        choices=DIFFICULTY_CHOICES,
        default=1,
        help_text="Course difficulty level"
    )
    max_members = models.PositiveIntegerField(
        default=1,
        help_text="Maximum number of students allowed in a group (for group exercises)",
    )
    is_published = models.BooleanField(default=False)
    domain_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Domain name of the virtual machine where JupyterHub is hosted"
    )
    enrollment_key = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Enrollment key required for students to join the course"
    )

    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")

    def __str__(self):
        return self.title

# Enrollment Model
class Enrollment(models.Model):
    student = models.ForeignKey(
        CustomUserModel, on_delete=models.PROTECT, related_name='enrollments',
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    progress = models.FloatField(default=0.0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','course'], name='unique_course_enrollment')]

    def save(self, *args, **kwargs):
        if not self.course_id:
            raise ValidationError('An explicit course is required')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.first_name} enrolled in {self.course.title}"


# Module Model
class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    instructor = models.ForeignKey(
        CustomUserModel,
        on_delete=models.PROTECT,
        related_name='modules',
        limit_choices_to={'is_instructor': True},
        help_text="Instructor responsible for this module"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField()
    difficulty_level = models.IntegerField(
        choices=Course.DIFFICULTY_CHOICES,
        default=1,
        help_text="Module difficulty level"
    )

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['instructor']),
        ]

    def __str__(self):
        return f"{self.title} ({self.course.title})"

    def can_edit(self, user):
        """Check if a user can edit this module.
        
        Args:
            user: The user attempting to edit the module
            
        Returns:
            bool: True if the user can edit the module, False otherwise
        """
        from course.policies.access import edits_module
        return edits_module(user,self)

    def clean(self):
        super().clean()
        if self.instructor and not self.instructor.is_instructor:
            raise ValidationError({
                'instructor': 'User must be an instructor to be assigned to a module'
            })

# Lesson Model
class Lesson(models.Model):
    LESSON_TYPES = (
        ('video', 'Video Lesson'),
        ('reading', 'Reading Material'),
        ('exercise', 'Exercise'),
    )
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    lesson_type = models.CharField(
        max_length=20,
        choices=LESSON_TYPES,
        default='reading',
        help_text="Type of lesson content"
    )
    duration = models.DurationField(default=timedelta(minutes=10), help_text="Expected time to complete this lesson")
    video_file = models.FileField(
        upload_to='media/',
        blank=True,
        null=True,
        help_text="Upload video content for the lesson",
        validators=[validate_file_size]
    )
    lesson_content = models.TextField(blank=True, null=True, help_text="Main lesson content/text material")

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(
                fields=['module', 'title'],
                name='unique_lesson_title_per_module'
            )
        ]
        indexes = [
            models.Index(fields=['module', 'title']),
        ]

    def __str__(self):
        return f"{self.title} ({self.module.title})"

class Exercise(models.Model):
    EXERCISE_TYPES = (
        ('traditional', 'Traditional Exercise'),
        ('jupyter', 'Jupyter Notebook Exercise'),
    )
    lesson = models.OneToOneField(
        Lesson, 
        on_delete=models.CASCADE, 
        related_name='lesson_exercise'
    )
    file = models.FileField(
        upload_to=get_exercise_file_path,
        validators=[validate_file_size],
        help_text="Exercise file uploaded by user or group",
        null=True,
        blank=True
    )
    reference_solution = models.FileField(
        upload_to=get_reference_solution_path,
        validators=[validate_file_size],
        help_text="Reference solution for the exercise (Jupyter Notebook)",
        null=True,
        blank=True
    )
    exercise_type = models.CharField(
        max_length=20,
        choices=EXERCISE_TYPES,
        default='traditional',
        help_text="Type of exercise"
    )
    maximum_points = models.PositiveIntegerField(
        default=10,
        help_text="Maximum points students can earn from the exercise"
    )
    pass_points = models.PositiveIntegerField(
        default=0,
        help_text="Minimum points required for students to pass the exercise"
    )
    version = models.PositiveIntegerField(default=1)
    jupyterhub_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="URL for JupyterHub notebook (optional)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['lesson', 'exercise_type']),
        ]

    def __str__(self):
        return f"{self.lesson.title} ({self.get_exercise_type_display()})"

    def clean(self):
        super().clean()
        if self.exercise_type == 'jupyter' and self.file and not self.file.name.endswith('.ipynb'):
            raise ValidationError("Jupyter notebook exercises must use .ipynb files")
        if self.reference_solution and not self.reference_solution.name.endswith('.ipynb'):
            raise ValidationError("Reference solution must be a Jupyter notebook (.ipynb) file")
        if self.maximum_points < self.pass_points:
            raise ValidationError("Maximum points must be greater than or equal to pass points")

class ExerciseMaterial(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='materials')
    file = models.FileField(
        upload_to=get_material_file_path,
        validators=[validate_file_size],
        help_text="Additional material file for the exercise"
    )
    description = models.CharField(max_length=255, help_text="Brief description of the material")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} for {self.exercise.lesson.title}"

class JupyterLabImage(models.Model):
    course = models.OneToOneField(
        Course, 
        on_delete=models.CASCADE, 
        related_name='jupyterlab_image'
    )
    image_name = models.CharField(
        max_length=255,
        help_text="Docker Hub image name (e.g., 'jupyter/datascience-notebook:latest')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"JupyterLab image for {self.course.title} ({self.image_name})"

class Group(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    group_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Sequential group number starting from 1, automatically assigned"
    )
    members = models.ManyToManyField(
        CustomUserModel,
        related_name='course_groups',
        limit_choices_to={'is_student': True},
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    lab_url = models.URLField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['course']),
            models.Index(fields=['created_at']),
            models.Index(fields=['course', 'group_number']),
        ]
        ordering = ['course', 'group_number']
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        constraints = [
            models.UniqueConstraint(
                fields=['course', 'group_number'],
                name='unique_group_number_per_course'
            )
        ]

    def __str__(self):
        return f"Group {self.group_number} - {self.course.title} ({self.members.count()} members)"

    def _get_next_group_number(self):
        """Get the next available group number for this course."""
        existing_numbers = set(
            Group.objects.filter(course=self.course)
            .exclude(pk=self.pk)  # Exclude current instance if updating
            .exclude(group_number__isnull=True)  # Exclude groups without numbers
            .values_list('group_number', flat=True)
        )
        
        # Find the first available number starting from 1
        number = 1
        while number in existing_numbers:
            number += 1
        return number

    def clean(self):
        # Skip member validation for new groups (not yet saved)
        if not self.pk:
            return
            
        if self.members.count() > self.course.max_members:
            raise ValidationError({
                'members': f"Group cannot have more than {self.course.max_members} members"
            })
        
        # Check for existing memberships in ANY group for this course
        for member in self.members.all():
            other_groups = Group.objects.filter(
                course=self.course,
                members=member
            ).exclude(pk=self.pk)
            
            if other_groups.exists():
                raise ValidationError({
                    'members': f'Student {member.get_full_name()} is already in another group for this course'
                })
            
            if not self.course.enrollments.filter(student=member).exists():
                raise ValidationError({
                    'members': f'Student {member.get_full_name()} is not enrolled in the course'
                })

    def save(self, *args, **kwargs):
        # Auto-assign group number if not set
        if self.group_number is None:
            self.group_number = self._get_next_group_number()
        
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def member_count(self):
        return self.members.count()

    def can_add_member(self, student):
        """Check if a student can be added to this group"""
        if self.members.count() >= self.course.max_members:
            return False, "Group is full"
        
        if student.course_groups.filter(course=self.course).exists():
            return False, "Student is already in another group"
        
        if not self.course.enrollments.filter(student=student).exists():
            return False, "Student is not enrolled in the course"
        
        return True, None

    def add_member(self, student):
        from course.services.enrollment import join
        return join(student,self)

    def remove_member(self, student):
        from course.services.enrollment import leave
        return leave(student,self)

# Submission Model
class Submission(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name='submissions')
    student = models.ForeignKey(CustomUserModel, on_delete=models.PROTECT, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(Group, on_delete=models.PROTECT, null=True, blank=True, related_name='submission_snapshots')
    roster = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=16, default='accepted', choices=[(x,x) for x in ['pending','validating','accepted','rejected']])
    accepted_at = models.DateTimeField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True)
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True)
    exercise_version = models.PositiveIntegerField(default=1)
    material_manifest = models.JSONField(default=list, blank=True)
    deadline_date = models.DateField(null=True, blank=True)
    maximum_points = models.PositiveIntegerField(null=True, blank=True)
    pass_points = models.PositiveIntegerField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['exercise', 'student']),
            models.Index(fields=['submitted_at']),
            models.Index(fields=['passed']),
        ]

    def __str__(self):
        return f"{self.student.get_full_name()}'s submission for {self.exercise.lesson.title}"

    def clean(self):
        super().clean()
        # Verify student is in a group
        group = Group.objects.filter(
            course=self.exercise.lesson.module.course,
            members=self.student
        ).first()
        if not group:
            raise ValidationError("Student must be in a group to submit exercises")
            
    def save(self, *args, **kwargs):
        # If score is set, determine if passed based on exercise pass_points
        if self.score is not None:
            self.passed = self.score >= (self.pass_points if self.pass_points is not None else self.exercise.pass_points)
        super().save(*args, **kwargs)

class SubmissionFile(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(
        upload_to=get_submission_file_path,
        validators=[validate_file_size],
        help_text="A file submitted by the student",
        max_length=255
    )
    description = models.CharField(max_length=255, blank=True, help_text="Optional description of the file")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']
        indexes = [
            models.Index(fields=['submission']),
            models.Index(fields=['uploaded_at']),
        ]

    def __str__(self):
        return f"File {self.file.name} for {self.submission}"

# Lesson Progress Model
class LessonProgress(models.Model):
    student = models.ForeignKey(
        CustomUserModel, 
        on_delete=models.CASCADE, 
        related_name='lesson_progress',
    )
    lesson = models.ForeignKey(
        Lesson, 
        on_delete=models.CASCADE, 
        related_name='student_progress'
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    time_spent = models.DurationField(default=timedelta(minutes=0))

    class Meta:
        unique_together = ('student', 'lesson')
        indexes = [
            models.Index(fields=['student', 'lesson']),
            models.Index(fields=['is_completed']),
        ]

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.lesson.title} Progress"

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    )

    user = models.ForeignKey(
        CustomUserModel,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    course = models.ForeignKey(Course, on_delete=models.PROTECT, null=True, blank=True, related_name="support_tickets")
    subject = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(
        upload_to=get_ticket_image_path,
        null=True,
        blank=True,
        help_text="Optional image to help describe the issue",
        validators=[validate_file_size]
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_to = models.ForeignKey(
        CustomUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        limit_choices_to={'is_staff': True, 'is_superuser': True}
    )
    resolution_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject} ({self.status})"

    def can_edit_status(self, user):
        """Check if a user can edit the ticket status."""
        return user.is_staff or user.is_instructor



class CourseStaff(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='staff_memberships')
    user = models.ForeignKey(CustomUserModel, on_delete=models.PROTECT, related_name='teaching_memberships')
    role = models.CharField(max_length=16, choices=[('owner','Owner'),('instructor','Instructor')], default='instructor')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['course','user'],name='unique_course_staff')]

class TeamMembership(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='team_membership')
    group = models.ForeignKey(Group, on_delete=models.PROTECT, related_name='enrolled_memberships')

class NotebookAccess(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='notebook_access')
    confirmed = models.BooleanField(default=False)
    confirmed_by = models.ForeignKey(CustomUserModel,on_delete=models.SET_NULL,null=True,blank=True)

class Asset(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    category = models.CharField(max_length=16,choices=[(x,x) for x in ['course','notebooks','assessment','support']])
    course = models.ForeignKey(Course,on_delete=models.PROTECT,null=True,blank=True,related_name='assets')
    lesson = models.ForeignKey(Lesson,on_delete=models.PROTECT,null=True,blank=True,related_name='assets')
    ticket = models.ForeignKey(Ticket,on_delete=models.PROTECT,null=True,blank=True,related_name='assets')
    submission = models.ForeignKey(Submission,on_delete=models.PROTECT,null=True,blank=True,related_name='assets')
    owner = models.ForeignKey(CustomUserModel,on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    legacy_source = models.CharField(max_length=512,null=True,blank=True,unique=True)
    staging_key = models.CharField(max_length=512,blank=True)
    object_key = models.CharField(max_length=512,blank=True)
    size = models.PositiveBigIntegerField(default=0)
    sha256 = models.CharField(max_length=64,blank=True)
    content_type = models.CharField(max_length=128,default='application/octet-stream')
    status = models.CharField(max_length=16,default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class GradeRevision(models.Model):
    is_legacy_snapshot = models.BooleanField(default=False)
    submission = models.ForeignKey(Submission,on_delete=models.PROTECT,related_name='grade_history')
    grader = models.ForeignKey(CustomUserModel,on_delete=models.PROTECT,null=True,blank=True)
    score = models.FloatField()
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Invitation(models.Model):
    token = models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    email = models.EmailField()
    course = models.ForeignKey(Course,on_delete=models.PROTECT,null=True,blank=True)
    role = models.CharField(max_length=16,default='student',choices=[('student','Student'),('instructor','Instructor')])
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True,blank=True)

class Identity(models.Model):
    issuer = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    user = models.ForeignKey(CustomUserModel,on_delete=models.PROTECT,related_name='external_identities')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['issuer','subject'],name='unique_external_identity')]

class Job(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    kind = models.CharField(max_length=32)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=16,default='pending')
    attempts = models.PositiveIntegerField(default=0)
    error = models.CharField(max_length=255,blank=True)
    updated_at = models.DateTimeField(auto_now=True)
