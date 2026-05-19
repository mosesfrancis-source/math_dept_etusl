import csv
from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from courses.forms import GradeForm
from courses.models import Course, CourseRegistration, Grade, calculate_gpa

from .models import (
    Announcement,
    AppointmentRequest,
    Attendance,
    Assignment,
    AssignmentSubmission,
    ConversationThread,
    CourseMaterial,
    Discussion,
    DiscussionReply,
    ExamSchedule,
    LecturerProfile,
    Message,
    Notification,
    OfficeHour,
    Timetable,
    Tutorial,
    User,
)


LECTURER_ROLES = ('lecturer', 'hod')
STUDENT_ROLES = ('student',)


def _has_role(user, roles):
    return user.is_authenticated and (user.role in roles or user.is_superuser)


def _role_guard(roles):
    def decorator(view_func):
        @login_required(login_url='login')
        def wrapper(request, *args, **kwargs):
            if not _has_role(request.user, roles):
                messages.error(request, 'Access denied.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def _parse_csv_list(raw_value):
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(',') if item.strip()]


def _parse_dt(raw_value):
    if not raw_value:
        return None
    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError:
        return None
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _portal_notifications(user):
    return Notification.objects.filter(user=user).order_by('-created_at')[:8]


def _create_notification(user, title, message, category='general', link=''):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        category=category,
        link=link,
    )


@_role_guard(LECTURER_ROLES)
def lecturer_dashboard(request):
    user = request.user
    courses = Course.objects.filter(lecturer=user, is_active=True).select_related('lecturer')
    registrations = CourseRegistration.objects.filter(
        course__lecturer=user,
        status='approved',
    )
    assignments_due = Assignment.objects.filter(course__lecturer=user, is_published=True).count()
    pending_grades = Grade.objects.filter(
        registration__course__lecturer=user,
        score__isnull=True,
    ).count()
    unread_messages = Message.objects.filter(recipient=user, is_read=False).count()
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()

    course_breakdown = []
    for course in courses:
        course_breakdown.append({
            'course': course,
            'students': registrations.filter(course=course).count(),
            'assignments': course.assignments.filter(is_published=True).count(),
            'materials': course.materials.filter(is_active=True).count(),
            'exams': course.exam_schedules.filter(is_published=True).count(),
        })

    analytics = {
        'students': registrations.values('student').distinct().count(),
        'courses': courses.count(),
        'avg_score': registrations.filter(grade__score__isnull=False).aggregate(avg=Avg('grade__score'))['avg'],
        'attendance_rate': Attendance.objects.filter(
            course__lecturer=user,
            status='present',
        ).count(),
    }

    context = {
        'courses': courses,
        'course_breakdown': course_breakdown,
        'pending_grades': pending_grades,
        'assignments_due': assignments_due,
        'unread_messages': unread_messages,
        'unread_notifications': unread_notifications,
        'appointments_pending': AppointmentRequest.objects.filter(lecturer=user, status='pending').count(),
        'office_hours': OfficeHour.objects.filter(lecturer=user, is_active=True)[:4],
        'notifications': _portal_notifications(user),
        'analytics': analytics,
        'recent_assignments': Assignment.objects.filter(course__lecturer=user).select_related('course')[:5],
        'recent_discussions': Discussion.objects.filter(Q(created_by=user) | Q(course__lecturer=user))[:5],
    }
    return render(request, 'accounts/lecturer/dashboard.html', context)


