from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
	Teachers, Class, Students, Attendance, AttendancePeriod,
	ClassSchedule, AcademicYear, ExcusedAbsence, SchoolPeriod
)
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from collections import defaultdict
import json

# Simple login view
def login_view(request):
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		
		user = authenticate(request, username=username, password=password)
		
		if user is not None:
			login(request, user)
			
			# Check if user is a teacher
			if hasattr(user, 'teacher_profile'):
				return redirect('teacher_current_classes')
			
			# Check if user is a parent
			elif hasattr(user, 'parent_profile'):
				return redirect('parent_dashboard')
			
			else:
				return HttpResponse("Account not linked to Teacher or Parent profile")
		else:
			return HttpResponse("Invalid username or password")
	
	return render(request, 'login.html')

# Logout view
def logout_view(request):
	logout(request)
	return redirect('login')

# Teacher dashboard (protected)
@login_required
def teacher_dashboard(request):
	if hasattr(request.user, 'teacher_profile'):
		teacher = request.user.teacher_profile
		return HttpResponse(f"Welcome Teacher: {teacher.teacher_full_name}")
	else:
		return HttpResponse("Access denied - not a teacher")

# Parent dashboard (protected)
@login_required
def parent_dashboard(request):
	"""Parent dashboard - view their child's attendance with period breakdown"""
	
	if not hasattr(request.user, 'parent_profile'):
		return HttpResponse("Access denied - not a parent")
	
	parent = request.user.parent_profile
	student = parent.student
	
	today = timezone.now().date()
	weekday = timezone.now().isoweekday()
	
	# Get today's daily attendance (gate scans)
	today_attendance = Attendance.objects.filter(
		student=student,
		check_in_date=today
	).first()
	
	# Get today's class schedule
	today_schedule = ClassSchedule.objects.filter(
		class_obj=student.student_class,
		day_of_week=weekday,
		is_active=True
	).select_related('period', 'teacher').order_by('period__period_number')
	
	# Get today's period attendance
	period_attendance = AttendancePeriod.objects.filter(
		student=student,
		period_date=today
	).select_related('schedule')
	
	# Create dict for quick lookup
	period_dict = {p.period_number: p for p in period_attendance}
	
	# Combine schedule with attendance status
	schedule_with_status = []
	for schedule in today_schedule:
		period_record = period_dict.get(schedule.period.period_number)
		schedule_with_status.append({
			'schedule': schedule,
			'period_record': period_record,
			'status': period_record.status if period_record else 'not_marked',
			'is_marked': period_record.marked_by_teacher if period_record else None
		})
	
	# Check for excused absence today
	excused_today = ExcusedAbsence.objects.filter(
		student=student,
		start_date__lte=today,
		end_date__gte=today,
		approved_by_homeroom=True
	).first()
	
	# Get this week's attendance (last 7 days)
	week_ago = today - timedelta(days=7)
	week_attendance = Attendance.objects.filter(
		student=student,
		check_in_date__gte=week_ago,
		check_in_date__lte=today
	).order_by('-check_in_date')
	
	# Calculate stats for last 30 days
	thirty_days_ago = today - timedelta(days=30)
	month_attendance = Attendance.objects.filter(
		student=student,
		check_in_date__gte=thirty_days_ago
	)
	
	# Period stats for last 30 days
	month_periods = AttendancePeriod.objects.filter(
		student=student,
		period_date__gte=thirty_days_ago
	)
	
	total_days = month_attendance.count()
	days_with_morning_scan = month_attendance.filter(morning_gate_scan_time__isnull=False).count()
	days_with_afternoon_scan = month_attendance.filter(afternoon_gate_scan_time__isnull=False).count()
	late_days = month_attendance.filter(status='late_arrival').count()
	
	# Period attendance stats
	total_periods = month_periods.count()
	present_periods = month_periods.filter(status='present').count()
	late_periods = month_periods.filter(status='late').count()
	absent_periods = month_periods.filter(status='absent').count()
	
	# Calculate attendance rate
	if total_periods > 0:
		attendance_rate = (present_periods / total_periods) * 100
	else:
		attendance_rate = 0
	
	# Recent alerts (absences in last 7 days)
	recent_absences = AttendancePeriod.objects.filter(
		student=student,
		period_date__gte=week_ago,
		status__in=['absent', 'sneaked_out']
	).select_related('schedule').order_by('-period_date', '-period_number')[:5]
	
	context = {
		'parent': parent,
		'student': student,
		'today': today,
		'today_attendance': today_attendance,
		'schedule_with_status': schedule_with_status,
		'excused_today': excused_today,
		'week_attendance': week_attendance,
		'total_days': total_days,
		'days_with_morning_scan': days_with_morning_scan,
		'days_with_afternoon_scan': days_with_afternoon_scan,
		'late_days': late_days,
		'total_periods': total_periods,
		'present_periods': present_periods,
		'late_periods': late_periods,
		'absent_periods': absent_periods,
		'attendance_rate': round(attendance_rate, 1),
		'recent_absences': recent_absences,
	}
	
	return render(request, 'parent/dashboard.html', context)


