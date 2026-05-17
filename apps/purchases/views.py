from django.views import View
from django.views.generic import ListView
from django.db.models import Q
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import date

from .models import Purchase
from .forms import PurchaseForm


class PurchaseListView(ListView):
    model = Purchase
    template_name = 'purchases/purchases_list.html'
    context_object_name = 'purchases'

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if query:
            queryset = queryset.filter(
                Q(invoice_number__icontains=query) |
                Q(product__icontains=query) |
                Q(supplier__icontains=query)
            )

        if start_date and end_date:
            queryset = queryset.filter(
                purchase_date__range=[start_date, end_date]
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PurchaseForm()
        return context


class PurchaseCreateView(View):
    template_name = 'purchases/purchases_list.html'

    def get(self, request):
        form = PurchaseForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PurchaseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('purchases:purchase_list')
        return render(request, self.template_name, {'form': form})


class PurchasePDFView(View):

    def get(self, request):
        return render(request, 'purchases/purchases_pdf_filters.html')

    def post(self, request):
        purchases = Purchase.objects.all()

        # Filtro por proveedor
        supplier = request.POST.get('supplier')
        if supplier:
            purchases = purchases.filter(supplier__icontains=supplier)

        # Filtro por producto
        product = request.POST.get('product')
        if product:
            purchases = purchases.filter(product__icontains=product)

        # Filtro por rango de fechas
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if start_date and end_date:
            purchases = purchases.filter(
                purchase_date__range=[start_date, end_date]
            )

        # Etiqueta legible del filtro aplicado
        filter_label = _build_filter_label(supplier, product, start_date, end_date)

        # Convertir a lista para poder iterar dos veces (total + template)
        purchases = list(purchases)
        total = sum(p.amount for p in purchases)

        html_string = render_to_string(
            'purchases/purchases_pdf.html',
            {
                'purchases': purchases,
                'filter_label': filter_label,
                'generated': date.today(),
                'total': total,
            }
        )

        html = HTML(string=html_string)
        pdf = html.write_pdf()

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