from django import forms
from .models import CashExpense, Income
from apps.businesses.models import Business


class IncomeForm(forms.ModelForm):
    business = forms.ModelChoiceField(
        queryset=Business.objects.all(),
        empty_label="— Selecciona negocio —",
        label="Negocio",
    )
    amount = forms.DecimalField(
        min_value=0, label="Valor", widget=forms.NumberInput(attrs={"placeholder": "0"})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), label="Fecha"
    )

    class Meta:
        model = Income
        fields = ["business", "amount", "date"]


class CashExpenseForm(forms.ModelForm):
    business = forms.ModelChoiceField(
        queryset=Business.objects.all(), empty_label="— Selecciona —", label="Negocio"
    )
    supplier = forms.CharField(
        label="Proveedor",
        widget=forms.TextInput(attrs={"placeholder": "Nombre proveedor"}),
    )
    invoice_number = forms.CharField(
        label="N° factura",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "0000"}),
    )
    amount = forms.DecimalField(
        min_value=0, label="Monto", widget=forms.NumberInput(attrs={"placeholder": "0"})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), label="Fecha"
    )

    class Meta:
        model = CashExpense
        fields = ["business", "supplier", "invoice_number", "amount", "date"]
