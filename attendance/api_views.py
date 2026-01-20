from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Students, Attendance, AcademicYear, ExcusedAbsence
import json
from datetime import datetime, time
from zoneinfo import ZoneInfo
from django.contrib.auth.decorators import login_required


def to_ascii_vietnamese(text):
	"""Convert Vietnamese characters to ASCII-friendly equivalents for LCD display"""
	replacements = {
		'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
		'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
		'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
		'đ': 'd',
		'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
		'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
		'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
		'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
		'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
		'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
		'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
		'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
		'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
	}
	result = text
	for vn_char, ascii_char in replacements.items():
		result = result.replace(vn_char, ascii_char)
		result = result.replace(vn_char.upper(), ascii_char.upper())
	return result


@csrf_exempt
@require_http_methods(["POST"])
def attendance_scan(request):
	try:
		data = json.loads(request.body)
		card_uid = data.get('card_uid')
		device_id = data.get('device_id', 'gate_reader_01')
		timestamp_str = data.get('timestamp')  # From Arduino/ESP32

		if not card_uid:
			return JsonResponse({
				'status': 'error',
				'message': 'Card UID is required',
				'lcd_message': to_ascii_vietnamese('Lỗi: Không có thẻ')
			}, status=400)

		# Find student by Card UID
		try:
			student = Students.objects.get(
				student_card_uid=card_uid,
				student_active_status=True
			)
		except Students.DoesNotExist:
			return JsonResponse({
				'status': 'error',
				'message': 'Card not found or inactive',
				'lcd_message': to_ascii_vietnamese('Thẻ không hợp lệ')
			}, status=404)

		# Get current academic year
		try:
			academic_year = AcademicYear.objects.get(academic_year_active_status=True)
		except AcademicYear.DoesNotExist:
			return JsonResponse({
				'status': 'error',
				'message': 'No active academic year',
				'lcd_message': to_ascii_vietnamese('Lỗi hệ thống')
			}, status=400)

		# Parse timestamp from ESP32 or use server time
		vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
		if timestamp_str:
			try:
				# Parse: "2026-01-05 06:15:44"
				naive_dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
				scan_datetime = naive_dt.replace(tzinfo=vn_tz)
			except ValueError:
				# Fallback to server time if timestamp format is wrong
				scan_datetime = timezone.now()
		else:
			# Use server time (already in Asia/Ho_Chi_Minh timezone)
			scan_datetime = timezone.now()

		scan_date = scan_datetime.date()
		scan_time = scan_datetime.time()

		# Determine if this is morning or afternoon scan
		morning_start = time(6, 0)   # 6:00 AM
		morning_end = time(11, 0)     # 11:00 AM
		afternoon_start = time(13, 0) # 1:00 PM
		afternoon_end = time(20, 0)   # 5:00 PM
		late_cutoff = time(7, 0)      # 7:00 AM - late if after this

		is_morning_period = morning_start <= scan_time <= morning_end
		is_afternoon_period = afternoon_start <= scan_time <= afternoon_end

		# Check if scanning outside allowed times
		if not is_morning_period and not is_afternoon_period:
			return JsonResponse({
				'status': 'warning',
				'message': 'Scan outside allowed time',
				'lcd_message': to_ascii_vietnamese('Ngoài giờ quét thẻ'),
				'student': student.student_full_name,
				'scan_time': scan_datetime.strftime('%H:%M:%S')
			})

		# Check for excused absence
		excused = ExcusedAbsence.objects.filter(
			student=student,
			start_date__lte=scan_date,
			end_date__gte=scan_date,
			approved_by_homeroom=True
		).first()

		if excused:
			# Student has approved excuse but still came to school
			lcd_msg = to_ascii_vietnamese(f'Xin chào {student.student_full_name}!\nBạn có phép nghỉ')
			return JsonResponse({
				'status': 'info',
				'message': 'Student has excused absence but scanned',
				'lcd_message': lcd_msg,
				'student': student.student_full_name,
				'class': str(student.student_class),
				'scan_time': scan_datetime.strftime('%H:%M:%S'),
				'excuse_reason': excused.reason
			})

		# Get or create attendance record for today
		attendance, created = Attendance.objects.get_or_create(
			student=student,
			check_in_date=scan_date,
			defaults={
				'academic_year': academic_year,
				'device_id': device_id,
				'status': 'no_scan'
			}
		)

		# Handle morning scan
		if is_morning_period:
			if attendance.morning_gate_scan_time:
				# Already scanned this morning
				existing_time = timezone.localtime(attendance.morning_gate_scan_time)
				lcd_msg = to_ascii_vietnamese(f'Đã quét buổi sáng!\n{existing_time.strftime("%H:%M")}')
				return JsonResponse({
					'status': 'warning',
					'message': 'Already scanned this morning',
					'lcd_message': lcd_msg,
					'student': student.student_full_name,
					'class': str(student.student_class),
					'first_scan_time': existing_time.strftime('%H:%M:%S'),
					'current_scan_time': scan_datetime.strftime('%H:%M:%S')
				})

			# Save morning scan
			attendance.morning_gate_scan_time = scan_datetime
			attendance.morning_scanned_card_uid = card_uid
			
			# Check if late
			is_late = scan_time > late_cutoff
			
			if is_late:
				attendance.status = 'late_arrival'
				status_message = to_ascii_vietnamese('Trễ')
				lcd_greeting = to_ascii_vietnamese(f'Bạn đến trễ!\n{student.student_full_name}')
			else:
				attendance.status = 'scanned_morning'
				status_message = to_ascii_vietnamese('Đã quét sáng')
				lcd_greeting = to_ascii_vietnamese(f'Chào buổi sáng!\n{student.student_full_name}')
			
			# Keep old fields for backward compatibility
			if not attendance.check_in_time:
				attendance.check_in_time = scan_datetime
				attendance.scanned_card_uid = card_uid
			
			attendance.save()

			return JsonResponse({
				'status': 'success',
				'message': 'Morning gate scan recorded',
				'lcd_message': lcd_greeting,
				'student': student.student_full_name,
				'class': str(student.student_class),
				'student_role': student.get_student_role_display(),
				'to_number': attendance.student.to_number,
				'seat_number': attendance.student.seat_number,
				'scan_time': scan_datetime.strftime('%H:%M:%S'),
				'scan_status': status_message,
				'is_late': is_late
			})

		# Handle afternoon scan
		elif is_afternoon_period:
			if not attendance.morning_gate_scan_time:
				# Scanned afternoon but not morning - unusual
				lcd_msg = to_ascii_vietnamese(f'Chào buổi chiều!\n{student.student_full_name}\nChưa quét buổi sáng')
				return JsonResponse({
					'status': 'warning',
					'message': 'Afternoon scan without morning scan',
					'lcd_message': lcd_msg,
					'student': student.student_full_name,
					'class': str(student.student_class),
					'scan_time': scan_datetime.strftime('%H:%M:%S'),
					'note': 'Student did not scan in morning'
				})

			if attendance.afternoon_gate_scan_time:
				# Already scanned this afternoon
				existing_time = timezone.localtime(attendance.afternoon_gate_scan_time)
				lcd_msg = to_ascii_vietnamese(f'Đã quét buổi chiều!\n{existing_time.strftime("%H:%M")}')
				return JsonResponse({
					'status': 'warning',
					'message': 'Already scanned this afternoon',
					'lcd_message': lcd_msg,
					'student': student.student_full_name,
					'class': str(student.student_class),
					'first_scan_time': existing_time.strftime('%H:%M:%S'),
					'current_scan_time': scan_datetime.strftime('%H:%M:%S')
				})

			# Save afternoon scan
			attendance.afternoon_gate_scan_time = scan_datetime
			attendance.afternoon_scanned_card_uid = card_uid
			attendance.status = 'scanned_both'  # Has both morning and afternoon
			attendance.save()

			lcd_greeting = to_ascii_vietnamese(f'Chào buổi chiều!\n{student.student_full_name}')
			status_message = to_ascii_vietnamese('Đã quét chiều')
			
			return JsonResponse({
				'status': 'success',
				'message': 'Afternoon gate scan recorded',
				'lcd_message': lcd_greeting,
				'student': student.student_full_name,
				'class': str(student.student_class),
				'student_role': student.get_student_role_display(),
				'to_number': attendance.student.to_number,
				'seat_number': attendance.student.seat_number,
				'scan_time': scan_datetime.strftime('%H:%M:%S'),
				'scan_status': status_message,
				'morning_scan': timezone.localtime(attendance.morning_gate_scan_time).strftime('%H:%M:%S'),
				'afternoon_scan': scan_datetime.strftime('%H:%M:%S')
			})

	except json.JSONDecodeError:
		return JsonResponse({
			'status': 'error',
			'message': 'Invalid JSON data',
			'lcd_message': to_ascii_vietnamese('Lỗi dữ liệu')
		}, status=400)
	except Exception as e:
		return JsonResponse({
			'status': 'error',
			'message': str(e),
			'lcd_message': to_ascii_vietnamese('Lỗi hệ thống')
		}, status=500)


