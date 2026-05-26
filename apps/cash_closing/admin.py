from django.contrib import admin
from django.utils.html import format_html
from apps.cash_closing.models import Income, Expense, BankAccount


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('date', 'business', 'amount_display', 'method_display', 'bank', 'shift', 'created_at')
    search_fields = ('business__name',)
    list_filter = ('date', 'business', 'payment_method', 'bank', 'shift')
    date_hierarchy = 'date'
    ordering = ('-date', '-created_at')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Información general', {'fields': ('business', 'date', 'shift')}),
        ('Pago', {'fields': ('amount', 'payment_method', 'bank')}),
        ('Auditoría', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    def amount_display(self, obj):
        return format_html('<span style="color:#1a7c4a;font-weight:600">${}</span>', f'{float(obj.amount):,.0f}')
    amount_display.short_description = 'Valor'
    amount_display.admin_order_field = 'amount'

    def method_display(self, obj):
        if obj.payment_method == 'cash':
            color, bg = '#a06b00', '#fdf8ec'
        else:
            color, bg = '#14213D', '#eef1fb'
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:4px;font-size:0.8em;font-weight:600">{}</span>',
            bg, color, obj.get_payment_method_display()
        )
    method_display.short_description = 'Método'
    method_display.admin_order_field = 'payment_method'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'business', 'supplier', 'invoice_number', 'amount_display', 'method_display', 'bank', 'created_at')
    search_fields = ('business__name', 'supplier', 'invoice_number')
    list_filter = ('date', 'business', 'payment_method', 'bank')
    date_hierarchy = 'date'
    ordering = ('-date', '-created_at')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Información general', {'fields': ('business', 'date')}),
        ('Proveedor', {'fields': ('supplier', 'invoice_number')}),
        ('Pago', {'fields': ('amount', 'payment_method', 'bank')}),
        ('Auditoría', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    def amount_display(self, obj):
        return format_html('<span style="color:#c8421a;font-weight:600">${}</span>', f'{float(obj.amount):,.0f}')
    amount_display.short_description = 'Monto'
    amount_display.admin_order_field = 'amount'

    def method_display(self, obj):
        if obj.payment_method == 'cash':
            color, bg = '#a06b00', '#fdf8ec'
        else:
            color, bg = '#14213D', '#eef1fb'
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:4px;font-size:0.8em;font-weight:600">{}</span>',
            bg, color, obj.get_payment_method_display()
        )
    method_display.short_description = 'Método'
    method_display.admin_order_field = 'payment_method'

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'initial_balance', 'current_balance', 'receives_transfers', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['current_balance']