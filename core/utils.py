"""
Enhanced utility functions for the core app with comprehensive validation
"""
import re
import logging
from urllib.parse import urlparse
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.models import User
from .models import Contact, NewsletterSubscription

logger = logging.getLogger(__name__)

# Enhanced validation constants
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
NAME_REGEX = r'^[a-zA-Z\s\-\'\.]+$'
USERNAME_REGEX = r'^[a-zA-Z0-9_.-]+$'
PHONE_REGEX = r'^\+?[\d\s\-\(\)\.]{10,17}$'
PHONE_CLEAN_REGEX = r'[\D]'

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
    """Validate email format with enhanced checks"""
    if not email:
        return False, "Email is required"
    
    if len(email) > 254:
        return False, "Email address is too long"
    
    if not re.match(EMAIL_REGEX, email):
        return False, "Please enter a valid email address"
    
    # Additional checks for common mistakes
    if email.count('@') != 1:
        return False, "Email must contain exactly one @ symbol"
    
    local, domain = email.split('@')
    if len(local) > 64:
        return False, "Email address is too long"
    
    if domain.startswith('.') or domain.endswith('.'):
        return False, "Invalid domain format"
    
    return True, "Email format is valid"

def validate_name(name, min_length=2, max_length=100, field_name="Name"):
    """Enhanced name validation"""
    if not name:
        return False, f"{field_name} is required"
    
    name = name.strip()
    
    if len(name) < min_length:
        return False, f"{field_name} must be at least {min_length} characters long"
    
    if len(name) > max_length:
        return False, f"{field_name} must be less than {max_length} characters"
    
    if not re.match(NAME_REGEX, name):
        return False, f"{field_name} can only contain letters, spaces, hyphens, apostrophes, and periods"
    
    # Check for suspicious patterns
    if len([c for c in name if c.isalpha()]) < 2:
        return False, f"{field_name} must contain at least 2 letters"
    
    return True, f"{field_name} looks good!"

def validate_username(username):
    """Enhanced username validation"""
    if not username:
        return False, "Username is required"
    
    username = username.strip()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 30:
        return False, "Username must be less than 30 characters"
    
    if not re.match(USERNAME_REGEX, username):
        return False, "Username can only contain letters, numbers, dots, hyphens, and underscores"
    
    # Check for reserved usernames
    reserved_usernames = ['admin', 'root', 'user', 'test', 'guest', 'administrator']
    if username.lower() in reserved_usernames:
        return False, "This username is reserved. Please choose another one"
    
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
        return False, "This email is already subscribed to our newsletter"
    
    return True, "Email is ready for subscription!"

def validate_password_strength(password):
    """Enhanced password strength validation"""
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
    
    # Additional checks for very strong passwords
    if len(password) >= 12:
        strength = min(strength + 0.5, 5)
    
    if not any(common in password.lower() for common in ['password', '123456', 'qwerty', 'admin']):
        strength = min(strength + 0.5, 5)
    
    return int(strength), feedback

def validate_subject(subject, min_length=5, max_length=200):
    """Enhanced subject validation"""
    if not subject:
        return False, "Subject is required"
    
    subject = subject.strip()
    
    if len(subject) < min_length:
        return False, f"Subject must be at least {min_length} characters"
    
    if len(subject) > max_length:
        return False, f"Subject must be less than {max_length} characters"
    
    # Check for meaningful content
    if subject.count(' ') == 0 and len(subject) > 20:
        return False, "Subject should contain spaces between words"
    
    return True, "Subject looks good!"

def validate_message(message, min_length=10, max_length=2000):
    """Enhanced message validation"""
    if not message:
        return False, "Message is required"
    
    message = message.strip()
    
    if len(message) < min_length:
        return False, f"Message must be at least {min_length} characters"
    
    if len(message) > max_length:
        return False, f"Message must be less than {max_length} characters"
    
    word_count = len(message.split())
    
    if word_count < 3:
        return False, "Message should contain at least 3 words"
    
    return True, f"Message looks good! ({word_count} words)"

