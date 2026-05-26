from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Income, Expense, PaymentMethod


# ── Guardamos el estado anterior al guardar para detectar cambios ──

@receiver(pre_save, sender=Income)
def income_pre_save(sender, instance, **kwargs):
    """Guarda snapshot del registro anterior para poder revertir si se edita."""
    if instance.pk:
        try:
            instance._pre_save_instance = Income.objects.get(pk=instance.pk)
        except Income.DoesNotExist:
            instance._pre_save_instance = None
    else:
        instance._pre_save_instance = None


@receiver(pre_save, sender=Expense)
def expense_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._pre_save_instance = Expense.objects.get(pk=instance.pk)
        except Expense.DoesNotExist:
            instance._pre_save_instance = None
    else:
        instance._pre_save_instance = None


# ── Income signals ──

@receiver(post_save, sender=Income)
def income_update_bank(sender, instance, created, **kwargs):
    """
    Ingreso por consignación → suma al banco (requerimiento: solo Bancolombia recibe).
    Si se edita, revierte el efecto anterior y aplica el nuevo.
    """
    if created:
        # Registro nuevo: sumar si es consignación
        if instance.payment_method == PaymentMethod.DEPOSIT and instance.bank:
            instance.bank.current_balance += instance.amount
            instance.bank.save(update_fields=["current_balance"])
    else:
        prev = getattr(instance, "_pre_save_instance", None)
        if prev:
            # Revertir efecto anterior
            if prev.payment_method == PaymentMethod.DEPOSIT and prev.bank:
                prev.bank.current_balance -= prev.amount
                prev.bank.save(update_fields=["current_balance"])
            # Aplicar efecto nuevo
            if instance.payment_method == PaymentMethod.DEPOSIT and instance.bank:
                instance.bank.current_balance += instance.amount
                instance.bank.save(update_fields=["current_balance"])


@receiver(post_delete, sender=Income)
def income_delete_bank(sender, instance, **kwargs):
    """Al eliminar un ingreso por consignación, restar del banco."""
    if instance.payment_method == PaymentMethod.DEPOSIT and instance.bank:
        instance.bank.current_balance -= instance.amount
        instance.bank.save(update_fields=["current_balance"])


# ── Expense signals ──

@receiver(post_save, sender=Expense)
def expense_update_bank(sender, instance, created, **kwargs):
    """
    Egreso por consignación → resta del banco seleccionado.
    """
    if created:
        if instance.payment_method == PaymentMethod.DEPOSIT and instance.bank:
            instance.bank.current_balance -= instance.amount
            instance.bank.save(update_fields=["current_balance"])
    else:
        prev = getattr(instance, "_pre_save_instance", None)
        if prev:
            # Revertir efecto anterior
            if prev.payment_method == PaymentMethod.DEPOSIT and prev.bank:
                prev.bank.current_balance += prev.amount
                prev.bank.save(update_fields=["current_balance"])
            # Aplicar efecto nuevo
            if instance.payment_method == PaymentMethod.DEPOSIT and instance.bank:
                instance.bank.current_balance -= instance.amount
                instance.bank.save(update_fields=["current_balance"])


@receiver(post_delete, sender=Expense)
def expense_delete_bank(sender, instance, **kwargs):
    """Al eliminar un egreso por consignación, devolver al banco."""
    if instance.payment_method == PaymentMethod.DEPOSIT and instance.bank:
        instance.bank.current_balance += instance.amount
        instance.bank.save(update_fields=["current_balance"])