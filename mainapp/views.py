from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone

from .forms import CustomUserRegisterForm, CustomLoginForm
from .models import CustomUser, Event, Ticket, Department

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
        return render(request, 'dashboard/superadmin_dashboard.html')

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

def admin_dashboard(request):
    if request.user.role not in ['admin', 'superadmin']:
        return redirect('dashboard')
        
    total_events = Event.objects.count()
    total_bookings = sum(event.ticket_set.count() for event in Event.objects.all())
    upcoming_events = Event.objects.filter(date__gte=timezone.now()).count()
    events = Event.objects.all()
    users = CustomUser.objects.all()

    return render(request, 'dashboard/admin_dashboard.html', {
        'total_events': total_events,
        'total_bookings': total_bookings,
        'upcoming_events': upcoming_events,
        'events': events,
        'users': users,
    })

@login_required
def event_details(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    tickets_available = event.tickets_left()
    user_has_ticket = Ticket.objects.filter(event=event, user=request.user).exists()
    
    return render(request, 'mainapp/event_details.html', {
        'event': event,
        'tickets_available': tickets_available,
        'user_has_ticket': user_has_ticket
    })

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
def system_settings(request):
    if request.user.role != 'superadmin':
        return HttpResponseForbidden("You don't have permission to view this page.")
    return render(request, 'mainapp/system_settings.html')

@login_required
def system_logs(request):
    if request.user.role != 'superadmin':
        return HttpResponseForbidden("You don't have permission to view this page.")
    return render(request, 'mainapp/system_logs.html')

@login_required
def system_backup(request):
    if request.user.role != 'superadmin':
        return HttpResponseForbidden("You don't have permission to view this page.")
    return render(request, 'mainapp/system_backup.html')
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
    from .models import Department, EVENT_CATEGORIES
    departments = Department.objects.all()
    
    return render(request, 'mainapp/create_event.html', {
        'form': form,
        'departments': departments,
        'categories': EVENT_CATEGORIES
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

    from .models import Department, EVENT_CATEGORIES
    departments = Department.objects.all()
    
    return render(request, 'mainapp/suggest_event.html', {
        'form': form,
        'departments': departments,
        'categories': EVENT_CATEGORIES
    })

def admin_user_details(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'dashboard/admin_user_details.html', {'user': user})
