from django.contrib import admin
from apps.purchases.models import Purchase

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    
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