@_role_guard(LECTURER_ROLES)
def lecturer_portal(request, section):
    user = request.user
    lecturer_profile, _ = LecturerProfile.objects.get_or_create(user=user, defaults={'staff_id': f'STAFF-{user.id}'})
    courses = Course.objects.filter(lecturer=user, is_active=True).select_related('lecturer')

    if section == 'profile':
        if request.method == 'POST':
            action = request.POST.get('action', 'profile')
            if action == 'profile':
                user.first_name = request.POST.get('first_name', '').strip()
                user.last_name = request.POST.get('last_name', '').strip()
                user.email = request.POST.get('email', '').strip()
                user.phone = request.POST.get('phone', '').strip()
                if request.FILES.get('profile_picture'):
                    if user.profile_picture:
                        user.profile_picture.delete(save=False)
                    user.profile_picture = request.FILES['profile_picture']
                lecturer_profile.department = request.POST.get('department', '').strip()
                lecturer_profile.position = request.POST.get('position', '').strip()
                lecturer_profile.office_number = request.POST.get('office_number', '').strip()
                lecturer_profile.office_hours = request.POST.get('office_hours', '').strip()
                lecturer_profile.office_location = request.POST.get('office_location', '').strip()
                lecturer_profile.specialization = request.POST.get('specialization', '').strip()
                lecturer_profile.bio = request.POST.get('bio', '').strip()
                user.save()
                lecturer_profile.save()
                messages.success(request, 'Lecturer profile updated.')
                return redirect('lecturer_profile')
            if action == 'password':
                old_pw = request.POST.get('old_password', '')
                new_pw = request.POST.get('new_password', '')
                new_pw2 = request.POST.get('new_password2', '')
                if not user.check_password(old_pw):
                    messages.error(request, 'Current password is incorrect.')
                elif new_pw != new_pw2:
                    messages.error(request, 'New passwords do not match.')
                elif len(new_pw) < 8:
                    messages.error(request, 'Password must be at least 8 characters.')
                else:
                    user.set_password(new_pw)
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, 'Password changed successfully.')
                return redirect('lecturer_profile')

        return render(request, 'accounts/lecturer/profile.html', {
            'lecturer_profile': lecturer_profile,
            'courses': courses,
        })

    if section == 'announcements':
        if request.method == 'POST':
            action = request.POST.get('action', 'create')
            announcement_id = request.POST.get('announcement_id')
            if action == 'delete' and announcement_id:
                announcement = get_object_or_404(Announcement, pk=announcement_id, created_by=user)
                announcement.delete()
                messages.success(request, 'Announcement deleted.')
                return redirect('lecturer_announcements')

            title = request.POST.get('title', '').strip()
            body = request.POST.get('body', '').strip()
            if not title or not body:
                messages.error(request, 'Title and body are required.')
            else:
                announcement = Announcement.objects.get(pk=announcement_id, created_by=user) if announcement_id and Announcement.objects.filter(pk=announcement_id, created_by=user).exists() else Announcement(created_by=user)
                announcement.title = title
                announcement.body = body
                announcement.target = request.POST.get('target', 'all')
                announcement.audience_type = request.POST.get('audience_type', 'all_students')
                announcement.target_levels = _parse_csv_list(request.POST.get('target_levels', ''))
                announcement.target_classes = _parse_csv_list(request.POST.get('target_classes', ''))
                target_course_id = request.POST.get('target_course')
                announcement.target_course = Course.objects.filter(pk=target_course_id).first() if target_course_id else None
                announcement.schedule_at = _parse_dt(request.POST.get('schedule_at'))
                announcement.allow_comments = bool(request.POST.get('allow_comments'))
                announcement.created_by = user
                announcement.save()
                messages.success(request, 'Announcement saved.')
                return redirect('lecturer_announcements')

        announcements = Announcement.objects.filter(Q(created_by=user) | Q(audience_type__in=['all_students', 'levels', 'classes', 'course_students', 'staff'])).order_by('-created_at')
        return render(request, 'accounts/lecturer/section.html', {
            'section': section,
            'lecturer_profile': lecturer_profile,
            'courses': courses,
            'announcements': announcements,
            'announcement_form': True,
        })

    if section == 'messages':
        if request.method == 'POST':
            action = request.POST.get('action', 'send')
            subject = request.POST.get('subject', '').strip()
            body = request.POST.get('body', '').strip()
            attachment = request.FILES.get('attachment')
            if action == 'send' and subject and body:
                scope = request.POST.get('scope', 'direct')
                recipients = []
                if scope == 'direct':
                    recipient_id = request.POST.get('recipient')
                    recipient = User.objects.filter(pk=recipient_id).first()
                    if recipient:
                        recipients = [recipient]
                elif scope == 'all_students':
                    recipients = list(User.objects.filter(role='student'))
                elif scope == 'course_students':
                    course_id = request.POST.get('course')
                    course = Course.objects.filter(pk=course_id, lecturer=user).first()
                    if course:
                        recipients = list(User.objects.filter(registrations__course=course, registrations__status='approved').distinct())
                elif scope == 'year_group':
                    year_value = request.POST.get('year_of_study')
                    recipients = list(User.objects.filter(role='student', student_profile__year_of_study=year_value))
                elif scope == 'selected':
                    recipient_ids = request.POST.getlist('recipient_ids') or _parse_csv_list(request.POST.get('recipient_ids_raw', ''))
                    recipients = list(User.objects.filter(pk__in=recipient_ids))

                if not recipients:
                    messages.error(request, 'No valid recipients found.')
                else:
                    thread = ConversationThread.objects.create(subject=subject, created_by=user)
                    thread.participants.add(user, *recipients)
                    for recipient in recipients:
                        Message.objects.create(
                            sender=user,
                            recipient=recipient,
                            subject=subject,
                            body=body,
                            thread=thread,
                            attachment=attachment,
                        )
                        _create_notification(recipient, subject, body[:160], 'message')
                    messages.success(request, f'Message sent to {len(recipients)} recipient(s).')
                    return redirect('lecturer_messages')

        inbox = Message.objects.filter(recipient=user, parent__isnull=True).select_related('sender').order_by('-sent_at')
        sent = Message.objects.filter(sender=user, parent__isnull=True).select_related('recipient').order_by('-sent_at')
        students = User.objects.filter(role='student').select_related('student_profile').order_by('first_name', 'last_name')
        return render(request, 'accounts/lecturer/section.html', {
            'section': section,
            'lecturer_profile': lecturer_profile,
            'courses': courses,
            'inbox': inbox,
            'sent': sent,
            'students': students,
            'unread_messages': Message.objects.filter(recipient=user, is_read=False).count(),
        })

    if section == 'grades':
        registrations = CourseRegistration.objects.filter(course__lecturer=user, status='approved').select_related('course', 'student', 'grade')
        if request.method == 'POST':
            action = request.POST.get('action', 'save')
            if action == 'save':
                reg = get_object_or_404(CourseRegistration, pk=request.POST.get('registration_id'), course__lecturer=user)
                grade_obj, _ = Grade.objects.get_or_create(registration=reg)
                form = GradeForm(request.POST, instance=grade_obj)
                if form.is_valid():
                    grade = form.save(commit=False)
                    grade.graded_by = user
                    grade.save()
                    _create_notification(reg.student, f'Grade updated: {reg.course.code}', f'Your grade has been updated for {reg.course.name}.', 'grade')
                    messages.success(request, 'Grade saved.')
                    return redirect('lecturer_grades')
            elif action == 'bulk_upload' and request.FILES.get('csv_file'):
                csv_file = request.FILES['csv_file'].read().decode('utf-8').splitlines()
                reader = csv.DictReader(csv_file)
                updated = 0
                for row in reader:
                    reg_id = row.get('registration_id')
                    score = row.get('score')
                    if not reg_id or score is None:
                        continue
                    reg = CourseRegistration.objects.filter(pk=reg_id, course__lecturer=user).first()
                    if not reg:
                        continue
                    grade_obj, _ = Grade.objects.get_or_create(registration=reg)
                    grade_obj.score = Decimal(score)
                    grade_obj.graded_by = user
                    grade_obj.save()
                    updated += 1
                messages.success(request, f'Bulk upload completed: {updated} records updated.')
                return redirect('lecturer_grades')

        return render(request, 'accounts/lecturer/section.html', {
            'section': section,
            'lecturer_profile': lecturer_profile,
            'courses': courses,
            'registrations': registrations,
            'grade_form': GradeForm(),
        })

    if section == 'assignments':
        if request.method == 'POST':
            action = request.POST.get('action', 'create')
            if action == 'create':
                course = get_object_or_404(Course, pk=request.POST.get('course_id'), lecturer=user)
                due_date = _parse_dt(request.POST.get('due_date')) or timezone.now()
                Assignment.objects.create(
                    course=course,
                    title=request.POST.get('title', '').strip(),
                    description=request.POST.get('description', '').strip(),
                    instructions=request.POST.get('instructions', '').strip(),
                    due_date=due_date,
                    attachment=request.FILES.get('attachment'),
                    total_marks=request.POST.get('total_marks') or 100,
                    allow_late_submission=bool(request.POST.get('allow_late_submission')),
                    created_by=user,
                )
                messages.success(request, 'Assignment created.')
                return redirect('lecturer_assignments')

        assignments = Assignment.objects.filter(course__lecturer=user).select_related('course').prefetch_related('submissions')
        return render(request, 'accounts/lecturer/section.html', {
            'section': section,
            'lecturer_profile': lecturer_profile,
            'courses': courses,
            'assignments': assignments,
        })

    if section == 'tutorials':
        if request.method == 'POST':
            course = get_object_or_404(Course, pk=request.POST.get('course_id'), lecturer=user)
            Tutorial.objects.create(
                course=course,
                title=request.POST.get('title', '').strip(),
                summary=request.POST.get('summary', '').strip(),
                worked_examples=request.POST.get('worked_examples', '').strip(),
                practice_exercises=request.POST.get('practice_exercises', '').strip(),
                file=request.FILES.get('file'),
                created_by=user,
            )
            messages.success(request, 'Tutorial posted.')
            return redirect('lecturer_tutorials')
        tutorials = Tutorial.objects.filter(course__lecturer=user).select_related('course')
        return render(request, 'accounts/lecturer/section.html', {'section': section, 'courses': courses, 'tutorials': tutorials, 'lecturer_profile': lecturer_profile})

    if section == 'materials':
        if request.method == 'POST':
            course = get_object_or_404(Course, pk=request.POST.get('course_id'), lecturer=user)
            CourseMaterial.objects.create(
                course=course,
                title=request.POST.get('title', '').strip(),
                description=request.POST.get('description', '').strip(),
                material_type=request.POST.get('material_type', 'notes'),
                file=request.FILES.get('file'),
                external_url=request.POST.get('external_url', '').strip(),
                outline={
                    'weekly_breakdown': _parse_csv_list(request.POST.get('weekly_breakdown', '')),
                    'learning_objectives': _parse_csv_list(request.POST.get('learning_objectives', '')),
                    'reading_list': _parse_csv_list(request.POST.get('reading_list', '')),
                    'policies': request.POST.get('policies', '').strip(),
                },
                uploaded_by=user,
            )
            messages.success(request, 'Course material uploaded.')
            return redirect('lecturer_materials')
        materials = CourseMaterial.objects.filter(course__lecturer=user).select_related('course')
        return render(request, 'accounts/lecturer/section.html', {'section': section, 'courses': courses, 'materials': materials, 'lecturer_profile': lecturer_profile})

    if section == 'office-hours':
        if request.method == 'POST':
            OfficeHour.objects.create(
                lecturer=user,
                day_of_week=request.POST.get('day_of_week', 'mon'),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
                location=request.POST.get('location', '').strip(),
                notes=request.POST.get('notes', '').strip(),
            )
            messages.success(request, 'Office hour saved.')
            return redirect('lecturer_office_hours')
        office_hours = OfficeHour.objects.filter(lecturer=user)
        return render(request, 'accounts/lecturer/section.html', {'section': section, 'office_hours': office_hours, 'lecturer_profile': lecturer_profile})

    if section == 'timetable':
        if request.method == 'POST':
            course = get_object_or_404(Course, pk=request.POST.get('course_id'), lecturer=user)
            Timetable.objects.create(
                course=course,
                lecturer=user,
                day_of_week=request.POST.get('day_of_week', 'mon'),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
                room=request.POST.get('room', '').strip(),
                activity_type=request.POST.get('activity_type', 'lecture'),
                notes=request.POST.get('notes', '').strip(),
            )
            messages.success(request, 'Timetable item saved.')
            return redirect('lecturer_timetable')
        timetable = Timetable.objects.filter(lecturer=user).select_related('course')
        return render(request, 'accounts/lecturer/section.html', {'section': section, 'timetable': timetable, 'courses': courses, 'lecturer_profile': lecturer_profile})

    if section == 'exams':
        if request.method == 'POST':
            course = get_object_or_404(Course, pk=request.POST.get('course_id'), lecturer=user)
            ExamSchedule.objects.create(
                course=course,
                lecturer=user,
                exam_type=request.POST.get('exam_type', 'test'),
                title=request.POST.get('title', '').strip(),
                instructions=request.POST.get('instructions', '').strip(),
                study_guide=request.FILES.get('study_guide'),
                scheduled_for=_parse_dt(request.POST.get('scheduled_for')) or timezone.now(),
                duration_minutes=request.POST.get('duration_minutes') or 120,
                room=request.POST.get('room', '').strip(),
            )
            messages.success(request, 'Exam schedule saved.')
            return redirect('lecturer_exams')
        exams = ExamSchedule.objects.filter(lecturer=user).select_related('course')
        return render(request, 'accounts/lecturer/section.html', {'section': section, 'exams': exams, 'courses': courses, 'lecturer_profile': lecturer_profile})

    if section == 'discussions':
        if request.method == 'POST':
            action = request.POST.get('action', 'create')
            if action == 'reply':
                discussion = get_object_or_404(Discussion, pk=request.POST.get('discussion_id'))
                DiscussionReply.objects.create(
                    discussion=discussion,
                    author=user,
                    body=request.POST.get('reply_body', '').strip(),
                )
                messages.success(request, 'Reply posted.')
                return redirect('lecturer_discussions')
            course_id = request.POST.get('course_id')
            discussion = Discussion.objects.create(
                course=Course.objects.filter(pk=course_id).first() if course_id else None,
                topic=request.POST.get('topic', '').strip(),
                body=request.POST.get('body', '').strip(),
                created_by=user,
                is_pinned=bool(request.POST.get('is_pinned')),
            )
            messages.success(request, 'Discussion created.')
            return redirect('lecturer_discussions')
        discussions = Discussion.objects.filter(Q(created_by=user) | Q(course__lecturer=user)).prefetch_related('replies', 'course')
        return render(request, 'accounts/lecturer/section.html', {'section': section, 'discussions': discussions, 'courses': courses, 'lecturer_profile': lecturer_profile})

    if section == 'attendance':
        attendance_rows = Attendance.objects.filter(course__lecturer=user).select_related('course', 'student')
        selected_course = None
        session_date_value = timezone.localdate()
        attendance_roster = []

        if request.method == 'POST':
            action = request.POST.get('action', 'load_roster')
            course = get_object_or_404(Course, pk=request.POST.get('course_id'), lecturer=user)
            selected_course = course
            session_date_value = request.POST.get('session_date') or timezone.localdate()

            if action == 'save':
                for registration in CourseRegistration.objects.filter(course=course, status='approved').select_related('student'):
                    status_value = request.POST.get(f'status_{registration.id}', 'present')
                    note_value = request.POST.get(f'note_{registration.id}', '').strip()
                    Attendance.objects.update_or_create(
                        course=course,
                        student=registration.student,
                        session_date=session_date_value,
                        defaults={'lecturer': user, 'status': status_value, 'note': note_value},
                    )
                messages.success(request, 'Attendance recorded.')
                return redirect('lecturer_attendance')

            attendance_roster = CourseRegistration.objects.filter(course=course, status='approved').select_related('student', 'grade')

        return render(request, 'accounts/lecturer/section.html', {
            'section': section,
            'attendance_rows': attendance_rows,
            'attendance_roster': attendance_roster,
            'selected_course': selected_course,
            'session_date_value': session_date_value,
            'courses': courses,
            'lecturer_profile': lecturer_profile,
        })

    if section == 'analytics':
        grade_qs = Grade.objects.filter(registration__course__lecturer=user, score__isnull=False)
        analytics = {
            'average_score': grade_qs.aggregate(avg=Avg('score'))['avg'],
            'highest_score': grade_qs.order_by('-score').values_list('score', flat=True).first(),
            'lowest_score': grade_qs.order_by('score').values_list('score', flat=True).first(),
            'students_tracked': grade_qs.values('registration__student').distinct().count(),
            'attendance_records': Attendance.objects.filter(course__lecturer=user).count(),
            'weak_students': CourseRegistration.objects.filter(course__lecturer=user, grade__score__lt=50).select_related('student', 'course', 'grade')[:10],
        }
        return render(request, 'accounts/lecturer/section.html', {'section': section, 'analytics': analytics, 'courses': courses, 'lecturer_profile': lecturer_profile})

    return redirect('lecturer_dashboard')