@login_required
@require_http_methods(["GET"])
def teacher_dashboard_stats(request):
	"""API endpoint for real-time dashboard stats - UPDATED for dual scan system"""
	
	if not hasattr(request.user, 'teacher_profile'):
		return JsonResponse({'error': 'Access denied'}, status=403)
	
	teacher = request.user.teacher_profile
	teacher_classes = teacher.homeroom_classes.all()
	
	if not teacher_classes.exists():
		return JsonResponse({
			'total_students': 0,
			'present_count': 0,
			'late_count': 0,
			'absent_count': 0,
			'morning_scanned': 0,
			'afternoon_scanned': 0,
			'recent_scans': []
		})
	
	today = timezone.now().date()
	
	# Get stats
	total_students = Students.objects.filter(
		student_class__in=teacher_classes,
		student_active_status=True
	).count()
	
	today_attendance = Attendance.objects.filter(
		student__student_class__in=teacher_classes,
		check_in_date=today
	)
	
	# Count different statuses
	morning_scanned = today_attendance.filter(
		morning_gate_scan_time__isnull=False
	).count()
	
	afternoon_scanned = today_attendance.filter(
		afternoon_gate_scan_time__isnull=False
	).count()
	
	late_count = today_attendance.filter(status='late_arrival').count()
	
	# Absent = total students - students who scanned morning
	absent_count = total_students - morning_scanned
	
	# Recent scans (last 10, either morning or afternoon)
	recent_scans_morning = Attendance.objects.filter(
		student__student_class__in=teacher_classes,
		check_in_date=today,
		morning_gate_scan_time__isnull=False
	).select_related('student', 'student__student_class').order_by('-morning_gate_scan_time')[:5]
	
	recent_scans_afternoon = Attendance.objects.filter(
		student__student_class__in=teacher_classes,
		check_in_date=today,
		afternoon_gate_scan_time__isnull=False
	).select_related('student', 'student__student_class').order_by('-afternoon_gate_scan_time')[:5]
	
	recent_scans_data = []
	
	# Add morning scans
	for scan in recent_scans_morning:
		recent_scans_data.append({
			'student_name': scan.student.student_full_name,
			'class_name': scan.student.student_class.class_name,
			'time': timezone.localtime(scan.morning_gate_scan_time).strftime('%H:%M:%S'),
			'status': scan.status,
			'scan_type': 'morning'
		})
	
	# Add afternoon scans
	for scan in recent_scans_afternoon:
		recent_scans_data.append({
			'student_name': scan.student.student_full_name,
			'class_name': scan.student.student_class.class_name,
			'time': timezone.localtime(scan.afternoon_gate_scan_time).strftime('%H:%M:%S'),
			'status': scan.status,
			'scan_type': 'afternoon'
		})
	
	# Sort by time (most recent first)
	recent_scans_data = sorted(recent_scans_data, key=lambda x: x['time'], reverse=True)[:10]
	
	return JsonResponse({
		'total_students': total_students,
		'morning_scanned': morning_scanned,
		'afternoon_scanned': afternoon_scanned,
		'late_count': late_count,
		'absent_count': absent_count,
		'present_count': morning_scanned,  # Consider morning scan as "present"
		'recent_scans': recent_scans_data,
		'timestamp': timezone.now().isoformat()
	})