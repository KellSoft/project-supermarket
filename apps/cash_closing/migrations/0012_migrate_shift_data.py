from django.db import migrations


def create_shifts_and_remap(apps, schema_editor):
    Shift = apps.get_model("cash_closing", "Shift")
    Income = apps.get_model("cash_closing", "Income")

    # Crea los dos turnos con los IDs originales (1 y 2)
    t1 = Shift.objects.create(id=1, name="Turno 1", order=1, is_active=True)
    t2 = Shift.objects.create(id=2, name="Turno 2", order=2, is_active=True)

    # Actualiza shift (entero) apuntando al objeto correcto
    # En este punto shift todavía es IntegerField, lo actualizamos directamente
    Income.objects.filter(shift=1).update(shift=t1.pk)
    Income.objects.filter(shift=2).update(shift=t2.pk)


def reverse_migration(apps, schema_editor):
    pass  # No reversible fácilmente


class Migration(migrations.Migration):
    dependencies = [
        ("cash_closing", "0011_create_shift_model"),
    ]

    operations = [
        migrations.RunPython(create_shifts_and_remap, reverse_migration),
    ]