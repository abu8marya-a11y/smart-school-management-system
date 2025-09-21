from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    School, Department, Subject, Teacher, Class, Student,
    ClassSubject, Attendance, Assessment, Grade, TimeTable
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class SchoolSerializer(serializers.ModelSerializer):
    """Serializer for School model"""
    class Meta:
        model = School
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model"""
    school_name = serializers.CharField(source='school.name', read_only=True)
    head_name = serializers.CharField(source='head_of_department.user.get_full_name', read_only=True)
    
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for Subject model"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Subject
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TeacherSerializer(serializers.ModelSerializer):
    """Serializer for Teacher model"""
    user = UserSerializer(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    subjects_taught = SubjectSerializer(source='subjects', many=True, read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Teacher
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClassSerializer(serializers.ModelSerializer):
    """Serializer for Class model"""
    school_name = serializers.CharField(source='school.name', read_only=True)
    class_teacher_name = serializers.CharField(source='class_teacher.user.get_full_name', read_only=True)
    current_students_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'current_students_count']


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model"""
    user = UserSerializer(read_only=True)
    class_name = serializers.CharField(source='current_class.name', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'age']


class ClassSubjectSerializer(serializers.ModelSerializer):
    """Serializer for ClassSubject model"""
    class_name = serializers.CharField(source='class_instance.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    
    class Meta:
        model = ClassSubject
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance model"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    subject_name = serializers.CharField(source='class_subject.subject.name', read_only=True)
    marked_by_name = serializers.CharField(source='marked_by.user.get_full_name', read_only=True)
    
    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Assessment model"""
    class_name = serializers.CharField(source='class_subject.class_instance.name', read_only=True)
    subject_name = serializers.CharField(source='class_subject.subject.name', read_only=True)
    teacher_name = serializers.CharField(source='class_subject.teacher.user.get_full_name', read_only=True)
    
    class Meta:
        model = Assessment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class GradeSerializer(serializers.ModelSerializer):
    """Serializer for Grade model"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    assessment_name = serializers.CharField(source='assessment.name', read_only=True)
    total_marks = serializers.DecimalField(source='assessment.total_marks', max_digits=5, decimal_places=2, read_only=True)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    graded_by_name = serializers.CharField(source='graded_by.user.get_full_name', read_only=True)
    
    class Meta:
        model = Grade
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'percentage', 'grade_letter', 'graded_date']


class TimeTableSerializer(serializers.ModelSerializer):
    """Serializer for TimeTable model"""
    class_name = serializers.CharField(source='class_subject.class_instance.name', read_only=True)
    subject_name = serializers.CharField(source='class_subject.subject.name', read_only=True)
    teacher_name = serializers.CharField(source='class_subject.teacher.user.get_full_name', read_only=True)
    
    class Meta:
        model = TimeTable
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


# Nested serializers for detailed views
class StudentDetailSerializer(StudentSerializer):
    """Detailed Student serializer with related data"""
    attendance_records = AttendanceSerializer(many=True, read_only=True)
    grades = GradeSerializer(many=True, read_only=True)
    
    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'age']


class TeacherDetailSerializer(TeacherSerializer):
    """Detailed Teacher serializer with related data"""
    teaching_assignments = ClassSubjectSerializer(many=True, read_only=True)
    
    class Meta:
        model = Teacher
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClassDetailSerializer(ClassSerializer):
    """Detailed Class serializer with related data"""
    students = StudentSerializer(many=True, read_only=True)
    class_subjects = ClassSubjectSerializer(many=True, read_only=True)
    
    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'current_students_count']