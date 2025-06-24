import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.exceptions import ValidationError

from .forms import ContactForm, NewsletterForm
from .models import Contact, NewsletterSubscription
from .utils import (
    is_htmx_request, validate_email_format, validate_name, 
    validate_subject, validate_message, validate_newsletter_email,
    render_validation_response, log_validation_attempt, get_contact_stats
)

logger = logging.getLogger(__name__)

def home(request):
    """Home page with dashboard stats"""
    try:
        context = get_contact_stats()
        context['newsletter_form'] = NewsletterForm()
        return render(request, 'core/home.html', context)
    except Exception as e:
        logger.error(f"Error loading home page: {e}")
        # Fallback context
        context = {
            'total_contacts': 0,
            'resolved_contacts': 0,
            'newsletter_subscribers': 0,
            'newsletter_form': NewsletterForm()
        }
        return render(request, 'core/home.html', context)

def contact_view(request):
    """Handle contact form submission with improved error handling"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        try:
            if form.is_valid():
                contact = form.save()
                logger.info(f"New contact created: {contact.id} from {contact.email}")
                messages.success(request, f'Inquiry from {contact.name} submitted. Ref: #{contact.id}.')
                
                if is_htmx_request(request):
                    return render(request, 'partials/contact_success.html', {'contact': contact})
                return redirect('core:contact')
            else:
                logger.warning(f"Invalid contact form submission: {form.errors}")
                if is_htmx_request(request):
                    return render(request, 'partials/contact_form.html', {'form': form})
        except Exception as e:
            logger.error(f"Error processing contact form: {e}")
            messages.error(request, 'An error occurred while submitting your message. Please try again.')
            if is_htmx_request(request):
                return render(request, 'partials/contact_form.html', {'form': form})
    else:
        form = ContactForm()

    # Get recent contacts for staff users with optimized query
    recent_contacts = None
    if request.user.is_staff:
        try:
            recent_contacts = Contact.objects.select_related('resolved_by').order_by('-created_at')[:5]
        except Exception as e:
            logger.error(f"Error fetching recent contacts: {e}")

    context = {
        'form': form, 
        'recent_contacts': recent_contacts
    }
    return render(request, 'core/contact.html', context)

def newsletter_subscribe(request):
    """Handle newsletter subscription with improved validation"""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        try:
            if form.is_valid():
                subscription = form.save()
                logger.info(f"New newsletter subscription: {subscription.email}")
                messages.success(request, 'Subscription successful. Thank you!')
                
                if is_htmx_request(request):
                    return render(request, 'partials/newsletter_success.html')
            else:
                logger.warning(f"Invalid newsletter form: {form.errors}")
                messages.warning(request, 'This email address is already subscribed or invalid.')
                if is_htmx_request(request):
                    return render(request, 'partials/newsletter_form.html', {'newsletter_form': form})
        except Exception as e:
            logger.error(f"Error processing newsletter subscription: {e}")
            messages.error(request, 'An error occurred. Please try again.')
            if is_htmx_request(request):
                return render(request, 'partials/newsletter_form.html', {'newsletter_form': form})
    
    return redirect('core:home')

@login_required
def contact_list_view(request):
    """Display contact list with optimized queries and improved filtering"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('core:home')

    try:
        query = request.GET.get('q', '').strip()
        status = request.GET.get('status', '')
        
        # Start with optimized base query
        contacts_list = Contact.objects.select_related('resolved_by').order_by('-created_at')
        
        # Apply filters
        if query:
            contacts_list = contacts_list.filter(
                Q(name__icontains=query) | 
                Q(email__icontains=query) | 
                Q(subject__icontains=query)
            )
        
        if status == 'resolved':
            contacts_list = contacts_list.filter(is_resolved=True)
        elif status == 'pending':
            contacts_list = contacts_list.filter(is_resolved=False)

        # Paginate results
        paginator = Paginator(contacts_list, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'contacts': page_obj, 
            'query': query, 
            'status': status
        }
        return render(request, 'core/contact_list.html', context)
        
    except Exception as e:
        logger.error(f"Error loading contact list: {e}")
        messages.error(request, 'Error loading contacts. Please try again.')
        return redirect('core:home')

@login_required
@require_http_methods(["GET"])
def api_pending_contacts_count(request):
    """API endpoint to get current pending contacts count"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        pending_count = Contact.objects.filter(is_resolved=False).count()
        total_count = Contact.objects.count()

        return JsonResponse({
            'pending_count': pending_count,
            'total_count': total_count
        })
    except Exception as e:
        logger.error(f"Error getting pending contacts count: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

# Fixed validation endpoints with proper error handling
@require_http_methods(["POST"])
def validate_name(request):
    """Validate name field"""
    name = request.POST.get('name', '').strip()
    if not name:
        return HttpResponse('')
    
    try:
        is_valid, message = validate_name(name)
        log_validation_attempt('name', name, is_valid, request)
        
        if is_valid:
            return render(request, 'partials/validation_success.html', {'message': message})
        else:
            return render(request, 'partials/validation_error.html', {'message': message})
    except Exception as e:
        logger.error(f"Error validating name: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Validation error occurred'})

@require_http_methods(["POST"])
def validate_email(request):
    """Validate email field for contact form"""
    email = request.POST.get('email', '').strip()
    if not email:
        return HttpResponse('')
    
    try:
        is_valid, message = validate_email_format(email)
        
        # Check if email has contacted before (warning, not error)
        if is_valid and Contact.objects.filter(email=email).exists():
            return render(request, 'partials/validation_warning.html', {'message': 'This email has contacted us before'})
        elif is_valid:
            return render(request, 'partials/validation_success.html', {'message': message})
        else:
            return render(request, 'partials/validation_error.html', {'message': message})
        
    except Exception as e:
        logger.error(f"Error validating email: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Validation error occurred'})

@require_http_methods(["POST"])
def validate_subject(request):
    """Validate subject field"""
    subject = request.POST.get('subject', '').strip()
    if not subject:
        return HttpResponse('')
    
    try:
        is_valid, message = validate_subject(subject)
        
        if is_valid:
            return render(request, 'partials/validation_success.html', {'message': message})
        else:
            return render(request, 'partials/validation_error.html', {'message': message})
    except Exception as e:
        logger.error(f"Error validating subject: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Validation error occurred'})

@require_http_methods(["POST"])
def validate_message(request):
    """Validate message field"""
    message = request.POST.get('message', '').strip()
    if not message:
        return HttpResponse('')
    
    try:
        is_valid, msg = validate_message(message)
        
        if is_valid:
            return render(request, 'partials/validation_success.html', {'message': msg})
        else:
            return render(request, 'partials/validation_error.html', {'message': msg})
    except Exception as e:
        logger.error(f"Error validating message: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Validation error occurred'})

@require_http_methods(["POST"])
def validate_newsletter_email(request):
    """Validate email for newsletter subscription"""
    email = request.POST.get('email', '').strip()
    if not email:
        return HttpResponse('')
    
    try:
        is_valid, message = validate_newsletter_email(email)
        
        if is_valid:
            return render(request, 'partials/validation_success.html', {'message': message})
        else:
            return render(request, 'partials/validation_warning.html', {'message': message})
    except Exception as e:
        logger.error(f"Error validating newsletter email: {e}")
        return render(request, 'partials/validation_error.html', {'message': 'Validation error occurred'})
