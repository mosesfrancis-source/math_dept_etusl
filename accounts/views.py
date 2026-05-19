from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .forms import StudentRegistrationForm, LecturerRegistrationForm
from .models import RegistrationPIN, Announcement, Resource, Message, FeePayment, User as UserModel


def about(request):
    return render(request, 'about.html')

def programs(request):
    from courses.models import Course
    qs = Course.objects.filter(is_active=True).order_by('code')
    context = {
        'y1s1': qs.filter(year_of_study=1, semester='1'),
        'y1s2': qs.filter(year_of_study=1, semester='2'),
        'y2s1': qs.filter(year_of_study=2, semester='1'),
        'y2s2': qs.filter(year_of_study=2, semester='2'),
        'y3s1': qs.filter(year_of_study=3, semester='1'),
        'y3s2': qs.filter(year_of_study=3, semester='2'),
        'y4s2': qs.filter(year_of_study=4, semester='2'),
    }
    return render(request, 'programs.html', context)

def faculty_page(request):
    from accounts.models import User as UserModel
    staff = UserModel.objects.filter(role__in=['lecturer', 'hod']).select_related('lecturer_profile')
    return render(request, 'faculty.html', {'staff': staff})

def students_page(request):
    return render(request, 'students.html')

def news(request):
    return render(request, 'news.html')

def contact(request):
    return render(request, 'contact.html')

def home(request):
    from accounts.models import User as UserModel
    from courses.models import Course
    context = {
        'total_students': UserModel.objects.filter(role='student').count(),
        'total_staff':    UserModel.objects.filter(role__in=['lecturer', 'hod']).count(),
        'total_courses':  Course.objects.filter(is_active=True).count(),
    }
    return render(request, 'home.html', context)