@login_required
def teacher_dashboard(request):
	"""Teacher dashboard - today's attendance overview"""
	
	# Check if user is a teacher
	if not hasattr(request.user, 'teacher_profile'):
		return HttpResponse("Access denied - not a teacher")
	
	teacher = request.user.teacher_profile
	
	# Get teacher's class (assuming homeroom_classes relationship)
	teacher_classes = teacher.homeroom_classes.all()
	
	# If teacher has no class assigned
	if not teacher_classes.exists():
		return render(request, 'teacher/dashboard.html', {
			'teacher': teacher,
			'no_class': True
		})
	
	# Get today's date
	now = timezone.now()
	local_now = timezone.localtime(now)
	today = local_now.date()
	
	# Statistics for all teacher's classes
	total_students = Students.objects.filter(
		student_class__in=teacher_classes,
		student_active_status=True
	).count()
	
	# Today's attendance
	today_attendance = Attendance.objects.filter(
		student__student_class__in=teacher_classes,
		check_in_date=today
	)
	
	present_count = today_attendance.filter(status='attended').count()
	late_count = today_attendance.filter(status='late').count()
	absent_count = total_students - (present_count + late_count)
	
	# Recent scans (last 10)
	recent_scans = Attendance.objects.filter(
		student__student_class__in=teacher_classes,
		check_in_date=today
	).order_by('-check_in_time')[:10]
	
	context = {
		'teacher': teacher,
		'teacher_classes': teacher_classes,
		'total_students': total_students,
		'present_count': present_count,
		'late_count': late_count,
		'absent_count': absent_count,
		'recent_scans': recent_scans,
		'today': today,
	}
	
	return render(request, 'teacher/dashboard.html', context)


@login_required
def teacher_attendance_list(request):
	"""View full attendance list for today"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return HttpResponse("Access denied")
	
	teacher = request.user.teacher_profile
	teacher_classes = teacher.homeroom_classes.all()
	
	if not teacher_classes.exists():
		return render(request, 'teacher/attendance_list.html', {
			'no_class': True
		})
	
	now = timezone.now()
	local_now = timezone.localtime(now)
	today = local_now.date()
	
	# Get all students in teacher's classes
	students = Students.objects.filter(
		student_class__in=teacher_classes,
		student_active_status=True
	).order_by('student_class', 'student_full_name')
	
	# Get today's attendance records
	today_attendance = Attendance.objects.filter(
		check_in_date=today
	).select_related('student')
	
	# Create a dict for quick lookup
	attendance_dict = {att.student.student_id: att for att in today_attendance}
	
	# Combine student list with attendance status
	student_attendance = []
	for student in students:
		attendance = attendance_dict.get(student.student_id)
		student_attendance.append({
			'student': student,
			'attendance': attendance,
			'status': attendance.status if attendance else 'absent',
			'check_in_time': attendance.check_in_time if attendance else None,
		})
	
	context = {
		'teacher': teacher,
		'student_attendance': student_attendance,
		'today': today,
	}
	
	return render(request, 'teacher/attendance_list.html', context)


@login_required
def teacher_students(request):
	"""View all students in teacher's class"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return HttpResponse("Access denied")
	
	teacher = request.user.teacher_profile
	teacher_classes = teacher.homeroom_classes.all()
	
	students = Students.objects.filter(
		student_class__in=teacher_classes,
		student_active_status=True
	).order_by('student_class', 'student_full_name')
	
	context = {
		'teacher': teacher,
		'students': students,
	}
	
	return render(request, 'teacher/students.html', context)


@login_required
@require_http_methods(["POST"])
def teacher_mark_attendance(request, student_id):
	"""Manually mark student attendance"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return JsonResponse({'error': 'Access denied'}, status=403)
	
	teacher = request.user.teacher_profile
	student = get_object_or_404(Students, student_id=student_id)
	
	# Check if student is in teacher's class
	if student.student_class not in teacher.homeroom_classes.all():
		return JsonResponse({'error': 'Student not in your class'}, status=403)
	
	# Get status from POST data
	status = request.POST.get('status', 'attended')
	if status not in ['attended', 'late', 'absent']:
		return JsonResponse({'error': 'Invalid status'}, status=400)
	
	# Get today's date
	now = timezone.now()  # This is in UTC
	local_now = timezone.localtime(now)
	today = local_now.date() 
	
	# Get active academic year
	try:
		academic_year = AcademicYear.objects.get(academic_year_active_status=True)
	except AcademicYear.DoesNotExist:
		return JsonResponse({'error': 'No active academic year'}, status=400)
	
	# Check if already marked today
	existing = Attendance.objects.filter(
		student=student,
		check_in_date=today
	).first()
	
	if existing:
		# Update existing record
		existing.status = status
		existing.is_verified_by_teacher = True
		existing.verified_at = timezone.now()
		existing.save()
		
		return JsonResponse({
			'success': True,
			'message': 'Attendance updated',
			'status': status
		})
	else:
		# Create new record
		attendance = Attendance.objects.create(
			student=student,
			academic_year=academic_year,
			status=status,
			is_verified_by_teacher=True,
			verified_at=timezone.now(),
			device_id='manual_entry'
		)
		
		return JsonResponse({
			'success': True,
			'message': 'Attendance marked',
			'status': status
		})


@login_required
@require_http_methods(["POST"])
def teacher_verify_attendance(request, attendance_id):
	"""Verify an IoT-scanned attendance record"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return JsonResponse({'error': 'Access denied'}, status=403)
	
	teacher = request.user.teacher_profile
	attendance = get_object_or_404(Attendance, attendance_id=attendance_id)
	
	# Check if student is in teacher's class
	if attendance.student.student_class not in teacher.homeroom_classes.all():
		return JsonResponse({'error': 'Student not in your class'}, status=403)
	
	# Mark as verified
	attendance.is_verified_by_teacher = True
	attendance.verified_at = timezone.now()
	attendance.save()
	
	return JsonResponse({
		'success': True,
		'message': 'Attendance verified'
	})


