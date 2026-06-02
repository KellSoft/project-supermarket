from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.core.models import TimeStampedModel
from apps.businesses.models import Business


class ExpenseType(models.TextChoices):
    PURCHASE = "purchase", "Compra"
    GENERAL_EXPENSE = "general_expense", "Gasto externo / retiro efectivo"
    STAFF_PAYMENT = "staff_payment", "Pago a personal"
    OTHER = "other", "Otros"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Efectivo"
    DEPOSIT = "deposit", "Consignación"


class Shift(models.Model):
    name = models.CharField(max_length=50, verbose_name="Nombre del turno")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"

    def __str__(self):
        return self.name


# ──────────────────────────────────────────────────────────────────────────────
# BankAccount — cuentas bancarias reales del negocio
# ──────────────────────────────────────────────────────────────────────────────

class BankAccount(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre del banco")
    slug = models.SlugField(
        max_length=50, unique=True,
        help_text="Identificador único, ej: bancolombia, agrario, bogota"
    )
    initial_balance = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0"),
        verbose_name="Saldo inicial"
    )
    current_balance = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0"),
        verbose_name="Saldo actual"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    receives_transfers = models.BooleanField(
        default=False,
        verbose_name="Recibe transferencias de ingresos",
        help_text="Solo esta cuenta aumenta cuando hay ingresos por consignación"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Cuenta bancaria"
        verbose_name_plural = "Cuentas bancarias"

    def recalculate(self):
        """Recalcula current_balance desde cero: inicial + ingresos consignación - egresos consignación."""
        ingresos = self.incomes.filter(
            payment_method=PaymentMethod.DEPOSIT
        ).aggregate(t=Sum("amount"))["t"] or Decimal("0")
        egresos = self.expenses.filter(
            payment_method=PaymentMethod.DEPOSIT
        ).aggregate(t=Sum("amount"))["t"] or Decimal("0")
        self.current_balance = self.initial_balance + ingresos - egresos
        self.save(update_fields=["current_balance"])

    def __str__(self):
        return f"{self.name} — ${self.current_balance:,.0f}"


# ──────────────────────────────────────────────────────────────────────────────
# Income
# ──────────────────────────────────────────────────────────────────────────────

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
    bank = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="incomes",
        verbose_name="Banco",
    )
    shift = models.ForeignKey(
        "Shift",
        on_delete=models.PROTECT,
        verbose_name="Turno",
    )
    person_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Persona que ingresó",
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


# ──────────────────────────────────────────────────────────────────────────────
# Expense
# ──────────────────────────────────────────────────────────────────────────────

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
    supplier = models.CharField(
        max_length=200, verbose_name="Proveedor", null=True, blank=True
    )
    invoice_number = models.CharField(
        max_length=100, verbose_name="N° Factura", null=True, blank=True
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Monto",
    )
    date = models.DateField(verbose_name="Fecha")
    bank = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="expenses",
        verbose_name="Banco",
    )
    expense_type = models.CharField(
        max_length=30,
        choices=ExpenseType.choices,
        default=ExpenseType.GENERAL_EXPENSE,
        verbose_name="Tipo de egreso",
    )
    employee_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Persona pagada",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Egreso"
        verbose_name_plural = "Egresos"

    def clean(self):
        if self.employee_name:
            self.employee_name = self.employee_name.strip()
        if self.supplier:
            self.supplier = self.supplier.strip()
        if self.invoice_number:
            self.invoice_number = self.invoice_number.strip()
        if self.description:
            self.description = self.description.strip()

        if self.payment_method == PaymentMethod.DEPOSIT and not self.bank:
            raise ValidationError(
                {"bank": "El banco es obligatorio para consignaciones."}
            )
        if self.payment_method == PaymentMethod.CASH and self.bank:
            raise ValidationError(
                {"bank": "Un movimiento en efectivo no debe tener banco."}
            )

        if self.expense_type == ExpenseType.PURCHASE:
            if not self.supplier:
                raise ValidationError({"supplier": "El proveedor es obligatorio."})
            if not self.invoice_number:
                raise ValidationError({"invoice_number": "La factura es obligatoria."})
        else:
            self.supplier = None
            self.invoice_number = None

        if self.expense_type == ExpenseType.STAFF_PAYMENT and not self.employee_name:
            raise ValidationError({"employee_name": "Debe indicar la persona."})
        if self.expense_type != ExpenseType.STAFF_PAYMENT:
            self.employee_name = None

    def __str__(self):
        return (
            f"{self.date} | "
            f"{self.get_expense_type_display()} | "
            f"${self.amount:,.0f}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# CashClosing
# ──────────────────────────────────────────────────────────────────────────────

class CashClosing(TimeStampedModel):
    date = models.DateField(unique=True, verbose_name="Fecha")
    opening_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0"),
        verbose_name="Saldo inicial",
    )
    physical_cash = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0"),
        verbose_name="Efectivo contado",
    )
    is_closed = models.BooleanField(default=False, verbose_name="Cerrado")
    notes = models.TextField(blank=True, verbose_name="Notas")

    class Meta:
        ordering = ["-date"]
        verbose_name = "Cuadre de caja"
        verbose_name_plural = "Cuadres de caja"

    @classmethod
    def get_or_create_for_today(cls):
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
        return cls.objects.filter(date__lt=closing.date, is_closed=True).exists()

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

    def recalculate_physical_cash(self):
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
        self.recalculate_physical_cash()
        self.is_closed = True
        self.save(update_fields=["physical_cash", "is_closed"])

    def __str__(self):
        estado = "Cerrado" if self.is_closed else "Abierto"
        return f"Cuadre {self.date} | {estado} | ${self.physical_cash:,.0f}"


# ──────────────────────────────────────────────────────────────────────────────
# CashDenomination
# ──────────────────────────────────────────────────────────────────────────────

class CashDenomination(models.Model):
    DENOMINATIONS = [
        (100000, "$100.000"),
        (50000,  "$50.000"),
        (20000,  "$20.000"),
        (10000,  "$10.000"),
        (5000,   "$5.000"),
        (2000,   "$2.000"),
        (1000,   "$1.000"),
        (500,    "$500"),
        (200,    "$200"),
        (100,    "$100"),
        (50,     "$50"),
    ]

    BILLS = {100000, 50000, 20000, 10000, 5000, 2000, 1000}
    COINS = {500, 200, 100, 50}

    closing = models.ForeignKey(
        CashClosing, on_delete=models.CASCADE, related_name="denominations",
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
