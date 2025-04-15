from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Event

class CustomUserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    profile_image = forms.ImageField(required=False, label='Profile Picture')

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'enrollment_no', 'department', 'role', 'profile_image', 'password1', 'password2']

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role not in ['student', 'admin']:
            raise forms.ValidationError("Only Students and Event Admins can register directly.")
        return role


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email")


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'department', 'date', 'time', 'location', 'image', 'available_tickets']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
