from django.utils import timezone
from mainapp.models import SystemBackup, SystemLog, CustomUser, Event, Department, Ticket
from django.conf import settings
import os
import json

def run():
    # Get a superadmin user
    try:
        admin_user = CustomUser.objects.filter(role='superadmin').first()
        if not admin_user:
            print("No superadmin user found. Please create one first.")
            return
    except CustomUser.DoesNotExist:
        print("No superadmin user found. Please create one first.")
        return

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
            created_by=admin_user
        )
        
        # Log backup creation
        SystemLog.objects.create(
            level='INFO',
            log_type='SYSTEM',
            event='Backup Created',
            user=admin_user,
            details=f'Backup created successfully: {backup.backup_id}'
        )
        
        print(f'Backup created successfully: {backup_filename}')
        print(f'Backup size: {backup.file_size} bytes')
        
    except Exception as e:
        print(f'Error creating backup: {str(e)}')
        SystemLog.objects.create(
            level='ERROR',
            log_type='SYSTEM',
            event='Backup Creation Failed',
            user=admin_user,
            details=f'Failed to create backup: {str(e)}'
        )

if __name__ == '__main__':
    run()