@login_required
@require_http_methods(["POST"])
def teacher_add_note(request, attendance_id):
	"""Add or update notes on attendance record"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return JsonResponse({'error': 'Access denied'}, status=403)
	
	teacher = request.user.teacher_profile
	attendance = get_object_or_404(Attendance, attendance_id=attendance_id)
	
	# Check if student is in teacher's class
	if attendance.student.student_class not in teacher.homeroom_classes.all():
		return JsonResponse({'error': 'Student not in your class'}, status=403)
	
	# Get note from POST data
	note = request.POST.get('note', '').strip()
	
	attendance.notes = note
	attendance.save()
	
	return JsonResponse({
		'success': True,
		'message': 'Note saved'
	})


@login_required
def teacher_students(request):
	"""View all students in teacher's class with attendance stats"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return HttpResponse("Access denied")
	
	teacher = request.user.teacher_profile
	teacher_classes = teacher.homeroom_classes.all()
	
	if not teacher_classes.exists():
		return render(request, 'teacher/students.html', {
			'no_class': True
		})
	
	# Get all students in teacher's classes
	students = Students.objects.filter(
		student_class__in=teacher_classes,
		student_active_status=True
	).order_by('student_class', 'student_full_name')
	
	# Calculate attendance stats for each student
	from django.db.models import Count, Q
	from datetime import timedelta
	
	now = timezone.now()  
	local_now = timezone.localtime(now)  
	today = local_now.date()
	thirty_days_ago = today - timedelta(days=30)
	
	student_stats = []
	for student in students:
		# Get attendance records for last 30 days
		attendance_records = Attendance.objects.filter(
			student=student,
			check_in_date__gte=thirty_days_ago,
			check_in_date__lte=today
		)
		
		total_days = attendance_records.count()
		present_days = attendance_records.filter(status='attended').count()
		late_days = attendance_records.filter(status='late').count()
		
		# Calculate attendance rate
		if total_days > 0:
			attendance_rate = (present_days / total_days) * 100
		else:
			attendance_rate = 0
		
		student_stats.append({
			'student': student,
			'total_days': total_days,
			'present_days': present_days,
			'late_days': late_days,
			'attendance_rate': round(attendance_rate, 1)
		})
	
	context = {
		'teacher': teacher,
		'student_stats': student_stats,
	}
	
	return render(request, 'teacher/students.html', context)


@login_required
def teacher_student_detail(request, student_id):
	"""View detailed info about a specific student"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return HttpResponse("Access denied")
	
	teacher = request.user.teacher_profile
	student = get_object_or_404(Students, student_id=student_id)
	
	# Check if student is in teacher's class
	if student.student_class not in teacher.homeroom_classes.all():
		return HttpResponse("Access denied - Student not in your class")
	
	# Get parent info
	parent = student.parents.first()
	
	# Get recent attendance (last 30 days)
	from datetime import timedelta
	now = timezone.now()  
	local_now = timezone.localtime(now)  
	today = local_now.date()
	thirty_days_ago = today - timedelta(days=30)
	
	recent_attendance = Attendance.objects.filter(
		student=student,
		check_in_date__gte=thirty_days_ago
	).order_by('-check_in_date')[:30]
	
	# Calculate stats
	total_days = recent_attendance.count()
	present_days = recent_attendance.filter(status='attended').count()
	late_days = recent_attendance.filter(status='late').count()
	absent_days = 30 - total_days  # Approximate
	
	context = {
		'teacher': teacher,
		'student': student,
		'parent': parent,
		'recent_attendance': recent_attendance,
		'total_days': total_days,
		'present_days': present_days,
		'late_days': late_days,
		'absent_days': absent_days,
	}
	
	return render(request, 'teacher/student_detail.html', context)


@login_required
def teacher_attendance_history(request):
	"""View attendance history with date filters"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return HttpResponse("Access denied")
	
	teacher = request.user.teacher_profile
	teacher_classes = teacher.homeroom_classes.all()
	
	if not teacher_classes.exists():
		return render(request, 'teacher/attendance_history.html', {
			'no_class': True
		})
	
	# Get date filters from GET parameters
	from datetime import timedelta
	now = timezone.now()  
	local_now = timezone.localtime(now)  
	today = local_now.date()
	
	# Default to last 7 days
	start_date = request.GET.get('start_date')
	end_date = request.GET.get('end_date')
	
	if start_date:
		start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
	else:
		start_date = today - timedelta(days=7)
	
	if end_date:
		end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
	else:
		end_date = today
	
	# Get attendance records
	attendance_records = Attendance.objects.filter(
		student__student_class__in=teacher_classes,
		check_in_date__gte=start_date,
		check_in_date__lte=end_date
	).select_related('student', 'student__student_class').order_by('-check_in_date', '-check_in_time')
	
	# Calculate summary stats
	total_records = attendance_records.count()
	present_count = attendance_records.filter(status='attended').count()
	late_count = attendance_records.filter(status='late').count()
	
	context = {
		'teacher': teacher,
		'attendance_records': attendance_records,
		'start_date': start_date,
		'end_date': end_date,
		'total_records': total_records,
		'present_count': present_count,
		'late_count': late_count,
	}
	
	return render(request, 'teacher/attendance_history.html', context)

