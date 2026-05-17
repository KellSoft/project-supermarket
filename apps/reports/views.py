from django.shortcuts import render

from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import date

from apps.purchases.models import Purchase


class PurchaseReportView(View):

    def get(self, request):
        return render(request, 'reports/purchase_report_filters.html')

    def post(self, request):
        purchases = Purchase.objects.all()

        supplier = request.POST.get('supplier')
        if supplier:
            purchases = purchases.filter(supplier__icontains=supplier)

        product = request.POST.get('product')
        if product:
            purchases = purchases.filter(product__icontains=product)

        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if start_date and end_date:
            purchases = purchases.filter(
                purchase_date__range=[start_date, end_date]
            )

        filter_label = _build_filter_label(supplier, product, start_date, end_date)

        purchases = list(purchases)
        total = sum(p.amount for p in purchases)

        html_string = render_to_string(
            'reports/purchase_report.html',
            {
                'purchases': purchases,
                'filter_label': filter_label,
                'generated': date.today(),
                'total': total,
            }
        )

        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="compras.pdf"'
        return response


def _build_filter_label(supplier, product, start_date, end_date):
    parts = []
    if supplier:
        parts.append(f'Proveedor: {supplier}')
    if product:
        parts.append(f'Producto: {product}')
    if start_date and end_date:
        parts.append(f'Período: {start_date} → {end_date}')
    return ' · '.join(parts) if parts else 'Todos los registros'