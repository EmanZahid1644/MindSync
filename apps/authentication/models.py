from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
	"""
	The base identity model for MindSync AI.
	Determines whether an account belongs to a student or teacher.
	"""

	is_student = models.BooleanField(default=False)
	is_teacher = models.BooleanField(default=False)

	def __str__(self):
		role = "Teacher" if self.is_teacher else "Student" if self.is_student else "Admin"
		return f"{self.username} ({role})"


class StudentProfile(models.Model):
	"""
	Extends the base user system to store student-specific metrics and attributes.
	"""

	user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name="student_profile")
	current_gpa = models.FloatField(default=0.0)
	academic_year = models.CharField(
		max_length=20,
		choices=[
			("freshman", "Freshman"),
			("sophomore", "Sophomore"),
			("junior", "Junior"),
			("senior", "Senior"),
		],
		default="freshman",
	)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Student: {self.user.get_full_name() or self.user.username}"


class TeacherProfile(models.Model):
	"""
	Extends the base user system to hold teacher identity profiles.
	"""

	user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name="teacher_profile")
	department = models.CharField(max_length=100, blank=True)
	employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Teacher: {self.user.get_full_name() or self.user.username}"