@login_required
def parent_dashboard(request):
	"""Parent dashboard - view their child's attendance"""
	
	if not hasattr(request.user, 'parent_profile'):
		return HttpResponse("Access denied - not a parent")
	
	parent = request.user.parent_profile
	student = parent.student
	
	# Get today's attendance
	now = timezone.now() 
	local_now = timezone.localtime(now)
	today = local_now.date()
	today_attendance = Attendance.objects.filter(
		student=student,
		check_in_date=today
	).first()
	
	# Get this week's attendance (last 7 days)
	from datetime import timedelta
	week_ago = today - timedelta(days=7)
	week_attendance = Attendance.objects.filter(
		student=student,
		check_in_date__gte=week_ago,
		check_in_date__lte=today
	).order_by('-check_in_date')
	
	# Calculate stats for last 30 days
	thirty_days_ago = today - timedelta(days=30)
	month_attendance = Attendance.objects.filter(
		student=student,
		check_in_date__gte=thirty_days_ago
	)
	
	total_days = month_attendance.count()
	present_days = month_attendance.filter(status='attended').count()
	late_days = month_attendance.filter(status='late').count()
	
	if total_days > 0:
		attendance_rate = (present_days / total_days) * 100
	else:
		attendance_rate = 0
	
	context = {
		'parent': parent,
		'student': student,
		'today_attendance': today_attendance,
		'week_attendance': week_attendance,
		'total_days': total_days,
		'present_days': present_days,
		'late_days': late_days,
		'attendance_rate': round(attendance_rate, 1),
		'today': today,
	}
	
	return render(request, 'parent/dashboard.html', context)


@login_required
def parent_attendance_history(request):
	"""Parent view detailed attendance history of their child"""
	
	if not hasattr(request.user, 'parent_profile'):
		return HttpResponse("Access denied")
	
	parent = request.user.parent_profile
	student = parent.student
	
	now = timezone.now()  
	local_now = timezone.localtime(now)  
	today = local_now.date()
	
	# Get date filters
	start_date = request.GET.get('start_date')
	end_date = request.GET.get('end_date')
	
	if start_date:
		start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
	else:
		start_date = today - timedelta(days=30)
	
	if end_date:
		end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
	else:
		end_date = today
	
	# Get daily attendance records
	attendance_records = Attendance.objects.filter(
		student=student,
		check_in_date__gte=start_date,
		check_in_date__lte=end_date
	).order_by('-check_in_date')
	
	# Get period attendance for each day
	period_records = AttendancePeriod.objects.filter(
		student=student,
		period_date__gte=start_date,
		period_date__lte=end_date
	).select_related('schedule').order_by('-period_date', 'period_number')
	
	# Group periods by date
	periods_by_date = defaultdict(list)
	for period in period_records:
		periods_by_date[period.period_date].append(period)
	
	# Combine daily and period data
	detailed_history = []
	for daily in attendance_records:
		day_periods = periods_by_date.get(daily.check_in_date, [])
		
		# Count period statuses
		present_count = sum(1 for p in day_periods if p.status == 'present')
		late_count = sum(1 for p in day_periods if p.status == 'late')
		absent_count = sum(1 for p in day_periods if p.status == 'absent')
		excused_count = sum(1 for p in day_periods if p.status == 'excused')
		
		detailed_history.append({
			'date': daily.check_in_date,
			'daily_attendance': daily,
			'periods': day_periods,
			'total_periods': len(day_periods),
			'present_count': present_count,
			'late_count': late_count,
			'absent_count': absent_count,
			'excused_count': excused_count
		})
	
	# Calculate summary stats for the date range
	total_days_in_range = attendance_records.count()
	total_periods_in_range = period_records.count()
	present_periods_in_range = period_records.filter(status='present').count()
	late_periods_in_range = period_records.filter(status='late').count()
	absent_periods_in_range = period_records.filter(status='absent').count()
	
	if total_periods_in_range > 0:
		range_attendance_rate = (present_periods_in_range / total_periods_in_range) * 100
	else:
		range_attendance_rate = 0
	
	context = {
		'parent': parent,
		'student': student,
		'start_date': start_date,
		'end_date': end_date,
		'detailed_history': detailed_history,
		'total_days_in_range': total_days_in_range,
		'total_periods_in_range': total_periods_in_range,
		'present_periods_in_range': present_periods_in_range,
		'late_periods_in_range': late_periods_in_range,
		'absent_periods_in_range': absent_periods_in_range,
		'range_attendance_rate': round(range_attendance_rate, 1),
	}
	
	return render(request, 'parent/attendance_history.html', context)

@login_required
def teacher_current_classes(request):
	"""Show classes teacher is teaching today with their periods"""
	if not hasattr(request.user, 'teacher_profile'):
		return redirect('login')

	teacher = request.user.teacher_profile
	now = timezone.now()

	
	local_now = timezone.localtime(now)
	today = local_now.date()
	current_time = local_now.time()
	weekday = local_now.isoweekday()

	try:
		active_year = AcademicYear.objects.get(academic_year_active_status=True)
	except AcademicYear.DoesNotExist:
		return render(request, 'teacher/current_classes.html', {
			'error': 'Không tìm thấy năm học đang hoạt động'
		})

	# Get all schedules for this teacher today
	schedules_today = ClassSchedule.objects.filter(
		teacher=teacher,
		academic_year=active_year,
		day_of_week=weekday,
		is_active=True
	).select_related('class_obj', 'period').order_by('period__period_number')

	# Determine current period
	current_period = None
	current_schedule = None
	
	for schedule in schedules_today:
		if schedule.period.start_time <= current_time <= schedule.period.end_time:
			current_period = schedule.period
			current_schedule = schedule
			break

	# Get attendance summary for each class
	schedules_with_stats = []
	for schedule in schedules_today:
		class_obj = schedule.class_obj
		
		# Total students in class
		total_students = Students.objects.filter(
			student_class=class_obj,
			student_active_status=True
		).count()
		
		# Gate scans today
		morning_scanned = Attendance.objects.filter(
			student__student_class=class_obj,
			check_in_date=today,
			morning_gate_scan_time__isnull=False
		).count()
		
		# Period attendance (if marked)
		period_marked = AttendancePeriod.objects.filter(
			schedule=schedule,
			period_date=today,
			marked_by_teacher__isnull=False
		).count()
		
		is_marked = period_marked > 0
		is_current = (schedule == current_schedule)
		
		schedules_with_stats.append({
			'schedule': schedule,
			'total_students': total_students,
			'morning_scanned': morning_scanned,
			'is_marked': is_marked,
			'is_current': is_current,
			'marked_count': period_marked
		})

	context = {
		'teacher': teacher,
		'schedules_with_stats': schedules_with_stats,
		'current_period': current_period,
		'current_schedule': current_schedule,
		'today': today,
		'current_time': now,
		'no_class_today': not schedules_today.exists()
	}

	return render(request, 'teacher/current_classes.html', context)


