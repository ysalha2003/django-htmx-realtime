from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, UserProfileForm
from .models import UserProfile
import re

def is_htmx_request(request):
    return request.headers.get('HX-Request', False)

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        login(self.request, form.get_user())
        if is_htmx_request(self.request):
            response = HttpResponse()
            response['HX-Redirect'] = self.get_success_url()
            return response
        return super().form_valid(form)

class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        return render(request, 'registration/logout.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account for {username} created successfully. Welcome!')
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if is_htmx_request(request):
                response = HttpResponse()
                response['HX-Redirect'] = reverse_lazy('core:home')
                return response
            return redirect('core:home')
        elif is_htmx_request(request):
            return render(request, 'partials/register_form.html', {'form': form})
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            if is_htmx_request(request):
                return render(request, 'partials/profile_form.html', {'form': form, 'profile': request.user.profile})
            return redirect('accounts:profile')
        elif is_htmx_request(request):
            return render(request, 'partials/profile_form.html', {'form': form, 'profile': request.user.profile})
    else:
        form = UserProfileForm(instance=request.user.profile)
    return render(request, 'accounts/profile.html', {'form': form, 'profile': request.user.profile})

@require_http_methods(["POST"])
def validate_username(request):
    username = request.POST.get('username', '').strip()
    if not username: return HttpResponse('')
    if len(username) < 3:
        return render(request, 'partials/validation_error.html', {'message': 'Username must be at least 3 characters long'})
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        return render(request, 'partials/validation_error.html', {'message': 'Invalid characters in username'})
    if User.objects.filter(username=username).exists():
        return render(request, 'partials/validation_error.html', {'message': 'This username is already taken'})
    return render(request, 'partials/validation_success.html', {'message': 'Username is available!'})

@require_http_methods(["POST"])
def validate_first_name(request):
    first_name = request.POST.get('first_name', '').strip()
    if not first_name: return HttpResponse('')
    if len(first_name) < 2:
        return render(request, 'partials/validation_error.html', {'message': 'First name is too short'})
    if not re.match(r'^[a-zA-Z\s]+$', first_name):
        return render(request, 'partials/validation_error.html', {'message': 'First name can only contain letters'})
    return render(request, 'partials/validation_success.html', {'message': 'Looks good!'})

@require_http_methods(["POST"])
def validate_last_name(request):
    last_name = request.POST.get('last_name', '').strip()
    if not last_name: return HttpResponse('')
    if len(last_name) < 2:
        return render(request, 'partials/validation_error.html', {'message': 'Last name is too short'})
    if not re.match(r'^[a-zA-Z\s]+$', last_name):
        return render(request, 'partials/validation_error.html', {'message': 'Last name can only contain letters'})
    return render(request, 'partials/validation_success.html', {'message': 'Looks good!'})

@require_http_methods(["POST"])
def validate_email_register(request):
    email = request.POST.get('email', '').strip()
    if not email: return HttpResponse('')
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return render(request, 'partials/validation_error.html', {'message': 'Please enter a valid email address'})
    if User.objects.filter(email=email).exists():
        return render(request, 'partials/validation_error.html', {'message': 'An account with this email already exists'})
    return render(request, 'partials/validation_success.html', {'message': 'Email is available!'})

@require_http_methods(["POST"])
def validate_password(request):
    password = request.POST.get('password1', '').strip()
    if not password: return HttpResponse('')
    strength, feedback = 0, []
    if len(password) >= 8: strength += 1
    else: feedback.append('At least 8 characters')
    if re.search(r'[A-Z]', password): strength += 1
    else: feedback.append('One uppercase letter')
    if re.search(r'[a-z]', password): strength += 1
    else: feedback.append('One lowercase letter')
    if re.search(r'\d', password): strength += 1
    else: feedback.append('One number')
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password): strength += 1
    else: feedback.append('One special character')
    return render(request, 'partials/password_strength.html', {'strength': strength, 'feedback': feedback, 'password_length': len(password)})

@require_http_methods(["POST"])
def validate_password2(request):
    password, password2 = request.POST.get('password1', ''), request.POST.get('password2', '')
    if not password2: return HttpResponse('')
    if password != password2:
        return render(request, 'partials/validation_error.html', {'message': 'Passwords do not match'})
    return render(request, 'partials/validation_success.html', {'message': 'Passwords match!'})
