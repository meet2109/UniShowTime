from django.utils import timezone
from mainapp.models import SystemLog, CustomUser
from datetime import datetime, timedelta
import random

def run():
    # Get a superadmin user
    try:
        admin_user = CustomUser.objects.filter(role='superadmin').first()
    except CustomUser.DoesNotExist:
        print("No superadmin user found. Please create one first.")
        return

    # Sample log data
    log_data = [
        {
            'level': 'INFO',
            'log_type': 'ADMIN',
            'event': 'User Login',
            'details': 'Successful login from admin panel'
        },
        {
            'level': 'WARNING',
            'log_type': 'SYSTEM',
            'event': 'High CPU Usage',
            'details': 'Server CPU usage exceeded 80%'
        },
        {
            'level': 'ERROR',
            'log_type': 'EVENT',
            'event': 'Event Creation Failed',
            'details': 'Failed to create event due to invalid data'
        },
        {
            'level': 'INFO',
            'log_type': 'USER',
            'event': 'Password Changed',
            'details': 'User successfully updated their password'
        },
        {
            'level': 'CRITICAL',
            'log_type': 'SYSTEM',
            'event': 'Database Connection Error',
            'details': 'Lost connection to database server'
        }
    ]

    # Create logs with different timestamps
    for i, log in enumerate(log_data):
        # Create logs over the past week
        timestamp = timezone.now() - timedelta(days=random.randint(0, 7),
                                             hours=random.randint(0, 23),
                                             minutes=random.randint(0, 59))
        
        SystemLog.objects.create(
            timestamp=timestamp,
            level=log['level'],
            log_type=log['log_type'],
            event=log['event'],
            user=admin_user,
            details=log['details']
        )
        print(f"Created log: {log['event']}")

if __name__ == '__main__':
    run()