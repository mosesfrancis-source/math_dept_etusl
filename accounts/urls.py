from django.contrib.auth import views as auth_views
from django.urls import path
from . import portal_views, views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('programs/', views.programs, name='programs'),
    path('faculty/', views.faculty_page, name='faculty'),
    path('students/', views.students_page, name='students'),
    path('news/', views.news, name='news'),
    path('contact/', views.contact, name='contact'),
    path('register/', views.register, name='register'),
    path('register/lecturer/', views.register_lecturer, name='register_lecturer'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/password-reset/done/',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/reset/done/',
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('lecturer/', portal_views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/profile/', portal_views.lecturer_portal, {'section': 'profile'}, name='lecturer_profile'),
    path('lecturer/announcements/', portal_views.lecturer_portal, {'section': 'announcements'}, name='lecturer_announcements'),
    path('lecturer/messages/', portal_views.lecturer_portal, {'section': 'messages'}, name='lecturer_messages'),
    path('lecturer/grades/', portal_views.lecturer_portal, {'section': 'grades'}, name='lecturer_grades'),
    path('lecturer/assignments/', portal_views.lecturer_portal, {'section': 'assignments'}, name='lecturer_assignments'),
    path('lecturer/tutorials/', portal_views.lecturer_portal, {'section': 'tutorials'}, name='lecturer_tutorials'),
    path('lecturer/materials/', portal_views.lecturer_portal, {'section': 'materials'}, name='lecturer_materials'),
    path('lecturer/syllabus/', portal_views.lecturer_portal, {'section': 'materials'}, name='lecturer_syllabus'),
    path('lecturer/office-hours/', portal_views.lecturer_portal, {'section': 'office-hours'}, name='lecturer_office_hours'),
    path('lecturer/timetable/', portal_views.lecturer_portal, {'section': 'timetable'}, name='lecturer_timetable'),
    path('lecturer/exams/', portal_views.lecturer_portal, {'section': 'exams'}, name='lecturer_exams'),
    path('lecturer/discussions/', portal_views.lecturer_portal, {'section': 'discussions'}, name='lecturer_discussions'),
    path('lecturer/attendance/', portal_views.lecturer_portal, {'section': 'attendance'}, name='lecturer_attendance'),
    path('lecturer/analytics/', portal_views.lecturer_portal, {'section': 'analytics'}, name='lecturer_analytics'),
    path('portal/pins/', views.admin_pins, name='admin_pins'),
    path('portal/pins/generate/', views.admin_generate_pin, name='admin_generate_pin'),

    # Announcements
    path('announcements/', views.announcements, name='announcements'),
    path('announcements/new/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),

    # Resources
    path('resources/', views.resources, name='resources'),
    path('resources/upload/', views.resource_upload, name='resource_upload'),
    path('resources/<int:pk>/delete/', views.resource_delete, name='resource_delete'),

    # Messages
    path('messages/', views.inbox, name='inbox'),
    path('messages/sent/', views.sent_box, name='sent_box'),
    path('messages/compose/', views.message_compose, name='message_compose'),
    path('messages/<int:pk>/', views.message_thread, name='message_thread'),
    path('messages/<int:pk>/delete/', views.message_delete, name='message_delete'),

    # Settings
    path('settings/', views.settings_view, name='settings'),

    # Fees
    path('fees/', views.fees, name='fees'),
    path('fees/submit/', views.fee_submit, name='fee_submit'),
    path('fees/<int:pk>/review/', views.fee_review, name='fee_review'),

    path('portal/announcements/', portal_views.student_portal, {'section': 'announcements'}, name='student_announcements'),
    path('portal/messages/', portal_views.student_portal, {'section': 'messages'}, name='student_messages'),
    path('portal/assignments/', portal_views.student_portal, {'section': 'assignments'}, name='student_assignments'),
    path('portal/materials/', portal_views.student_portal, {'section': 'materials'}, name='student_materials'),
    path('portal/discussions/', portal_views.student_portal, {'section': 'discussions'}, name='student_discussions'),
    path('portal/grades/', portal_views.student_portal, {'section': 'grades'}, name='student_grades'),
    path('portal/appointments/', portal_views.student_portal, {'section': 'appointments'}, name='student_appointments'),
    path('portal/timetable/', portal_views.student_portal, {'section': 'timetable'}, name='student_timetable'),
]
