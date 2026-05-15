from django import forms
from .models import Purchase

class PurchaseForm(forms.ModelForm):
    
    class Meta:
        model = Purchase
        
        fields = [
            'invoice_number',
            'purchase_date',
            'product',
            'supplier',
            'amount'
        ]
        
        widgets = {
            'purchase_date':forms.DateInput(
                attrs = {'type' : 'date'}
            )
        }