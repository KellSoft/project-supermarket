from django.db import models
from apps.core.models import TimeStampedModel
from apps.businesses.models import Business
from django.db import models
from apps.businesses.models import Business


class Income(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.PROTECT,
        related_name="incomes",
        verbose_name="Negocio",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    date = models.DateField(verbose_name="Fecha")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Ingreso"
        verbose_name_plural = "Ingresos"

    def __str__(self):
        return f"{self.date} | {self.business} | ${self.amount:,.0f}"


class CashExpense(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.PROTECT,
        related_name="cash_expenses",
        verbose_name="Negocio",
    )
    supplier = models.CharField(max_length=200, verbose_name="Proveedor")
    invoice_number = models.CharField(max_length=100, verbose_name="N° factura")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    date = models.DateField(verbose_name="Fecha")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Egreso efectivo"
        verbose_name_plural = "Egresos efectivo"

    def __str__(self):
        return f"{self.date} | {self.business} | {self.supplier} | ${self.amount:,.0f}"
