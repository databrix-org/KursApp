from django.db import migrations

def preserve(apps,schema_editor):
    Course=apps.get_model('course','Course');Staff=apps.get_model('course','CourseStaff')
    Module=apps.get_model('course','Module');Enrollment=apps.get_model('course','Enrollment')
    Group=apps.get_model('course','Group');Membership=apps.get_model('course','TeamMembership')
    Submission=apps.get_model('course','Submission')
    for c in Course.objects.exclude(instructor_id=None).iterator():
        Staff.objects.get_or_create(course_id=c.pk,user_id=c.instructor_id,defaults={'role':'owner'})
    for m in Module.objects.all().iterator():
        Staff.objects.get_or_create(course_id=m.course_id,user_id=m.instructor_id,defaults={'role':'instructor'})
    for e in Enrollment.objects.all().iterator():
        groups=list(Group.objects.filter(course_id=e.course_id,members=e.student_id).values_list('pk',flat=True))
        if len(groups)==1:Membership.objects.get_or_create(enrollment_id=e.pk,defaults={'group_id':groups[0]})
    # Current membership cannot prove historical membership. Only a unique recorded file path is evidence.
    for sub in Submission.objects.all().iterator():
        groups=set()
        for name in sub.files.values_list('file',flat=True):
            for part in str(name).replace('\\','/').split('/'):
                if part.startswith('group_') and part[6:].isdigit():groups.add(int(part[6:]))
        if len(groups)==1:
            gid=next(iter(groups))
            if Group.objects.filter(pk=gid,course__modules__lessons__lesson_exercise=sub.exercise_id).exists():sub.group_id=gid
        sub.roster=[sub.student_id]  # Do not guess historical peers from today's membership.
        sub.accepted_at=sub.submitted_at
        sub.save(update_fields=['group','roster','accepted_at'])

class Migration(migrations.Migration):
    dependencies=[('course','0027_platform_boundaries')]
    operations=[migrations.RunPython(preserve,migrations.RunPython.noop)]
