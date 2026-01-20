from django.db import models
import uuid_utils
import uuid
from django.core.validators import RegexValidator, FileExtensionValidator
from django.utils import timezone
from django.contrib.auth.models import User

# Custom UUID Field
def generate_uuid7():
    return uuid.UUID(str(uuid_utils.uuid7()))


class UUIDv7Field(models.UUIDField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', generate_uuid7)
        kwargs.setdefault('editable', False)
        super().__init__(*args, **kwargs)


# Profile image path helpers
def student_profile_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.student_id}.{ext}"
    return f"uploads/students/profiles/{filename}"

def teacher_profile_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.teacher_id}.{ext}"
    return f"uploads/teachers/profiles/{filename}"

def parent_profile_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.parent_id}.{ext}"
    return f"uploads/parents/profiles/{filename}"



class AcademicYear(models.Model):
    """Academic year (e.g., 2025-2026)"""
    academic_year_id = UUIDv7Field(primary_key=True, editable=False)
    academic_start_year = models.CharField(max_length=10, blank=False, null=False)
    academic_end_year = models.CharField(max_length=10, blank=False, null=False)
    academic_year_active_status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'academic_year'
        unique_together = [['academic_start_year', 'academic_end_year']]
        ordering = ['-academic_start_year']

    def __str__(self):
        return f"{self.academic_start_year}-{self.academic_end_year}"


class Class(models.Model):
    """Class/Grade (e.g., 6A1, 7B2)"""
    class_id = UUIDv7Field(primary_key=True, editable=False)
    class_name = models.CharField(max_length=50)  
    grade_level = models.IntegerField()  
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='classes')
    homeroom_teacher = models.ForeignKey('Teachers', models.SET_NULL, null=True, blank=True, related_name='homeroom_classes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'class'
        unique_together = [['class_name', 'academic_year'], ['homeroom_teacher', 'academic_year']]
        ordering = ['grade_level', 'class_name']
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'

    def __str__(self):
        return f"{self.class_name} ({self.academic_year})"



class Teachers(models.Model):
    """Teacher information (NO CHANGES)"""
    GENDER_CHOICES = [
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ]

    teacher_id = UUIDv7Field(primary_key=True, editable=False)
    teacher_card_id = models.CharField(max_length=10, unique=True, blank=False, null=False)
    teacher_full_name = models.CharField(max_length=150, blank=False, null=False)
    #teacher_class = models.ForeignKey(Class, on_delete=models.SET_NULL, blank=True, null=True, related_name='teachers')
    teacher_gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    teacher_birthday = models.DateField(null=True, blank=True)
    teacher_phone_number = models.CharField(
        max_length=20, unique=True, blank=True, null=True,
        validators=[RegexValidator(regex=r'^\d{10,11}$', message='Enter a valid 10-11 digit phone number')]
    )
    teacher_subject = models.CharField(max_length=30, blank=True, null=True)
    
    teacher_regular_address = models.CharField(max_length=255, blank=True, null=True)
    teacher_temporary_address = models.CharField(max_length=255, blank=True, null=True)

    teacher_profile_image = models.ImageField(
        upload_to=teacher_profile_path, null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    teacher_active_status = models.BooleanField(default=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name="teacher_profile")

    class Meta:
        db_table = 'teachers'
        ordering = ['teacher_full_name']
        indexes = [
            models.Index(fields=['teacher_card_id']),
            models.Index(fields=['teacher_active_status']),
        ]
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'

    def __str__(self):
        return f"{self.teacher_card_id} - {self.teacher_full_name}"


class Students(models.Model):
    """Student information - SAFE MIGRATION VERSION"""
    GENDER_CHOICES = [
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ]
    
    ROLE_CHOICES = [
        ('student', 'Học sinh'),
        ('lop_truong', 'Lớp trưởng'),
        ('lop_pho', 'Lớp phó'),
        ('to_truong', 'Tổ trưởng'),
    ]

    student_id = UUIDv7Field(primary_key=True, editable=False)
    student_card_uid = models.CharField(max_length=8, unique=True, blank=False, null=False, db_index=True)
    student_full_name = models.CharField(max_length=150, blank=False, null=False)
    student_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name='students')
    student_gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    student_birthday = models.DateField(null=True, blank=True)
    student_phone_number = models.CharField(
        max_length=20, unique=True, blank=True, null=True,
        validators=[RegexValidator(regex=r'^\d{10,11}$', message='Enter a valid 10-11 digit phone number')]
    )
    
    student_regular_address = models.CharField(max_length=255, blank=True, null=True)
    student_temporary_address = models.CharField(max_length=255, blank=True, null=True)
    
    student_profile_image = models.ImageField(
        upload_to=student_profile_path, null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    
    # NEW FIELDS - All nullable to preserve existing data
    student_role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='student',
        null=True,  # Makes migration safe
        blank=True
    )
    to_number = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Tổ number (1-4)"
    )
    seat_number = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Seat in tổ (1-10)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    student_active_status = models.BooleanField(default=True)

    class Meta:
        db_table = 'students'
        ordering = ['student_full_name']
        indexes = [
            models.Index(fields=['student_card_uid']),
            models.Index(fields=['student_active_status']),
            models.Index(fields=['student_class']),
            models.Index(fields=['student_full_name']),
            models.Index(fields=['student_role']),
        ]
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return f"{self.student_full_name} ({self.student_card_uid})"
    
    def is_class_monitor(self):
        return self.student_role == 'lop_truong'
    
    def is_vice_monitor(self):
        return self.student_role == 'lop_pho'
    
    def is_group_leader(self):
        return self.student_role == 'to_truong'


