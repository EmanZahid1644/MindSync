from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    The Base Identity Model for MindSync AI.
    Determines whether the authenticating account belongs to a Student or Teacher.
    """
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({'Teacher' if self.is_teacher else 'Student' if self.is_student else 'Admin'})"


class StudentProfile(models.Model):
    """
    Extends the base User system to store student-specific metrics, logs, and attributes.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='student_profile')
    current_gpa = models.FloatField(default=0.0)
    academic_year = models.CharField(max_length=20, choices=[
        ('freshman', 'Freshman'),
        ('sophomore', 'Sophomore'),
        ('junior', 'Junior'),
        ('senior', 'Senior'),
    ], default='freshman')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Student: {self.user.get_full_name() or self.user.username}"


class TeacherProfile(models.Model):
    """
    Extends the base User system to hold teacher identity profiles.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='teacher_profile')
    department = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Teacher: {self.user.get_full_name() or self.user.username}"