def validate_phone_number(phone):
    """Validate phone number format"""
    if not phone:
        return False, "Phone number is required"
    
    phone = phone.strip()
    
    # Basic format check
    if not re.match(PHONE_REGEX, phone):
        return False, "Please enter a valid phone number (e.g., +1-234-567-8900)"
    
    # Clean phone number for digit counting
    clean_phone = re.sub(PHONE_CLEAN_REGEX, '', phone)
    
    if len(clean_phone) < 10:
        return False, "Phone number must contain at least 10 digits"
    
    if len(clean_phone) > 15:
        return False, "Phone number is too long"
    
    # Check for obvious fake numbers
    if clean_phone in ['0000000000', '1111111111', '1234567890']:
        return False, "Please enter a valid phone number"
    
    return True, "Phone number format is valid"

def validate_website(website):
    """Validate website URL format"""
    if not website:
        return False, "Website URL is required"
    
    website = website.strip()
    
    # Add protocol if missing
    if not website.startswith(('http://', 'https://')):
        website = 'https://' + website
    
    try:
        parsed = urlparse(website)
        
        if not parsed.netloc:
            return False, "Please enter a valid website URL"
        
        if not parsed.scheme in ['http', 'https']:
            return False, "Website URL must use http or https"
        
        # Basic domain validation
        domain_parts = parsed.netloc.split('.')
        if len(domain_parts) < 2:
            return False, "Please enter a complete domain name"
        
        if any(len(part) == 0 for part in domain_parts):
            return False, "Invalid domain format"
        
        return True, "Website URL looks good!"
        
    except Exception:
        return False, "Please enter a valid website URL"

def validate_location(location, max_length=100):
    """Validate location field"""
    if not location:
        return False, "Location is required"
    
    location = location.strip()
    
    if len(location) < 2:
        return False, "Location must be at least 2 characters"
    
    if len(location) > max_length:
        return False, f"Location must be less than {max_length} characters"
    
    # Allow letters, spaces, commas, hyphens, apostrophes, and periods
    if not re.match(r'^[a-zA-Z\s,\-\'\.]+$', location):
        return False, "Location can only contain letters, spaces, commas, hyphens, apostrophes, and periods"
    
    # Check for meaningful content
    if location.replace(' ', '').replace(',', '').replace('-', '') == '':
        return False, "Please enter a valid location"
    
    return True, "Location looks good!"

def log_validation_attempt(field_name, value, is_valid, request=None):
    """Enhanced validation logging"""
    user_id = request.user.id if request and request.user.is_authenticated else None
    
    logger.info(
        f"Validation attempt - Field: {field_name}, "
        f"Valid: {is_valid}, User: {user_id}, "
        f"IP: {get_client_ip(request) if request else 'Unknown'}, "
        f"Length: {len(str(value)) if value else 0}"
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

def sanitize_input(text, max_length=None):
    """Sanitize user input"""
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Truncate if necessary
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text

def format_phone_display(phone):
    """Format phone number for display"""
    if not phone:
        return ""
    
    # Clean phone number
    clean = re.sub(r'[\D]', '', phone)
    
    # Format US numbers
    if len(clean) == 10:
        return f"({clean[:3]}) {clean[3:6]}-{clean[6:]}"
    elif len(clean) == 11 and clean.startswith('1'):
        return f"+1 ({clean[1:4]}) {clean[4:7]}-{clean[7:]}"
    
    return phone  # Return original if we can't format

def validate_form_security(request):
    """Basic form security validation"""
    # Check for suspicious patterns
    if request.method == 'POST':
        # Check for script injection attempts
        for field, value in request.POST.items():
            if isinstance(value, str) and any(pattern in value.lower() for pattern in ['<script', 'javascript:', 'vbscript:']):
                logger.warning(f"Potential script injection attempt from {get_client_ip(request)}")
                return False, "Invalid characters detected in form submission"
    
    return True, "Form security check passed"
