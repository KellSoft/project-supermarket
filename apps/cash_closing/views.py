from django.views.generic import ListView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Sum
from django.utils import timezone

from .models import CashExpense, Income
from .forms import CashExpenseForm, IncomeForm
from apps.businesses.models import Business


class IncomeListView(ListView):
    model = Income
    template_name = "cash_closing/income_list.html"
    context_object_name = "incomes"

    def get_queryset(self):
        date = self._get_selected_date()
        business = self.request.GET.get("business", "")
        qs = Income.objects.filter(date=date).select_related("business")
        if business:
            qs = qs.filter(business_id=business)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        date = self._get_selected_date()
        businesses = Business.objects.all()

        # Totales por negocio siempre sobre el día completo (sin filtro de negocio)
        full_qs = Income.objects.filter(date=date)

        ctx["businesses"] = businesses
        ctx["total_income"] = full_qs.aggregate(total=Sum("amount"))["total"] or 0
        ctx["income_by_business"] = [
            {
                "business": b,
                "total": full_qs.filter(business=b).aggregate(total=Sum("amount"))[
                    "total"
                ]
                or 0,
            }
            for b in businesses
        ]
        ctx["form"] = IncomeForm(initial={"date": date})
        ctx["selected_date"] = date
        ctx["selected_business"] = self.request.GET.get("business", "")
        return ctx

    def _get_selected_date(self):
        return self.request.GET.get("date", str(timezone.localdate()))


class IncomeCreateView(CreateView):
    model = Income
    form_class = IncomeForm
    success_url = reverse_lazy("cash_closing:income_list")

    def form_valid(self, form):
        messages.success(self.request, "Ingreso registrado correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al guardar. Revisa los campos.")
        return redirect(self.success_url)


class IncomeDeleteView(DeleteView):
    model = Income
    success_url = reverse_lazy("income_list")

    def post(self, request, *args, **kwargs):
        messages.success(request, "Ingreso eliminado.")
        return super().post(request, *args, **kwargs)


class CashExpenseListView(ListView):
    model = CashExpense
    template_name = "cash_closing/expense_list.html"
    context_object_name = "expenses"

    def get_queryset(self):
        date = self._get_selected_date()
        business = self.request.GET.get("business", "")
        qs = CashExpense.objects.filter(date=date).select_related("business")
        if business:
            qs = qs.filter(business_id=business)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        date = self._get_selected_date()
        businesses = Business.objects.all()
        full_qs = CashExpense.objects.filter(date=date)

        ctx["businesses"] = businesses
        ctx["total_expense"] = full_qs.aggregate(total=Sum("amount"))["total"] or 0
        ctx["expense_by_business"] = [
            {
                "business": b,
                "total": full_qs.filter(business=b).aggregate(total=Sum("amount"))[
                    "total"
                ]
                or 0,
            }
            for b in businesses
        ]
        ctx["form"] = CashExpenseForm(initial={"date": date})
        ctx["selected_date"] = date
        ctx["selected_business"] = self.request.GET.get("business", "")
        return ctx

    def _get_selected_date(self):
        return self.request.GET.get("date", str(timezone.localdate()))


class CashExpenseCreateView(CreateView):
    model = CashExpense
    form_class = CashExpenseForm
    success_url = reverse_lazy("cash_closing:expense_list")

    def form_valid(self, form):
        messages.success(self.request, "Egreso registrado correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al guardar. Revisa los campos.")
        return redirect(self.success_url)


class CashExpenseDeleteView(DeleteView):
    model = CashExpense
    success_url = reverse_lazy("cash_closing:expense_list")

    def post(self, request, *args, **kwargs):
        messages.success(request, "Egreso eliminado.")
        return super().post(request, *args, **kwargs)
