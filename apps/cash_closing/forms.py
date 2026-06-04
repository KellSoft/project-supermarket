from django import forms
from .models import (
    Income,
    Expense,
    PaymentMethod,
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
        self.fields["shift"].required = True
        self.fields["shift"].queryset = Shift.objects.filter(is_active=True)  # ← único cambio

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get("payment_method")
        bank = cleaned_data.get("bank")
        shift = cleaned_data.get("shift")

        if payment_method == PaymentMethod.DEPOSIT and not bank:
            self.add_error("bank", "El banco es obligatorio para consignaciones.")
        if payment_method == PaymentMethod.CASH and bank:
            cleaned_data["bank"] = None
        if not shift:
            self.add_error("shift", "El turno es obligatorio.")
        return cleaned_data

from .models import (
    Income, Expense, PaymentMethod, BankAccount,
    CashClosing, CashDenomination, Shift, Supplier,  # ← agrega Supplier
)

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
        self.fields["supplier"].queryset = Supplier.objects.all()  # ← agrega esto
        self.fields["supplier"].empty_label = "— Selecciona —"     # ← y esto

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("payment_method") == "cash":
            cleaned_data["bank"] = None
        return cleaned_data


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
