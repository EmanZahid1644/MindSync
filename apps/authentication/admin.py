from django.contrib import admin

from .models import StudentProfile, TeacherProfile, User


admin.site.register(User)
admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
