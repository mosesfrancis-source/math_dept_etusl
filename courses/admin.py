from django.contrib import admin
from .models import Course, CourseRegistration, Grade


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'credits', 'lecturer', 'semester', 'academic_year',
                    'year_of_study', 'enrolled_count', 'max_students', 'is_active']
    list_filter = ['semester', 'academic_year', 'year_of_study', 'is_active']
    search_fields = ['code', 'name']
    list_editable = ['is_active']


@admin.register(CourseRegistration)
class CourseRegistrationAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'registered_at']
    list_filter = ['status', 'course__semester']
    search_fields = ['student__username', 'student__first_name', 'course__code']
    list_editable = ['status']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['registration', 'score', 'letter_grade', 'grade_point', 'graded_by', 'graded_at']
    list_filter = ['letter_grade']
    search_fields = ['registration__student__username', 'registration__course__code']
    readonly_fields = ['letter_grade', 'grade_point', 'graded_at']
