from django.urls import path
from . import views

urlpatterns = [
    # Student
    path('courses/', views.available_courses, name='available_courses'),
    path('courses/register/<int:course_id>/', views.register_course, name='register_course'),
    path('courses/drop/<int:reg_id>/', views.drop_course, name='drop_course'),
    path('courses/my-courses/', views.my_courses, name='my_courses'),
    path('courses/grades/', views.my_grades, name='my_grades'),
    # Lecturer
    path('courses/teach/', views.lecturer_courses, name='lecturer_courses'),
    path('courses/teach/<int:course_id>/students/', views.course_students, name='course_students'),
    path('courses/teach/grade/<int:reg_id>/', views.grade_student, name='grade_student'),
    # HOD / Admin
    path('courses/manage/', views.manage_courses, name='manage_courses'),
    path('courses/manage/add/', views.add_course, name='add_course'),
    path('courses/manage/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('courses/manage/<int:course_id>/delete/', views.delete_course, name='delete_course'),
]
