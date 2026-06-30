from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dummy_dashboard_view, name='dashboard'),
    path('about/', views.about_view, name='about_us'),
    path('products/', views.products_view, name='products'),
    path('contact/', views.contact_view, name='contact_us'),
]