@login_required
def teacher_take_period_attendance(request, schedule_id):
	"""Main view for taking attendance for a specific period"""
	if not hasattr(request.user, 'teacher_profile'):
		return redirect('login')

	schedule = get_object_or_404(ClassSchedule, schedule_id=schedule_id)
	teacher = request.user.teacher_profile

	# Security check: Only assigned teacher can mark
	if schedule.teacher != teacher:
		return render(request, 'teacher/period_attendance.html', {
			'error': 'Bạn không được phân công dạy tiết này',
			'schedule': schedule
		})

	class_obj = schedule.class_obj
	now = timezone.now()  
	local_now = timezone.localtime(now)  
	today = local_now.date()
	period_number = schedule.period.period_number

	# Get all active students in this class, ordered by tổ and seat
	students = Students.objects.filter(
		student_class=class_obj,
		student_active_status=True
	).order_by('to_number', 'seat_number')

	# Group students by Tổ
	groups = defaultdict(list)
	for student in students:
		to_num = student.to_number if student.to_number else 0
		groups[to_num].append(student)

	# Get today's gate attendance for all students
	gate_attendance_dict = {}
	gate_attendance = Attendance.objects.filter(
		student__in=students,
		check_in_date=today
	)
	for att in gate_attendance:
		gate_attendance_dict[att.student.student_id] = att

	# Get excused absences for today
	excused_dict = {}
	excused_absences = ExcusedAbsence.objects.filter(
		student__in=students,
		start_date__lte=today,
		end_date__gte=today,
		approved_by_homeroom=True
	)
	for excuse in excused_absences:
		# Check if excuse applies to this period
		if excuse.applies_to_period(period_number):
			excused_dict[excuse.student.student_id] = excuse

	# Get or create period attendance records
	period_records = {}
	for student in students:
		# Get daily attendance
		daily_attendance = gate_attendance_dict.get(student.student_id)
		
		# Get or create period record
		record, created = AttendancePeriod.objects.get_or_create(
			student=student,
			period_date=today,
			period_number=period_number,
			defaults={
				'attendance': daily_attendance,
				'schedule': schedule,
				'subject_name': schedule.subject_name,
				'status': 'absent'  # Default status
			}
		)

		# Auto-initialize status if not yet marked by teacher
		if created or not record.marked_by_teacher:
			if student.student_id in excused_dict:
				# Student has approved excuse
				record.status = 'excused'
				record.notes = f"Excused: {excused_dict[student.student_id].reason}"
			elif daily_attendance and daily_attendance.morning_gate_scan_time:
				# Student scanned gate in morning
				if daily_attendance.status == 'late_arrival':
					record.status = 'late'
				else:
					record.status = 'present'
			else:
				# No gate scan - likely absent
				record.status = 'absent'
			
			record.save()

		period_records[student.student_id] = record

	# Count statistics
	total_students = students.count()
	excused_count = len(excused_dict)
	expected_count = total_students - excused_count
	
	present_count = sum(1 for r in period_records.values() if r.status == 'present')
	late_count = sum(1 for r in period_records.values() if r.status == 'late')
	absent_count = sum(1 for r in period_records.values() if r.status == 'absent')
	
	# Check if already marked
	already_marked = any(r.marked_by_teacher for r in period_records.values())

	context = {
		'teacher': teacher,
		'class_obj': class_obj,
		'schedule': schedule,
		'period': schedule.period,
		'groups': dict(sorted(groups.items())),  # Sort by tổ number
		'period_records': period_records,
		'gate_attendance_dict': gate_attendance_dict,
		'excused_dict': excused_dict,
		'today': today,
		'total_students': total_students,
		'expected_count': expected_count,
		'excused_count': excused_count,
		'present_count': present_count,
		'late_count': late_count,
		'absent_count': absent_count,
		'already_marked': already_marked
	}

	return render(request, 'teacher/period_attendance.html', context)


