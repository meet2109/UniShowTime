from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.utils import timezone
from django.core.files import File
from io import BytesIO
import qrcode
import json

ROLE_CHOICES = (
    ('student', 'Student'),
    ('admin', 'Event Admin'),
    ('superadmin', 'Super Admin'),
)

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        verbose_name_plural = "Departments"

    def __str__(self):
        return f"{self.name} ({self.code})"

class CustomUser(AbstractUser, PermissionsMixin):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    enrollment_no = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_event_admin(self):
        return self.role == 'admin'

    @property
    def is_super_admin(self):
        return self.role == 'superadmin'

class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="events_created")
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    available_tickets = models.PositiveIntegerField(default=100)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'time']

    def __str__(self):
        return f"{self.title} - {self.department.code}"

    def tickets_left(self):
        return self.available_tickets - self.ticket_set.count()

class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.user.enrollment_no} | {self.event.title}"

    def save(self, *args, **kwargs):
        if not self.qr_code:
            data = {
                "username": self.user.username,
                "enrollment_no": self.user.enrollment_no,
                "event": self.event.title,
                "date": str(self.event.date),
                "booked_at": self.booked_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            qr_img = qrcode.make(json.dumps(data))
            canvas = BytesIO()
            qr_img.save(canvas, format='PNG')
            self.qr_code.save(f"qr_{self.user.username}_{self.event.id}.png", File(canvas), save=False)
        super().save(*args, **kwargs)
