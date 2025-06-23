from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('contact/', views.contact_view, name='contact'),
    path('contacts/', views.contact_list_view, name='contact_list'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),

    # API endpoints
    path('api/pending-contacts-count/', views.api_pending_contacts_count, name='api_pending_contacts_count'),

    # Validation endpoints
    path('validate/name/', views.validate_name, name='validate_name'),
    path('validate/email/', views.validate_email, name='validate_email'),
    path('validate/subject/', views.validate_subject, name='validate_subject'),
    path('validate/message/', views.validate_message, name='validate_message'),
    path('validate/newsletter-email/', views.validate_newsletter_email, name='validate_newsletter_email'),
]