@require_POST
@login_required
def teacher_save_period_attendance(request, schedule_id):
	"""AJAX endpoint to save period attendance"""
	if not hasattr(request.user, 'teacher_profile'):
		return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

	schedule = get_object_or_404(ClassSchedule, schedule_id=schedule_id)
	teacher = request.user.teacher_profile

	# Security check
	if schedule.teacher != teacher:
		return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

	try:
		data = json.loads(request.body)
	except json.JSONDecodeError:
		return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

	now = timezone.now()  
	local_now = timezone.localtime(now)  
	today = local_now.date()
	period_number = schedule.period.period_number
	updated_students = []

	# Handle "Mark All Present" action
	if data.get('mark_all_present'):
		students = Students.objects.filter(
			student_class=schedule.class_obj,
			student_active_status=True
		)
		
		for student in students:
			record = AttendancePeriod.objects.filter(
				student=student,
				period_date=today,
				period_number=period_number
			).first()
			
			if record:
				# Don't override excused absences
				if record.status != 'excused':
					record.status = 'present'
				record.marked_by_teacher = teacher
				record.marked_at = timezone.now()
				record.is_verified = True
				record.save()
				updated_students.append({
					'id': str(student.student_id),
					'name': student.student_full_name,
					'status': record.status
				})

		return JsonResponse({
			'success': True,
			'message': f'Marked {len(updated_students)} students',
			'updated': updated_students
		})

	# Handle individual student status update
	elif data.get('student_id') and data.get('status'):
		student_id = data.get('student_id')
		new_status = data.get('status')
		notes = data.get('notes', '')

		# Validate status
		valid_statuses = ['present', 'absent', 'late', 'excused', 'sneaked_out']
		if new_status not in valid_statuses:
			return JsonResponse({
				'success': False,
				'error': f'Invalid status: {new_status}'
			}, status=400)

		record = AttendancePeriod.objects.filter(
			student_id=student_id,
			period_date=today,
			period_number=period_number
		).first()

		if not record:
			return JsonResponse({
				'success': False,
				'error': 'Attendance record not found'
			}, status=404)

		# Update record
		record.status = new_status
		record.marked_by_teacher = teacher
		record.marked_at = timezone.now()
		record.is_verified = True
		if notes:
			record.notes = notes
		record.save()

		return JsonResponse({
			'success': True,
			'message': 'Status updated',
			'student_id': student_id,
			'status': new_status
		})

	else:
		return JsonResponse({
			'success': False,
			'error': 'Missing required parameters'
		}, status=400)


@login_required
def teacher_period_attendance_summary(request):
	"""View summary of all periods marked today"""
	if not hasattr(request.user, 'teacher_profile'):
		return redirect('login')

	teacher = request.user.teacher_profile
	now = timezone.now()  
	local_now = timezone.localtime(now)  
	today = local_now.date()
	weekday = local_now.isoweekday()

	try:
		active_year = AcademicYear.objects.get(academic_year_active_status=True)
	except AcademicYear.DoesNotExist:
		return render(request, 'teacher/period_summary.html', {
			'error': 'No active academic year'
		})

	# Get all periods taught today
	schedules = ClassSchedule.objects.filter(
		teacher=teacher,
		academic_year=active_year,
		day_of_week=weekday,
		is_active=True
	).select_related('class_obj', 'period').order_by('period__period_number')

	# Get attendance data for each period
	summary_data = []
	for schedule in schedules:
		class_obj = schedule.class_obj
		period_num = schedule.period.period_number
		
		total_students = Students.objects.filter(
			student_class=class_obj,
			student_active_status=True
		).count()
		
		period_attendance = AttendancePeriod.objects.filter(
			schedule=schedule,
			period_date=today
		)
		
		present = period_attendance.filter(status='present').count()
		late = period_attendance.filter(status='late').count()
		absent = period_attendance.filter(status='absent').count()
		excused = period_attendance.filter(status='excused').count()
		marked = period_attendance.filter(marked_by_teacher__isnull=False).count()
		
		summary_data.append({
			'schedule': schedule,
			'total': total_students,
			'present': present,
			'late': late,
			'absent': absent,
			'excused': excused,
			'is_marked': marked > 0,
			'completion': round((marked / total_students * 100) if total_students > 0 else 0, 1)
		})

	context = {
		'teacher': teacher,
		'summary_data': summary_data,
		'today': today
	}

	return render(request, 'teacher/period_summary.html', context)

@login_required
def parent_request_excuse(request):
	"""Parent can request excused absence for their child"""
	
	if not hasattr(request.user, 'parent_profile'):
		return HttpResponse("Access denied - not a parent")
	
	parent = request.user.parent_profile
	student = parent.student
	
	if request.method == 'POST':
		# Get form data
		start_date = request.POST.get('start_date')
		end_date = request.POST.get('end_date')
		absence_type = request.POST.get('absence_type')
		specific_periods = request.POST.get('specific_periods', '')
		reason = request.POST.get('reason')
		
		# Validate dates
		try:
			start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
			end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
		except (ValueError, TypeError):
			return render(request, 'parent/request_excuse.html', {
				'error': 'Ngày không hợp lệ',
				'student': student
			})
		
		# Validate date range
		if end_date < start_date:
			return render(request, 'parent/request_excuse.html', {
				'error': 'Ngày kết thúc phải sau ngày bắt đầu',
				'student': student
			})
		
		# Validate reason
		if not reason or len(reason.strip()) < 10:
			return render(request, 'parent/request_excuse.html', {
				'error': 'Lý do phải có ít nhất 10 ký tự',
				'student': student
			})
		
		# Validate specific periods if needed
		if absence_type == 'specific_periods':
			if not specific_periods:
				return render(request, 'parent/request_excuse.html', {
					'error': 'Vui lòng chọn các tiết cụ thể',
					'student': student
				})
			# Validate period format (should be comma-separated numbers)
			try:
				periods = [int(p.strip()) for p in specific_periods.split(',')]
				if not all(1 <= p <= 8 for p in periods):
					raise ValueError
				specific_periods = ','.join(map(str, sorted(periods)))
			except ValueError:
				return render(request, 'parent/request_excuse.html', {
					'error': 'Tiết học không hợp lệ (1-8)',
					'student': student
				})
		
		# Create excuse request
		excuse = ExcusedAbsence.objects.create(
			student=student,
			start_date=start_date,
			end_date=end_date,
			absence_type=absence_type,
			specific_periods=specific_periods if absence_type == 'specific_periods' else '',
			reason=reason.strip(),
			parent_contact_method='Web Portal',
			approved_by_homeroom=False  # Pending approval
		)
		
		# Success message
		return render(request, 'parent/request_excuse.html', {
			'success': 'Đã gửi đơn xin phép thành công! Chờ giáo viên chủ nhiệm phê duyệt.',
			'student': student,
			'excuse_requests': ExcusedAbsence.objects.filter(student=student).order_by('-created_at')[:10]
		})
	
	# GET request - show form
	# Get recent requests
	recent_requests = ExcusedAbsence.objects.filter(
		student=student
	).order_by('-created_at')[:10]
	
	context = {
		'parent': parent,
		'student': student,
		'excuse_requests': recent_requests,
		'today': timezone.now().date()
	}
	
	return render(request, 'parent/request_excuse.html', context)


