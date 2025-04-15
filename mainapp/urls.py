from django.urls import path
from . import views

from django.shortcuts import redirect

def home_redirect(request):
    return redirect('dashboard')

urlpatterns = [
    path('', home_redirect), 
     path('user/<int:user_id>/', views.admin_user_details, name='admin_user_details'), 
    path('create-event/', views.create_event, name='create_event'),
    path('admindashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('ticket/<int:ticket_id>/qr/', views.qr_view, name='qr_view'),
    path('ticket/<int:ticket_id>/download/', views.qr_download, name='qr_download'),
]