def register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student account created! Please log in.')
            return redirect('login')
    else:
        form = StudentRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def register_lecturer(request):
    if request.method == 'POST':
        form = LecturerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lecturer account created! Please log in.')
            return redirect('login')
    else:
        form = LecturerRegistrationForm()
    return render(request, 'accounts/register_lecturer.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        identifier = request.POST['username'].strip()
        password = request.POST['password']
        user_obj = UserModel.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier)).first()
        auth_username = user_obj.username if user_obj else identifier
        user = authenticate(request, username=auth_username, password=password)
        if user:
            login(request, user)
            if user.role in ('lecturer', 'hod'):
                return redirect('lecturer_dashboard')
            if user.role == 'admin' or user.is_superuser:
                return redirect('dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def admin_pins(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    pins = RegistrationPIN.objects.select_related('created_by', 'used_by').order_by('-created_at')
    return render(request, 'accounts/admin_pins.html', {'pins': pins})


@login_required(login_url='login')
def admin_generate_pin(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        role  = request.POST.get('role', 'student')
        if not email:
            messages.error(request, 'Email is required.')
            return redirect('admin_pins')
        if role not in ('student', 'lecturer', 'hod'):
            messages.error(request, 'Invalid role.')
            return redirect('admin_pins')

        pin_obj = RegistrationPIN.objects.create(
            email=email,
            role=role,
            created_by=request.user,
        )

        role_display = dict(RegistrationPIN.ROLE_CHOICES).get(role, role)
        send_mail(
            subject='Your ETU Mathematics Portal Registration PIN',
            message=(
                f"Dear {role_display},\n\n"
                f"Your registration PIN for the ETU Mathematics Department Portal is:\n\n"
                f"    {pin_obj.pin}\n\n"
                f"Use this PIN when registering at the portal. It is valid for one use only.\n\n"
                f"Portal: {request.build_absolute_uri('/register/')}\n\n"
                f"— ETU Mathematics Department"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        messages.success(request, f'PIN {pin_obj.pin} generated and sent to {email}.')
    return redirect('admin_pins')


@login_required(login_url='login')
def dashboard(request):
    import json
    from decimal import Decimal
    from accounts.models import User as UserModel

    user = request.user

    if user.role in ('lecturer', 'hod'):
        return redirect('lecturer_dashboard')

    hod = UserModel.objects.filter(role='hod').select_related('lecturer_profile').first()
    context = {
        'total_students': UserModel.objects.filter(role='student').count(),
        'total_faculty':  UserModel.objects.filter(role__in=['lecturer', 'hod']).count(),
        'hod': hod,
    }

    if user.role == 'student':
        from courses.models import CourseRegistration, Grade, calculate_gpa, get_gpa_trend

        registrations = list(
            CourseRegistration.objects
            .filter(student=user, status='approved')
            .select_related('course', 'course__lecturer', 'grade')
            .order_by('course__code')
        )
        gpa = calculate_gpa(user)
        total_credits = sum(r.course.credits for r in registrations)

        if gpa >= Decimal('3.5'):
            gpa_standing = 'First Class'
        elif gpa >= Decimal('3.0'):
            gpa_standing = 'Good Standing'
        elif gpa >= Decimal('2.5'):
            gpa_standing = 'Satisfactory'
        elif gpa >= Decimal('1.0'):
            gpa_standing = 'Below Average'
        else:
            gpa_standing = 'Academic Probation'

        trend = get_gpa_trend(user)
        recent_results = list(
            Grade.objects
            .filter(registration__student=user, score__isnull=False)
            .select_related('registration__course')
            .order_by('-graded_at')[:5]
        )
        from courses.models import Course
        academic_year = (
            Course.objects
            .filter(registrations__student=user, registrations__status='approved', is_active=True)
            .values_list('academic_year', flat=True)
            .first()
        ) or '2024/2025'

        context.update({
            'registrations':  registrations,
            'gpa':            gpa,
            'gpa_standing':   gpa_standing,
            'total_credits':  total_credits,
            'recent_results': recent_results,
            'academic_year':  academic_year,
            'trend_labels':   json.dumps([t['label'] for t in trend]),
            'trend_values':   json.dumps([t['gpa'] for t in trend]),
        })

    elif user.role in ('lecturer', 'hod'):
        from courses.models import Course, Grade
        courses = list(Course.objects.filter(lecturer=user, is_active=True))
        pending_grades = Grade.objects.filter(
            registration__course__lecturer=user,
            score__isnull=True,
            registration__status='approved',
        ).count()
        context.update({'courses': courses, 'pending_grades': pending_grades})

    elif user.role == 'admin':
        from courses.models import Course, CourseRegistration
        context.update({
            'total_courses':       Course.objects.filter(is_active=True).count(),
            'total_registrations': CourseRegistration.objects.filter(status='approved').count(),
            'total_lecturers':     UserModel.objects.filter(role__in=['lecturer', 'hod']).count(),
        })

    return render(request, 'accounts/dashboard.html', context)


# ── Announcements ─────────────────────────────────────────────────────────────

@login_required(login_url='login')
def announcements(request):
    user = request.user
    qs = Announcement.objects.filter(is_active=True)
    if user.role == 'student':
        qs = qs.filter(target__in=['all', 'student'])
    elif user.role in ('lecturer', 'hod'):
        qs = qs.filter(target__in=['all', 'staff'])
    return render(request, 'accounts/announcements.html', {'announcements': qs})


@login_required(login_url='login')
def announcement_create(request):
    if request.user.role not in ('admin', 'hod', 'lecturer') and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('announcements')
    if request.method == 'POST':
        title  = request.POST.get('title', '').strip()
        body   = request.POST.get('body', '').strip()
        target = request.POST.get('target', 'all')
        if not title or not body:
            messages.error(request, 'Title and body are required.')
        else:
            Announcement.objects.create(
                title=title, body=body, target=target, created_by=request.user
            )
            messages.success(request, 'Announcement posted.')
            return redirect('announcements')
    return render(request, 'accounts/announcement_form.html')


@login_required(login_url='login')
def announcement_delete(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if request.user.role not in ('admin', 'hod') and ann.created_by != request.user and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('announcements')
    ann.delete()
    messages.success(request, 'Announcement deleted.')
    return redirect('announcements')


# ── Resources ─────────────────────────────────────────────────────────────────

@login_required(login_url='login')
def resources(request):
    category = request.GET.get('cat', '')
    qs = Resource.objects.filter(is_active=True)
    if category:
        qs = qs.filter(category=category)
    return render(request, 'accounts/resources.html', {
        'resources': qs,
        'active_cat': category,
        'categories': Resource.CATEGORY_CHOICES,
    })


@login_required(login_url='login')
def resource_upload(request):
    if request.user.role not in ('admin', 'hod', 'lecturer') and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('resources')
    if request.method == 'POST':
        title    = request.POST.get('title', '').strip()
        desc     = request.POST.get('description', '').strip()
        category = request.POST.get('category', 'notes')
        f        = request.FILES.get('file')
        if not title or not f:
            messages.error(request, 'Title and file are required.')
        else:
            Resource.objects.create(
                title=title, description=desc, category=category,
                file=f, uploaded_by=request.user
            )
            messages.success(request, f'"{title}" uploaded successfully.')
            return redirect('resources')
    return render(request, 'accounts/resource_upload.html', {'categories': Resource.CATEGORY_CHOICES})


@login_required(login_url='login')
def resource_delete(request, pk):
    res = get_object_or_404(Resource, pk=pk)
    if request.user.role not in ('admin', 'hod') and res.uploaded_by != request.user and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('resources')
    res.file.delete(save=False)
    res.delete()
    messages.success(request, 'Resource deleted.')
    return redirect('resources')


# ── Messages ──────────────────────────────────────────────────────────────────

@login_required(login_url='login')
def inbox(request):
    msgs = Message.objects.filter(recipient=request.user, parent__isnull=True).select_related('sender')
    return render(request, 'accounts/inbox.html', {'msgs': msgs, 'tab': 'inbox'})


@login_required(login_url='login')
def sent_box(request):
    msgs = Message.objects.filter(sender=request.user, parent__isnull=True).select_related('recipient')
    return render(request, 'accounts/inbox.html', {'msgs': msgs, 'tab': 'sent'})


@login_required(login_url='login')
def message_compose(request):
    to_user = None
    to_id = request.GET.get('to')
    if to_id:
        to_user = UserModel.objects.filter(pk=to_id).first()

    recipients = UserModel.objects.exclude(pk=request.user.pk).order_by('first_name', 'last_name')

    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        subject      = request.POST.get('subject', '').strip()
        body         = request.POST.get('body', '').strip()
        recipient    = UserModel.objects.filter(pk=recipient_id).first()
        if not recipient or not subject or not body:
            messages.error(request, 'Recipient, subject, and message are required.')
        else:
            Message.objects.create(sender=request.user, recipient=recipient, subject=subject, body=body)
            messages.success(request, f'Message sent to {recipient.get_full_name()}.')
            return redirect('inbox')
    return render(request, 'accounts/message_compose.html', {
        'recipients': recipients,
        'to_user': to_user,
    })


@login_required(login_url='login')
def message_thread(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    if msg.recipient != request.user and msg.sender != request.user:
        messages.error(request, 'Access denied.')
        return redirect('inbox')
    if msg.recipient == request.user:
        msg.mark_read()
    replies = msg.replies.select_related('sender', 'recipient').order_by('sent_at')

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            recipient = msg.sender if request.user == msg.recipient else msg.recipient
            Message.objects.create(
                sender=request.user, recipient=recipient,
                subject=f"Re: {msg.subject}", body=body, parent=msg
            )
            messages.success(request, 'Reply sent.')
            return redirect('message_thread', pk=pk)
    return render(request, 'accounts/message_thread.html', {'msg': msg, 'replies': replies})


@login_required(login_url='login')
def message_delete(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    if msg.sender != request.user and msg.recipient != request.user:
        messages.error(request, 'Access denied.')
        return redirect('inbox')
    msg.delete()
    messages.success(request, 'Message deleted.')
    return redirect('inbox')


# ── Settings ──────────────────────────────────────────────────────────────────

@login_required(login_url='login')
def settings_view(request):
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'profile':
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name  = request.POST.get('last_name', '').strip()
            user.email      = request.POST.get('email', '').strip()
            user.phone      = request.POST.get('phone', '').strip()
            if 'profile_picture' in request.FILES:
                if user.profile_picture:
                    user.profile_picture.delete(save=False)
                user.profile_picture = request.FILES['profile_picture']
            user.save()
            messages.success(request, 'Profile updated.')

        elif action == 'password':
            old_pw  = request.POST.get('old_password', '')
            new_pw  = request.POST.get('new_password', '')
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

        return redirect('settings')

    return render(request, 'accounts/settings.html')


# ── Fee Payments ──────────────────────────────────────────────────────────────

@login_required(login_url='login')
def fees(request):
    user = request.user
    is_staff = user.role in ('admin', 'hod', 'lecturer') or user.is_superuser
    if is_staff:
        payments = FeePayment.objects.select_related('student', 'verified_by').all()
        pending_count = payments.filter(status='pending').count()
    else:
        payments = FeePayment.objects.filter(student=user)
        pending_count = 0
    return render(request, 'accounts/fees.html', {
        'payments': payments,
        'is_staff': is_staff,
        'pending_count': pending_count,
    })


@login_required(login_url='login')
def fee_submit(request):
    if request.user.role not in ('student',):
        messages.error(request, 'Only students can submit fee payments.')
        return redirect('fees')
    if request.method == 'POST':
        description    = request.POST.get('description', '').strip()
        amount         = request.POST.get('amount', '').strip()
        transaction_id = request.POST.get('transaction_id', '').strip()
        receipt        = request.FILES.get('receipt')
        if not description or not amount or not receipt:
            messages.error(request, 'Description, amount, and receipt photo are required.')
        else:
            try:
                amt = float(amount)
                if amt <= 0:
                    raise ValueError
            except ValueError:
                messages.error(request, 'Enter a valid positive amount.')
                return redirect('fee_submit')
            FeePayment.objects.create(
                student=request.user,
                description=description,
                amount=amt,
                transaction_id=transaction_id,
                receipt=receipt,
            )
            messages.success(request, 'Payment receipt submitted. Admin will verify shortly.')
            return redirect('fees')
    return render(request, 'accounts/fee_submit.html')


@login_required(login_url='login')
def fee_review(request, pk):
    if request.user.role not in ('admin', 'hod') and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('fees')
    payment = get_object_or_404(FeePayment, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        notes  = request.POST.get('notes', '').strip()
        if action in ('verify', 'reject'):
            payment.status      = 'verified' if action == 'verify' else 'rejected'
            payment.notes       = notes
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save()
            messages.success(request, f'Payment {payment.status}.')
    return redirect('fees')
