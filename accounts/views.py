# accounts/views.py
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.views.decorators.csrf import csrf_exempt

from .forms import CustomUserCreationForm, UserProfileForm
from .models import UserProfile
from core.utils import (
    is_htmx_request, validate_name, validate_username, 
    validate_email_availability, validate_password_strength,
    log_validation_attempt
)

logger = logging.getLogger(__name__)

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        """Handle successful login"""
        try:
            login(self.request, form.get_user())
            logger.info(f"User {form.get_user().username} logged in successfully")
            
            if is_htmx_request(self.request):
                response = HttpResponse()
                response['HX-Redirect'] = self.get_success_url()
                return response
            
            messages.success(
                self.request, 
                f'Welcome back, {form.get_user().get_full_name() or form.get_user().username}!',
                extra_tags='success-notification'
            )
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error during login: {e}")
            messages.error(self.request, 'An error occurred during login. Please try again.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle failed login"""
        username = form.data.get('username', 'unknown')
        logger.warning(f"Failed login attempt for user: {username}")
        
        if is_htmx_request(self.request):
            return render(self.request, 'registration/login.html', {'form': form})
        
        messages.error(
            self.request, 
            'Invalid username or password. Please check your credentials and try again.',
            extra_tags='error-notification'
        )
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        return render(request, 'registration/logout.html')

def register_view(request):
    """Handle user registration with improved error handling"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        try:
            if form.is_valid():
                user = form.save()
                username = form.cleaned_data.get('username')
                logger.info(f"New user registered: {username}")
                
                # Log the user in
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                if is_htmx_request(request):
                    response = HttpResponse()
                    response['HX-Redirect'] = reverse_lazy('core:home')
                    return response
                
                messages.success(
                    request, 
                    f'Welcome to our platform, {user.get_full_name() or username}! Your account has been created successfully.',
                    extra_tags='success-notification'
                )
                return redirect('core:home')
            else:
                logger.warning(f"Invalid registration form: {form.errors}")
                if is_htmx_request(request):
                    return render(request, 'partials/register_form.html', {'form': form})
                # For regular requests, show form with errors
                messages.error(request, 'Please correct the errors below.')
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            if is_htmx_request(request):
                return render(request, 'partials/register_form.html', {'form': form})
            messages.error(request, 'An error occurred during registration. Please try again.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile_view(request):
    """Handle user profile updates with improved error handling"""
    try:
        # Ensure user has a profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if request.method == 'POST':
            form = UserProfileForm(request.POST, request.FILES, instance=profile)
            try:
                if form.is_valid():
                    form.save()
                    logger.info(f"Profile updated for user: {request.user.username}")
                    
                    # For AJAX/HTMX requests, return JSON response
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or is_htmx_request(request):
                        messages.success(request, 'Profile updated successfully!')
                        return render(request, 'partials/profile_form.html', {
                            'form': UserProfileForm(instance=profile), 
                            'profile': profile
                        })
                    
                    messages.success(
                        request, 
                        'Your profile has been updated successfully!',
                        extra_tags='success-notification'
                    )
                    return redirect('accounts:profile')
                else:
                    logger.warning(f"Invalid profile form for user {request.user.username}: {form.errors}")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or is_htmx_request(request):
                        return render(request, 'partials/profile_form.html', {
                            'form': form, 
                            'profile': profile
                        })
                    messages.error(request, 'Please correct the errors below.')
            except ValidationError as e:
                logger.warning(f"Profile validation error for user {request.user.username}: {e}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or is_htmx_request(request):
                    return render(request, 'partials/profile_form.html', {
                        'form': form, 
                        'profile': profile
                    })
                messages.error(request, 'Please correct the errors in your profile.')
            except Exception as e:
                logger.error(f"Error updating profile for user {request.user.username}: {e}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or is_htmx_request(request):
                    return render(request, 'partials/profile_form.html', {
                        'form': form, 
                        'profile': profile
                    })
                messages.error(request, 'An error occurred while updating your profile.')
        else:
            form = UserProfileForm(instance=profile)
        
        return render(request, 'accounts/profile.html', {
            'form': form, 
            'profile': profile
        })
        
    except Exception as e:
        logger.error(f"Error loading profile for user {request.user.username}: {e}")
        messages.error(request, 'Error loading profile. Please try again.')
        return redirect('core:home')

# Enhanced validation endpoints with comprehensive field support
@require_http_methods(["POST"])
def validate_username(request):
    """Validate username availability and format"""
    username = request.POST.get('username', '').strip()
    if not username:
        return HttpResponse('')
    
    try:
        is_valid, message = validate_username(username)
        log_validation_attempt('username', username, is_valid, request)
        
        if is_valid:
            return render(request, 'partials/validation_success.html', {'message': message})
        else:
            return render(request, 'partials/validation_error.html', {'message': message})
    except Exception as e:
        logger.error(f"Error validating username: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Username validation failed'})

@require_http_methods(["POST"])
def validate_login_username(request):
    """Validate username for login form - Fixed to handle length properly"""
    username = request.POST.get('username', '').strip()
    if not username:
        return HttpResponse('')
    
    try:
        # First check basic format requirements
        if len(username) < 3:
            return render(request, 'partials/validation_warning.html', {
                'message': f'Username too short ({len(username)}/3 characters minimum)'
            })
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            return render(request, 'partials/validation_success.html', {
                'message': '✓ Username found'
            })
        else:
            return render(request, 'partials/validation_warning.html', {
                'message': 'Username not found in our system'
            })
    except Exception as e:
        logger.error(f"Error validating login username: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Validation error occurred'})

@require_http_methods(["POST"])
def validate_first_name(request):
    """Validate first name"""
    first_name = request.POST.get('first_name', '').strip()
    if not first_name:
        return HttpResponse('')
    
    try:
        is_valid, message = validate_name(first_name, field_name="First name")
        log_validation_attempt('first_name', first_name, is_valid, request)
        
        if is_valid:
            return render(request, 'partials/validation_success.html', {'message': message})
        else:
            return render(request, 'partials/validation_error.html', {'message': message})
    except Exception as e:
        logger.error(f"Error validating first name: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'First name validation failed'})

@require_http_methods(["POST"])
def validate_last_name(request):
    """Validate last name"""
    last_name = request.POST.get('last_name', '').strip()
    if not last_name:
        return HttpResponse('')
    
    try:
        is_valid, message = validate_name(last_name, field_name="Last name")
        log_validation_attempt('last_name', last_name, is_valid, request)
        
        if is_valid:
            return render(request, 'partials/validation_success.html', {'message': message})
        else:
            return render(request, 'partials/validation_error.html', {'message': message})
    except Exception as e:
        logger.error(f"Error validating last name: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Last name validation failed'})

@require_http_methods(["POST"])
def validate_email_register(request):
    """Validate email for registration"""
    email = request.POST.get('email', '').strip()
    if not email:
        return HttpResponse('')
    
    try:
        is_valid, message = validate_email_availability(email)
        log_validation_attempt('registration_email', email, is_valid, request)
        
        if is_valid:
            return render(request, 'partials/validation_success.html', {'message': message})
        else:
            return render(request, 'partials/validation_error.html', {'message': message})
    except Exception as e:
        logger.error(f"Error validating registration email: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Email validation failed'})

@require_http_methods(["POST"])
def validate_password_reset_email(request):
    """Validate email for password reset"""
    email = request.POST.get('email', '').strip()
    if not email:
        return HttpResponse('')
    
    try:
        # Check if user exists with this email
        if User.objects.filter(email=email).exists():
            return render(request, 'partials/validation_success.html', {'message': 'Email found in our system'})
        else:
            return render(request, 'partials/validation_warning.html', {'message': 'No account found with this email'})
    except Exception as e:
        logger.error(f"Error validating password reset email: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Email validation failed'})

@require_http_methods(["POST"])
def validate_password(request):
    """Enhanced password strength validation"""
    password = request.POST.get('password1', '').strip()
    if not password:
        return HttpResponse('')
    
    try:
        # Get Django's built-in password validation
        django_errors = []
        try:
            validate_password(password)
        except ValidationError as e:
            django_errors = e.messages
        
        # Get custom strength validation
        strength, feedback = validate_password_strength(password)
        
        # Combine validation results
        if django_errors:
            return render(request, 'partials/validation_error.html', {
                'message': django_errors[0]  # Show first Django validation error
            })
        elif strength < 3:
            return render(request, 'partials/validation_warning.html', {
                'message': f'Password strength: {"Weak" if strength <= 1 else "Fair"}. Missing: {", ".join(feedback)}'
            })
        else:
            strength_label = "Strong" if strength >= 4 else "Good"
            return render(request, 'partials/validation_success.html', {
                'message': f'✓ {strength_label} password!'
            })
            
    except Exception as e:
        logger.error(f"Error validating password: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Password validation failed'})

@require_http_methods(["POST"])
def validate_password2(request):
    """Enhanced password confirmation validation"""
    password1 = request.POST.get('password1', '')
    password2 = request.POST.get('password2', '')
    
    if not password2:
        return HttpResponse('')
    
    try:
        if not password1:
            return render(request, 'partials/validation_warning.html', {
                'message': 'Enter password first'
            })
        elif password1 != password2:
            return render(request, 'partials/validation_error.html', {
                'message': 'Passwords do not match'
            })
        else:
            return render(request, 'partials/validation_success.html', {
                'message': '✓ Passwords match!'
            })
        
    except Exception as e:
        logger.error(f"Error validating password confirmation: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Password confirmation failed'})