@_role_guard(STUDENT_ROLES)
def student_portal(request, section):
    user = request.user
    courses = CourseRegistration.objects.filter(student=user, status='approved').select_related('course', 'course__lecturer', 'grade')

    if section == 'announcements':
        announcements = [announcement for announcement in Announcement.objects.filter(is_active=True).order_by('-created_at') if announcement.is_visible_to(user)]
        return render(request, 'accounts/student/section.html', {'section': section, 'announcements': announcements, 'registrations': courses})

    if section == 'messages':
        if request.method == 'POST':
            recipient = User.objects.filter(pk=request.POST.get('recipient')).first()
            subject = request.POST.get('subject', '').strip()
            body = request.POST.get('body', '').strip()
            if recipient and subject and body:
                thread = ConversationThread.objects.create(subject=subject, created_by=user)
                thread.participants.add(user, recipient)
                Message.objects.create(sender=user, recipient=recipient, subject=subject, body=body, thread=thread)
                _create_notification(recipient, subject, body[:160], 'message')
                messages.success(request, 'Message sent.')
                return redirect('student_messages')
        inbox = Message.objects.filter(recipient=user, parent__isnull=True).select_related('sender').order_by('-sent_at')
        sent = Message.objects.filter(sender=user, parent__isnull=True).select_related('recipient').order_by('-sent_at')
        lecturers = User.objects.filter(role__in=LECTURER_ROLES).order_by('first_name', 'last_name')
        return render(request, 'accounts/student/section.html', {'section': section, 'inbox': inbox, 'sent': sent, 'lecturers': lecturers, 'registrations': courses})

    if section == 'assignments':
        assignments = Assignment.objects.filter(course__registrations__student=user, is_published=True).distinct().select_related('course')
        if request.method == 'POST':
            assignment = get_object_or_404(Assignment, pk=request.POST.get('assignment_id'))
            submission, _ = AssignmentSubmission.objects.get_or_create(assignment=assignment, student=user)
            submission.uploaded_file = request.FILES.get('uploaded_file', submission.uploaded_file)
            submission.text_submission = request.POST.get('text_submission', submission.text_submission)
            submission.resubmitted_at = timezone.now()
            submission.is_late = timezone.now() > assignment.due_date
            submission.save()
            _create_notification(assignment.created_by, f'Submission received: {assignment.title}', f'{user.get_full_name()} submitted an assignment.', 'assignment')
            messages.success(request, 'Assignment submitted.')
            return redirect('student_assignments')
        submissions = AssignmentSubmission.objects.filter(student=user).select_related('assignment', 'assignment__course')
        return render(request, 'accounts/student/section.html', {'section': section, 'assignments': assignments, 'submissions': submissions, 'registrations': courses})

    if section == 'materials':
        materials = CourseMaterial.objects.filter(course__registrations__student=user, is_active=True).distinct().select_related('course')
        tutorials = Tutorial.objects.filter(course__registrations__student=user, is_published=True).distinct().select_related('course')
        return render(request, 'accounts/student/section.html', {'section': section, 'materials': materials, 'tutorials': tutorials, 'registrations': courses})

    if section == 'discussions':
        if request.method == 'POST':
            discussion = get_object_or_404(Discussion, pk=request.POST.get('discussion_id'))
            DiscussionReply.objects.create(discussion=discussion, author=user, body=request.POST.get('reply_body', '').strip())
            messages.success(request, 'Reply posted.')
            return redirect('student_discussions')
        discussions = Discussion.objects.filter(Q(course__registrations__student=user) | Q(created_by__role__in=LECTURER_ROLES)).distinct().prefetch_related('replies', 'course')
        return render(request, 'accounts/student/section.html', {'section': section, 'discussions': discussions, 'registrations': courses})

    if section == 'grades':
        registrations = courses.select_related('grade')
        gpa = calculate_gpa(user)
        return render(request, 'accounts/student/section.html', {'section': section, 'registrations': registrations, 'gpa': gpa})

    if section == 'appointments':
        if request.method == 'POST':
            lecturer = User.objects.filter(pk=request.POST.get('lecturer_id'), role__in=LECTURER_ROLES).first()
            if lecturer:
                AppointmentRequest.objects.create(
                    lecturer=lecturer,
                    student=user,
                    preferred_datetime=_parse_dt(request.POST.get('preferred_datetime')) or timezone.now(),
                    reason=request.POST.get('reason', '').strip(),
                )
                _create_notification(lecturer, 'New appointment request', f'{user.get_full_name()} requested a meeting.', 'appointment')
                messages.success(request, 'Appointment request sent.')
                return redirect('student_appointments')
        appointments = AppointmentRequest.objects.filter(student=user).select_related('lecturer', 'office_hour')
        lecturers = User.objects.filter(role__in=LECTURER_ROLES).order_by('first_name', 'last_name')
        return render(request, 'accounts/student/section.html', {'section': section, 'appointments': appointments, 'lecturers': lecturers, 'registrations': courses})

    if section == 'timetable':
        timetable = Timetable.objects.filter(course__registrations__student=user, is_published=True).distinct().select_related('course', 'lecturer')
        exams = ExamSchedule.objects.filter(course__registrations__student=user, is_published=True).distinct().select_related('course', 'lecturer')
        return render(request, 'accounts/student/section.html', {'section': section, 'timetable': timetable, 'exams': exams, 'registrations': courses})

    return redirect('dashboard')