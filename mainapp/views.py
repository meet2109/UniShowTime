from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import CustomUserRegisterForm, CustomLoginForm
from .models import CustomUser

def register_view(request):
    if request.method == 'POST':
        form = CustomUserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('dashboard')
    else:
        form = CustomUserRegisterForm()
    return render(request, 'auth/register.html', {'form': form})

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
        return render(request, 'dashboard/student_dashboard.html')
    elif user.role == 'admin':
        return render(request, 'dashboard/admin_dashboard.html')
    elif user.role == 'superadmin':
        return render(request, 'dashboard/superadmin_dashboard.html')

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
# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import EventForm

def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Event created successfully!")
            return redirect('admin_dashboard')  # Redirect after successful event creation
        else:
            # Print form errors for debugging
            print(form.errors)  # Optional: You can remove this after debugging
            messages.error(request, "There was an error in the form.")
    else:
        form = EventForm()

    return render(request, 'mainapp/create_event.html', {'form': form})

def admin_user_details(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'dashboard/admin_user_details.html', {'user': user})