@login_required
@require_POST
def parent_cancel_excuse(request, excuse_id):
	"""Parent can cancel pending excuse request"""
	
	if not hasattr(request.user, 'parent_profile'):
		return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
	
	parent = request.user.parent_profile
	excuse = get_object_or_404(ExcusedAbsence, excuse_id=excuse_id)
	
	# Check if this excuse belongs to parent's child
	if excuse.student != parent.student:
		return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
	
	# Can only cancel if not yet approved
	if excuse.approved_by_homeroom:
		return JsonResponse({
			'success': False, 
			'error': 'Không thể hủy đơn đã được duyệt'
		}, status=400)
	
	# Delete the excuse
	excuse.delete()
	
	return JsonResponse({
		'success': True,
		'message': 'Đã hủy đơn xin phép'
	})


# ============================================================================
# TEACHER VIEWS - Approve/Reject Excuses
# ============================================================================

@login_required
def teacher_manage_excuses(request):
	"""Homeroom teacher can approve/reject excuse requests"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return HttpResponse("Access denied - not a teacher")
	
	teacher = request.user.teacher_profile
	teacher_classes = teacher.homeroom_classes.all()
	
	if not teacher_classes.exists():
		return render(request, 'teacher/manage_excuses.html', {
			'no_class': True
		})
	
	# Get all excuse requests for students in teacher's classes
	pending_requests = ExcusedAbsence.objects.filter(
		student__student_class__in=teacher_classes,
		approved_by_homeroom=False
	).select_related('student', 'student__student_class').order_by('-created_at')
	
	approved_requests = ExcusedAbsence.objects.filter(
		student__student_class__in=teacher_classes,
		approved_by_homeroom=True
	).select_related('student', 'student__student_class').order_by('-approved_at')[:20]
	
	context = {
		'teacher': teacher,
		'pending_requests': pending_requests,
		'approved_requests': approved_requests,
		'pending_count': pending_requests.count()
	}
	
	return render(request, 'teacher/manage_excuses.html', context)


@login_required
@require_POST
def teacher_approve_excuse(request, excuse_id):
	"""Teacher approves an excuse request"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
	
	teacher = request.user.teacher_profile
	excuse = get_object_or_404(ExcusedAbsence, excuse_id=excuse_id)
	
	# Check if student is in teacher's homeroom class
	if excuse.student.student_class not in teacher.homeroom_classes.all():
		return JsonResponse({
			'success': False, 
			'error': 'Student not in your homeroom class'
		}, status=403)
	
	# Approve the excuse
	excuse.approved_by_homeroom = True
	excuse.approved_at = timezone.now()
	excuse.save()
	
	return JsonResponse({
		'success': True,
		'message': f'Đã phê duyệt đơn xin phép cho {excuse.student.student_full_name}'
	})


