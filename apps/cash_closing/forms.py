from django import forms
from .models import (
    Income,
    Expense,
    PaymentMethod,
    ExpenseType,
    BankAccount,
    CashClosing,
    CashDenomination,
    Shift,
    Supplier,
)


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ["business", "amount", "person_name", "payment_method", "bank", "shift", "date"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["bank"].required = False
        self.fields["person_name"].required = False
        self.fields["shift"].required = True
        self.fields["shift"].queryset = Shift.objects.filter(is_active=True)
        self.fields["bank"].queryset = BankAccount.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get("payment_method")
        bank = cleaned_data.get("bank")

        if payment_method == PaymentMethod.DEPOSIT and not bank:
            self.add_error("bank", "El banco es obligatorio para consignaciones.")

        if payment_method == PaymentMethod.CASH:
            cleaned_data["bank"] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            "business", "date", "expense_type",
            "supplier", "invoice_number", "employee_name",
            "amount", "payment_method", "bank", "description",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

        for name in ("bank", "supplier", "invoice_number", "employee_name", "description"):
            self.fields[name].required = False

        self.fields["supplier"].queryset = Supplier.objects.all()
        self.fields["supplier"].empty_label = "— Selecciona —"
        self.fields["bank"].queryset = BankAccount.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        expense_type = cleaned_data.get("expense_type")
        payment_method = cleaned_data.get("payment_method")

        # ── Método de pago ───────────────────────────────────────────────────
        if payment_method == PaymentMethod.CASH:
            cleaned_data["bank"] = None
        elif payment_method == PaymentMethod.DEPOSIT:
            if not cleaned_data.get("bank"):
                self.add_error("bank", "El banco es obligatorio para consignaciones.")

        # ── Validaciones por tipo de egreso ──────────────────────────────────
        if expense_type == ExpenseType.PURCHASE:
            if not cleaned_data.get("supplier"):
                self.add_error("supplier", "El proveedor es obligatorio para compras.")
            cleaned_data["employee_name"] = None

        elif expense_type == ExpenseType.STAFF_PAYMENT:
            if not cleaned_data.get("employee_name", "").strip():
                self.add_error("employee_name", "Indica la persona a quien se le pagó.")
            cleaned_data["supplier"] = None
            cleaned_data["invoice_number"] = None

        else:
            cleaned_data["supplier"] = None
            cleaned_data["invoice_number"] = None
            cleaned_data["employee_name"] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
        return instance


class OpeningBalanceForm(forms.ModelForm):
    class Meta:
        model = CashClosing
        fields = ["opening_balance"]
        widgets = {
            "opening_balance": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0",
                    "min": "0",
                    "step": "1",
                }
            )
        }
        labels = {"opening_balance": "Saldo inicial de caja ($)"}


class CashClosingEditForm(forms.ModelForm):
    """
    Permite editar el saldo inicial y las notas
    en cualquier momento mientras el cuadre esté abierto.
    """

    class Meta:
        model = CashClosing
        fields = ["opening_balance", "notes"]
        widgets = {
            "opening_balance": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "min": "0",
                    "step": "1",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control form-control-sm",
                    "rows": 2,
                    "placeholder": "Observaciones del día...",
                }
            ),
        }
        labels = {
            "opening_balance": "Saldo inicial ($)",
            "notes": "Notas",
        }