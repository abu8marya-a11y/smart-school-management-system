from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, F, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    School, Department, Subject, Teacher, Class, Student,
    ClassSubject, Attendance, Assessment, Grade, TimeTable
)
from .serializers import (
    SchoolSerializer, DepartmentSerializer, SubjectSerializer,
    TeacherSerializer, TeacherDetailSerializer, ClassSerializer, 
    ClassDetailSerializer, StudentSerializer, StudentDetailSerializer,
    ClassSubjectSerializer, AttendanceSerializer, AssessmentSerializer,
    GradeSerializer, TimeTableSerializer
)
from .permissions import (
    IsAdminUser, IsTeacherUser, IsStudentUser, IsOwnerOrReadOnly,
    IsTeacherOfClassOrReadOnly, CanManageAttendance, CanManageGrades,
    CanViewStudentData
)


def home(request):
    """Basic home view"""
    return HttpResponse("Welcome to Smart School Management System!")


class SchoolViewSet(viewsets.ModelViewSet):
    """ViewSet for School model"""
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAdminUser]  # Only admins can manage schools
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address', 'email']
    ordering_fields = ['name', 'established_date']
    ordering = ['name']


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Department model"""
    queryset = Department.objects.select_related('school', 'head_of_department__user')
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminUser]  # Only admins can manage departments
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['school']
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']


class SubjectViewSet(viewsets.ModelViewSet):
    """ViewSet for Subject model"""
    queryset = Subject.objects.select_related('department')
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]  # All authenticated users can view subjects
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'is_active', 'credits']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'credits']
    ordering = ['name']

    def get_permissions(self):
        """Only admins can create/update/delete subjects"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class TeacherViewSet(viewsets.ModelViewSet):
    """ViewSet for Teacher model"""
    queryset = Teacher.objects.select_related('user', 'department').prefetch_related('subjects')
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'is_active']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'user__email']
    ordering_fields = ['employee_id', 'hire_date']
    ordering = ['employee_id']

    def get_permissions(self):
        """Different permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TeacherDetailSerializer
        return TeacherSerializer

    @action(detail=True, methods=['get'])
    def teaching_schedule(self, request, pk=None):
        """Get teacher's teaching schedule"""
        teacher = self.get_object()
        timetable = TimeTable.objects.filter(
            class_subject__teacher=teacher
        ).select_related('class_subject__class_instance', 'class_subject__subject')
        serializer = TimeTableSerializer(timetable, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def classes_taught(self, request, pk=None):
        """Get classes taught by teacher"""
        teacher = self.get_object()
        class_subjects = ClassSubject.objects.filter(teacher=teacher).select_related(
            'class_instance', 'subject'
        )
        serializer = ClassSubjectSerializer(class_subjects, many=True)
        return Response(serializer.data)


class ClassViewSet(viewsets.ModelViewSet):
    """ViewSet for Class model"""
    queryset = Class.objects.select_related('school', 'class_teacher__user')
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['school', 'level', 'academic_year', 'is_active']
    search_fields = ['name', 'section']
    ordering_fields = ['level', 'section', 'name']
    ordering = ['level', 'section']

    def get_permissions(self):
        """Only admins can create/update/delete classes"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClassDetailSerializer
        return ClassSerializer

    @action(detail=True, methods=['get'])
    def students_list(self, request, pk=None):
        """Get list of students in the class"""
        class_instance = self.get_object()
        students = Student.objects.filter(current_class=class_instance, is_active=True)
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def attendance_summary(self, request, pk=None):
        """Get attendance summary for the class"""
        class_instance = self.get_object()
        today = timezone.now().date()
        
        # Get attendance for today
        today_attendance = Attendance.objects.filter(
            student__current_class=class_instance,
            date=today
        ).values('status').annotate(count=Count('id'))
        
        # Get attendance for last 7 days
        week_ago = today - timedelta(days=7)
        week_attendance = Attendance.objects.filter(
            student__current_class=class_instance,
            date__gte=week_ago,
            date__lte=today
        ).values('date', 'status').annotate(count=Count('id'))
        
        return Response({
            'today': list(today_attendance),
            'last_week': list(week_attendance),
            'total_students': class_instance.current_students_count
        })


class StudentViewSet(viewsets.ModelViewSet):
    """ViewSet for Student model"""
    queryset = Student.objects.select_related('user', 'current_class')
    serializer_class = StudentSerializer
    permission_classes = [CanViewStudentData]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['current_class', 'is_active']
    search_fields = ['student_id', 'admission_number', 'user__first_name', 'user__last_name']
    ordering_fields = ['student_id', 'admission_date']
    ordering = ['student_id']

    def get_permissions(self):
        """Different permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [CanViewStudentData]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Admins see all students
        if user.is_staff:
            return queryset
        
        # Students see only themselves
        if hasattr(user, 'student_profile'):
            return queryset.filter(user=user)
        
        # Teachers see their students
        if hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            # Students in classes where teacher is class teacher or teaches subjects
            return queryset.filter(
                Q(current_class__class_teacher=teacher) |
                Q(current_class__class_subjects__teacher=teacher)
            ).distinct()
        
        return queryset.none()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StudentDetailSerializer
        return StudentSerializer

    @action(detail=True, methods=['get'])
    def attendance_record(self, request, pk=None):
        """Get student's attendance record"""
        student = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        attendance_qs = Attendance.objects.filter(student=student)
        
        if start_date:
            attendance_qs = attendance_qs.filter(date__gte=start_date)
        if end_date:
            attendance_qs = attendance_qs.filter(date__lte=end_date)
            
        attendance = attendance_qs.select_related('class_subject__subject', 'marked_by__user')
        serializer = AttendanceSerializer(attendance, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def grade_report(self, request, pk=None):
        """Get student's grade report"""
        student = self.get_object()
        grades = Grade.objects.filter(student=student).select_related(
            'assessment__class_subject__subject', 'graded_by__user'
        )
        serializer = GradeSerializer(grades, many=True)
        
        # Calculate overall statistics
        total_marks = sum(grade.marks_obtained for grade in grades)
        total_possible = sum(grade.assessment.total_marks for grade in grades)
        average_percentage = (total_marks / total_possible * 100) if total_possible > 0 else 0
        
        return Response({
            'grades': serializer.data,
            'statistics': {
                'total_assessments': grades.count(),
                'average_percentage': round(average_percentage, 2),
                'total_marks_obtained': total_marks,
                'total_possible_marks': total_possible
            }
        })


class ClassSubjectViewSet(viewsets.ModelViewSet):
    """ViewSet for ClassSubject model"""
    queryset = ClassSubject.objects.select_related(
        'class_instance', 'subject', 'teacher__user'
    )
    serializer_class = ClassSubjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['class_instance', 'subject', 'teacher', 'academic_year']
    search_fields = ['class_instance__name', 'subject__name', 'teacher__user__first_name']
    ordering = ['class_instance__level', 'class_instance__section', 'subject__name']

    def get_permissions(self):
        """Only admins can create/update/delete class-subject assignments"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet for Attendance model"""
    queryset = Attendance.objects.select_related(
        'student__user', 'class_subject__subject', 'marked_by__user'
    )
    serializer_class = AttendanceSerializer
    permission_classes = [CanManageAttendance]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'status', 'date', 'class_subject']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_id']
    ordering_fields = ['date']
    ordering = ['-date']

    def get_queryset(self):
        """Filter attendance records based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Admins see all attendance records
        if user.is_staff:
            return queryset
        
        # Teachers see attendance for their students only
        if hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            return queryset.filter(
                Q(student__current_class__class_teacher=teacher) |
                Q(class_subject__teacher=teacher)
            ).distinct()
        
        return queryset.none()

    @action(detail=False, methods=['post'])
    def mark_attendance(self, request):
        """Bulk mark attendance for multiple students"""
        attendance_data = request.data.get('attendance_records', [])
        created_records = []
        
        for record in attendance_data:
            serializer = self.get_serializer(data=record)
            if serializer.is_valid():
                serializer.save()
                created_records.append(serializer.data)
        
        return Response({
            'created_records': len(created_records),
            'records': created_records
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def attendance_report(self, request):
        """Generate attendance report"""
        class_id = request.query_params.get('class_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        attendance_qs = self.get_queryset()
        
        if class_id:
            attendance_qs = attendance_qs.filter(student__current_class_id=class_id)
        if start_date:
            attendance_qs = attendance_qs.filter(date__gte=start_date)
        if end_date:
            attendance_qs = attendance_qs.filter(date__lte=end_date)
        
        # Aggregate data
        report = attendance_qs.values('status').annotate(count=Count('id'))
        
        return Response(list(report))


class AssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Assessment model"""
    queryset = Assessment.objects.select_related('class_subject__class_instance', 'class_subject__subject')
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['class_subject', 'assessment_type', 'is_published']
    search_fields = ['name', 'description']
    ordering_fields = ['date', 'name']
    ordering = ['-date']

    def get_permissions(self):
        """Teachers can manage assessments for their subjects, admins can manage all"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter assessments based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Admins see all assessments
        if user.is_staff:
            return queryset
        
        # Teachers see assessments for their subjects
        if hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            return queryset.filter(class_subject__teacher=teacher)
        
        # Students see published assessments for their class
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            return queryset.filter(
                class_subject__class_instance=student.current_class,
                is_published=True
            )
        
        return queryset

    @action(detail=True, methods=['get'])
    def grades_summary(self, request, pk=None):
        """Get grades summary for an assessment"""
        assessment = self.get_object()
        grades = Grade.objects.filter(assessment=assessment)
        
        summary = {
            'total_students': grades.count(),
            'average_marks': grades.aggregate(Avg('marks_obtained'))['marks_obtained__avg'] or 0,
            'highest_marks': grades.aggregate(max_marks=Max('marks_obtained'))['max_marks'] or 0,
            'lowest_marks': grades.aggregate(min_marks=Min('marks_obtained'))['min_marks'] or 0,
            'grade_distribution': grades.values('grade_letter').annotate(count=Count('id'))
        }
        
        return Response(summary)


class GradeViewSet(viewsets.ModelViewSet):
    """ViewSet for Grade model"""
    queryset = Grade.objects.select_related(
        'student__user', 'assessment__class_subject__subject', 'graded_by__user'
    )
    serializer_class = GradeSerializer
    permission_classes = [CanManageGrades]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'assessment', 'grade_letter']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'assessment__name']
    ordering_fields = ['marks_obtained', 'graded_date']
    ordering = ['-graded_date']

    def get_queryset(self):
        """Filter grades based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Admins see all grades
        if user.is_staff:
            return queryset
        
        # Teachers see grades for their assessments
        if hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            return queryset.filter(assessment__class_subject__teacher=teacher)
        
        # Students see their own grades
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            return queryset.filter(student=student)
        
        return queryset.none()

    @action(detail=False, methods=['get'])
    def class_performance(self, request):
        """Get class performance statistics"""
        class_id = request.query_params.get('class_id')
        subject_id = request.query_params.get('subject_id')
        
        grades_qs = self.get_queryset()
        
        if class_id:
            grades_qs = grades_qs.filter(student__current_class_id=class_id)
        if subject_id:
            grades_qs = grades_qs.filter(assessment__class_subject__subject_id=subject_id)
        
        performance = {
            'total_grades': grades_qs.count(),
            'average_percentage': grades_qs.aggregate(
                avg_pct=Avg(F('marks_obtained') / F('assessment__total_marks') * 100)
            )['avg_pct'] or 0,
            'grade_distribution': grades_qs.values('grade_letter').annotate(count=Count('id'))
        }
        
        return Response(performance)


class TimeTableViewSet(viewsets.ModelViewSet):
    """ViewSet for TimeTable model"""
    queryset = TimeTable.objects.select_related(
        'class_subject__class_instance', 'class_subject__subject', 'class_subject__teacher__user'
    )
    serializer_class = TimeTableSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['class_subject__class_instance', 'day_of_week', 'academic_year']
    search_fields = ['class_subject__class_instance__name', 'class_subject__subject__name']
    ordering_fields = ['day_of_week', 'start_time']
    ordering = ['day_of_week', 'start_time']

    def get_permissions(self):
        """Only admins can create/update/delete timetables"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'])
    def weekly_schedule(self, request):
        """Get weekly schedule for a class or teacher"""
        class_id = request.query_params.get('class_id')
        teacher_id = request.query_params.get('teacher_id')
        
        timetable_qs = self.get_queryset()
        
        if class_id:
            timetable_qs = timetable_qs.filter(class_subject__class_instance_id=class_id)
        elif teacher_id:
            timetable_qs = timetable_qs.filter(class_subject__teacher_id=teacher_id)
        
        # Group by day of week
        schedule = {}
        for entry in timetable_qs:
            day = entry.day_of_week
            if day not in schedule:
                schedule[day] = []
            schedule[day].append(TimeTableSerializer(entry).data)
        
        return Response(schedule)