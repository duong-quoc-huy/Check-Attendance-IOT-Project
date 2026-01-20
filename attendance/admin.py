from django.contrib import admin
from .models import (
    AcademicYear, Class, Teachers, Students, Parents,
    Attendance, SchoolPeriod, ClassSchedule, AttendancePeriod, ExcusedAbsence
)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['academic_start_year', 'academic_end_year', 'academic_year_active_status', 'created_at']
    list_filter = ['academic_year_active_status']
    search_fields = ['academic_start_year', 'academic_end_year']
    ordering = ['-academic_start_year']


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['class_name', 'grade_level', 'get_homeroom_teacher', 'academic_year', 'created_at']
    list_filter = ['grade_level', 'academic_year']
    search_fields = ['class_name', 'homeroom_teacher__teacher_full_name']
    ordering = ['grade_level', 'class_name']
    autocomplete_fields = ['homeroom_teacher']

    def get_homeroom_teacher(self, obj):
        if obj.homeroom_teacher:
            return f"{obj.homeroom_teacher.teacher_card_id} - {obj.homeroom_teacher.teacher_full_name}"
        return '-'
    get_homeroom_teacher.short_description = 'Homeroom Teacher'


@admin.register(Teachers)
class TeachersAdmin(admin.ModelAdmin):
    list_display = ['teacher_card_id', 'teacher_full_name', 'teacher_gender', 'teacher_phone_number', 'teacher_subject', 'teacher_active_status']
    list_filter = ['teacher_active_status', 'teacher_gender']
    search_fields = ['teacher_card_id', 'teacher_full_name', 'teacher_phone_number']
    ordering = ['teacher_full_name']
    readonly_fields = ['teacher_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('teacher_card_id', 'teacher_full_name', 'teacher_gender', 'teacher_birthday', 'teacher_subject')
        }),
        ('Contact', {
            'fields': ('teacher_phone_number', 'teacher_regular_address', 'teacher_temporary_address')
        }),
        ('Assignment', {
            'fields': ('teacher_class', 'teacher_active_status')
        }),
        ('Profile', {
            'fields': ('teacher_profile_image',)
        }),
        ('System', {
            'fields': ('teacher_id', 'user', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Students)
class StudentsAdmin(admin.ModelAdmin):
    list_display = [
        'student_card_uid', 
        'student_full_name', 
        'get_class_name', 
        'student_role',  
        'to_number',     
        'seat_number',   
        'student_active_status'
    ]
    list_filter = [
        'student_active_status', 
        'student_gender', 
        'student_class',
        'student_role',  
        'to_number'      
    ]
    autocomplete_fields = ['student_class']
    search_fields = ['student_card_uid', 'student_full_name', 'student_phone_number']
    ordering = ['student_class', 'to_number', 'seat_number', 'student_full_name']
    readonly_fields = ['student_id', 'created_at', 'updated_at']
    
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student_card_uid', 'student_full_name', 'student_gender', 'student_birthday')
        }),
        ('Class Assignment', {
            'fields': ('student_class', 'student_role', 'to_number', 'seat_number')
        }),
        ('Contact', {
            'fields': ('student_phone_number', 'student_regular_address', 'student_temporary_address')
        }),
        ('Profile', {
            'fields': ('student_profile_image',)
        }),
        ('Status', {
            'fields': ('student_active_status',)
        }),
        ('System', {
            'fields': ('student_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    
    actions = ['assign_as_regular_student', 'bulk_assign_to']
    
    @admin.action(description='Mark as regular student')
    def assign_as_regular_student(self, request, queryset):
        updated = queryset.update(student_role='student')
        self.message_user(request, f'{updated} students marked as regular students.')
    
    @admin.action(description='Assign to Tổ')
    def bulk_assign_to(self, request, queryset):
        # You can expand this to show a form for selecting tổ
        self.message_user(request, 'Use individual edit to assign Tổ and seat numbers.')

    def get_class_name(self, obj):
        return obj.student_class.class_name if obj.student_class else '-'
    get_class_name.short_description = 'Class'


@admin.register(Parents)
class ParentsAdmin(admin.ModelAdmin):
    list_display = ['student', 'parent_father_name', 'parent_mother_name', 'parent_father_phone_number', 'parent_mother_phone_number']
    search_fields = [
        'student__student_full_name', 
        'parent_father_name', 
        'parent_mother_name',
        'parent_father_phone_number',
        'parent_mother_phone_number'
    ]
    raw_id_fields = ['student']
    readonly_fields = ['parent_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Student Link', {
            'fields': ('student',)
        }),
        ('Father Information', {
            'fields': ('parent_father_name', 'parent_father_phone_number', 'parent_father_birthday', 
                      'parent_father_job', 'parent_father_workplace')
        }),
        ('Mother Information', {
            'fields': ('parent_mother_name', 'parent_mother_phone_number', 'parent_mother_birthday',
                      'parent_mother_job', 'parent_mother_workplace')
        }),
        ('Addresses', {
            'fields': ('parent_regular_address', 'parent_temporary_address')
        }),
        ('System', {
            'fields': ('parent_id', 'user', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'student', 
        'check_in_date', 
        'morning_gate_scan_time',  # NEW
        'afternoon_gate_scan_time',  # NEW
        'status',
        'is_verified_by_teacher'
    ]
    list_filter = [
        'status', 
        'check_in_date', 
        'is_verified_by_teacher',
        'student__student_class'
    ]
    search_fields = [
        'student__student_full_name', 
        'student__student_card_uid',
        'morning_scanned_card_uid',
        'afternoon_scanned_card_uid'
    ]
    ordering = ['-check_in_date', '-morning_gate_scan_time']
    readonly_fields = ['attendance_id', 'created_at', 'updated_at']
    raw_id_fields = ['student', 'academic_year']
    date_hierarchy = 'check_in_date'
    
    fieldsets = (
        ('Student & Date', {
            'fields': ('student', 'academic_year', 'check_in_date')
        }),
        ('Old System (Backwards Compatible)', {
            'fields': ('check_in_time', 'scanned_card_uid'),
            'classes': ('collapse',)
        }),
        ('New System - Gate Scans', {
            'fields': (
                'morning_gate_scan_time', 
                'morning_scanned_card_uid',
                'afternoon_gate_scan_time',
                'afternoon_scanned_card_uid'
            )
        }),
        ('Status', {
            'fields': ('status', 'device_id')
        }),
        ('Teacher Verification', {
            'fields': ('is_verified_by_teacher', 'verified_at')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('System', {
            'fields': ('attendance_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )



@admin.register(SchoolPeriod)
class SchoolPeriodAdmin(admin.ModelAdmin):
    list_display = ['period_number', 'period_name', 'start_time', 'end_time', 'is_active']
    list_filter = ['is_active']
    ordering = ['period_number']
    readonly_fields = ['period_id']
    
    fieldsets = (
        ('Period Information', {
            'fields': ('period_number', 'period_name', 'start_time', 'end_time')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System', {
            'fields': ('period_id',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'class_obj', 
        'day_of_week_display', 
        'period', 
        'subject_name', 
        'teacher',
        'is_active'
    ]
    list_filter = [
        'day_of_week', 
        'period__period_number', 
        'is_active',
        'academic_year',
        'class_obj__grade_level'
    ]
    search_fields = [
        'class_obj__class_name', 
        'subject_name', 
        'teacher__teacher_full_name'
    ]
    ordering = ['class_obj', 'day_of_week', 'period__period_number']
    readonly_fields = ['schedule_id', 'created_at']
    raw_id_fields = ['class_obj', 'teacher', 'academic_year']
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('class_obj', 'academic_year', 'day_of_week', 'period')
        }),
        ('Subject & Teacher', {
            'fields': ('subject_name', 'teacher')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System', {
            'fields': ('schedule_id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def day_of_week_display(self, obj):
        return obj.get_day_of_week_display()
    day_of_week_display.short_description = 'Day'
    
    # Helpful actions
    actions = ['duplicate_schedule_to_next_week', 'deactivate_schedules']
    
    @admin.action(description='Deactivate selected schedules')
    def deactivate_schedules(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} schedules deactivated.')




@admin.register(AttendancePeriod)
class AttendancePeriodAdmin(admin.ModelAdmin):
    list_display = [
        'student',
        'period_date',
        'period_number',
        'subject_name',
        'status',
        'marked_by_teacher',
        'marked_at',
        'is_verified'
    ]
    list_filter = [
        'status',
        'period_date',
        'period_number',
        'is_verified',
        'student__student_class',
        'marked_by_teacher'
    ]
    search_fields = [
        'student__student_full_name',
        'student__student_card_uid',
        'subject_name',
        'marked_by_teacher__teacher_full_name'
    ]
    ordering = ['-period_date', 'student__student_class', 'period_number']
    readonly_fields = ['period_attendance_id', 'created_at', 'updated_at']
    raw_id_fields = ['attendance', 'student', 'schedule', 'marked_by_teacher']
    date_hierarchy = 'period_date'
    
    fieldsets = (
        ('Student & Date', {
            'fields': ('student', 'period_date', 'attendance')
        }),
        ('Period Information', {
            'fields': ('period_number', 'subject_name', 'schedule')
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('Teacher Marking', {
            'fields': ('marked_by_teacher', 'marked_at', 'is_verified')
        }),
        ('System', {
            'fields': ('period_attendance_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Useful actions
    actions = ['mark_as_verified', 'mark_as_present', 'mark_as_absent']
    
    @admin.action(description='Mark as verified')
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} period attendance records verified.')
    
    @admin.action(description='Mark as present')
    def mark_as_present(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='present', is_verified=True, marked_at=timezone.now())
        self.message_user(request, f'{updated} students marked present.')
    
    @admin.action(description='Mark as absent')
    def mark_as_absent(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='absent', is_verified=True, marked_at=timezone.now())
        self.message_user(request, f'{updated} students marked absent.')


@admin.register(ExcusedAbsence)
class ExcusedAbsenceAdmin(admin.ModelAdmin):
    list_display = [
        'student',
        'start_date',
        'end_date',
        'absence_type',
        'approved_by_homeroom',
        'created_at'
    ]
    list_filter = [
        'absence_type',
        'approved_by_homeroom',
        'start_date',
        'student__student_class'
    ]
    search_fields = [
        'student__student_full_name',
        'student__student_card_uid',
        'reason'
    ]
    ordering = ['-start_date']
    readonly_fields = ['excuse_id', 'created_at']
    raw_id_fields = ['student']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Student', {
            'fields': ('student',)
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Absence Type', {
            'fields': ('absence_type', 'specific_periods')
        }),
        ('Reason', {
            'fields': ('reason',)
        }),
        ('Approval', {
            'fields': ('approved_by_homeroom', 'approved_at', 'parent_contact_method')
        }),
        ('System', {
            'fields': ('excuse_id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Helpful actions
    actions = ['approve_absences', 'reject_absences']
    
    @admin.action(description='Approve selected absences')
    def approve_absences(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(approved_by_homeroom=True, approved_at=timezone.now())
        self.message_user(request, f'{updated} absences approved.')
    
    @admin.action(description='Reject selected absences')
    def reject_absences(self, request, queryset):
        updated = queryset.update(approved_by_homeroom=False, approved_at=None)
        self.message_user(request, f'{updated} absences rejected.')


class AttendancePeriodInline(admin.TabularInline):
    """Show period attendance when viewing daily Attendance"""
    model = AttendancePeriod
    extra = 0
    readonly_fields = ['period_number', 'subject_name', 'status', 'marked_by_teacher', 'marked_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class ExcusedAbsenceInline(admin.TabularInline):
    """Show excused absences when viewing Student"""
    model = ExcusedAbsence
    extra = 0
    readonly_fields = ['start_date', 'end_date', 'absence_type', 'reason', 'approved_by_homeroom']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

