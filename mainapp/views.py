from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.db import models, transaction
import os
import json

from .forms import CustomUserRegisterForm, CustomLoginForm
from .models import CustomUser, Event, Ticket, Department, SystemLog, SystemBackup

def register_view(request):
    from .models import Department
    
    if request.method == 'POST':
        form = CustomUserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
            return redirect('dashboard')
    else:
        form = CustomUserRegisterForm()
    
    departments = Department.objects.all()
    return render(request, 'auth/register.html', {
        'form': form,
        'departments': departments
    })

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomLoginForm()
    return render(request, 'auth/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    user = request.user
    if user.role == 'student':
        return redirect('student_dashboard')
    elif user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'superadmin':
        return redirect('superadmin_dashboard')

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    
    # Get upcoming events
    from django.utils import timezone
    from .models import Event, Ticket
    
    events = Event.objects.filter(date__gte=timezone.now().date())
    past_events = Event.objects.filter(date__lt=timezone.now().date())
    attended_events = Ticket.objects.filter(user=request.user)
    
    return render(request, 'dashboard/student_dashboard.html', {
        'events': events,
        'past_events': past_events,
        'attended_events': attended_events
    })

from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, HttpResponseForbidden
from .models import Ticket

def qr_view(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if ticket.user != request.user:
        return HttpResponseForbidden("You are not allowed to view this QR code.")
    return render(request, 'mainapp/show_qr.html', {'ticket': ticket})

def qr_download(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if ticket.user != request.user:
        return HttpResponseForbidden("You are not allowed to download this QR code.")
    return FileResponse(ticket.qr_code, as_attachment=True, filename=ticket.qr_code.name.split('/')[-1])

from django.shortcuts import render
from .models import Event, CustomUser
from django.utils import timezone

@login_required
def superadmin_dashboard(request):
    if request.user.role != 'superadmin':
        return redirect('dashboard')
    
    departments = Department.objects.all()
    users = CustomUser.objects.all()
    events = Event.objects.all()
    
    # Calculate statistics
    total_bookings = Ticket.objects.count()
    
    # Filter users by role
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    context = {
        'departments': departments,
        'users': users,
        'events': events,
        'total_departments': departments.count(),
        'total_users': users.count(),
        'total_events': events.count(),
        'total_bookings': total_bookings,
    }
    
    return render(request, 'dashboard/superadmin_dashboard.html', context)

def admin_dashboard(request):
    if request.user.role not in ['admin', 'superadmin']:
        return redirect('dashboard')
        
    # Apply filters
    events = Event.objects.all()
    users = CustomUser.objects.all()
    
    # Filter users by role
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Filter events by category
    category_filter = request.GET.get('category')
    if category_filter:
        events = events.filter(category=category_filter)
        
    # Calculate statistics
    total_events = Event.objects.count()
    total_bookings = Ticket.objects.count()
    upcoming_events = Event.objects.filter(date__gte=timezone.now()).count()

    return render(request, 'dashboard/admin_dashboard.html', {
        'total_events': total_events,
        'total_bookings': total_bookings,
        'upcoming_events': upcoming_events,
        'events': events,
        'users': users,
    })

@login_required
def filter_events(request):
    if request.user.role not in ['admin', 'superadmin']:
        return HttpResponseForbidden()
    
    category = request.GET.get('category')
    search = request.GET.get('search', '').strip()
    events = Event.objects.all()
    
    if category:
        events = events.filter(category=category)
    if search:
        events = events.filter(
            title__icontains=search
        )
    
    html = render_to_string('dashboard/partials/event_list.html', {
        'events': events
    })
    
    return JsonResponse({'html': html})

@login_required
def filter_users(request):
    if request.user.role not in ['admin', 'superadmin']:
        return HttpResponseForbidden()
    
    role = request.GET.get('role')
    search = request.GET.get('search', '').strip()
    users = CustomUser.objects.all()
    
    if role:
        users = users.filter(role=role)
    if search:
        users = users.filter(
            username__icontains=search
        )
    
    html = render_to_string('dashboard/partials/user_list.html', {
        'users': users
    })
    
    return JsonResponse({'html': html})

def event_details(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user_has_ticket = False
    user_ticket = None
    
    if request.user.is_authenticated:
        user_ticket = Ticket.objects.filter(event=event, user=request.user).first()
        user_has_ticket = user_ticket is not None
    
    context = {
        'event': event,
        'user_has_ticket': user_has_ticket,
        'user_ticket': user_ticket
    }
    return render(request, 'mainapp/event_detail.html', context)

@login_required
def book_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user already has a ticket
    if Ticket.objects.filter(event=event, user=request.user).exists():
        messages.error(request, 'You already have a ticket for this event!')
        return redirect('event_details', event_id=event_id)
    
    # Check if tickets are available
    if event.tickets_left() <= 0:
        messages.error(request, 'Sorry, this event is sold out!')
        return redirect('event_details', event_id=event_id)
    
    # Handle payment if event is not free
    if not event.is_free:
        # Add your payment processing logic here
        # For now, we'll just create the ticket
        pass
    
    # Create ticket
    ticket = Ticket.objects.create(
        event=event,
        user=request.user
    )
    
    messages.success(request, 'Ticket booked successfully!')
    return redirect('qr_view', ticket_id=ticket.id)

@login_required
def admin_event_details(request, event_id):
    if request.user.role not in ['admin', 'superadmin']:
        return HttpResponseForbidden("You don't have permission to view this page.")
        
    event = get_object_or_404(Event, id=event_id)
    tickets = Ticket.objects.filter(event=event)
    
    return render(request, 'mainapp/admin_event_details.html', {
        'event': event,
        'tickets': tickets
    })

@login_required
def event_memories(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if event.date >= timezone.now().date():
        messages.error(request, "Event memories are only available after the event has ended.")
        return redirect('event_details', event_id=event_id)
        
    return render(request, 'mainapp/event_memories.html', {
        'event': event
    })

@login_required
def department_details(request, department_id):
    if request.user.role != 'superadmin':
        return HttpResponseForbidden("You don't have permission to view this page.")
    
    department = get_object_or_404(Department, id=department_id)
    users = CustomUser.objects.filter(department=department)
    
    return render(request, 'mainapp/department_details.html', {
        'department': department,
        'users': users
    })

@login_required
def create_department(request):
    if request.user.role != 'superadmin':
        return HttpResponseForbidden("You don't have permission to view this page.")
    
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        if name and code:
            Department.objects.create(name=name, code=code)
            messages.success(request, 'Department created successfully.')
            return redirect('superadmin_dashboard')
        messages.error(request, 'Please fill all required fields.')
    
    return render(request, 'mainapp/create_department.html')

@login_required
def user_details(request, user_id):
    if request.user.role != 'superadmin':
        return HttpResponseForbidden("You don't have permission to view this page.")
    
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'mainapp/user_details.html', {'user': user})

@login_required
def edit_user(request, user_id):
    if request.user.role != 'superadmin':
        return HttpResponseForbidden("You don't have permission to view this page.")
    
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.role = request.POST.get('role', user.role)
        if request.POST.get('department'):
            user.department = get_object_or_404(Department, id=request.POST.get('department'))
        user.save()
        messages.success(request, 'User updated successfully.')
        return redirect('user_details', user_id=user.id)
    
    departments = Department.objects.all()
    return render(request, 'mainapp/edit_user.html', {
        'user': user,
        'departments': departments
    })

@login_required
def create_user(request):
    if request.user.role != 'superadmin':
        return HttpResponseForbidden("You don't have permission to view this page.")
    
    if request.method == 'POST':
        form = CustomUserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'User created successfully.')
            return redirect('user_details', user_id=user.id)
    else:
        form = CustomUserRegisterForm()
    
    return render(request, 'mainapp/create_user.html', {'form': form})

@login_required
def admin_settings(request):
    if request.user.role != 'superadmin':
        return HttpResponseForbidden("You don't have permission to view this page.")
    return render(request, 'dashboard/admin_settings.html')

@login_required
def admin_logs(request):
    if request.user.role != 'superadmin':
        return HttpResponseForbidden("You don't have permission to view this page.")
    
    # Get filter parameters
    date_range = request.GET.get('date_range')
    log_level = request.GET.get('log_level')
    log_type = request.GET.get('log_type')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    logs = SystemLog.objects.all()
    
    # Apply date range filter
    if date_range:
        now = timezone.now()
        if date_range == 'last_24_hours':
            logs = logs.filter(timestamp__gte=now - timezone.timedelta(days=1))
        elif date_range == 'last_7_days':
            logs = logs.filter(timestamp__gte=now - timezone.timedelta(days=7))
        elif date_range == 'last_30_days':
            logs = logs.filter(timestamp__gte=now - timezone.timedelta(days=30))
    
    # Apply log level filter
    if log_level and log_level != 'all':
        logs = logs.filter(level=log_level.upper())
    
    # Apply log type filter
    if log_type and log_type != 'all':
        logs = logs.filter(log_type=log_type.upper())
    
    # Apply search filter
    if search_query:
        logs = logs.filter(
            models.Q(event__icontains=search_query) |
            models.Q(details__icontains=search_query) |
            models.Q(user__username__icontains=search_query)
        )
    
    # Handle AJAX request for filtered results
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('dashboard/partials/log_entries.html', {'logs': logs})
        return JsonResponse({'html': html})
    
    return render(request, 'dashboard/admin_logs.html', {
        'logs': logs,
        'log_levels': SystemLog.LOG_LEVELS,
        'log_types': SystemLog.LOG_TYPES
    })

@login_required
def admin_backup(request):
    if request.user.role != 'superadmin':
        return HttpResponseForbidden("You don't have permission to view this page.")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_backup':
            try:
                # Create backup directory if it doesn't exist
                backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                # Generate backup filename
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f'backup_{timestamp}.json'
                backup_path = os.path.join(backup_dir, backup_filename)
                
                # Get all data to backup
                data = {
                    'events': list(Event.objects.values()),
                    'users': list(CustomUser.objects.values()),
                    'departments': list(Department.objects.values()),
                    'tickets': list(Ticket.objects.values()),
                }
                
                # Write backup file
                with open(backup_path, 'w') as f:
                    json.dump(data, f, indent=4, default=str)
                
                # Create backup record
                backup = SystemBackup.objects.create(
                    backup_type='FULL',
                    status='COMPLETED',
                    file_path=backup_path,
                    file_size=os.path.getsize(backup_path),
                    created_by=request.user
                )
                
                # Log backup creation
                SystemLog.objects.create(
                    level='INFO',
                    log_type='SYSTEM',
                    event='Backup Created',
                    user=request.user,
                    details=f'Backup created successfully: {backup.backup_id}'
                )
                
                messages.success(request, 'Backup created successfully.')
                
            except Exception as e:
                SystemLog.objects.create(
                    level='ERROR',
                    log_type='SYSTEM',
                    event='Backup Failed',
                    user=request.user,
                    details=str(e)
                )
                messages.error(request, f'Failed to create backup: {str(e)}')
        
        elif action == 'restore_backup':
            backup_id = request.POST.get('backup_id')
            try:
                backup = SystemBackup.objects.get(backup_id=backup_id)
                
                # Read backup file
                with open(backup.file_path, 'r') as f:
                    data = json.load(f)
                
                # Restore data (you might want to add more validation and error handling)
                with transaction.atomic():
                    # Clear existing data
                    Ticket.objects.all().delete()
                    Event.objects.all().delete()
                    Department.objects.all().delete()
                    CustomUser.objects.exclude(id=request.user.id).delete()
                    
                    # Restore data
                    for dept in data['departments']:
                        Department.objects.create(**dept)
                    for user in data['users']:
                        if user['id'] != request.user.id:  # Skip current user
                            CustomUser.objects.create(**user)
                    for event in data['events']:
                        Event.objects.create(**event)
                    for ticket in data['tickets']:
                        Ticket.objects.create(**ticket)
                
                SystemLog.objects.create(
                    level='INFO',
                    log_type='SYSTEM',
                    event='Backup Restored',
                    user=request.user,
                    details=f'Backup restored successfully: {backup_id}'
                )
                
                messages.success(request, 'Backup restored successfully.')
                
            except Exception as e:
                SystemLog.objects.create(
                    level='ERROR',
                    log_type='SYSTEM',
                    event='Restore Failed',
                    user=request.user,
                    details=str(e)
                )
                messages.error(request, f'Failed to restore backup: {str(e)}')
    
    # Get all backups for display
    backups = SystemBackup.objects.all()
    
    # Calculate statistics
    total_backups = backups.count()
    storage_used = sum(backup.file_size for backup in backups)
    last_backup = backups.first()
    
    return render(request, 'dashboard/admin_backup.html', {
        'backups': backups,
        'total_backups': total_backups,
        'storage_used': storage_used,
        'last_backup': last_backup,
    })
from django.contrib import messages
from .forms import EventForm

def create_event(request):
    # Check if user is authenticated and has appropriate permissions
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to create an event.")
        return redirect('login')
    
    if not (request.user.is_event_admin or request.user.is_super_admin):
        messages.error(request, "You don't have permission to create events.")
        return redirect('student_dashboard')
        
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user  # Set the created_by field to the current user
            event.save()
            messages.success(request, "Event created successfully!")
            
            # Redirect based on user role
            if request.user.is_super_admin:
                return redirect('superadmin_dashboard')
            else:
                return redirect('admin_dashboard')
        else:
            # Print form errors for debugging
            print(form.errors)  # Optional: You can remove this after debugging
            messages.error(request, "There was an error in the form. Please check all fields.")
    else:
        form = EventForm()
        
        # Pre-select department if admin belongs to a department
        if request.user.department and hasattr(request.user, 'is_event_admin') and request.user.is_event_admin:
            form.initial['department'] = request.user.department

    # Get all departments for the dropdown
    from .models import Department
    departments = Department.objects.all()
    
    return render(request, 'mainapp/create_event.html', {
        'form': form,
        'departments': departments,
        'categories': Event.CATEGORY_CHOICES
    })

@login_required
def suggest_event(request):
    if request.method == 'POST':
        form = SuggestEventForm(request.POST)
        if form.is_valid():
            suggestion = form.save(commit=False)
            suggestion.created_by = request.user
            # Removed is_active=False as this field doesn't exist
            suggestion.available_tickets = 0  # Will be set by admin when approved
            suggestion.save()
            messages.success(request, "Event suggestion submitted successfully! An admin will review it.")
            return redirect('student_dashboard')
        else:
            messages.error(request, "There was an error in your suggestion. Please check all fields.")
    else:
        form = SuggestEventForm()
        if request.user.department:
            form.initial['department'] = request.user.department

    from .models import Department
    departments = Department.objects.all()
    
    return render(request, 'mainapp/suggest_event.html', {
        'form': form,
        'departments': departments,
        'categories': Event.CATEGORY_CHOICES
    })

def admin_user_details(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'dashboard/admin_user_details.html', {'user': user})
