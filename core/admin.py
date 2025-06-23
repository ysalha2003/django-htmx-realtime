from django.contrib import admin
from .models import Contact, NewsletterSubscription

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'category', 'created_at', 'is_resolved')
    list_filter = ('is_resolved', 'category', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    actions = ['mark_as_resolved']

    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True, resolved_by=request.user)
    mark_as_resolved.short_description = "Mark selected contacts as resolved"

@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at', 'is_active')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email',)
