from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('cash_closing', '0007_migrate_bank_data'),
    ]
    operations = [
        migrations.RemoveField('income',  'bank_old'),
        migrations.RemoveField('expense', 'bank_old'),
    ]