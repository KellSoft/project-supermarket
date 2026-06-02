from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.utils.timezone import localdate
from django.db.models import Sum
from apps.businesses.models import Business
from .models import CashClosing, CashDenomination, Income, Expense, BankAccount, ExpenseType, Shift
from .forms import ExpenseForm, IncomeForm, OpeningBalanceForm, CashClosingEditForm


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
                "bank_accounts": BankAccount.objects.filter(is_active=True),
                "shifts": Shift.objects.filter(is_active=True),
                "expense_type_choices": ExpenseType.choices,
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




def _build_denominations(closing):
    saved = {d.value: d.quantity for d in closing.denominations.all()}
    rows = []
    for value, label in CashDenomination.DENOMINATIONS:
        qty = saved.get(value, 0)
        rows.append({
            "value":    value,
            "label":    label,
            "quantity": qty,
            "subtotal": value * qty,
            "is_bill":  value in CashDenomination.BILLS,
        })
    return rows
 
 
def _closing_context(closing):
    """Contexto financiero completo para el template del cuadre."""
    return {
        "closing":               closing,
        "is_first":              not CashClosing.has_previous_closing(closing),
        "opening_form":          OpeningBalanceForm(instance=closing),
        "edit_form":             CashClosingEditForm(instance=closing),
        "denominations":         _build_denominations(closing),
        "total_income_cash":     closing.total_income_cash,
        "total_expense_cash":    closing.total_expense_cash,
        "expected_cash":         closing.expected_cash,
        "difference":            closing.difference,
    }
 
 
class CashClosingView(View):
    template_name = "cash_closing/cash_closing.html"
 
    def get(self, request):
        closing, _ = CashClosing.get_or_create_for_today()
        return render(request, self.template_name, _closing_context(closing))
 
    def post(self, request):
        closing, _ = CashClosing.get_or_create_for_today()
        action = request.POST.get("_action", "")
 
        if action == "set_opening":
            if closing.is_closed:
                messages.error(request, "El cuadre ya está cerrado.")
                return redirect("cash_closing:cash-closing")
            form = OpeningBalanceForm(request.POST, instance=closing)
            if form.is_valid():
                form.save()
                messages.success(request, "Saldo inicial guardado.")
            else:
                messages.error(request, "Valor inválido para el saldo inicial.")
            return redirect("cash_closing:cash-closing")
 
        if action == "edit_closing":
            if closing.is_closed:
                messages.error(request, "El cuadre ya está cerrado.")
                return redirect("cash_closing:cash-closing")
            form = CashClosingEditForm(request.POST, instance=closing)
            if form.is_valid():
                form.save()
                messages.success(request, "Cuadre actualizado.")
            else:
                messages.error(request, "Error al actualizar el cuadre.")
            return redirect("cash_closing:cash-closing")
 
        if action == "save_denominations":
            if closing.is_closed:
                messages.error(request, "El cuadre ya está cerrado.")
                return redirect("cash_closing:cash-closing")
            for value, _ in CashDenomination.DENOMINATIONS:
                qty = int(request.POST.get(f"qty_{value}", 0) or 0)
                CashDenomination.objects.update_or_create(
                    closing=closing,
                    value=value,
                    defaults={"quantity": qty},
                )
            closing.recalculate_physical_cash()
            messages.success(request, "Conteo guardado.")
            return redirect("cash_closing:cash-closing")
 
        if action == "close_closing":
            if closing.is_closed:
                messages.error(request, "El cuadre ya estaba cerrado.")
                return redirect("cash_closing:cash-closing")
            closing.close()
            messages.success(
                request,
                f"Cuadre cerrado. Efectivo final: ${closing.physical_cash:,.0f}"
            )
            return redirect("cash_closing:cash-closing")
 
        if action == "reopen_closing":
            if closing.is_closed:
                closing.is_closed = False
                closing.save(update_fields=["is_closed"])
                messages.warning(request, "Cuadre reabierto. Recuerda volver a cerrarlo.")
            return redirect("cash_closing:cash-closing")
 
        messages.error(request, "Acción no reconocida.")
        return redirect("cash_closing:cash-closing")
 
 
class CashClosingHistoryView(View):
    template_name = "cash_closing/cash_closing_history.html"
 
    def get(self, request):
        closings = CashClosing.objects.all()
        return render(request, self.template_name, {"closings": closings})
    
# ── Agrega este import en views.py ──
# from .models import BankAccount

# ── Agrega esta vista al final de cash_closing/views.py ──

class BankAccountView(View):
    template_name = "cash_closing/bank_accounts.html"

    def get(self, request):
        from django.db.models import Sum, Q
        from .models import BankAccount

        selected_date  = request.GET.get("date", str(localdate()))
        selected_biz   = request.GET.get("business", "")

        banks = BankAccount.objects.filter(is_active=True)

        # Movimientos del día filtrados por negocio
        income_qs  = Income.objects.filter(
            payment_method="deposit", date=selected_date
        ).select_related("business", "bank")

        expense_qs = Expense.objects.filter(
            payment_method="deposit", date=selected_date
        ).select_related("business", "bank")

        if selected_biz:
            income_qs  = income_qs.filter(business_id=selected_biz)
            expense_qs = expense_qs.filter(business_id=selected_biz)

        # Totales por banco en el día
        bank_stats = []
        for bank in banks:
            day_in  = income_qs.filter(bank=bank).aggregate(
                t=Sum("amount"))["t"] or 0
            day_out = expense_qs.filter(bank=bank).aggregate(
                t=Sum("amount"))["t"] or 0
            bank_stats.append({
                "bank":    bank,
                "day_in":  day_in,
                "day_out": day_out,
            })

        return render(request, self.template_name, {
            "bank_stats":      bank_stats,
            "incomes":         income_qs.order_by("-created_at"),
            "expenses":        expense_qs.order_by("-created_at"),
            "businesses":      Business.objects.all(),
            "selected_date":   selected_date,
            "selected_business": selected_biz,
        })

class IncomeEditView(View):
    def post(self, request, pk):
        income = get_object_or_404(Income, pk=pk)
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, "Ingreso actualizado.")
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())
        url = reverse("cash_closing:cash-flow")
        date = request.POST.get("date", str(localdate()))
        return HttpResponseRedirect(f"{url}?date={date}&tab=income")


class ExpenseEditView(View):
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk)
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Egreso actualizado.")
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())
        url = reverse("cash_closing:cash-flow")
        date = request.POST.get("date", str(localdate()))
        return HttpResponseRedirect(f"{url}?date={date}&tab=expense")