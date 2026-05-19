from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import date

from apps.purchases.models import Purchase
from apps.cash_closing.models import Income, CashExpense
from apps.businesses.models import Business


class ReportIndexView(View):
    def get(self, request):
        businesses = Business.objects.all()
        return render(request, 'reports/report_index.html', {'businesses': businesses})


class PurchaseReportView(View):
    def get(self, request):
        businesses = Business.objects.all()
        return render(request, 'reports/purchase_report_filters.html', {'businesses': businesses})

    def post(self, request):
        purchases = Purchase.objects.all()

        supplier = request.POST.get('supplier')
        product = request.POST.get('product')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if supplier:
            purchases = purchases.filter(supplier__icontains=supplier)
        if product:
            purchases = purchases.filter(product__icontains=product)
        if start_date and end_date:
            purchases = purchases.filter(purchase_date__range=[start_date, end_date])

        purchases = list(purchases)
        total = sum(p.amount for p in purchases)
        filter_label = _build_filter_label(supplier=supplier, product=product,
                                           start_date=start_date, end_date=end_date)

        html_string = render_to_string('reports/purchase_report.html', {
            'purchases': purchases,
            'filter_label': filter_label,
            'generated': date.today(),
            'total': total,
        })

        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_compras.pdf"'
        return response


class IncomeReportView(View):
    def get(self, request):
        businesses = Business.objects.all()
        return render(request, 'reports/report_index.html', {'businesses': businesses})

    def post(self, request):
        incomes = Income.objects.select_related('business').all()

        business_id = request.POST.get('business')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        business_name = 'Todos los negocios'

        if business_id:
            incomes = incomes.filter(business_id=business_id)
            try:
                business_name = Business.objects.get(pk=business_id).name
            except Business.DoesNotExist:
                pass

        if start_date and end_date:
            incomes = incomes.filter(date__range=[start_date, end_date])

        incomes = list(incomes)
        total = sum(i.amount for i in incomes)
        filter_label = _build_filter_label(business=business_name,
                                           start_date=start_date, end_date=end_date)

        html_string = render_to_string('reports/income_report.html', {
            'incomes': incomes,
            'filter_label': filter_label,
            'generated': date.today(),
            'total': total,
            'business_name': business_name,
        })

        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_ingresos.pdf"'
        return response


class ExpenseReportView(View):
    def get(self, request):
        businesses = Business.objects.all()
        return render(request, 'reports/report_index.html', {'businesses': businesses})

    def post(self, request):
        expenses = CashExpense.objects.select_related('business').all()

        business_id = request.POST.get('business')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        business_name = 'Todos los negocios'

        if business_id:
            expenses = expenses.filter(business_id=business_id)
            try:
                business_name = Business.objects.get(pk=business_id).name
            except Business.DoesNotExist:
                pass

        if start_date and end_date:
            expenses = expenses.filter(date__range=[start_date, end_date])

        expenses = list(expenses)
        total = sum(e.amount for e in expenses)
        filter_label = _build_filter_label(business=business_name,
                                           start_date=start_date, end_date=end_date)

        html_string = render_to_string('reports/expense_report.html', {
            'expenses': expenses,
            'filter_label': filter_label,
            'generated': date.today(),
            'total': total,
            'business_name': business_name,
        })

        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_egresos.pdf"'
        return response


def _build_filter_label(supplier=None, product=None, business=None,
                        start_date=None, end_date=None):
    parts = []
    if business and business != 'Todos los negocios':
        parts.append(f'Negocio: {business}')
    if supplier:
        parts.append(f'Proveedor: {supplier}')
    if product:
        parts.append(f'Producto: {product}')
    if start_date and end_date:
        parts.append(f'Período: {start_date} → {end_date}')
    return ' · '.join(parts) if parts else 'Todos los registros'