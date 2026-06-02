from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("cash_closing", "0012_migrate_shift_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="income",
            name="shift",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="cash_closing.shift",
                verbose_name="Turno",
            ),
        ),
    ]