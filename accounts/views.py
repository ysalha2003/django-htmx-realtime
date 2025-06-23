import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError

from .forms import CustomUserCreationForm, UserProfileForm
from .models import UserProfile
from core.utils import (
    is_htmx_request, validate_name, validate_username, 
    validate_email_availability, validate_password_strength,
    render_validation_response, log_validation_attempt
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
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error during login: {e}")
            messages.error(self.request, 'An error occurred during login. Please try again.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle failed login"""
        logger.warning(f"Failed login attempt for user: {form.data.get('username', 'unknown')}")
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
                messages.success(request, f'Account for {username} created successfully. Welcome!')
                
                # Log the user in
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                if is_htmx_request(request):
                    response = HttpResponse()
                    response['HX-Redirect'] = reverse_lazy('core:home')
                    return response
                return redirect('core:home')
            else:
                logger.warning(f"Invalid registration form: {form.errors}")
                if is_htmx_request(request):
                    return render(request, 'partials/register_form.html', {'form': form})
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            messages.error(request, 'An error occurred during registration. Please try again.')
            if is_htmx_request(request):
                return render(request, 'partials/register_form.html', {'form': form})
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
                    messages.success(request, 'Profile updated successfully.')
                    
                    if is_htmx_request(request):
                        return render(request, 'partials/profile_form.html', {
                            'form': form, 
                            'profile': profile
                        })
                    return redirect('accounts:profile')
                else:
                    logger.warning(f"Invalid profile form for user {request.user.username}: {form.errors}")
                    if is_htmx_request(request):
                        return render(request, 'partials/profile_form.html', {
                            'form': form, 
                            'profile': profile
                        })
            except ValidationError as e:
                logger.warning(f"Profile validation error for user {request.user.username}: {e}")
                messages.error(request, 'Please correct the errors below.')
                if is_htmx_request(request):
                    return render(request, 'partials/profile_form.html', {
                        'form': form, 
                        'profile': profile
                    })
            except Exception as e:
                logger.error(f"Error updating profile for user {request.user.username}: {e}")
                messages.error(request, 'An error occurred while updating your profile.')
                if is_htmx_request(request):
                    return render(request, 'partials/profile_form.html', {
                        'form': form, 
                        'profile': profile
                    })
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

# Validation endpoints with improved error handling
@require_http_methods(["POST"])
def validate_username(request):
    """Validate username availability and format"""
    username = request.POST.get('username', '').strip()
    if not username:
        return HttpResponse('')
    
    try:
        is_valid, message = validate_username(username)
        log_validation_attempt('username', username, is_valid, request)
        
        template_type = 'success' if is_valid else 'error'
        return render(request, *render_validation_response(template_type, message))
    except Exception as e:
        logger.error(f"Error validating username: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Validation error'})

@require_http_methods(["POST"])
def validate_first_name(request):
    """Validate first name"""
    first_name = request.POST.get('first_name', '').strip()
    if not first_name:
        return HttpResponse('')
    
    try:
        is_valid, message = validate_name(first_name, field_name="First name")
        log_validation_attempt('first_name', first_name, is_valid, request)
        
        template_type = 'success' if is_valid else 'error'
        return render(request, *render_validation_response(template_type, message))
    except Exception as e:
        logger.error(f"Error validating first name: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Validation error'})

@require_http_methods(["POST"])
def validate_last_name(request):
    """Validate last name"""
    last_name = request.POST.get('last_name', '').strip()
    if not last_name:
        return HttpResponse('')
    
    try:
        is_valid, message = validate_name(last_name, field_name="Last name")
        log_validation_attempt('last_name', last_name, is_valid, request)
        
        template_type = 'success' if is_valid else 'error'
        return render(request, *render_validation_response(template_type, message))
    except Exception as e:
        logger.error(f"Error validating last name: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Validation error'})

@require_http_methods(["POST"])
def validate_email_register(request):
    """Validate email for registration"""
    email = request.POST.get('email', '').strip()
    if not email:
        return HttpResponse('')
    
    try:
        is_valid, message = validate_email_availability(email)
        log_validation_attempt('registration_email', email, is_valid, request)
        
        template_type = 'success' if is_valid else 'error'
        return render(request, *render_validation_response(template_type, message))
    except Exception as e:
        logger.error(f"Error validating registration email: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Validation error'})

@require_http_methods(["POST"])
def validate_password(request):
    """Validate password strength"""
    password = request.POST.get('password1', '').strip()
    if not password:
        return HttpResponse('')
    
    try:
        strength, feedback = validate_password_strength(password)
        log_validation_attempt('password', '***', strength >= 3, request)
        
        context = {
            'strength': strength,
            'feedback': feedback,
            'password_length': len(password)
        }
        return render(request, 'partials/password_strength.html', context)
    except Exception as e:
        logger.error(f"Error validating password: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Validation error'})

@require_http_methods(["POST"])
def validate_password2(request):
    """Validate password confirmation"""
    password1 = request.POST.get('password1', '')
    password2 = request.POST.get('password2', '')
    
    if not password2:
        return HttpResponse('')
    
    try:
        if password1 != password2:
            template_type = 'error'
            message = 'Passwords do not match'
        else:
            template_type = 'success'
            message = 'Passwords match!'
        
        log_validation_attempt('password_confirmation', '***', password1 == password2, request)
        return render(request, *render_validation_response(template_type, message))
    except Exception as e:
        logger.error(f"Error validating password confirmation: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Validation error'})
