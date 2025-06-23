from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator

class Contact(models.Model):
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('support', 'Technical Support'),
        ('feedback', 'Feedback'),
        ('business', 'Business Inquiry'),
        ('other', 'Other'),
    ]

    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        help_text="Your full name"
    )
    email = models.EmailField(help_text="We'll respond to this email address")
    subject = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5)],
        help_text="Brief description of your inquiry"
    )
    category = models.CharField(
        max_length=20,
        choices=SUBJECT_CHOICES,
        default='general',
        help_text="What type of inquiry is this?"
    )
    message = models.TextField(
        validators=[MinLengthValidator(10)],
        help_text="Detailed message (minimum 10 characters)"
    )
    created_at = models.DateTimeField(default=timezone.now)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_contacts'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"Contact from {self.name} - {self.subject[:50]}"

    def mark_resolved(self, user=None):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save()

class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Newsletter Subscription"
        verbose_name_plural = "Newsletter Subscriptions"

    def __str__(self):
        return f"Newsletter: {self.email}"
