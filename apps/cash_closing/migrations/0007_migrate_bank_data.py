from django.db import migrations


def create_banks_and_migrate(apps, schema_editor):
    BankAccount = apps.get_model('cash_closing', 'BankAccount')
    Income      = apps.get_model('cash_closing', 'Income')
    Expense     = apps.get_model('cash_closing', 'Expense')

    banks = {
        'bancolombia': BankAccount.objects.create(
            name='Bancolombia', slug='bancolombia',
            initial_balance=0, current_balance=0, receives_transfers=True
        ),
        'agrario': BankAccount.objects.create(
            name='Banco Agrario', slug='agrario',
            initial_balance=0, current_balance=0
        ),
        'bogota': BankAccount.objects.create(
            name='Banco de Bogotá', slug='bogota',
            initial_balance=0, current_balance=0
        ),
    }

    for income in Income.objects.exclude(bank_old='').exclude(bank_old__isnull=True):
        income.bank = banks.get(income.bank_old)
        income.save(update_fields=['bank'])

    for expense in Expense.objects.exclude(bank_old='').exclude(bank_old__isnull=True):
        expense.bank = banks.get(expense.bank_old)
        expense.save(update_fields=['bank'])


class Migration(migrations.Migration):
    dependencies = [
        ('cash_closing', '0006_bankaccount_alter_expense_bank_alter_income_bank'),
    ]
    operations = [
        migrations.RunPython(create_banks_and_migrate, migrations.RunPython.noop),
    ]