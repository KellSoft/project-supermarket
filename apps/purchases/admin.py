from django.contrib import admin
from django.utils.html import format_html
from apps.purchases.models import Purchase


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'purchase_date', 'product', 'supplier', 'amount_display', 'created_at')
    search_fields = ('invoice_number', 'product', 'supplier')
    list_filter = ('purchase_date', 'supplier')
    date_hierarchy = 'purchase_date'
    ordering = ('-purchase_date',)
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Información de la factura', {'fields': ('invoice_number', 'purchase_date')}),
        ('Producto', {'fields': ('product', 'supplier', 'amount')}),
        ('Auditoría', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    def amount_display(self, obj):
        return format_html('<span style="color:#c8421a;font-weight:600">${}</span>', f'{float(obj.amount):,.0f}')
    amount_display.short_description = 'Monto'
    amount_display.admin_order_field = 'amount'