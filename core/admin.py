from django.contrib import admin
from django.utils.html import format_html
from .models import (
    School, Department, Subject, Teacher, Class, Student,
    ClassSubject, Attendance, Assessment, Grade, TimeTable
)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'established_date']
    search_fields = ['name', 'email']
    list_filter = ['established_date']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def get_logo_display(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "No Logo"
    get_logo_display.short_description = "Logo"


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'head_of_department']
    list_filter = ['school']
    search_fields = ['name', 'school__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'credits', 'is_active']
    list_filter = ['department', 'is_active', 'credits']
    search_fields = ['name', 'code', 'department__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'department', 'phone', 'is_active']
    list_filter = ['department', 'is_active', 'hire_date']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['subjects']

    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.short_description = "Full Name"

    def get_photo_display(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" />', obj.photo.url)
        return "No Photo"
    get_photo_display.short_description = "Photo"


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'section', 'school', 'class_teacher', 'current_students_count', 'max_students', 'is_active']
    list_filter = ['school', 'level', 'academic_year', 'is_active']
    search_fields = ['name', 'section', 'class_teacher__user__first_name', 'class_teacher__user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'current_students_count']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'full_name', 'current_class', 'guardian_name', 'guardian_phone', 'is_active']
    list_filter = ['current_class', 'is_active', 'admission_date']
    search_fields = ['student_id', 'admission_number', 'user__first_name', 'user__last_name', 'guardian_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'age']

    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.short_description = "Full Name"

    def get_photo_display(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" />', obj.photo.url)
        return "No Photo"
    get_photo_display.short_description = "Photo"


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ['class_instance', 'subject', 'teacher', 'academic_year', 'periods_per_week']
    list_filter = ['academic_year', 'subject__department']
    search_fields = ['class_instance__name', 'subject__name', 'teacher__user__first_name', 'teacher__user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'class_subject', 'marked_by']
    list_filter = ['status', 'date', 'class_subject__subject']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'date'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['student', 'date', 'class_subject']
        return self.readonly_fields


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_subject', 'assessment_type', 'total_marks', 'date', 'is_published']
    list_filter = ['assessment_type', 'is_published', 'date', 'class_subject__subject']
    search_fields = ['name', 'class_subject__class_instance__name', 'class_subject__subject__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'assessment', 'marks_obtained', 'total_marks', 'percentage', 'grade_letter', 'graded_by']
    list_filter = ['grade_letter', 'assessment__assessment_type', 'graded_date']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'assessment__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'percentage', 'grade_letter', 'graded_date']

    def total_marks(self, obj):
        return obj.assessment.total_marks
    total_marks.short_description = "Total Marks"

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['student', 'assessment', 'graded_by']
        return self.readonly_fields


@admin.register(TimeTable)
class TimeTableAdmin(admin.ModelAdmin):
    list_display = ['class_subject', 'day_of_week', 'start_time', 'end_time', 'room_number', 'academic_year']
    list_filter = ['day_of_week', 'academic_year', 'class_subject__class_instance']
    search_fields = ['class_subject__class_instance__name', 'class_subject__subject__name', 'room_number']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'class_subject__class_instance',
            'class_subject__subject',
            'class_subject__teacher'
        )


# Customize Admin Site
admin.site.site_header = "Smart School Management System"
admin.site.site_title = "School Admin"
admin.site.index_title = "Welcome to School Management System"