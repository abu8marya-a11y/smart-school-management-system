from rest_framework import permissions
from django.contrib.auth.models import Group


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access certain views.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsTeacherUser(permissions.BasePermission):
    """
    Custom permission for teacher users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has teacher profile
        return hasattr(request.user, 'teacher_profile')


class IsStudentUser(permissions.BasePermission):
    """
    Custom permission for student users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has student profile
        return hasattr(request.user, 'student_profile')


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions are only allowed to the owner of the object
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsTeacherOfClassOrReadOnly(permissions.BasePermission):
    """
    Permission that allows teachers to modify records for their classes only.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions for teachers of the class
        if hasattr(request.user, 'teacher_profile'):
            teacher = request.user.teacher_profile
            
            # Check if teacher is class teacher or teaches the subject
            if hasattr(obj, 'current_class'):
                # For student objects
                class_instance = obj.current_class
                return (class_instance.class_teacher == teacher or 
                       teacher.teaching_assignments.filter(class_instance=class_instance).exists())
            elif hasattr(obj, 'student'):
                # For attendance, grade objects
                class_instance = obj.student.current_class
                return (class_instance.class_teacher == teacher or 
                       teacher.teaching_assignments.filter(class_instance=class_instance).exists())
            elif hasattr(obj, 'class_subject'):
                # For assessment objects
                return obj.class_subject.teacher == teacher
        
        return False


class CanManageAttendance(permissions.BasePermission):
    """
    Permission for attendance management.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins and teachers can manage attendance
        return (request.user.is_staff or 
                hasattr(request.user, 'teacher_profile'))


class CanManageGrades(permissions.BasePermission):
    """
    Permission for grade management.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins and teachers can manage grades
        return (request.user.is_staff or 
                hasattr(request.user, 'teacher_profile'))
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Teachers can only modify grades for their subjects
        if hasattr(request.user, 'teacher_profile'):
            teacher = request.user.teacher_profile
            if hasattr(obj, 'assessment'):
                return obj.assessment.class_subject.teacher == teacher
            elif hasattr(obj, 'class_subject'):
                return obj.class_subject.teacher == teacher
        
        # Admins can modify all grades
        return request.user.is_staff


class CanViewStudentData(permissions.BasePermission):
    """
    Permission for viewing student data.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # All authenticated users can view (but object-level permissions apply)
        return True
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admins can view all student data
        if user.is_staff:
            return True
        
        # Students can view their own data
        if hasattr(user, 'student_profile') and hasattr(obj, 'user'):
            return obj.user == user
        
        # Teachers can view data for their students
        if hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            if hasattr(obj, 'current_class'):
                # For student objects
                class_instance = obj.current_class
                return (class_instance.class_teacher == teacher or 
                       teacher.teaching_assignments.filter(class_instance=class_instance).exists())
            elif hasattr(obj, 'student'):
                # For attendance, grade objects
                class_instance = obj.student.current_class
                return (class_instance.class_teacher == teacher or 
                       teacher.teaching_assignments.filter(class_instance=class_instance).exists())
        
        return False


def create_user_groups():
    """
    Create default user groups for the school management system.
    """
    # Create groups
    admin_group, created = Group.objects.get_or_create(name='School Administrators')
    teacher_group, created = Group.objects.get_or_create(name='Teachers')
    student_group, created = Group.objects.get_or_create(name='Students')
    parent_group, created = Group.objects.get_or_create(name='Parents')
    
    return {
        'admin': admin_group,
        'teacher': teacher_group,
        'student': student_group,
        'parent': parent_group
    }


def assign_user_to_group(user, role):
    """
    Assign a user to appropriate group based on their role.
    
    Args:
        user: User instance
        role: String - 'admin', 'teacher', 'student', or 'parent'
    """
    groups = create_user_groups()
    
    if role in groups:
        # Remove user from all school-related groups first
        for group in groups.values():
            user.groups.remove(group)
        
        # Add user to the specific group
        user.groups.add(groups[role])
        
        # Set additional permissions for admins
        if role == 'admin':
            user.is_staff = True
            user.save()
        
        return True
    
    return False