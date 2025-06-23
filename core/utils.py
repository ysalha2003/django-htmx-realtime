"""
Utility functions for the core app
"""
import re
import logging
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.models import User
from .models import Contact, NewsletterSubscription

logger = logging.getLogger(__name__)

# Validation Constants
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
NAME_REGEX = r'^[a-zA-Z\s\-\'\.]+$'
USERNAME_REGEX = r'^[a-zA-Z0-9_.-]+$'

# Response Templates
VALIDATION_TEMPLATES = {
    'success': 'partials/validation_success.html',
    'error': 'partials/validation_error.html',
    'warning': 'partials/validation_warning.html',
}

def is_htmx_request(request):
    """Check if request is from HTMX"""
    return request.headers.get('HX-Request', False)

def render_validation_response(template_type, message, request=None):
    """Render validation response with proper template"""
    if template_type not in VALIDATION_TEMPLATES:
        template_type = 'error'
    
    template = VALIDATION_TEMPLATES[template_type]
    context = {'message': message}
    
    if request:
        return render(request, template, context)
    return template, context

def validate_email_format(email):
    """Validate email format"""
    if not email:
        return False, "Email is required"
    
    if not re.match(EMAIL_REGEX, email):
        return False, "Please enter a valid email address"
    
    return True, "Email format is valid"

def validate_name(name, min_length=2, field_name="Name"):
    """Validate name fields"""
    if not name:
        return False, f"{field_name} is required"
    
    if len(name.strip()) < min_length:
        return False, f"{field_name} must be at least {min_length} characters long"
    
    if not re.match(NAME_REGEX, name.strip()):
        return False, f"{field_name} can only contain letters, spaces, hyphens, apostrophes, and periods"
    
    return True, f"{field_name} looks good!"

def validate_username(username):
    """Validate username format and availability"""
    if not username:
        return False, "Username is required"
    
    username = username.strip()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if not re.match(USERNAME_REGEX, username):
        return False, "Username can only contain letters, numbers, dots, hyphens, and underscores"
    
    if User.objects.filter(username=username).exists():
        return False, "This username is already taken"
    
    return True, "Username is available!"

def validate_email_availability(email, exclude_user=None):
    """Check if email is available for registration"""
    is_valid, message = validate_email_format(email)
    if not is_valid:
        return False, message
    
    query = User.objects.filter(email=email)
    if exclude_user:
        query = query.exclude(id=exclude_user.id)
    
    if query.exists():
        return False, "An account with this email already exists"
    
    return True, "Email is available!"

def validate_newsletter_email(email):
    """Validate email for newsletter subscription"""
    is_valid, message = validate_email_format(email)
    if not is_valid:
        return False, message
    
    if NewsletterSubscription.objects.filter(email=email, is_active=True).exists():
        return False, "This email is already subscribed"
    
    return True, "Email is ready for subscription!"

def validate_password_strength(password):
    """Validate password strength and return feedback"""
    if not password:
        return 0, ["Password is required"]
    
    strength = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        strength += 1
    else:
        feedback.append("At least 8 characters")
    
    # Uppercase check
    if re.search(r'[A-Z]', password):
        strength += 1
    else:
        feedback.append("One uppercase letter")
    
    # Lowercase check
    if re.search(r'[a-z]', password):
        strength += 1
    else:
        feedback.append("One lowercase letter")
    
    # Number check
    if re.search(r'\d', password):
        strength += 1
    else:
        feedback.append("One number")
    
    # Special character check
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        strength += 1
    else:
        feedback.append("One special character")
    
    return strength, feedback

def validate_subject(subject, min_length=5):
    """Validate contact subject"""
    if not subject:
        return False, "Subject is required"
    
    subject = subject.strip()
    
    if len(subject) < min_length:
        return False, f"Subject must be at least {min_length} characters"
    
    return True, "Subject looks good!"

def validate_message(message, min_length=10):
    """Validate contact message"""
    if not message:
        return False, "Message is required"
    
    message = message.strip()
    
    if len(message) < min_length:
        return False, f"Message must be at least {min_length} characters"
    
    word_count = len(message.split())
    return True, f"Looks good! ({word_count} words)"

def log_validation_attempt(field_name, value, is_valid, request=None):
    """Log validation attempts for monitoring"""
    user_id = request.user.id if request and request.user.is_authenticated else None
    
    logger.info(
        f"Validation attempt - Field: {field_name}, "
        f"Valid: {is_valid}, User: {user_id}, "
        f"IP: {get_client_ip(request) if request else 'Unknown'}"
    )

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def safe_int(value, default=0):
    """Safely convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def truncate_text(text, max_length=50, suffix="..."):
    """Truncate text with proper suffix"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_contact_stats():
    """Get contact statistics for dashboard"""
    try:
        stats = {
            'total_contacts': Contact.objects.count(),
            'resolved_contacts': Contact.objects.filter(is_resolved=True).count(),
            'pending_contacts': Contact.objects.filter(is_resolved=False).count(),
            'newsletter_subscribers': NewsletterSubscription.objects.filter(is_active=True).count(),
        }
        return stats
    except Exception as e:
        logger.error(f"Error getting contact stats: {e}")
        return {
            'total_contacts': 0,
            'resolved_contacts': 0,
            'pending_contacts': 0,
            'newsletter_subscribers': 0,
        }