class Parents(models.Model):
    """Parent/Guardian information (NO CHANGES)"""
    parent_id = UUIDv7Field(primary_key=True, editable=False)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='parents')
    
    parent_mother_name = models.CharField(max_length=150, blank=True, null=True)
    parent_mother_phone_number = models.CharField(
        max_length=20, unique=True, blank=True, null=True,
        validators=[RegexValidator(regex=r'^\d{10,11}$', message='Enter a valid 10-11 digit phone number')]
    )
    parent_mother_birthday = models.DateField(null=True, blank=True)
    parent_mother_job = models.CharField(max_length=150, blank=True, null=True)
    parent_mother_workplace = models.CharField(max_length=255, blank=True, null=True)
    
    parent_father_name = models.CharField(max_length=150, blank=True, null=True)
    parent_father_phone_number = models.CharField(
        max_length=20, unique=True, blank=True, null=True,
        validators=[RegexValidator(regex=r'^\d{10,11}$', message='Enter a valid 10-11 digit phone number')]
    )
    parent_father_birthday = models.DateField(null=True, blank=True)
    parent_father_job = models.CharField(max_length=150, blank=True, null=True)
    parent_father_workplace = models.CharField(max_length=255, blank=True, null=True)
    
    parent_regular_address = models.CharField(max_length=255, blank=True, null=True)
    parent_temporary_address = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name="parent_profile")

    class Meta:
        db_table = 'parents'
        verbose_name = 'Parent'
        verbose_name_plural = 'Parents'

    def __str__(self):
        return f"Parents of {self.student.student_full_name}"



class SchoolPeriod(models.Model):
    """Defines school period structure"""
    period_id = UUIDv7Field(primary_key=True, editable=False)
    period_number = models.IntegerField(unique=True)
    period_name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'school_periods'
        ordering = ['period_number']
    
    def __str__(self):
        return f"{self.period_name} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"


class ClassSchedule(models.Model):
    """Weekly class timetable"""
    WEEKDAY_CHOICES = [
        (1, 'Thứ Hai'),
        (2, 'Thứ Ba'),
        (3, 'Thứ Tư'),
        (4, 'Thứ Năm'),
        (5, 'Thứ Sáu'),
        (6, 'Thứ Bảy'),
    ]
    
    schedule_id = UUIDv7Field(primary_key=True, editable=False)
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='schedules')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='schedules')
    
    day_of_week = models.IntegerField(choices=WEEKDAY_CHOICES)
    period = models.ForeignKey(SchoolPeriod, on_delete=models.CASCADE, related_name='schedules')
    
    subject_name = models.CharField(max_length=100)
    teacher = models.ForeignKey(Teachers, on_delete=models.SET_NULL, null=True, related_name='teaching_schedules')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'class_schedules'
        unique_together = [['class_obj', 'academic_year', 'day_of_week', 'period']]
        ordering = ['day_of_week', 'period__period_number']
    
    def __str__(self):
        return f"{self.class_obj.class_name} - {self.get_day_of_week_display()} - {self.period.period_name} - {self.subject_name}"



