import secrets
import string
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


def _generate_pin():
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(8))


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('hod', 'Head of Department'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


class StudentProfile(models.Model):
    YEAR_CHOICES = (
        (1, 'Year 1'),
        (2, 'Year 2'),
        (3, 'Year 3'),
        (4, 'Year 4'),
        (5, 'Year 5'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    year_of_study = models.IntegerField(choices=YEAR_CHOICES, default=1)
    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_id}"


class LecturerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_profile')
    staff_id = models.CharField(max_length=20, unique=True)
    specialization = models.CharField(max_length=100, blank=True)
    is_hod = models.BooleanField(default=False)
    department = models.CharField(max_length=120, blank=True, default='Mathematics')
    position = models.CharField(max_length=120, blank=True)
    office_number = models.CharField(max_length=50, blank=True)
    office_hours = models.CharField(max_length=255, blank=True)
    office_location = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.staff_id}"


class RegistrationPIN(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('hod', 'Head of Department'),
    )
    pin = models.CharField(max_length=8, unique=True, default=_generate_pin)
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_used = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='generated_pins'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='registration_pin'
    )

    def __str__(self):
        return f"{self.pin} ({self.role}) — {'used' if self.is_used else 'unused'}"


# ── Announcements ─────────────────────────────────────────────────────────────

class Announcement(models.Model):
    TARGET_CHOICES = [
        ('all', 'Everyone'),
        ('student', 'Students Only'),
        ('staff', 'Staff Only'),
    ]
    AUDIENCE_CHOICES = [
        ('all_students', 'All Students'),
        ('levels', 'Selected Levels'),
        ('classes', 'Specific Classes'),
        ('course_students', 'Specific Course Students'),
        ('staff', 'Staff Only'),
    ]
    title      = models.CharField(max_length=200)
    body       = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active  = models.BooleanField(default=True)
    target     = models.CharField(max_length=10, choices=TARGET_CHOICES, default='all')
    audience_type = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all_students')
    target_levels = models.JSONField(default=list, blank=True)
    target_classes = models.JSONField(default=list, blank=True)
    target_course = models.ForeignKey(
        'courses.Course', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='announcements'
    )
    schedule_at = models.DateTimeField(null=True, blank=True)
    allow_comments = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_visible_to(self, user):
        if not self.is_active:
            return False
        if self.audience_type == 'staff':
            return user.role in ('lecturer', 'hod', 'admin') or user.is_superuser
        if self.audience_type == 'course_students':
            if self.target_course is None:
                return True
            return user.role == 'student' and user.registrations.filter(course=self.target_course).exists()
        if self.audience_type == 'levels':
            if user.role != 'student':
                return False
            year = getattr(getattr(user, 'student_profile', None), 'year_of_study', None)
            return year is not None and str(year) in {str(level) for level in self.target_levels}
        return True


# ── Resources ─────────────────────────────────────────────────────────────────

class Resource(models.Model):
    CATEGORY_CHOICES = [
        ('notes',       'Lecture Notes'),
        ('past_papers', 'Past Papers'),
        ('assignments', 'Assignments'),
        ('forms',       'Department Forms'),
        ('other',       'Other'),
    ]
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file        = models.FileField(upload_to='resources/')
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='notes')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='resources')
    created_at  = models.DateTimeField(auto_now_add=True)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def filename(self):
        import os
        return os.path.basename(self.file.name)

    @property
    def ext(self):
        return self.filename.rsplit('.', 1)[-1].lower() if '.' in self.filename else ''


# ── Internal Messages ─────────────────────────────────────────────────────────

class Message(models.Model):
    sender    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject   = models.CharField(max_length=200)
    body      = models.TextField()
    thread    = models.ForeignKey('ConversationThread', on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True)
    sent_at   = models.DateTimeField(auto_now_add=True)
    is_read   = models.BooleanField(default=False)
    read_at   = models.DateTimeField(null=True, blank=True)
    parent    = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.sender} → {self.recipient}: {self.subject}"

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class ConversationThread(models.Model):
    subject = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_threads')
    participants = models.ManyToManyField(User, related_name='message_threads', blank=True)
    related_course = models.ForeignKey(
        'courses.Course', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='message_threads'
    )
    is_closed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.subject


