from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.utils.timezone import localdate
from django.db.models import Sum
from apps.businesses.models import Business
from .models import BankChoices, Income, Expense
from .forms import IncomeForm, ExpenseForm


class BaseListView(ListView):
    paginate_by = None

    def get_filters(self):
        return {
            "date": self.request.GET.get("date", str(localdate())),
            "business": self.request.GET.get("business", ""),
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        filters = self.get_filters()
        ctx["selected_date"] = filters["date"]
        ctx["selected_business"] = filters["business"]
        ctx["businesses"] = Business.objects.all()
        return ctx


# ──────────────────────────────────────────
# INGRESOS
# ──────────────────────────────────────────


class IncomeListView(BaseListView):
    model = Income
    template_name = "cash_closing/income_list.html"
    context_object_name = "incomes"

    def get_queryset(self):
        filters = self.get_filters()
        qs = Income.objects.select_related("business").filter(date=filters["date"])
        if filters["business"]:
            qs = qs.filter(business_id=filters["business"])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        selected_date = ctx["selected_date"]
        ctx["total_income"] = (
            Income.objects.filter(date=selected_date).aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0
        )
        ctx["income_by_business"] = (
            Income.objects.filter(date=selected_date)
            .values("business__name")
            .annotate(total=Sum("amount"))
        )
        return ctx


class IncomeCreateView(View):
    def post(self, request):
        form = IncomeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ingreso registrado correctamente.")
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())
        return redirect("cash_closing:income-list")


# ──────────────────────────────────────────
# EGRESOS
# ──────────────────────────────────────────


class ExpenseListView(BaseListView):
    model = Expense
    template_name = "cash_closing/expense_list.html"
    context_object_name = "expenses"

    def get_queryset(self):
        filters = self.get_filters()
        qs = Expense.objects.select_related("business").filter(date=filters["date"])
        if filters["business"]:
            qs = qs.filter(business_id=filters["business"])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        selected_date = ctx["selected_date"]
        ctx["total_expense"] = (
            Expense.objects.filter(date=selected_date).aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0
        )
        ctx["expense_by_business"] = (
            Expense.objects.filter(date=selected_date)
            .values("business__name")
            .annotate(total=Sum("amount"))
        )
        return ctx


class ExpenseCreateView(View):
    def post(self, request):
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Egreso registrado correctamente.")
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())
        return redirect("cash_closing:expense-list")


class CashFlowView(View):
    template_name = "cash_closing/cash_flow.html"

    def _get_filters(self, request):
        return {
            "date": request.GET.get("date", str(localdate())),
            "business": request.GET.get("business", ""),
        }

    def get(self, request):
        filters = self._get_filters(request)
        date = filters["date"]
        biz = filters["business"]

        income_qs = Income.objects.select_related("business").filter(date=date)
        expense_qs = Expense.objects.select_related("business").filter(date=date)
        if biz:
            income_qs = income_qs.filter(business_id=biz)
            expense_qs = expense_qs.filter(business_id=biz)

        def agg(qs, method):
            return qs.filter(payment_method=method).aggregate(t=Sum("amount"))["t"] or 0

        total_income_cash = agg(income_qs, "cash")
        total_income_deposit = agg(income_qs, "deposit")
        total_expense_cash = agg(expense_qs, "cash")
        total_expense_deposit = agg(expense_qs, "deposit")
        total_income = total_income_cash + total_income_deposit
        total_expense = total_expense_cash + total_expense_deposit

        return render(
            request,
            self.template_name,
            {
                "incomes": income_qs,
                "expenses": expense_qs,
                "businesses": Business.objects.all(),
                "selected_date": date,
                "selected_business": biz,
                "bank_choices": BankChoices.choices,
                "total_income": total_income,
                "total_expense": total_expense,
                "total_income_cash": total_income_cash,
                "total_income_deposit": total_income_deposit,
                "total_expense_cash": total_expense_cash,
                "total_expense_deposit": total_expense_deposit,
                "net_balance": total_income - total_expense,
                "active_tab": request.GET.get("tab", "income"),
            },
        )

    def post(self, request):
        kind = request.POST.get("_kind")
        form = (
            IncomeForm(request.POST) if kind == "income" else ExpenseForm(request.POST)
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Ingreso registrado." if kind == "income" else "Egreso registrado.",
            )
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())

        date = request.POST.get("date", str(localdate()))
        biz = request.POST.get("_business_filter", "")
        tab = kind if kind in ("income", "expense") else "income"
        qs = f"?date={date}&tab={tab}" + (f"&business={biz}" if biz else "")
        url = reverse("cash_closing:cash-flow")
        url += f"?date={date}&tab={tab}"
        if biz:
            url += f"&business={biz}"
        return HttpResponseRedirect(url)


class IncomeDeleteView(View):
    def post(self, request, pk):
        get_object_or_404(Income, pk=pk).delete()
        messages.success(request, "Ingreso eliminado.")
        url = reverse("cash_closing:cash-flow")
        date = request.POST.get("date", str(localdate()))
        return HttpResponseRedirect(f"{url}?date={date}&tab=income")


class ExpenseDeleteView(View):
    def post(self, request, pk):
        get_object_or_404(Expense, pk=pk).delete()
        messages.success(request, "Egreso eliminado.")
        url = reverse("cash_closing:cash-flow")
        date = request.POST.get("date", str(localdate()))
        return HttpResponseRedirect(f"{url}?date={date}&tab=expense")
