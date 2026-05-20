from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel
from apps.businesses.models import Business


class BankChoices(models.TextChoices):
    AGRARIO = "agrario", "Banco Agrario"
    BANCOLOMBIA = "bancolombia", "Bancolombia"
    BOGOTA = "bogota", "Banco de Bogotá"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Efectivo"
    DEPOSIT = "deposit", "Consignación"


class Income(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.PROTECT,
        related_name="incomes",
        verbose_name="Negocio",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        verbose_name="Método de pago",
    )
    bank = models.CharField(
        max_length=30,
        choices=BankChoices.choices,
        blank=True,
        null=True,
        verbose_name="Banco",
    )
    date = models.DateField(verbose_name="Fecha")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Ingreso"
        verbose_name_plural = "Ingresos"

    def clean(self):
        if self.payment_method == PaymentMethod.DEPOSIT and not self.bank:
            raise ValidationError(
                {"bank": "El banco es obligatorio para ingresos por consignación."}
            )
        if self.payment_method == PaymentMethod.CASH and self.bank:
            raise ValidationError(
                {"bank": "Un ingreso en efectivo no debe tener banco asociado."}
            )

    def __str__(self):
        return f"{self.date} | {self.business} | {self.get_payment_method_display()} | ${self.amount:,.0f}"


class Expense(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.PROTECT,
        related_name="expenses",
        verbose_name="Negocio",
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        verbose_name="Método de pago",
    )
    supplier = models.CharField(max_length=200, verbose_name="Proveedor")
    invoice_number = models.CharField(max_length=100, verbose_name="N° Factura")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Monto",
    )
    date = models.DateField(verbose_name="Fecha")
    bank = models.CharField(
        max_length=30,
        choices=BankChoices.choices,
        blank=True,
        null=True,
        verbose_name="Banco",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Egreso"
        verbose_name_plural = "Egresos"

    def clean(self):
        if self.payment_method == PaymentMethod.DEPOSIT and not self.bank:
            raise ValidationError(
                {"bank": "El banco es obligatorio para egresos por consignación."}
            )
        if self.payment_method == PaymentMethod.CASH and self.bank:
            raise ValidationError(
                {"bank": "Un egreso en efectivo no debe tener banco asociado."}
            )

    def __str__(self):
        return f"{self.date} | {self.business} | {self.supplier} | ${self.amount:,.0f}"
