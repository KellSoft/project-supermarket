from django.contrib import admin
from .models import Purchase

@admin.register(Purchase)
class PutchaseAdmin(admin.ModelAdmin):
    
    list_display = (
        'invoice_number',
        'purchase_date',
        'product',
        'supplier',
        'amount'
    )

    search_fields = (
        'invoice_number',
        'product',
        'supplier',
    )
    
    list_filter = (
        'purchase_date',
        'supplier',
    )