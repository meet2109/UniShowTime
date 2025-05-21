from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Event

class CustomUserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    profile_image = forms.ImageField(required=False, label='Profile Picture')
    enrollment_no = forms.CharField(required=False)
    department = forms.ModelChoiceField(queryset=None, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'enrollment_no', 'department', 'profile_image', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Department
        self.fields['department'].queryset = Department.objects.all()

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role not in ['student', 'admin']:
            raise forms.ValidationError("Only Students and Event Admins can register directly.")
        return role

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        enrollment_no = cleaned_data.get('enrollment_no')
        department = cleaned_data.get('department')

        if role == 'student' and not enrollment_no:
            self.add_error('enrollment_no', 'Enrollment number is required for students.')
        elif role == 'admin' and not department:
            self.add_error('department', 'Department is required for teachers.')

        return cleaned_data


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email")


class EventForm(forms.ModelForm):
    # Add a time field that doesn't exist in the model
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'location', 'image', 'available_tickets', 'department', 'category']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        
    def clean_date(self):
        date = self.cleaned_data.get('date')
        from django.utils import timezone
        if date and date < timezone.now().date():
            raise forms.ValidationError("Event date cannot be in the past.")
        return date
        
    def clean_available_tickets(self):
        tickets = self.cleaned_data.get('available_tickets')
        if tickets is not None and tickets <= 0:
            raise forms.ValidationError("Number of available tickets must be greater than zero.")
        return tickets
        
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        
        if date and time:
            # Combine date and time into a datetime object
            import datetime
            combined_datetime = datetime.datetime.combine(date, time)
            cleaned_data['date'] = combined_datetime
            
        return cleaned_data


class SuggestEventForm(forms.ModelForm):
    # Add a time field that doesn't exist in the model
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'department', 'date', 'location']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mark the form as a suggestion
        self.is_suggestion = True
        
    def clean_date(self):
        date = self.cleaned_data.get('date')
        from django.utils import timezone
        if date and date < timezone.now().date():
            raise forms.ValidationError("Event date cannot be in the past.")
        return date
        
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        
        if date and time:
            # Combine date and time into a datetime object
            import datetime
            combined_datetime = datetime.datetime.combine(date, time)
            cleaned_data['date'] = combined_datetime
            
        return cleaned_data
