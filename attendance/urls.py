from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from . import views
from . import api_views

urlpatterns = [
	# Auth
	path('', RedirectView.as_view(url='/login/', permanent=False)),
	path('login/', views.login_view, name='login'),
	path('logout/', views.logout_view, name='logout'),
	
	# Teacher
	path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
	path('teacher/attendance/', views.teacher_attendance_list, name='teacher_attendance_list'),
	path('teacher/students/', views.teacher_students, name='teacher_students'),
	path('teacher/student/<uuid:student_id>/', views.teacher_student_detail, name='teacher_student_detail'),
	path('teacher/history/', views.teacher_attendance_history, name='teacher_attendance_history'),
	path('api/teacher/dashboard-stats/', api_views.teacher_dashboard_stats, name='teacher_dashboard_stats'),
	
	# Teacher actions
	path('teacher/mark-attendance/<uuid:student_id>/', views.teacher_mark_attendance, name='teacher_mark_attendance'),
	path('teacher/verify-attendance/<uuid:attendance_id>/', views.teacher_verify_attendance, name='teacher_verify_attendance'),
	path('teacher/add-note/<uuid:attendance_id>/', views.teacher_add_note, name='teacher_add_note'),
	path('teacher/my-schedule/', views.teacher_my_schedule, name='teacher_my_schedule'),

	# Teacher - Period based attendance
	path('teacher/current-classes/', views.teacher_current_classes, name='teacher_current_classes'),
	path('teacher/period-attendance/<uuid:schedule_id>/', views.teacher_take_period_attendance, name='teacher_take_period_attendance'),
	path('teacher/period-attendance/<uuid:schedule_id>/save/', views.teacher_save_period_attendance, name='teacher_save_period_attendance'),
	path('teacher/period-summary/', views.teacher_period_attendance_summary, name='teacher_period_summary'),
	
	# Teacher excuse management URLs
	path('teacher/manage-excuses/', views.teacher_manage_excuses, name='teacher_manage_excuses'),
	path('teacher/excuse/<uuid:excuse_id>/approve/', views.teacher_approve_excuse, name='teacher_approve_excuse'),
	path('teacher/excuse/<uuid:excuse_id>/reject/', views.teacher_reject_excuse, name='teacher_reject_excuse'),


	# Parent
	path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),
	path('parent/history/', views.parent_attendance_history, name='parent_attendance_history'),
	path('parent/request-excuse/', views.parent_request_excuse, name='parent_request_excuse'),
	path('parent/excuse/<uuid:excuse_id>/cancel/', views.parent_cancel_excuse, name='parent_cancel_excuse'),
	path('parent/timetable/', views.parent_student_timetable, name='parent_student_timetable'),

	

	# Password Management
	path('password-change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
	path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
	path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
	path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
	path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
	path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
	
	# API
	path('api/attendance-scan/', api_views.attendance_scan, name='attendance_scan'),
]
