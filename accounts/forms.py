from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import UserProfile
import re

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input', 'placeholder': 'user@example.com',
            'hx-post': '/accounts/validate/email/', 'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#email-validation', 'hx-swap': 'innerHTML'
        })
    )
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': 'Enter first name',
            'hx-post': '/accounts/validate/first-name/', 'hx-trigger': 'keyup changed delay:300ms',
            'hx-target': '#first-name-validation', 'hx-swap': 'innerHTML'
        })
    )
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': 'Enter last name',
            'hx-post': '/accounts/validate/last-name/', 'hx-trigger': 'keyup changed delay:300ms',
            'hx-target': '#last-name-validation', 'hx-swap': 'innerHTML'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-input', 'placeholder': 'Enter a unique username',
            'hx-post': '/accounts/validate/username/', 'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#username-validation', 'hx-swap': 'innerHTML'
        })
        self.fields['password2'].label = "Confirm password"
        for field in ['password1', 'password2']:
            self.fields[field].widget.attrs.update({
                'class': 'form-input', 'placeholder': 'Enter a secure password'
            })

        self.fields['password1'].widget.attrs.update({
            'hx-post': '/accounts/validate/password/', 'hx-trigger': 'keyup changed delay:300ms',
            'hx-target': '#password-validation', 'hx-swap': 'innerHTML'
        })
        self.fields['password2'].widget.attrs.update({
            'hx-post': '/accounts/validate/password2/', 'hx-trigger': 'keyup changed delay:300ms',
            'hx-target': '#password2-validation', 'hx-swap': 'innerHTML'
        })

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'birth_date', 'phone_number', 'website', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Enter a brief bio...'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+1 (555) 123-4567'}),
            'website': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://your-website.com'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City, Country'})
        }
