from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from django.forms import ClearableFileInput
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import GENDER_CHOICES


class ChangePasswordForm(PasswordChangeForm):
    error_messages = {
        'password_mismatch': 'The two password fields do not match.',
        'password_incorrect': 'Your old password was entered incorrectly.',
    }


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    address = forms.CharField(max_length=100, required=False)
    staff_status = forms.BooleanField(required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    job_title = forms.CharField(max_length=50, required=False)
    birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    avatar = forms.ImageField(required=False, widget=ClearableFileInput(attrs={'multiple': False}))

    class Meta:
        model = get_user_model()
        fields = ['email', 'password1', 'password2', 'first_name', 'last_name',
                  'address', 'staff_status', 'phone_number', 'job_title', 'birth', 'gender', 'avatar']


class InfoEdit(forms.Form):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    address = forms.CharField(max_length=100, required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    job_title = forms.CharField(max_length=50, required=False)
    birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    avatar = forms.ImageField(required=False, widget=ClearableFileInput(attrs={'multiple': False}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(InfoEdit, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        # Perform any additional form-level validation here
        return cleaned_data

    def save(self):
        # Update the user object with the form data
        self.user.first_name = self.cleaned_data.get('first_name')
        self.user.last_name = self.cleaned_data.get('last_name')
        self.user.address = self.cleaned_data.get('address')
        self.user.phone_number = self.cleaned_data.get('phone_number')
        self.user.job_title = self.cleaned_data.get('job_title')
        self.user.birth = self.cleaned_data.get('birth')
        self.user.gender = self.cleaned_data.get('gender')
        self.user.avatar = self.cleaned_data.get('avatar')
        self.user.save()


