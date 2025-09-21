from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Register API ViewSets
router = DefaultRouter()
router.register(r'schools', views.SchoolViewSet)
router.register(r'departments', views.DepartmentViewSet)
router.register(r'subjects', views.SubjectViewSet)
router.register(r'teachers', views.TeacherViewSet)
router.register(r'classes', views.ClassViewSet)
router.register(r'students', views.StudentViewSet)
router.register(r'class-subjects', views.ClassSubjectViewSet)
router.register(r'attendance', views.AttendanceViewSet)
router.register(r'assessments', views.AssessmentViewSet)
router.register(r'grades', views.GradeViewSet)
router.register(r'timetables', views.TimeTableViewSet)

urlpatterns = [
    path('', views.home, name='home'),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]