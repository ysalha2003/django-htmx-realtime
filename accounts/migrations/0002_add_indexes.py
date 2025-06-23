# Generated manually for adding database indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # Add UserProfile indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS accounts_userprofile_user_id_idx ON accounts_userprofile (user_id);",
            reverse_sql="DROP INDEX IF EXISTS accounts_userprofile_user_id_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS accounts_userprofile_birth_date_idx ON accounts_userprofile (birth_date);",
            reverse_sql="DROP INDEX IF EXISTS accounts_userprofile_birth_date_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS accounts_userprofile_location_idx ON accounts_userprofile (location);",
            reverse_sql="DROP INDEX IF EXISTS accounts_userprofile_location_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS accounts_userprofile_created_at_idx ON accounts_userprofile (created_at);",
            reverse_sql="DROP INDEX IF EXISTS accounts_userprofile_created_at_idx;"
        ),
        
        # Add composite indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS accounts_userprofile_location_created_idx ON accounts_userprofile (location, created_at);",
            reverse_sql="DROP INDEX IF EXISTS accounts_userprofile_location_created_idx;"
        ),
    ]
