from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.core.models import TimeStampedModel
from apps.businesses.models import Business


class BankChoices(models.TextChoices):
    AGRARIO = "agrario", "Banco Agrario"
    BANCOLOMBIA = "bancolombia", "Bancolombia"
    BOGOTA = "bogota", "Banco de Bogotá"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Efectivo"
    DEPOSIT = "deposit", "Consignación"


class Shift(models.IntegerChoices):
    SHIFT_1 = 1, "Turno 1"
    SHIFT_2 = 2, "Turno 2"


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
    shift = models.IntegerField(
        choices=Shift.choices,
        verbose_name="Turno",
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


class CashClosing(TimeStampedModel):
    date = models.DateField(
        unique=True,
        verbose_name="Fecha",
    )
    opening_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Saldo inicial",
    )
    physical_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Efectivo contado",
    )
    is_closed = models.BooleanField(
        default=False,
        verbose_name="Cerrado",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notas",
    )

    class Meta:
        ordering = ["-date"]
        verbose_name = "Cuadre de caja"
        verbose_name_plural = "Cuadres de caja"

    # ── Apertura automática ───────────────────────────────────────────────

    @classmethod
    def get_or_create_for_today(cls):
        """
        Retorna (closing, created).
        Si se crea nuevo, toma el opening_balance del último cuadre cerrado.
        Si no existe ninguno, lo deja en 0 y la vista muestra el campo editable.
        """
        from django.utils.timezone import localdate

        today = localdate()
        closing, created = cls.objects.get_or_create(date=today)
        if created:
            prev = (
                cls.objects.filter(date__lt=today, is_closed=True)
                .order_by("-date")
                .first()
            )
            if prev:
                closing.opening_balance = prev.physical_cash
                closing.save(update_fields=["opening_balance"])
        return closing, created

    @classmethod
    def has_previous_closing(cls, closing):
        """True si existe al menos un cuadre cerrado anterior a este."""
        return cls.objects.filter(
            date__lt=closing.date,
            is_closed=True,
        ).exists()

    # ── Propiedades financieras ───────────────────────────────────────────

    @property
    def total_income_cash(self):
        return Income.objects.filter(
            date=self.date, payment_method=PaymentMethod.CASH
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    @property
    def total_expense_cash(self):
        return Expense.objects.filter(
            date=self.date, payment_method=PaymentMethod.CASH
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    @property
    def expected_cash(self):
        return self.opening_balance + self.total_income_cash - self.total_expense_cash

    @property
    def difference(self):
        return self.physical_cash - self.expected_cash

    # ── Acciones ──────────────────────────────────────────────────────────

    def recalculate_physical_cash(self):
        """Suma value × quantity de todas las denominaciones y actualiza physical_cash."""
        total = self.denominations.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("value") * F("quantity"),
                    output_field=DecimalField(),
                )
            )
        )["total"] or Decimal("0")
        self.physical_cash = total
        self.save(update_fields=["physical_cash"])
        return self.physical_cash

    def close(self):
        """Recalcula, marca como cerrado y guarda."""
        self.recalculate_physical_cash()
        self.is_closed = True
        self.save(update_fields=["physical_cash", "is_closed"])

    def __str__(self):
        estado = "Cerrado" if self.is_closed else "Abierto"
        return f"Cuadre {self.date} | {estado} | ${self.physical_cash:,.0f}"


# ──────────────────────────────────────────────────────────────────────────────
# CashDenomination — conteo de billetes y monedas
# ──────────────────────────────────────────────────────────────────────────────


class CashDenomination(models.Model):
    DENOMINATIONS = [
        (100000, "$100.000"),
        (50000, "$50.000"),
        (20000, "$20.000"),
        (10000, "$10.000"),
        (5000, "$5.000"),
        (2000, "$2.000"),
        (1000, "$1.000"),
        (500, "$500"),
        (200, "$200"),
        (100, "$100"),
        (50, "$50"),
    ]

    BILLS = {100000, 50000, 20000, 10000, 5000, 2000, 1000}
    COINS = {500, 200, 100, 50}

    closing = models.ForeignKey(
        CashClosing,
        on_delete=models.CASCADE,
        related_name="denominations",
    )
    value = models.IntegerField(choices=DENOMINATIONS, verbose_name="Denominación")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Cantidad")

    class Meta:
        unique_together = ("closing", "value")
        ordering = ["-value"]
        verbose_name = "Denominación"
        verbose_name_plural = "Denominaciones"

    @property
    def subtotal(self):
        return self.value * self.quantity

    @property
    def is_bill(self):
        return self.value in self.BILLS

    def __str__(self):
        return f"${self.value:,} × {self.quantity} = ${self.subtotal:,}"
