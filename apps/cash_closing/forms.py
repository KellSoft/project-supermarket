from django import forms
from .models import Income
from apps.businesses.models import Business


class IncomeForm(forms.ModelForm):
    business = forms.ModelChoiceField(
        queryset=Business.objects.all(),
        empty_label="— Selecciona negocio —",
        label="Negocio"
    )
    amount = forms.DecimalField(
        min_value=0,
        label="Valor",
        widget=forms.NumberInput(attrs={'placeholder': '0'})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Fecha"
    )

    class Meta:
        model  = Income
        fields = ['business', 'amount', 'date']