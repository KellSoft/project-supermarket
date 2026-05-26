import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cash_closing', '0005_income_person_name'),
    ]

    operations = [
        # 1. Crear el modelo BankAccount
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre del banco')),
                ('slug', models.SlugField(unique=True)),
                ('initial_balance', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Saldo inicial')),
                ('current_balance', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Saldo actual')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('receives_transfers', models.BooleanField(default=False, verbose_name='Recibe transferencias de ingresos')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Cuenta bancaria',
                'verbose_name_plural': 'Cuentas bancarias',
                'ordering': ['name'],
            },
        ),

        # 2. Renombrar bank → bank_old en Income y Expense (conservar datos)
        migrations.RenameField('income',  'bank', 'bank_old'),
        migrations.RenameField('expense', 'bank', 'bank_old'),

        # 3. Agregar el nuevo campo bank como FK (null por ahora)
        migrations.AddField(
            model_name='income',
            name='bank',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='incomes',
                to='cash_closing.bankaccount',
                verbose_name='Banco',
            ),
        ),
        migrations.AddField(
            model_name='expense',
            name='bank',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='expenses',
                to='cash_closing.bankaccount',
                verbose_name='Banco',
            ),
        ),
    ]