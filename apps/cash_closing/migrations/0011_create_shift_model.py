from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("cash_closing", "0010_alter_bankaccount_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Shift",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("name", models.CharField(max_length=50, verbose_name="Nombre del turno")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="Orden")),
                ("is_active", models.BooleanField(default=True, verbose_name="Activo")),
            ],
            options={
                "verbose_name": "Turno",
                "verbose_name_plural": "Turnos",
                "ordering": ["order", "name"],
            },
        ),
    ]