class Attendance(models.Model):
    """Daily attendance - SAFE MIGRATION with old fields preserved"""
    ATTENDANCE_STATUS_CHOICES = [
        ('attended', 'Đã điểm danh'),  # OLD - kept for compatibility
        ('late', 'Trễ'),  # OLD
        ('absent', 'Vắng'),  # OLD
        ('scanned_morning', 'Đã quét buổi sáng'),  # NEW
        ('scanned_afternoon', 'Đã quét buổi chiều'),  # NEW
        ('scanned_both', 'Đã quét cả 2 buổi'),  # NEW
        ('no_scan', 'Chưa quét'),  # NEW
        ('late_arrival', 'Đến trễ'),  # NEW
    ]

    attendance_id = UUIDv7Field(primary_key=True, editable=False)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='attendances')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='attendances')
    
    # OLD FIELDS - Keep for backwards compatibility
    check_in_time = models.DateTimeField(null=True, blank=True)  # Made nullable
    check_in_date = models.DateField()
    scanned_card_uid = models.CharField(max_length=8, blank=True, null=True)
    
    # NEW FIELDS - For dual gate scan system
    morning_gate_scan_time = models.DateTimeField(null=True, blank=True)
    afternoon_gate_scan_time = models.DateTimeField(null=True, blank=True)
    morning_scanned_card_uid = models.CharField(max_length=8, blank=True, null=True)
    afternoon_scanned_card_uid = models.CharField(max_length=8, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS_CHOICES, default='absent')
    
    # IoT Tracking
    device_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Teacher Verification (OLD - kept)
    is_verified_by_teacher = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance'
        # Remove unique_together temporarily to allow migration
        # unique_together = [['student', 'check_in_date']]
        ordering = ['-check_in_date']
        indexes = [
            models.Index(fields=['check_in_date']),
            models.Index(fields=['student', 'check_in_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.student.student_full_name} - {self.check_in_date} ({self.status})"
    
    def mark_late_if_needed(self, cutoff_time="07:00:00"):
        """Backwards compatible method"""
        from datetime import time
        cutoff = timezone.datetime.strptime(cutoff_time, "%H:%M:%S").time()
        
        # Check new field first, fall back to old field
        scan_time = self.morning_gate_scan_time or self.check_in_time
        
        if scan_time and scan_time.time() > cutoff:
            self.status = 'late_arrival' if self.morning_gate_scan_time else 'late'
            self.save()


class AttendancePeriod(models.Model):
    """Per-period attendance tracking (NEW - COMPLETELY SAFE)"""
    PERIOD_STATUS_CHOICES = [
        ('present', 'Có mặt'),
        ('absent', 'Vắng'),
        ('late', 'Trễ'),
        ('excused', 'Có phép'),
        ('sneaked_out', 'Trốn học'),
    ]
    
    period_attendance_id = UUIDv7Field(primary_key=True, editable=False)
    
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='period_records', null=True, blank=True)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='period_attendances')
    schedule = models.ForeignKey(ClassSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_records')
    
    period_number = models.IntegerField()
    subject_name = models.CharField(max_length=100)
    period_date = models.DateField()
    
    status = models.CharField(max_length=20, choices=PERIOD_STATUS_CHOICES, default='present')
    
    marked_by_teacher = models.ForeignKey(Teachers, on_delete=models.SET_NULL, null=True, related_name='marked_periods')
    marked_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance_periods'
        unique_together = [['student', 'period_date', 'period_number']]
        ordering = ['period_date', 'period_number']
        indexes = [
            models.Index(fields=['period_date']),
            models.Index(fields=['student', 'period_date']),
            models.Index(fields=['status']),
            models.Index(fields=['marked_by_teacher']),
        ]
    
    def __str__(self):
        return f"{self.student.student_full_name} - Period {self.period_number} - {self.period_date} ({self.status})"


class ExcusedAbsence(models.Model):
    ABSENCE_TYPE_CHOICES = [
        ('full_day', 'Cả ngày'),
        ('morning', 'Buổi sáng'),
        ('afternoon', 'Buổi chiều'),
        ('specific_periods', 'Tiết cụ thể'),
    ]
    
    excuse_id = UUIDv7Field(primary_key=True, editable=False)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='excused_absences')
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    absence_type = models.CharField(max_length=20, choices=ABSENCE_TYPE_CHOICES, default='full_day')
    specific_periods = models.CharField(max_length=100, blank=True, null=True)
    
    reason = models.TextField()
    
    approved_by_homeroom = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    parent_contact_method = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'excused_absences'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['student', 'start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.student.student_full_name} - {self.start_date} to {self.end_date}"
    
    def is_active_on_date(self, check_date):
        return self.start_date <= check_date <= self.end_date
    
    def applies_to_period(self, period_number):
        if self.absence_type == 'full_day':
            return True
        elif self.absence_type == 'morning' and period_number <= 5:
            return True
        elif self.absence_type == 'afternoon' and period_number >= 6:
            return True
        elif self.absence_type == 'specific_periods' and self.specific_periods:
            periods = [int(p.strip()) for p in self.specific_periods.split(',')]
            return period_number in periods
        return False