from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, StudentProfile, LecturerProfile, RegistrationPIN,
    Announcement, Resource, Message, FeePayment,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'role']
    list_filter = ['role']
    fieldsets = UserAdmin.fieldsets + (
        ('ETU Info', {'fields': ('role', 'profile_picture', 'phone')}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_id', 'year_of_study']
    search_fields = ['student_id', 'user__first_name', 'user__last_name']


@admin.register(LecturerProfile)
class LecturerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'staff_id', 'specialization', 'is_hod']
    search_fields = ['staff_id', 'user__first_name', 'user__last_name']


@admin.register(RegistrationPIN)
class RegistrationPINAdmin(admin.ModelAdmin):
    list_display = ['pin', 'email', 'role', 'is_used', 'created_by', 'created_at', 'used_at']
    list_filter = ['role', 'is_used']
    search_fields = ['pin', 'email']
    readonly_fields = ['pin', 'created_at', 'used_at', 'used_by']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'target', 'created_by', 'created_at', 'is_active']
    list_filter = ['target', 'is_active']
    search_fields = ['title', 'body']
    readonly_fields = ['created_at']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'uploaded_by', 'created_at', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender', 'recipient', 'sent_at', 'is_read']
    list_filter = ['is_read']
    search_fields = ['subject', 'body', 'sender__username', 'recipient__username']
    readonly_fields = ['sent_at', 'read_at']


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'description', 'amount', 'status', 'submitted_at', 'verified_by']
    list_filter = ['status']
    search_fields = ['student__username', 'description', 'transaction_id']
    readonly_fields = ['submitted_at', 'verified_at']