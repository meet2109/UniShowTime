from django.urls import path
from django.shortcuts import redirect
from . import views

def home_redirect(request):
    return redirect('dashboard')

urlpatterns = [
    # Filter endpoints
    path('filter-events/', views.filter_events, name='filter_events'),
    path('filter-users/', views.filter_users, name='filter_users'),
    path('', home_redirect),
    path('superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('user/<int:user_id>/', views.admin_user_details, name='admin_user_details'),
    path('create-event/', views.create_event, name='create_event'),
    path('suggest-event/', views.suggest_event, name='suggest_event'),
    path('admindashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('ticket/<int:ticket_id>/qr/', views.qr_view, name='qr_view'),
    path('ticket/<int:ticket_id>/download/', views.qr_download, name='qr_download'),
    path('event/<int:event_id>/', views.event_details, name='event_details'),
    path('event/<int:event_id>/book/', views.book_ticket, name='book_ticket'),
    path('event/<int:event_id>/admin/', views.admin_event_details, name='admin_event_details'),
    path('event/<int:event_id>/memories/', views.event_memories, name='event_memories'),
    path('department/<int:department_id>/', views.department_details, name='department_details'),
    path('department/create/', views.create_department, name='create_department'),
    path('user/<int:user_id>/details/', views.user_details, name='user_details'),
    path('user/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('user/create/', views.create_user, name='create_user'),
    path('admin/settings/', views.admin_settings, name='admin_settings'),
    path('admin/logs/', views.admin_logs, name='admin_logs'),
    path('admin/backup/', views.admin_backup, name='admin_backup'),
]
