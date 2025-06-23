from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from core.models import Contact
from django.utils import timezone


@receiver(post_save, sender=Contact)
def notify_new_contact(sender, instance, created, **kwargs):
    """
    Send real-time notification when a new contact is created
    """
    if created:  # Only trigger for new contacts
        channel_layer = get_channel_layer()

        # Prepare notification data
        notification_data = {
            'id': instance.id,
            'name': instance.name,
            'email': instance.email,
            'subject': instance.subject,
            'category': instance.get_category_display(),
            'created_at': instance.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_at_relative': f"Just now",
            'message_preview': instance.message[:100] + "..." if len(instance.message) > 100 else instance.message,
        }

        # Send notification to admin group
        async_to_sync(channel_layer.group_send)(
            'admin_notifications',
            {
                'type': 'new_contact_notification',
                'data': notification_data
            }
        )

        # Also send updated count
        pending_count = Contact.objects.filter(is_resolved=False).count()
        async_to_sync(channel_layer.group_send)(
            'admin_notifications',
            {
                'type': 'notification_count_update',
                'data': {
                    'pending_count': pending_count,
                    'total_count': Contact.objects.count()
                }
            }
        )
