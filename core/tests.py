from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, time
from .models import (
    School, Department, Subject, Teacher, Class, Student,
    ClassSubject, Attendance, Assessment, Grade, TimeTable
)


class SchoolModelTest(TestCase):
    """Test cases for School model"""
    
    def setUp(self):
        self.school = School.objects.create(
            name="Test High School",
            address="123 Education St, Learning City",
            phone="+1234567890",
            email="admin@testschool.edu",
            website="https://testschool.edu",
            established_date=date(2000, 1, 1)
        )
    
    def test_school_creation(self):
        """Test school creation and string representation"""
        self.assertEqual(str(self.school), "Test High School")
        self.assertEqual(self.school.name, "Test High School")
        self.assertEqual(self.school.email, "admin@testschool.edu")
    
    def test_school_fields(self):
        """Test all school fields are correctly set"""
        self.assertTrue(self.school.id)
        self.assertTrue(self.school.created_at)
        self.assertTrue(self.school.updated_at)


class StudentModelTest(TestCase):
    """Test cases for Student model"""
    
    def setUp(self):
        # Create required objects
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St",
            phone="1234567890",
            email="test@school.com",
            established_date=date(2020, 1, 1)
        )
        
        self.user = User.objects.create_user(
            username="john_doe",
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        self.class_instance = Class.objects.create(
            name="Grade 10A",
            level=10,
            section="A",
            school=self.school,
            academic_year="2023-2024"
        )
        
        self.student = Student.objects.create(
            user=self.user,
            student_id="STU001",
            admission_number="ADM001",
            address="456 Student Ave",
            date_of_birth=date(2008, 5, 15),
            admission_date=date(2023, 9, 1),
            current_class=self.class_instance,
            guardian_name="Jane Doe",
            guardian_phone="0987654321",
            guardian_email="jane@example.com",
            emergency_contact="1112223333"
        )
    
    def test_student_creation(self):
        """Test student creation"""
        self.assertEqual(str(self.student), "STU001 - John Doe")
        self.assertEqual(self.student.user.get_full_name(), "John Doe")
    
    def test_student_age_calculation(self):
        """Test age calculation property"""
        # This will depend on current date, but should be around 15-16
        self.assertGreater(self.student.age, 10)
        self.assertLess(self.student.age, 20)


class TeacherModelTest(TestCase):
    """Test cases for Teacher model"""
    
    def setUp(self):
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St",
            phone="1234567890",
            email="test@school.com",
            established_date=date(2020, 1, 1)
        )
        
        self.department = Department.objects.create(
            name="Mathematics",
            school=self.school
        )
        
        self.user = User.objects.create_user(
            username="prof_smith",
            first_name="Professor",
            last_name="Smith",
            email="smith@school.com"
        )
        
        self.teacher = Teacher.objects.create(
            user=self.user,
            employee_id="EMP001",
            phone="5555551234",
            address="789 Teacher Blvd",
            date_of_birth=date(1980, 3, 20),
            hire_date=date(2020, 8, 15),
            department=self.department,
            qualification="M.Sc. Mathematics",
            experience_years=10
        )
    
    def test_teacher_creation(self):
        """Test teacher creation"""
        self.assertEqual(str(self.teacher), "EMP001 - Professor Smith")
        self.assertEqual(self.teacher.qualification, "M.Sc. Mathematics")


class GradeModelTest(TestCase):
    """Test cases for Grade model with grade calculation"""
    
    def setUp(self):
        # Create all required objects
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St",
            phone="1234567890",
            email="test@school.com",
            established_date=date(2020, 1, 1)
        )
        
        self.department = Department.objects.create(
            name="Mathematics",
            school=self.school
        )
        
        self.subject = Subject.objects.create(
            name="Algebra",
            code="MATH101",
            department=self.department
        )
        
        self.teacher_user = User.objects.create_user(
            username="teacher",
            first_name="Teacher",
            last_name="One"
        )
        
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            employee_id="T001",
            phone="1234567890",
            address="Teacher Address",
            date_of_birth=date(1980, 1, 1),
            hire_date=date(2020, 1, 1),
            department=self.department
        )
        
        self.class_instance = Class.objects.create(
            name="Grade 10A",
            level=10,
            section="A",
            school=self.school,
            academic_year="2023-2024"
        )
        
        self.student_user = User.objects.create_user(
            username="student",
            first_name="Student",
            last_name="One"
        )
        
        self.student = Student.objects.create(
            user=self.student_user,
            student_id="S001",
            admission_number="A001",
            address="Student Address",
            date_of_birth=date(2008, 1, 1),
            admission_date=date(2023, 1, 1),
            current_class=self.class_instance,
            guardian_name="Guardian",
            guardian_phone="1234567890"
        )
        
        self.class_subject = ClassSubject.objects.create(
            class_instance=self.class_instance,
            subject=self.subject,
            teacher=self.teacher,
            academic_year="2023-2024"
        )
        
        self.assessment = Assessment.objects.create(
            name="Mid-term Exam",
            class_subject=self.class_subject,
            assessment_type="midterm",
            total_marks=100,
            date=date.today()
        )
    
    def test_grade_calculation(self):
        """Test grade letter calculation"""
        # Test A+ grade (90-100%)
        grade_a_plus = Grade.objects.create(
            student=self.student,
            assessment=self.assessment,
            marks_obtained=95,
            graded_by=self.teacher
        )
        self.assertEqual(grade_a_plus.grade_letter, 'A+')
        self.assertEqual(grade_a_plus.percentage, 95.0)
        
        # Test B grade (60-69%)
        grade_b = Grade.objects.create(
            student=self.student,
            assessment=Assessment.objects.create(
                name="Quiz 1",
                class_subject=self.class_subject,
                assessment_type="quiz",
                total_marks=50,
                date=date.today()
            ),
            marks_obtained=32.5,
            graded_by=self.teacher
        )
        self.assertEqual(grade_b.grade_letter, 'B')
        self.assertEqual(grade_b.percentage, 65.0)


