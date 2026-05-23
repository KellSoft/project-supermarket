from django.views import View
from django.views.generic import ListView
from django.db.models import Q
from django.shortcuts import redirect, render

from .models import Purchase
from .forms import PurchaseForm


class PurchaseListView(ListView):
    model = Purchase
    template_name = "purchases/purchases_list.html"
    context_object_name = "purchases"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if query:
            queryset = queryset.filter(
                Q(invoice_number__icontains=query)
                | Q(product__icontains=query)
                | Q(supplier__icontains=query)
            )

        if start_date and end_date:
            queryset = queryset.filter(purchase_date__range=[start_date, end_date])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = PurchaseForm()
        return context


class PurchaseCreateView(View):
    template_name = "purchases/purchases_list.html"

    def get(self, request):
        form = PurchaseForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = PurchaseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("purchases:purchase_list")
        return render(request, self.template_name, {"form": form})
