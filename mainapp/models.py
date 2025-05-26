from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.utils import timezone
from django.core.files import File
from io import BytesIO
import qrcode
import json
import os
import datetime

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

    @property
    def has_active_events(self):
        return self.events.filter(date__gte=timezone.now()).exists()

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
    CATEGORY_CHOICES = (
        ('seminar', 'Seminar'),
        ('concert', 'Concert'),
        ('stage_event', 'Stage Event'),
        ('educational', 'Educational'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='event_images/', null=True, blank=True)
    available_tickets = models.IntegerField(default=0)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='events')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_events')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    
    def __str__(self):
        return self.title

    def tickets_left(self):
        return self.available_tickets - self.ticket_set.count()

    @property
    def is_free(self):
        return self.ticket_price == 0

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
        if not self.booked_at:
            self.booked_at = timezone.now()
        if not self.qr_code:
            data = {
                "username": self.user.username,
                "enrollment_no": self.user.enrollment_no,
                "event": self.event.title,
                "date": str(self.event.date) if self.event.date else "Not scheduled",
                "booked_at": self.booked_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            qr_img = qrcode.make(json.dumps(data))
            canvas = BytesIO()
            qr_img.save(canvas, format='PNG')
            self.qr_code.save(f"qr_{self.user.username}_{self.event.id}.png", File(canvas), save=False)
            super().save(*args, **kwargs)

class SystemLog(models.Model):
    LOG_LEVELS = (
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    )

    LOG_TYPES = (
        ('ADMIN', 'Admin Action'),
        ('EVENT', 'Event Log'),
        ('USER', 'User Action'),
        ('SYSTEM', 'System Log'),
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    log_type = models.CharField(max_length=10, choices=LOG_TYPES)
    event = models.CharField(max_length=255)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField()

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp} - {self.level} - {self.event}"

class SystemBackup(models.Model):
    BACKUP_TYPES = (
        ('FULL', 'Full Backup'),
        ('PARTIAL', 'Partial Backup'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )

    backup_id = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    backup_type = models.CharField(max_length=10, choices=BACKUP_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    file_path = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)  # Size in bytes
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.backup_id} - {self.created_at}"

    def save(self, *args, **kwargs):
        if not self.backup_id:
            # Generate a unique backup ID (e.g., BK2401201)
            date_str = self.created_at.strftime("%y%m%d")
            count = SystemBackup.objects.filter(backup_id__startswith=f"BK{date_str}").count() + 1
            self.backup_id = f"BK{date_str}{count}"
        super().save(*args, **kwargs)
