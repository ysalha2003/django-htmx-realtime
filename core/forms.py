from django import forms
from .models import Contact, NewsletterSubscription

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'category', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Your full name',
                'hx-post': '/validate/name/', 'hx-trigger': 'keyup changed delay:300ms',
                'hx-target': '#name-validation', 'hx-swap': 'innerHTML'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input', 'placeholder': 'your.email@example.com',
                'hx-post': '/validate/email/', 'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#email-validation', 'hx-swap': 'innerHTML'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'What is this about?',
                'hx-post': '/validate/subject/', 'hx-trigger': 'keyup changed delay:300ms',
                'hx-target': '#subject-validation', 'hx-swap': 'innerHTML'
            }),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'message': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 5, 'placeholder': 'Your detailed message...',
                'hx-post': '/validate/message/', 'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#message-validation', 'hx-swap': 'innerHTML'
            })
        }

class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscription
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input', 'placeholder': 'Enter your email address',
                'hx-post': '/validate/newsletter-email/', 'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#newsletter-validation', 'hx-swap': 'innerHTML'
            })
        }