class SchoolAPITest(APITestCase):
    """Test cases for School API endpoints"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.school_data = {
            'name': 'API Test School',
            'address': '123 API Street',
            'phone': '+1234567890',
            'email': 'api@testschool.edu',
            'website': 'https://apitestschool.edu',
            'established_date': '2020-01-01'
        }
    
    def test_create_school_as_admin(self):
        """Test creating a school via API as admin"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/schools/', self.school_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(School.objects.count(), 1)
        self.assertEqual(School.objects.get().name, 'API Test School')
    
    def test_create_school_as_regular_user(self):
        """Test that regular users cannot create schools"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post('/api/schools/', self.school_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(School.objects.count(), 0)
    
    def test_get_schools_list_as_admin(self):
        """Test retrieving schools list as admin"""
        self.client.force_authenticate(user=self.admin_user)
        School.objects.create(**self.school_data)
        response = self.client.get('/api/schools/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_get_schools_list_as_regular_user(self):
        """Test that regular users cannot view schools list"""
        self.client.force_authenticate(user=self.regular_user)
        School.objects.create(**self.school_data)
        response = self.client.get('/api/schools/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthorized_access(self):
        """Test that unauthenticated users cannot access API"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/schools/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AttendanceAPITest(APITestCase):
    """Test cases for Attendance API functionality"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        
        self.teacher_user = User.objects.create_user(
            username='teacher',
            first_name="Teacher",
            last_name="One"
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Create required objects
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St",
            phone="1234567890",
            email="test@school.com",
            established_date=date(2020, 1, 1)
        )
        
        self.department = Department.objects.create(
            name="Test Department",
            school=self.school
        )
        
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            employee_id="T001",
            phone="1234567890",
            address="Teacher Address",
            date_of_birth=date(1980, 1, 1),
            hire_date=date(2020, 1, 1),
            department=self.department
        )
        
        self.class_instance = Class.objects.create(
            name="Grade 10A",
            level=10,
            section="A",
            school=self.school,
            academic_year="2023-2024"
        )
        
        self.student_user = User.objects.create_user(
            username="student",
            first_name="Student",
            last_name="One"
        )
        
        self.student = Student.objects.create(
            user=self.student_user,
            student_id="S001",
            admission_number="A001",
            address="Student Address",
            date_of_birth=date(2008, 1, 1),
            admission_date=date(2023, 1, 1),
            current_class=self.class_instance,
            guardian_name="Guardian",
            guardian_phone="1234567890"
        )
    
    def test_mark_attendance_as_teacher(self):
        """Test marking attendance for a student as teacher"""
        # Authenticate as teacher
        self.client.force_authenticate(user=self.teacher_user)
        
        attendance_data = {
            'student': self.student.id,
            'date': date.today().isoformat(),
            'status': 'present',
            'marked_by': self.teacher.id
        }
        
        response = self.client.post('/api/attendance/', attendance_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Attendance.objects.count(), 1)
        
        attendance = Attendance.objects.get()
        self.assertEqual(attendance.status, 'present')
        self.assertEqual(attendance.student, self.student)
    
    def test_mark_attendance_as_admin(self):
        """Test marking attendance for a student as admin"""
        # Already authenticated as admin in setUp
        attendance_data = {
            'student': self.student.id,
            'date': date.today().isoformat(),
            'status': 'absent',
            'marked_by': self.teacher.id
        }
        
        response = self.client.post('/api/attendance/', attendance_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Attendance.objects.count(), 1)