from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError

# Constants
MAX_CONTACT_SUBJECT_LENGTH = 200
MAX_CONTACT_NAME_LENGTH = 100
MIN_CONTACT_NAME_LENGTH = 2
MIN_CONTACT_SUBJECT_LENGTH = 5
MIN_CONTACT_MESSAGE_LENGTH = 10

class Contact(models.Model):
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('support', 'Technical Support'),
        ('feedback', 'Feedback'),
        ('business', 'Business Inquiry'),
        ('other', 'Other'),
    ]

    name = models.CharField(
        max_length=MAX_CONTACT_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_CONTACT_NAME_LENGTH)],
        help_text="Your full name",
        db_index=True  # Added index for search queries
    )
    email = models.EmailField(
        help_text="We'll respond to this email address",
        db_index=True  # Added index for search queries
    )
    subject = models.CharField(
        max_length=MAX_CONTACT_SUBJECT_LENGTH,
        validators=[MinLengthValidator(MIN_CONTACT_SUBJECT_LENGTH)],
        help_text="Brief description of your inquiry",
        db_index=True  # Added index for search queries
    )
    category = models.CharField(
        max_length=20,
        choices=SUBJECT_CHOICES,
        default='general',
        help_text="What type of inquiry is this?",
        db_index=True  # Added index for filtering
    )
    message = models.TextField(
        validators=[MinLengthValidator(MIN_CONTACT_MESSAGE_LENGTH)],
        help_text="Detailed message (minimum 10 characters)"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True  # Added index for date filtering and ordering
    )
    is_resolved = models.BooleanField(
        default=False,
        db_index=True  # Added index for status filtering
    )
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
        indexes = [
            # Composite indexes for common query patterns
            models.Index(fields=['is_resolved', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['email', '-created_at']),
        ]

    def __str__(self):
        return f"Contact from {self.name} - {self.subject[:50]}"

    def clean(self):
        """Custom validation"""
        super().clean()
        if self.resolved_at and not self.is_resolved:
            raise ValidationError("Cannot have resolved_at without is_resolved being True")

    def mark_resolved(self, user=None):
        """Mark contact as resolved with proper timestamp"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save(update_fields=['is_resolved', 'resolved_at', 'resolved_by'])

class NewsletterSubscription(models.Model):
    email = models.EmailField(
        unique=True,
        db_index=True  # Added index for lookups
    )
    subscribed_at = models.DateTimeField(
        default=timezone.now,
        db_index=True  # Added index for date filtering
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True  # Added index for filtering active subscriptions
    )

    class Meta:
        verbose_name = "Newsletter Subscription"
        verbose_name_plural = "Newsletter Subscriptions"
        indexes = [
            models.Index(fields=['is_active', '-subscribed_at']),
        ]

    def __str__(self):
        return f"Newsletter: {self.email}"

    def deactivate(self):
        """Deactivate subscription instead of deleting"""
        self.is_active = False
        self.save(update_fields=['is_active'])
