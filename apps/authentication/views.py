from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User, StudentProfile, TeacherProfile


def _render_public_page(request, template_name, title, description, highlights):
    return render(
        request,
        template_name,
        {
            'page_title': title,
            'page_description': description,
            'page_highlights': highlights,
        },
    )

def signup_view(request):
    """Handles account creation and dynamic profile mapping."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role') # Will capture 'student' or 'teacher' from UI

        # Basic server-side redundancy validation
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'authentication/signup.html')

        # 1. Create Base User
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # 2. Bind Profile based on chosen role
        if role == 'teacher':
            user.is_teacher = True
            user.save()
            TeacherProfile.objects.create(user=user)
            messages.success(request, "Teacher account created successfully!")
        else:
            user.is_student = True
            user.save()
            StudentProfile.objects.create(user=user)
            messages.success(request, "Student account created successfully!")

        # 3. Log user in and send them to the setup phase/dashboard
        login(request, user)
        return redirect('platform_home')

    return render(request, 'authentication/signup.html')


def login_view(request):
    """Handles secure credentials verification and session binding."""
    if request.user.is_authenticated:
        return redirect('platform_home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('platform_home')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'authentication/login.html')


def logout_view(request):
    """Terminates session and purges cookie states."""
    logout(request)
    messages.info(request, "You have logged out of MindSync AI.")
    return redirect('login')


@login_required
def dummy_dashboard_view(request):
    """Temporary landing dashboard to confirm successful logins."""
    return render(request, 'authentication/dashboard.html')


def about_view(request):
    return _render_public_page(
        request,
        'authentication/about.html',
        'About Us',
        'MindSync AI combines intelligent study planning, resource discovery, and wellbeing support for students.',
        [
            'Personalized learning support',
            'AI-assisted resource discovery',
            'Progress and wellness awareness',
        ],
    )


def products_view(request):
    return _render_public_page(
        request,
        'authentication/products.html',
        'Products',
        'Explore the tools that power planning, coaching, and academic tracking across the MindSync platform.',
        [
            'Planner hub and topic discovery',
            'AI coach and study support',
            'Dashboard analytics and telemetry',
        ],
    )


def contact_view(request):
    return _render_public_page(
        request,
        'authentication/contact.html',
        'Contact Us',
        'Reach the MindSync team for support, feedback, or partnership questions.',
        [
            'Support: support@mindsync.local',
            'Partnerships: hello@mindsync.local',
            'Response time: within one business day',
        ],
    )