# Generated manually for adding database indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # Add individual field indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_contact_name_idx ON core_contact (name);",
            reverse_sql="DROP INDEX IF EXISTS core_contact_name_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_contact_email_idx ON core_contact (email);",
            reverse_sql="DROP INDEX IF EXISTS core_contact_email_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_contact_subject_idx ON core_contact (subject);",
            reverse_sql="DROP INDEX IF EXISTS core_contact_subject_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_contact_category_idx ON core_contact (category);",
            reverse_sql="DROP INDEX IF EXISTS core_contact_category_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_contact_created_at_idx ON core_contact (created_at);",
            reverse_sql="DROP INDEX IF EXISTS core_contact_created_at_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_contact_is_resolved_idx ON core_contact (is_resolved);",
            reverse_sql="DROP INDEX IF EXISTS core_contact_is_resolved_idx;"
        ),
        
        # Add composite indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_contact_resolved_created_idx ON core_contact (is_resolved, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS core_contact_resolved_created_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_contact_category_created_idx ON core_contact (category, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS core_contact_category_created_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_contact_email_created_idx ON core_contact (email, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS core_contact_email_created_idx;"
        ),
        
        # Newsletter subscription indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_newsletter_email_idx ON core_newslettersubscription (email);",
            reverse_sql="DROP INDEX IF EXISTS core_newsletter_email_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_newsletter_subscribed_at_idx ON core_newslettersubscription (subscribed_at);",
            reverse_sql="DROP INDEX IF EXISTS core_newsletter_subscribed_at_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_newsletter_is_active_idx ON core_newslettersubscription (is_active);",
            reverse_sql="DROP INDEX IF EXISTS core_newsletter_is_active_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_newsletter_active_subscribed_idx ON core_newslettersubscription (is_active, subscribed_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS core_newsletter_active_subscribed_idx;"
        ),
    ]
