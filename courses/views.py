from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CourseForm, GradeForm
from .models import Course, CourseRegistration, Grade, calculate_gpa


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ─── Student views ────────────────────────────────────────────────────────────

@login_required(login_url='login')
@role_required('student')
def available_courses(request):
    registered_ids = CourseRegistration.objects.filter(
        student=request.user,
    ).exclude(status='dropped').values_list('course_id', flat=True)

    profile = getattr(request.user, 'student_profile', None)
    qs = Course.objects.filter(is_active=True).exclude(id__in=registered_ids).order_by('code')
    if profile:
        qs = qs.filter(year_of_study=profile.year_of_study)

    sem = request.GET.get('sem', '')
    if sem in ('1', '2'):
        qs = qs.filter(semester=sem)

    context = {
        'courses': qs,
        'active_sem': sem,
        'year_of_study': profile.year_of_study if profile else None,
    }
    return render(request, 'courses/available_courses.html', context)


@login_required(login_url='login')
@role_required('student')
def register_course(request, course_id):
    if request.method != 'POST':
        return redirect('available_courses')

    course = get_object_or_404(Course, id=course_id, is_active=True)

    if course.is_full:
        messages.error(request, f"{course.code} is full ({course.max_students} students max).")
        return redirect('available_courses')

    try:
        CourseRegistration.objects.create(
            student=request.user, course=course, status='approved'
        )
        messages.success(request, f"Registered for {course.code} — {course.name}.")
    except IntegrityError:
        messages.warning(request, f"You are already registered for {course.code}.")

    return redirect('my_courses')


@login_required(login_url='login')
@role_required('student')
def drop_course(request, reg_id):
    if request.method != 'POST':
        return redirect('my_courses')

    reg = get_object_or_404(CourseRegistration, id=reg_id, student=request.user)

    if hasattr(reg, 'grade') and reg.grade.score is not None:
        messages.error(request, "Cannot drop a course that has already been graded.")
        return redirect('my_courses')

    reg.status = 'dropped'
    reg.save()
    messages.success(request, f"Dropped {reg.course.code} successfully.")
    return redirect('my_courses')


@login_required(login_url='login')
@role_required('student')
def my_courses(request):
    registrations = (
        CourseRegistration.objects
        .filter(student=request.user, status='approved')
        .select_related('course', 'course__lecturer', 'grade')
        .order_by('course__code')
    )
    return render(request, 'courses/my_courses.html', {'registrations': registrations})


@login_required(login_url='login')
@role_required('student')
def my_grades(request):
    registrations = (
        CourseRegistration.objects
        .filter(student=request.user, status='approved')
        .select_related('course', 'grade')
        .order_by('course__code')
    )
    gpa = calculate_gpa(request.user)
    return render(request, 'courses/my_grades.html', {
        'registrations': registrations,
        'gpa': gpa,
    })


# ─── Lecturer views ───────────────────────────────────────────────────────────

@login_required(login_url='login')
@role_required('lecturer', 'hod')
def lecturer_courses(request):
    courses = Course.objects.filter(lecturer=request.user, is_active=True)
    return render(request, 'courses/lecturer_courses.html', {'courses': courses})


@login_required(login_url='login')
@role_required('lecturer', 'hod')
def course_students(request, course_id):
    course = get_object_or_404(Course, id=course_id, lecturer=request.user)
    registrations = (
        CourseRegistration.objects
        .filter(course=course, status='approved')
        .select_related('student', 'student__student_profile', 'grade')
        .order_by('student__last_name', 'student__first_name')
    )
    return render(request, 'courses/course_students.html', {
        'course': course,
        'registrations': registrations,
    })


@login_required(login_url='login')
@role_required('lecturer', 'hod')
def grade_student(request, reg_id):
    reg = get_object_or_404(
        CourseRegistration,
        id=reg_id,
        course__lecturer=request.user,
        status='approved',
    )
    grade_obj, _ = Grade.objects.get_or_create(registration=reg)

    if request.method == 'POST':
        form = GradeForm(request.POST, instance=grade_obj)
        if form.is_valid():
            g = form.save(commit=False)
            g.graded_by = request.user
            g.save()
            messages.success(request, f"Grade saved for {reg.student.get_full_name()}.")
            return redirect('course_students', course_id=reg.course.id)
    else:
        form = GradeForm(instance=grade_obj)

    return render(request, 'courses/grade_student.html', {
        'form': form,
        'registration': reg,
    })


# ─── HOD / Admin views ────────────────────────────────────────────────────────

@login_required(login_url='login')
@role_required('hod', 'admin')
def manage_courses(request):
    courses = Course.objects.all().select_related('lecturer').order_by('code')
    return render(request, 'courses/manage_courses.html', {'courses': courses})


@login_required(login_url='login')
@role_required('hod', 'admin')
def add_course(request):
    form = CourseForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Course created successfully.")
        return redirect('manage_courses')
    return render(request, 'courses/course_form.html', {'form': form, 'action': 'Add'})


@login_required(login_url='login')
@role_required('hod', 'admin')
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, instance=course)
    if form.is_valid():
        form.save()
        messages.success(request, "Course updated.")
        return redirect('manage_courses')
    return render(request, 'courses/course_form.html', {
        'form': form, 'action': 'Edit', 'course': course,
    })


@login_required(login_url='login')
@role_required('hod', 'admin')
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        code = course.code
        course.delete()
        messages.success(request, f"Course {code} deleted.")
    return redirect('manage_courses')
