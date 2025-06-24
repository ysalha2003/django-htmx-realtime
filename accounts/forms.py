from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input', 
            'placeholder': 'your.email@example.com',
            'hx-post': '/accounts/validate/email/', 
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#email-validation', 
            'hx-swap': 'innerHTML'
        })
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'form-input', 
            'placeholder': 'Enter your first name',
            'hx-post': '/accounts/validate/first-name/', 
            'hx-trigger': 'keyup changed delay:300ms',
            'hx-target': '#first-name-validation', 
            'hx-swap': 'innerHTML'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'form-input', 
            'placeholder': 'Enter your last name',
            'hx-post': '/accounts/validate/last-name/', 
            'hx-trigger': 'keyup changed delay:300ms',
            'hx-target': '#last-name-validation', 
            'hx-swap': 'innerHTML'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Update username field
        self.fields['username'].widget.attrs.update({
            'class': 'form-input', 
            'placeholder': 'Choose a unique username',
            'hx-post': '/accounts/validate/username/', 
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#username-validation', 
            'hx-swap': 'innerHTML'
        })
        
        # Update password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input', 
            'placeholder': 'Create a strong password',
            'hx-post': '/accounts/validate/password/', 
            'hx-trigger': 'keyup changed delay:300ms',
            'hx-target': '#password-validation', 
            'hx-swap': 'innerHTML'
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input', 
            'placeholder': 'Confirm your password',
            'hx-post': '/accounts/validate/password2/', 
            'hx-trigger': 'keyup changed delay:300ms',
            'hx-target': '#password2-validation', 
            'hx-swap': 'innerHTML'
        })
        
        # Update field labels and help text
        self.fields['password2'].label = "Confirm Password"
        self.fields['password1'].help_text = None
        self.fields['username'].help_text = None
        
        # Add autocomplete attributes
        self.fields['username'].widget.attrs['autocomplete'] = 'username'
        self.fields['email'].widget.attrs['autocomplete'] = 'email'
        self.fields['first_name'].widget.attrs['autocomplete'] = 'given-name'
        self.fields['last_name'].widget.attrs['autocomplete'] = 'family-name'
        self.fields['password1'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['password2'].widget.attrs['autocomplete'] = 'new-password'

    def clean_email(self):
        """Enhanced email validation"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            if User.objects.filter(email=email).exists():
                raise ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        """Enhanced username validation"""
        username = self.cleaned_data.get('username')
        if username:
            username = username.strip()
            
            # Check for reserved usernames
            reserved_usernames = ['admin', 'root', 'user', 'test', 'guest', 'administrator', 'api', 'www']
            if username.lower() in reserved_usernames:
                raise ValidationError("This username is reserved. Please choose another one.")
                
            # Check for profanity or inappropriate content (basic check)
            inappropriate_words = ['spam', 'fake', 'scam', 'phishing']
            if any(word in username.lower() for word in inappropriate_words):
                raise ValidationError("Please choose a more appropriate username.")
                
        return username

    def clean(self):
        """Additional form-level validation"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        username = cleaned_data.get('username')
        
        # Check if password contains username
        if password1 and username and username.lower() in password1.lower():
            raise ValidationError("Password cannot contain your username.")
            
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'birth_date', 'phone_number', 'website', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-input resize-y min-h-[100px]', 
                'rows': 4, 
                'placeholder': 'Tell us about yourself... (optional, max 500 characters)',
                'maxlength': 500
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-input', 
                'accept': 'image/*'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-input', 
                'type': 'date',
                'max': '2010-01-01'  # Reasonable max date
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': '+1 (555) 123-4567',
                'hx-post': '/validate/phone-number/',
                'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#phone-validation',
                'hx-swap': 'innerHTML'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-input', 
                'placeholder': 'https://your-website.com',
                'hx-post': '/validate/website/',
                'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#website-validation',
                'hx-swap': 'innerHTML'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'City, Country',
                'hx-post': '/validate/location/',
                'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#location-validation',
                'hx-swap': 'innerHTML'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add autocomplete attributes
        self.fields['phone_number'].widget.attrs['autocomplete'] = 'tel'
        self.fields['website'].widget.attrs['autocomplete'] = 'url'
        self.fields['location'].widget.attrs['autocomplete'] = 'address-level2'
        
        # Add helpful labels
        self.fields['bio'].label = 'Bio'
        self.fields['profile_picture'].label = 'Profile Picture'
        self.fields['birth_date'].label = 'Birth Date'
        self.fields['phone_number'].label = 'Phone Number'
        self.fields['website'].label = 'Website'
        self.fields['location'].label = 'Location'

    def clean_bio(self):
        """Enhanced bio validation"""
        bio = self.cleaned_data.get('bio')
        if bio:
            bio = bio.strip()
            
            # Check for minimum meaningful content
            if len(bio) < 10 and len(bio) > 0:
                raise ValidationError("Bio should be at least 10 characters if provided.")
                
            # Check for excessive special characters
            special_char_count = sum(1 for char in bio if not char.isalnum() and not char.isspace())
            if special_char_count > len(bio) * 0.3:  # More than 30% special characters
                raise ValidationError("Bio contains too many special characters.")
                
        return bio

    def clean_phone_number(self):
        """Enhanced phone number validation"""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            phone = phone.strip()
            
            # Remove all non-digit characters for validation
            digits_only = ''.join(filter(str.isdigit, phone))
            
            if len(digits_only) < 10:
                raise ValidationError("Phone number must contain at least 10 digits.")
            if len(digits_only) > 15:
                raise ValidationError("Phone number is too long.")
                
            # Check for obviously fake numbers
            if digits_only in ['0000000000', '1111111111', '1234567890', '9999999999']:
                raise ValidationError("Please enter a valid phone number.")
                
        return phone

    def clean_website(self):
        """Enhanced website validation"""
        website = self.cleaned_data.get('website')
        if website:
            website = website.strip()
            
            # Add protocol if missing
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website
                
            # Additional validation for suspicious patterns
            suspicious_patterns = ['bit.ly', 'tinyurl', 'localhost', '127.0.0.1', 'example.com']
            if any(pattern in website.lower() for pattern in suspicious_patterns):
                if 'example.com' in website.lower():
                    raise ValidationError("Please enter your actual website URL.")
                    
        return website

    def clean_location(self):
        """Enhanced location validation"""
        location = self.cleaned_data.get('location')
        if location:
            location = location.strip()
            
            # Check for minimum meaningful content
            if len(location) < 2:
                raise ValidationError("Location must be at least 2 characters.")
                
            # Check for valid characters (letters, spaces, commas, hyphens, apostrophes)
            import re
            if not re.match(r'^[a-zA-Z\s,\-\'\.]+$', location):
                raise ValidationError("Location can only contain letters, spaces, commas, hyphens, apostrophes, and periods.")
                
            # Check for obvious test data
            test_locations = ['test', 'testing', 'xyz', 'abc', 'none', 'n/a']
            if location.lower() in test_locations:
                raise ValidationError("Please enter a valid location.")
                
        return location

    def clean_birth_date(self):
        """Enhanced birth date validation"""
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            from datetime import date
            today = date.today()
            
            # Check if date is in the future
            if birth_date > today:
                raise ValidationError("Birth date cannot be in the future.")
                
            # Check for reasonable age limits
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age > 120:
                raise ValidationError("Please verify your birth date.")
            if age < 13:
                raise ValidationError("You must be at least 13 years old to use this service.")
                
        return birth_date

class CustomLoginForm(AuthenticationForm):
    """Enhanced login form with better styling and validation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Update username field
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Enter your username',
            'autocomplete': 'username',
            'hx-post': '/accounts/validate/login-username/',
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#username-validation',
            'hx-swap': 'innerHTML'
        })
        
        # Update password field
        self.fields['password'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
        
    def clean_username(self):
        """Enhanced username validation for login"""
        username = self.cleaned_data.get('username')
        if username:
            username = username.strip()
        return username
