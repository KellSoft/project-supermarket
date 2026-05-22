from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from apps.businesses.models import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_ingresos', 'total_egresos', 'balance')
    search_fields = ('name',)

    def total_ingresos(self, obj):
        total = float(obj.incomes.aggregate(t=Sum('amount'))['t'] or 0)
        return format_html('<span style="color:#1a7c4a;font-weight:600">${}</span>', f'{total:,.0f}')
    total_ingresos.short_description = 'Total ingresos'

    def total_egresos(self, obj):
        total = float(obj.expenses.aggregate(t=Sum('amount'))['t'] or 0)
        return format_html('<span style="color:#c8421a;font-weight:600">${}</span>', f'{total:,.0f}')
    total_egresos.short_description = 'Total egresos'

    def balance(self, obj):
        ing = float(obj.incomes.aggregate(t=Sum('amount'))['t'] or 0)
        egr = float(obj.expenses.aggregate(t=Sum('amount'))['t'] or 0)
        bal = ing - egr
        color = '#1a7c4a' if bal >= 0 else '#c8421a'
        return format_html('<span style="color:{};font-weight:700">${}</span>', color, f'{bal:,.0f}')
    balance.short_description = 'Balance'