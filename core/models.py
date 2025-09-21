from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    """Abstract base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class School(BaseModel):
    """School/Institution model"""
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    established_date = models.DateField()
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"


class Department(BaseModel):
    """Department model for organizing subjects and teachers"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='departments')
    head_of_department = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='head_of_departments')

    def __str__(self):
        return f"{self.name} - {self.school.name}"

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        unique_together = ['name', 'school']


class Subject(BaseModel):
    """Subject model"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='subjects')
    credits = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"


class Teacher(BaseModel):
    """Teacher model extending User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    date_of_birth = models.DateField()
    hire_date = models.DateField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teachers')
    subjects = models.ManyToManyField(Subject, related_name='teachers', blank=True)
    qualification = models.CharField(max_length=200)
    experience_years = models.PositiveIntegerField(default=0)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"

    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"


class Class(BaseModel):
    """Class/Grade model"""
    name = models.CharField(max_length=50)  # e.g., "Grade 1A", "10th Science"
    level = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])  # 1-12 for grades
    section = models.CharField(max_length=5)  # A, B, C, etc.
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classes')
    class_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='class_teacher_of')
    academic_year = models.CharField(max_length=9)  # e.g., "2023-2024"
    max_students = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.academic_year})"

    @property
    def current_students_count(self):
        return self.students.filter(is_active=True).count()

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        unique_together = ['level', 'section', 'school', 'academic_year']


class Student(BaseModel):
    """Student model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    admission_number = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    date_of_birth = models.DateField()
    admission_date = models.DateField()
    current_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='students')
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=20)
    guardian_email = models.EmailField(blank=True)
    emergency_contact = models.CharField(max_length=20)
    medical_conditions = models.TextField(blank=True)
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name()}"

    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"


class ClassSubject(BaseModel):
    """Association between Class and Subject with assigned teacher"""
    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='class_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='teaching_assignments')
    academic_year = models.CharField(max_length=9)
    periods_per_week = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.class_instance.name} - {self.subject.name} ({self.teacher.user.get_full_name()})"

    class Meta:
        verbose_name = "Class Subject Assignment"
        verbose_name_plural = "Class Subject Assignments"
        unique_together = ['class_instance', 'subject', 'academic_year']


class Attendance(BaseModel):
    """Attendance model for tracking student attendance"""
    ATTENDANCE_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=ATTENDANCE_CHOICES)
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='attendance_records', null=True, blank=True)
    notes = models.TextField(blank=True)
    marked_by = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='marked_attendance')

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.date} - {self.status}"

    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance Records"
        unique_together = ['student', 'date', 'class_subject']


class Assessment(BaseModel):
    """Assessment/Exam model"""
    ASSESSMENT_TYPES = [
        ('quiz', 'Quiz'),
        ('test', 'Test'),
        ('midterm', 'Midterm Exam'),
        ('final', 'Final Exam'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
    ]

    name = models.CharField(max_length=100)
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='assessments')
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    total_marks = models.PositiveIntegerField()
    date = models.DateField()
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.class_subject.class_instance.name} - {self.class_subject.subject.name}"

    class Meta:
        verbose_name = "Assessment"
        verbose_name_plural = "Assessments"


class Grade(BaseModel):
    """Grade model for storing student grades/marks"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='grades')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    grade_letter = models.CharField(max_length=2, blank=True)  # A+, A, B+, etc.
    comments = models.TextField(blank=True)
    graded_by = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='graded_assessments')
    graded_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assessment.name} - {self.marks_obtained}/{self.assessment.total_marks}"

    @property
    def percentage(self):
        return (self.marks_obtained / self.assessment.total_marks) * 100

    def save(self, *args, **kwargs):
        # Auto-calculate grade letter based on percentage
        percentage = self.percentage
        if percentage >= 90:
            self.grade_letter = 'A+'
        elif percentage >= 80:
            self.grade_letter = 'A'
        elif percentage >= 70:
            self.grade_letter = 'B+'
        elif percentage >= 60:
            self.grade_letter = 'B'
        elif percentage >= 50:
            self.grade_letter = 'C+'
        elif percentage >= 40:
            self.grade_letter = 'C'
        else:
            self.grade_letter = 'F'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        unique_together = ['student', 'assessment']


class TimeTable(BaseModel):
    """Time table model for scheduling classes"""
    WEEKDAYS = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='timetable_slots')
    day_of_week = models.CharField(max_length=10, choices=WEEKDAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=20, blank=True)
    academic_year = models.CharField(max_length=9)

    def __str__(self):
        return f"{self.class_subject.class_instance.name} - {self.class_subject.subject.name} - {self.day_of_week} {self.start_time}-{self.end_time}"

    class Meta:
        verbose_name = "Time Table"
        verbose_name_plural = "Time Tables"
        unique_together = ['class_subject', 'day_of_week', 'start_time', 'academic_year']