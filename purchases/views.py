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
        current_month = date.today().month
        purchases = Purchase.objects.filter(
            purchase_date__month=current_month
        )
        html_string = render_to_string(
            'purchases/purchase_pdf.html', {'purchases': purchases}
        )
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'filename="compras.pdf"'
        return response