@login_required
@require_POST
def teacher_reject_excuse(request, excuse_id):
	"""Teacher rejects an excuse request"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
	
	teacher = request.user.teacher_profile
	excuse = get_object_or_404(ExcusedAbsence, excuse_id=excuse_id)
	
	# Check if student is in teacher's homeroom class
	if excuse.student.student_class not in teacher.homeroom_classes.all():
		return JsonResponse({
			'success': False, 
			'error': 'Student not in your homeroom class'
		}, status=403)
	
	try:
		data = json.loads(request.body)
		reject_reason = data.get('reason', 'Không được phê duyệt')
	except:
		reject_reason = 'Không được phê duyệt'
	
	# Add rejection note and delete
	student_name = excuse.student.student_full_name
	excuse.notes = f"Rejected by {teacher.teacher_full_name}: {reject_reason}"
	excuse.delete()
	
	return JsonResponse({
		'success': True,
		'message': f'Đã từ chối đơn xin phép của {student_name}'
	})

def teacher_my_schedule(request):
	"""Teacher views their daily/weekly teaching schedule"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return HttpResponse("Access denied - not a teacher")
	
	teacher = request.user.teacher_profile
	
	# FIX: Use local timezone consistently
	now = timezone.localtime(timezone.now())
	today = now.date()
	current_time = now.time()
	today_weekday = now.isoweekday()
	
	# Get selected day from query params (default to today)
	selected_day = request.GET.get('day')
	if selected_day:
		try:
			selected_day = int(selected_day)
		except (ValueError, TypeError):
			selected_day = today_weekday  
	else:
		selected_day = today_weekday  
	
	try:
		active_year = AcademicYear.objects.get(academic_year_active_status=True)
	except AcademicYear.DoesNotExist:
		return render(request, 'teacher/my_schedule.html', {
			'error': 'No active academic year'
		})
	
	# Get teacher's schedule for selected day
	daily_schedule = ClassSchedule.objects.filter(
		teacher=teacher,
		academic_year=active_year,
		day_of_week=selected_day,
		is_active=True
	).select_related('class_obj', 'period').order_by('period__period_number')
	
	# Get all periods to show empty slots
	all_periods = SchoolPeriod.objects.filter(is_active=True).order_by('period_number')
	
	# Create schedule with all periods (show empty if not teaching)
	schedule_with_status = []
	period_dict = {s.period.period_number: s for s in daily_schedule}
	
	for period in all_periods:
		schedule_item = period_dict.get(period.period_number)
		
		is_current = False
		is_past = False
		is_upcoming = False
		
		# Determine time status (only for today)
		if selected_day == today_weekday:  
			if period.start_time <= current_time <= period.end_time:
				is_current = True
			elif current_time > period.end_time:
				is_past = True
			else:
				is_upcoming = True
		
		schedule_with_status.append({
			'period': period,
			'schedule': schedule_item,
			'has_class': schedule_item is not None,
			'is_current': is_current,
			'is_past': is_past,
			'is_upcoming': is_upcoming
		})
	
	# Get weekly summary (total periods per day)
	weekly_summary = []
	days = [
		(1, 'Thứ Hai'),
		(2, 'Thứ Ba'),
		(3, 'Thứ Tư'),
		(4, 'Thứ Năm'),
		(5, 'Thứ Sáu'),
		(6, 'Thứ Bảy')
	]
	
	for day_num, day_name in days:
		day_schedule = ClassSchedule.objects.filter(
			teacher=teacher,
			academic_year=active_year,
			day_of_week=day_num,
			is_active=True
		).select_related('class_obj')
		
		weekly_summary.append({
			'day_num': day_num,
			'day_name': day_name,
			'total_periods': day_schedule.count(),
			'is_selected': day_num == selected_day,
			'is_today': day_num == today_weekday  
		})
	
	context = {
		'teacher': teacher,
		'schedule_with_status': schedule_with_status,
		'weekly_summary': weekly_summary,
		'selected_day': selected_day,
		'selected_day_name': dict(days).get(selected_day, ''),
		'today': today,
		'current_time': current_time,
		'total_today': daily_schedule.count()
	}
	
	return render(request, 'teacher/my_schedule.html', context)


@login_required
def parent_student_timetable(request):
	"""Parent views their child's weekly timetable"""
	
	if not hasattr(request.user, 'parent_profile'):
		return HttpResponse("Access denied - not a parent")
	
	parent = request.user.parent_profile
	student = parent.student
	
	# FIX: Use local timezone
	now = timezone.localtime(timezone.now())
	today = now.date()
	today_weekday = now.isoweekday()
	
	try:
		active_year = AcademicYear.objects.get(academic_year_active_status=True)
	except AcademicYear.DoesNotExist:
		return render(request, 'parent/student_timetable.html', {
			'error': 'No active academic year'
		})
	
	# Get all periods
	all_periods = SchoolPeriod.objects.filter(is_active=True).order_by('period_number')
	
	# Get student's class schedule for the week
	class_schedule = ClassSchedule.objects.filter(
		class_obj=student.student_class,
		academic_year=active_year,
		is_active=True
	).select_related('period', 'teacher').order_by('day_of_week', 'period__period_number')
	
	# Days of the week
	days = [
		(1, 'Thứ Hai'),
		(2, 'Thứ Ba'),
		(3, 'Thứ Tư'),
		(4, 'Thứ Năm'),
		(5, 'Thứ Sáu'),
		(6, 'Thứ Bảy')
	]
	
	# Organize schedule by day and period
	# Structure: schedule_grid[day][period_number] = schedule_item
	schedule_grid = defaultdict(dict)
	
	for schedule in class_schedule:
		schedule_grid[schedule.day_of_week][schedule.period.period_number] = schedule
	
	# Build timetable structure for template
	timetable = []
	for period in all_periods:
		row = {
			'period': period,
			'classes': []
		}
		
		for day_num, day_name in days:
			schedule_item = schedule_grid[day_num].get(period.period_number)
			row['classes'].append({
				'schedule': schedule_item,
				'has_class': schedule_item is not None
			})
		
		timetable.append(row)
	
	# Today's schedule highlight
	# FIX: Use local weekday instead of UTC
	today_schedule = class_schedule.filter(day_of_week=today_weekday).order_by('period__period_number')
	
	# Summary statistics
	total_periods_per_week = class_schedule.count()
	unique_subjects = class_schedule.values('subject_name').distinct().count()
	unique_teachers = class_schedule.values('teacher').distinct().count()
	
	# Subject breakdown
	subject_summary = defaultdict(int)
	for schedule in class_schedule:
		subject_summary[schedule.subject_name] += 1
	
	context = {
		'parent': parent,
		'student': student,
		'days': days,
		'timetable': timetable,
		'today_schedule': today_schedule,
		'today_weekday': today_weekday,
		'total_periods_per_week': total_periods_per_week,
		'unique_subjects': unique_subjects,
		'unique_teachers': unique_teachers,
		'subject_summary': dict(subject_summary),
		'today': today  # FIX: Use local date
	}
	
	return render(request, 'parent/student_timetable.html', context)