from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import School, Department, Subject, Teacher, Class, Student, Attendance, Grade
from core.permissions import create_user_groups


class Command(BaseCommand):
    help = 'Setup initial user groups and permissions for the school management system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up user groups and permissions...'))
        
        # Create user groups
        groups = create_user_groups()
        
        # Get content types for our models
        school_ct = ContentType.objects.get_for_model(School)
        department_ct = ContentType.objects.get_for_model(Department)
        subject_ct = ContentType.objects.get_for_model(Subject)
        teacher_ct = ContentType.objects.get_for_model(Teacher)
        class_ct = ContentType.objects.get_for_model(Class)
        student_ct = ContentType.objects.get_for_model(Student)
        attendance_ct = ContentType.objects.get_for_model(Attendance)
        grade_ct = ContentType.objects.get_for_model(Grade)
        
        # Define permissions for each group
        admin_permissions = [
            # School administrators can do everything
            'add_school', 'change_school', 'delete_school', 'view_school',
            'add_department', 'change_department', 'delete_department', 'view_department',
            'add_subject', 'change_subject', 'delete_subject', 'view_subject',
            'add_teacher', 'change_teacher', 'delete_teacher', 'view_teacher',
            'add_class', 'change_class', 'delete_class', 'view_class',
            'add_student', 'change_student', 'delete_student', 'view_student',
            'add_attendance', 'change_attendance', 'delete_attendance', 'view_attendance',
            'add_grade', 'change_grade', 'delete_grade', 'view_grade',
        ]
        
        teacher_permissions = [
            # Teachers can view most things and manage attendance/grades for their classes
            'view_school', 'view_department', 'view_subject', 'view_teacher',
            'view_class', 'view_student',
            'add_attendance', 'change_attendance', 'view_attendance',
            'add_grade', 'change_grade', 'view_grade',
        ]
        
        student_permissions = [
            # Students can only view their own data
            'view_school', 'view_department', 'view_subject', 'view_class',
            'view_attendance', 'view_grade',
        ]
        
        parent_permissions = [
            # Parents can view their children's data
            'view_school', 'view_class', 'view_student', 'view_attendance', 'view_grade',
        ]
        
        # Assign permissions to groups
        permission_mapping = {
            groups['admin']: admin_permissions,
            groups['teacher']: teacher_permissions,
            groups['student']: student_permissions,
            groups['parent']: parent_permissions,
        }
        
        for group, perm_codes in permission_mapping.items():
            for perm_code in perm_codes:
                try:
                    # Find the permission
                    app_label, codename = perm_code.split('_', 1)
                    
                    # Map model names to content types
                    model_ct_map = {
                        'school': school_ct,
                        'department': department_ct,
                        'subject': subject_ct,
                        'teacher': teacher_ct,
                        'class': class_ct,
                        'student': student_ct,
                        'attendance': attendance_ct,
                        'grade': grade_ct,
                    }
                    
                    if codename in model_ct_map:
                        ct = model_ct_map[codename]
                        perm = Permission.objects.get(
                            content_type=ct,
                            codename=f'{app_label}_{codename}'
                        )
                        group.permissions.add(perm)
                        
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Permission {perm_code} not found')
                    )
                    continue
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up user groups and permissions!')
        )
        
        # Display group information
        for group_name, group in groups.items():
            self.stdout.write(f'\n{group_name.title()} Group:')
            self.stdout.write(f'  - Name: {group.name}')
            self.stdout.write(f'  - Permissions: {group.permissions.count()}')
            
        self.stdout.write(
            self.style.SUCCESS(f'\nCreated {len(groups)} user groups with appropriate permissions.')
        )