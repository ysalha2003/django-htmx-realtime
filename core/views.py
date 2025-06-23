from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import ContactForm, NewsletterForm
from .models import Contact, NewsletterSubscription, User
import re

def is_htmx_request(request):
    return request.headers.get('HX-Request', False)

def home(request):
    context = {
        'total_contacts': Contact.objects.count(),
        'resolved_contacts': Contact.objects.filter(is_resolved=True).count(),
        'newsletter_subscribers': NewsletterSubscription.objects.filter(is_active=True).count(),
        'newsletter_form': NewsletterForm()
    }
    return render(request, 'core/home.html', context)

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            messages.success(request, f'Inquiry from {contact.name} submitted. Ref: #{contact.id}.')
            if is_htmx_request(request):
                return render(request, 'partials/contact_success.html', {'contact': contact})
            return redirect('core:contact')
        elif is_htmx_request(request):
            return render(request, 'partials/contact_form.html', {'form': form})
    else:
        form = ContactForm()
    context = {'form': form, 'recent_contacts': Contact.objects.all()[:5] if request.user.is_staff else None}
    return render(request, 'core/contact.html', context)

def newsletter_subscribe(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subscription successful. Thank you!')
            if is_htmx_request(request):
                return render(request, 'partials/newsletter_success.html')
        else:
            messages.warning(request, 'This email address is already subscribed or invalid.')
            if is_htmx_request(request):
                return render(request, 'partials/newsletter_form.html', {'newsletter_form': form})
    return redirect('core:home')

@login_required
def contact_list_view(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('core:home')

    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    contacts_list = Contact.objects.all()
    if query:
        contacts_list = contacts_list.filter(Q(name__icontains=query) | Q(email__icontains=query) | Q(subject__icontains=query))
    if status == 'resolved':
        contacts_list = contacts_list.filter(is_resolved=True)
    elif status == 'pending':
        contacts_list = contacts_list.filter(is_resolved=False)

    paginator = Paginator(contacts_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'contacts': page_obj, 'query': query, 'status': status}
    return render(request, 'core/contact_list.html', context)

# API endpoint for pending contacts count
@login_required
def api_pending_contacts_count(request):
    """API endpoint to get current pending contacts count"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    pending_count = Contact.objects.filter(is_resolved=False).count()
    total_count = Contact.objects.count()

    return JsonResponse({
        'pending_count': pending_count,
        'total_count': total_count
    })

@require_http_methods(["POST"])
def validate_name(request):
    name = request.POST.get('name', '').strip()
    if not name: return HttpResponse('')
    if len(name) < 2:
        return render(request, 'partials/validation_error.html', {'message': 'Name is too short'})
    if not re.match(r'^[a-zA-Z\s]+$', name):
        return render(request, 'partials/validation_error.html', {'message': 'Name can only contain letters'})
    return render(request, 'partials/validation_success.html', {'message': 'Name looks good!'})

@require_http_methods(["POST"])
def validate_email(request):
    email = request.POST.get('email', '').strip()
    if not email: return HttpResponse('')
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return render(request, 'partials/validation_error.html', {'message': 'Please enter a valid email address'})
    if Contact.objects.filter(email=email).exists():
        return render(request, 'partials/validation_warning.html', {'message': 'This email has contacted us before'})
    return render(request, 'partials/validation_success.html', {'message': 'Email is valid!'})

@require_http_methods(["POST"])
def validate_subject(request):
    subject = request.POST.get('subject', '').strip()
    if not subject: return HttpResponse('')
    if len(subject) < 5:
        return render(request, 'partials/validation_error.html', {'message': 'Subject must be at least 5 characters'})
    return render(request, 'partials/validation_success.html', {'message': 'Subject looks good!'})

@require_http_methods(["POST"])
def validate_message(request):
    message = request.POST.get('message', '').strip()
    if not message: return HttpResponse('')
    if len(message) < 10:
        return render(request, 'partials/validation_error.html', {'message': 'Message must be at least 10 characters'})
    return render(request, 'partials/validation_success.html', {'message': f'Looks good! ({len(message.split())} words)'})

@require_http_methods(["POST"])
def validate_newsletter_email(request):
    email = request.POST.get('email', '').strip()
    if not email: return HttpResponse('')
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return render(request, 'partials/validation_error.html', {'message': 'Please enter a valid email address'})
    if NewsletterSubscription.objects.filter(email=email).exists():
        return render(request, 'partials/validation_warning.html', {'message': 'This email is already subscribed'})
    return render(request, 'partials/validation_success.html', {'message': 'Email is ready for subscription!'})