class CourseMaterial(models.Model):
    MATERIAL_CHOICES = [
        ('notes', 'Lecture Notes'),
        ('ppt', 'PowerPoint'),
        ('pdf', 'PDF'),
        ('outline', 'Course Outline'),
        ('reading', 'Reading Material'),
        ('video', 'Video'),
        ('link', 'Reference Link'),
        ('syllabus', 'Syllabus'),
    ]
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_CHOICES, default='notes')
    file = models.FileField(upload_to='course_materials/', blank=True, null=True)
    external_url = models.URLField(blank=True)
    outline = models.JSONField(default=dict, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='course_materials')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course.code} - {self.title}"


class Assignment(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField(blank=True)
    due_date = models.DateTimeField()
    attachment = models.FileField(upload_to='assignments/', blank=True, null=True)
    total_marks = models.PositiveSmallIntegerField(default=100)
    allow_late_submission = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_assignments')
    published_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.course.code} - {self.title}"


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions')
    uploaded_file = models.FileField(upload_to='assignment_submissions/', blank=True, null=True)
    text_submission = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    resubmitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    is_late = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assignment.title}"


class Tutorial(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='tutorials')
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    worked_examples = models.TextField(blank=True)
    practice_exercises = models.TextField(blank=True)
    file = models.FileField(upload_to='tutorials/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tutorials_created')
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course.code} - {self.title}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    lecturer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='attendance_marked')
    session_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-session_date']
        unique_together = ['course', 'student', 'session_date']

    def __str__(self):
        return f"{self.course.code} - {self.student.get_full_name()} ({self.status})"


class Discussion(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='discussions', null=True, blank=True)
    topic = models.CharField(max_length=255)
    body = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussions_created')
    is_pinned = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    related_assignment = models.ForeignKey(Assignment, on_delete=models.SET_NULL, null=True, blank=True, related_name='discussions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-updated_at']

    def __str__(self):
        return self.topic


class DiscussionReply(models.Model):
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_replies')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply by {self.author.get_full_name()}"


class OfficeHour(models.Model):
    DAY_CHOICES = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='office_hours')
    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255)
    notes = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.lecturer.get_full_name()} - {self.get_day_of_week_display()}"


class AppointmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
    ]
    office_hour = models.ForeignKey(OfficeHour, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointment_requests')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointment_requests_made')
    preferred_datetime = models.DateTimeField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.get_full_name()} -> {self.lecturer.get_full_name()}"


class Timetable(models.Model):
    ACTIVITY_CHOICES = [
        ('lecture', 'Lecture'),
        ('tutorial', 'Tutorial'),
        ('practical', 'Practical'),
        ('extra', 'Extra Class'),
    ]
    DAY_CHOICES = OfficeHour.DAY_CHOICES
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='timetable_entries')
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='timetable_entries')
    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=120)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default='lecture')
    notes = models.CharField(max_length=255, blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.course.code} - {self.get_day_of_week_display()}"


class ExamSchedule(models.Model):
    EXAM_CHOICES = [
        ('quiz', 'Quiz'),
        ('test', 'Test'),
        ('midterm', 'Midterm'),
        ('exam', 'Exam'),
        ('practical', 'Practical'),
    ]
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='exam_schedules')
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_schedules')
    exam_type = models.CharField(max_length=20, choices=EXAM_CHOICES, default='test')
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    study_guide = models.FileField(upload_to='exam_guides/', blank=True, null=True)
    scheduled_for = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=120)
    room = models.CharField(max_length=120, blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-scheduled_for']

    def __str__(self):
        return f"{self.course.code} - {self.title}"


class Notification(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('message', 'Message'),
        ('assignment', 'Assignment'),
        ('grade', 'Grade'),
        ('discussion', 'Discussion'),
        ('appointment', 'Appointment'),
        ('announcement', 'Announcement'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"


# ── Fee Payments ──────────────────────────────────────────────────────────────

class FeePayment(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    student        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fee_payments')
    description    = models.CharField(max_length=200)
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, help_text='Orange Money transaction reference')
    receipt        = models.ImageField(upload_to='receipts/')
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_at   = models.DateTimeField(auto_now_add=True)
    verified_by    = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_fees'
    )
    verified_at    = models.DateTimeField(null=True, blank=True)
    notes          = models.TextField(blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student} — {self.description} ({self.status})"