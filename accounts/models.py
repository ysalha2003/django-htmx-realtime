import os
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from PIL import Image

# Constants
MAX_PROFILE_BIO_LENGTH = 500
MAX_PROFILE_LOCATION_LENGTH = 100
MAX_PHONE_NUMBER_LENGTH = 17
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
MAX_IMAGE_DIMENSIONS = (1024, 1024)

def validate_image_file(file):
    """Validate uploaded image files"""
    if not file:
        return
    
    # Check file size
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(f'File size must be less than {MAX_FILE_SIZE // (1024*1024)}MB')
    
    # Check file extension
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(f'File type not supported. Allowed types: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}')
    
    # Check if it's actually an image
    try:
        with Image.open(file) as img:
            img.verify()
    except Exception:
        raise ValidationError('Invalid image file')

def profile_picture_upload_path(instance, filename):
    """Generate upload path for profile pictures"""
    # Clean filename and add user ID for uniqueness
    name, ext = os.path.splitext(filename)
    return f'profile_pics/user_{instance.user.id}/{name[:50]}{ext}'

class UserProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        db_index=True
    )
    bio = models.TextField(
        max_length=MAX_PROFILE_BIO_LENGTH, 
        blank=True, 
        help_text="Tell us about yourself"
    )
    profile_picture = models.ImageField(
        upload_to=profile_picture_upload_path,
        blank=True,
        help_text="Upload a profile picture (max 5MB)",
        validators=[validate_image_file]
    )
    birth_date = models.DateField(
        null=True, 
        blank=True, 
        help_text="Your birth date",
        db_index=True  # For age-based queries
    )

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=MAX_PHONE_NUMBER_LENGTH,
        blank=True,
        help_text="Contact phone number"
    )

    website = models.URLField(
        blank=True, 
        help_text="Personal website or portfolio"
    )
    location = models.CharField(
        max_length=MAX_PROFILE_LOCATION_LENGTH, 
        blank=True, 
        help_text="City, Country",
        db_index=True  # For location-based queries
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['location']),
        ]

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_full_name(self):
        """Get user's full name with fallback"""
        full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        return full_name if full_name else self.user.username

    def clean(self):
        """Custom validation"""
        super().clean()
        
        # Validate birth date is not in the future
        if self.birth_date and self.birth_date > timezone.now().date():
            raise ValidationError("Birth date cannot be in the future")

    def save(self, *args, **kwargs):
        """Override save to optimize image"""
        super().save(*args, **kwargs)
        
        # Optimize profile picture after saving
        if self.profile_picture:
            self._optimize_image()

    def _optimize_image(self):
        """Optimize uploaded image"""
        try:
            with Image.open(self.profile_picture.path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.size[0] > MAX_IMAGE_DIMENSIONS[0] or img.size[1] > MAX_IMAGE_DIMENSIONS[1]:
                    img.thumbnail(MAX_IMAGE_DIMENSIONS, Image.Resampling.LANCZOS)
                    img.save(self.profile_picture.path, optimize=True, quality=85)
        except Exception as e:
            # Log error but don't break the save process
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error optimizing image for user {self.user.id}: {e}")

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update user profile when user is saved"""
    if created:
        UserProfile.objects.create(user=instance)
    elif hasattr(instance, 'profile'):
        instance.profile.save()
