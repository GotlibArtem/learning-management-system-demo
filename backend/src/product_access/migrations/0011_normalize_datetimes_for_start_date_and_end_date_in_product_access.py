from django.db import migrations


SQL_FIX_START = """
UPDATE product_access_productaccess
SET start_date = (
    (start_date AT TIME ZONE 'Europe/Moscow')::date::timestamp AT TIME ZONE 'Europe/Moscow' AT TIME ZONE 'UTC'
)
WHERE start_date IS NOT NULL;
"""

SQL_FIX_END = """
UPDATE product_access_productaccess
SET end_date = (
    ((end_date AT TIME ZONE 'Europe/Moscow')::date + INTERVAL '1 day' - INTERVAL '1 microsecond') 
    AT TIME ZONE 'Europe/Moscow' AT TIME ZONE 'UTC'
)
WHERE end_date IS NOT NULL;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("product_access", "0010_alter_field_start_date_and_end_date_in_product_access"),
    ]
    operations = [
        migrations.RunSQL(SQL_FIX_START, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(SQL_FIX_END, reverse_sql=migrations.RunSQL.noop),
    ]
