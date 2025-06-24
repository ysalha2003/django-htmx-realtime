from django import forms
from django.core.exceptions import ValidationError
from .models import Contact, NewsletterSubscription
import re

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'category', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'Enter your full name',
                'hx-post': '/validate/name/', 
                'hx-trigger': 'keyup changed delay:300ms',
                'hx-target': '#name-validation', 
                'hx-swap': 'innerHTML',
                'autocomplete': 'name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input', 
                'placeholder': 'your.email@example.com',
                'hx-post': '/validate/email/', 
                'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#email-validation', 
                'hx-swap': 'innerHTML',
                'autocomplete': 'email'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'Brief description of your inquiry',
                'hx-post': '/validate/subject/', 
                'hx-trigger': 'keyup changed delay:300ms',
                'hx-target': '#subject-validation', 
                'hx-swap': 'innerHTML',
                'maxlength': 200
            }),
            'category': forms.Select(attrs={
                'class': 'form-input'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-input resize-y min-h-[120px]', 
                'rows': 5, 
                'placeholder': 'Please provide detailed information about your inquiry...',
                'hx-post': '/validate/message/', 
                'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#message-validation', 
                'hx-swap': 'innerHTML',
                'maxlength': 2000
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add required attributes and improve labels
        self.fields['name'].required = True
        self.fields['email'].required = True
        self.fields['subject'].required = True
        self.fields['message'].required = True
        
        # Update labels
        self.fields['name'].label = 'Full Name'
        self.fields['email'].label = 'Email Address'
        self.fields['subject'].label = 'Subject'
        self.fields['category'].label = 'Category'
        self.fields['message'].label = 'Message'
        
        # Add help text
        self.fields['name'].help_text = 'Your first and last name'
        self.fields['email'].help_text = "We'll respond to this email address"
        self.fields['subject'].help_text = 'Brief description of your inquiry (5-200 characters)'
        self.fields['category'].help_text = 'What type of inquiry is this?'
        self.fields['message'].help_text = 'Detailed message (10-2000 characters)'

    def clean_name(self):
        """Enhanced name validation"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            
            # Check minimum length
            if len(name) < 2:
                raise ValidationError("Name must be at least 2 characters long.")
            
            # Check maximum length
            if len(name) > 100:
                raise ValidationError("Name is too long (maximum 100 characters).")
            
            # Check for valid characters (letters, spaces, hyphens, apostrophes, periods)
            if not re.match(r'^[a-zA-Z\s\-\'\.]+$', name):
                raise ValidationError("Name can only contain letters, spaces, hyphens, apostrophes, and periods.")
            
            # Check for at least 2 letters
            if len([c for c in name if c.isalpha()]) < 2:
                raise ValidationError("Name must contain at least 2 letters.")
            
            # Check for obvious test data
            test_names = ['test', 'testing', 'john doe', 'jane doe', 'test user', 'asdf']
            if name.lower() in test_names:
                raise ValidationError("Please enter your real name.")
                
        return name

    def clean_email(self):
        """Enhanced email validation"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            
            # Basic format validation
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                raise ValidationError("Please enter a valid email address.")
            
            # Check for suspicious patterns
            suspicious_domains = ['10minutemail.com', 'tempmail.org', 'guerrillamail.com']
            domain = email.split('@')[1]
            if domain in suspicious_domains:
                raise ValidationError("Please use a permanent email address.")
                
            # Check for consecutive dots
            if '..' in email:
                raise ValidationError("Email address contains invalid characters.")
                
        return email

    def clean_subject(self):
        """Enhanced subject validation"""
        subject = self.cleaned_data.get('subject')
        if subject:
            subject = subject.strip()
            
            # Check minimum length
            if len(subject) < 5:
                raise ValidationError("Subject must be at least 5 characters long.")
            
            # Check maximum length
            if len(subject) > 200:
                raise ValidationError("Subject is too long (maximum 200 characters).")
            
            # Check for meaningful content
            if subject.count(' ') == 0 and len(subject) > 20:
                raise ValidationError("Subject should contain spaces between words.")
            
            # Check for obvious spam patterns
            spam_patterns = ['!!!', 'URGENT', 'FREE', 'WINNER', '$$$']
            if any(pattern in subject.upper() for pattern in spam_patterns):
                raise ValidationError("Subject appears to be spam. Please use a professional subject line.")
                
        return subject

    def clean_message(self):
        """Enhanced message validation"""
        message = self.cleaned_data.get('message')
        if message:
            message = message.strip()
            
            # Check minimum length
            if len(message) < 10:
                raise ValidationError("Message must be at least 10 characters long.")
            
            # Check maximum length
            if len(message) > 2000:
                raise ValidationError("Message is too long (maximum 2000 characters).")
            
            # Check for minimum word count
            word_count = len(message.split())
            if word_count < 3:
                raise ValidationError("Message should contain at least 3 words.")
            
            # Check for suspicious patterns
            if message.count('http') > 3:
                raise ValidationError("Message contains too many links.")
            
            # Check for excessive repetition
            words = message.lower().split()
            if len(words) > 10:
                word_freq = {}
                for word in words:
                    word_freq[word] = word_freq.get(word, 0) + 1
                
                # Check if any word appears more than 30% of the time
                max_freq = max(word_freq.values())
                if max_freq > len(words) * 0.3:
                    raise ValidationError("Message contains excessive repetition.")
                    
        return message

    def clean(self):
        """Form-level validation"""
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        email = cleaned_data.get('email')
        subject = cleaned_data.get('subject')
        message = cleaned_data.get('message')
        
        # Check if name appears in email (potential spam)
        if name and email:
            name_parts = name.lower().split()
            email_local = email.split('@')[0].lower()
            if all(part in email_local for part in name_parts if len(part) > 2):
                # This is actually normal, so we'll allow it
                pass
        
        # Check for consistent language/content
        if subject and message:
            # Very basic check - if subject is very different in style from message
            if len(subject.split()) > 10 and len(message.split()) < 5:
                raise ValidationError("Subject and message content seem inconsistent.")
        
        return cleaned_data

class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscription
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input w-full text-white placeholder-blue-200 bg-white/10 border-white/20 focus:border-white focus:ring-white', 
                'placeholder': 'Enter your email address',
                'hx-post': '/validate/newsletter-email/', 
                'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#newsletter-validation', 
                'hx-swap': 'innerHTML',
                'autocomplete': 'email'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make email required
        self.fields['email'].required = True
        self.fields['email'].label = 'Email Address'
        self.fields['email'].help_text = 'Subscribe to receive updates and exclusive content'

    def clean_email(self):
        """Enhanced email validation for newsletter"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            
            # Basic format validation
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                raise ValidationError("Please enter a valid email address.")
            
            # Check if already subscribed
            if NewsletterSubscription.objects.filter(email=email, is_active=True).exists():
                raise ValidationError("This email address is already subscribed to our newsletter.")
            
            # Check for suspicious patterns
            suspicious_domains = ['10minutemail.com', 'tempmail.org', 'guerrillamail.com', 'mailinator.com']
            domain = email.split('@')[1]
            if domain in suspicious_domains:
                raise ValidationError("Please use a permanent email address for newsletter subscription.")
            
            # Check for role-based emails (optional warning)
            role_prefixes = ['admin', 'info', 'support', 'sales', 'marketing', 'noreply', 'no-reply']
            email_local = email.split('@')[0]
            if email_local in role_prefixes:
                # We'll allow it but could show a warning
                pass
                
        return email

# Additional utility forms

class QuickContactForm(forms.Form):
    """Simplified contact form for quick inquiries"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your name',
            'autocomplete': 'name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'your@email.com',
            'autocomplete': 'email'
        })
    )
    message = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Quick message...',
            'rows': 3
        })
    )

class FeedbackForm(forms.Form):
    """User feedback form"""
    RATING_CHOICES = [
        (5, '⭐⭐⭐⭐⭐ Excellent'),
        (4, '⭐⭐⭐⭐ Good'),
        (3, '⭐⭐⭐ Average'),
        (2, '⭐⭐ Poor'),
        (1, '⭐ Very Poor'),
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    feedback = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Tell us about your experience...',
            'rows': 4
        })
    )
    recommend = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )

class UnsubscribeForm(forms.Form):
    """Newsletter unsubscribe form"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email to unsubscribe',
            'autocomplete': 'email'
        })
    )
    reason = forms.ChoiceField(
        required=False,
        choices=[
            ('too_frequent', 'Too many emails'),
            ('not_relevant', 'Content not relevant'),
            ('never_signed_up', 'Never signed up'),
            ('technical_issues', 'Technical issues'),
            ('other', 'Other reason'),
        ],
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    feedback = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Optional: Tell us how we can improve',
            'rows': 3
        })
    )
