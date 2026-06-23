from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views import View
from django.views.generic import ListView
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.utils.timezone import localdate
from django.db.models import Sum
from apps.businesses.models import Business
from .models import (
    CashClosing,
    CashDenomination,
    Income,
    Expense,
    BankAccount,
    ExpenseType,
    Shift,
    Supplier,
)
from .forms import ExpenseForm, IncomeForm, OpeningBalanceForm, CashClosingEditForm
from datetime import date as date_type


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_ajax(request):
    """Detecta si la petición viene del fetch() del autosave."""
    return request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
           request.content_type == "application/x-www-form-urlencoded" and \
           request.headers.get("Accept") == "application/json"


def _build_denominations(closing):
    saved = {d.value: d.quantity for d in closing.denominations.all()}
    rows = []
    for value, label in CashDenomination.DENOMINATIONS:
        qty = saved.get(value, 0)
        rows.append(
            {
                "value": value,
                "label": label,
                "quantity": qty,
                "subtotal": value * qty,
                "is_bill": value in CashDenomination.BILLS,
            }
        )
    return rows


def _closing_context(closing):
    total_income_cash = closing.total_income_cash
    total_expense_cash = closing.total_expense_cash
    expected_cash = closing.opening_balance + total_income_cash - total_expense_cash
    
    return {
        "closing": closing,
        "opening_form": OpeningBalanceForm(instance=closing),
        "edit_form": CashClosingEditForm(instance=closing),
        "denominations": _build_denominations(closing),
        "total_income_cash": total_income_cash,
        "total_expense_cash": total_expense_cash,
        "expected_cash": expected_cash,
        "difference": closing.physical_cash - expected_cash,
    }


def _redirect_to_closing(date):
    url = reverse("cash_closing:cash-closing")
    if date != localdate():
        url += f"?date={date.isoformat()}"
    return redirect(url)


def _get_closing_for_date(date_str):
    """
    Dado un string de fecha ISO, devuelve (closing, error_msg).
    Si date_str está vacío usa hoy.
    """
    if not date_str:
        closing, _ = CashClosing.get_or_create_for_today()
        return closing, None

    try:
        target_date = date_type.fromisoformat(date_str)
    except ValueError:
        return None, "Fecha inválida."

    if target_date > localdate():
        return None, "No puedes consultar fechas futuras."

    if target_date == localdate():
        closing, _ = CashClosing.get_or_create_for_today()
        return closing, None

    try:
        return CashClosing.objects.get(date=target_date), None
    except CashClosing.DoesNotExist:
        return None, None   # caller distingue None-sin-error como "no existe"


# ---------------------------------------------------------------------------
# CashClosingView — manejadores separados por acción
# ---------------------------------------------------------------------------

class CashClosingView(View):
    template_name = "cash_closing/cash_closing.html"

    # ── GET ─────────────────────────────────────────────────────────────────

    def get(self, request):
        date_str = request.GET.get("date", "").strip()
        closing, error = _get_closing_for_date(date_str)
        selected_date = date_str or localdate().isoformat()

        if error:
            messages.error(request, error)
            closing, _ = CashClosing.get_or_create_for_today()
            selected_date = localdate().isoformat()

        if closing is None:
            # Fecha pasada sin cuadre registrado
            return render(request, self.template_name, {
                "closing": None,
                "is_today": False,
                "selected_date": selected_date,
                "no_closing_for_date": True,
            })

        is_today = (closing.date == localdate())
        ctx = _closing_context(closing)
        ctx["is_today"] = is_today
        ctx["selected_date"] = closing.date.isoformat()
        return render(request, self.template_name, ctx)

    # ── POST — despachador ──────────────────────────────────────────────────

    # Mapa acción → método manejador
    _HANDLERS = {
        "create_closing":    "_handle_create_closing",
        "set_opening":       "_handle_set_opening",
        "edit_closing":      "_handle_edit_closing",
        "save_denominations":"_handle_save_denominations",
        "close_closing":     "_handle_close_closing",
        "reopen_closing":    "_handle_reopen_closing",
        "save_notes":        "_handle_save_notes",
    }

    def post(self, request):
        action = request.POST.get("_action", "")
        handler_name = self._HANDLERS.get(action)

        if not handler_name:
            messages.error(request, "Acción no reconocida.")
            closing, _ = CashClosing.get_or_create_for_today()
            return _redirect_to_closing(closing.date)

        return getattr(self, handler_name)(request)

    # ── Manejadores individuales ─────────────────────────────────────────────

    def _resolve_closing(self, request):
        """
        Obtiene el cuadre indicado en _date, o el de hoy como fallback.
        Retorna (closing, error_response_or_None).
        """
        date_str = request.POST.get("_date", "").strip()
        closing, error = _get_closing_for_date(date_str)
        if error or closing is None:
            closing, _ = CashClosing.get_or_create_for_today()
        return closing

    def _handle_create_closing(self, request):
        date_str = request.POST.get("_date", "").strip()
        try:
            target_date = date_type.fromisoformat(date_str)
        except ValueError:
            messages.error(request, "Fecha inválida.")
            closing, _ = CashClosing.get_or_create_for_today()
            return _redirect_to_closing(closing.date)

        closing, created = CashClosing.objects.get_or_create(date=target_date)
        if created:
            messages.success(
                request,
                f"Cuadre creado para el {target_date.strftime('%d/%m/%Y')}.",
            )
        return _redirect_to_closing(target_date)

    def _handle_set_opening(self, request):
        closing = self._resolve_closing(request)
        if closing.is_closed:
            messages.error(request, "El cuadre ya está cerrado.")
            return _redirect_to_closing(closing.date)

        form = OpeningBalanceForm(request.POST, instance=closing)
        if form.is_valid():
            form.save()
            messages.success(request, "Saldo inicial guardado.")
        else:
            messages.error(request, "Valor inválido para el saldo inicial.")
        return _redirect_to_closing(closing.date)

    def _handle_edit_closing(self, request):
        closing = self._resolve_closing(request)
        if closing.is_closed:
            messages.error(request, "El cuadre ya está cerrado.")
            return _redirect_to_closing(closing.date)

        form = CashClosingEditForm(request.POST, instance=closing)
        if form.is_valid():
            form.save()
            messages.success(request, "Cuadre actualizado.")
        else:
            messages.error(request, "Error al actualizar el cuadre.")
        return _redirect_to_closing(closing.date)

    def _handle_save_denominations(self, request):
        """
        Soporta dos modos:
        - AJAX (autosave del JS): responde JSON {"ok": true/false, "msg": "..."}
        - POST normal: redirect de vuelta al cuadre
        """
        closing = self._resolve_closing(request)
        is_ajax = request.headers.get("X-Save-Mode") == "autosave"

        if closing.is_closed:
            if is_ajax:
                return JsonResponse({"ok": False, "msg": "El cuadre ya está cerrado."}, status=403)
            messages.error(request, "El cuadre ya está cerrado.")
            return _redirect_to_closing(closing.date)

        for value, _ in CashDenomination.DENOMINATIONS:
            qty = int(request.POST.get(f"qty_{value}", 0) or 0)
            CashDenomination.objects.update_or_create(
                closing=closing,
                value=value,
                defaults={"quantity": qty},
            )
        closing.recalculate_physical_cash()

        if is_ajax:
            return JsonResponse({"ok": True, "msg": "Guardado"})

        messages.success(request, "Conteo guardado.")
        return _redirect_to_closing(closing.date)

    def _handle_close_closing(self, request):
        closing = self._resolve_closing(request)
        if closing.is_closed:
            messages.error(request, "El cuadre ya estaba cerrado.")
            return _redirect_to_closing(closing.date)

        closing.close()
        messages.success(
            request,
            f"Cuadre cerrado. Efectivo final: ${closing.physical_cash:,.0f}",
        )
        return _redirect_to_closing(closing.date)

    def _handle_reopen_closing(self, request):
        closing = self._resolve_closing(request)
        if closing.is_closed:
            closing.is_closed = False
            closing.save(update_fields=["is_closed"])
            messages.warning(request, "Cuadre reabierto. Recuerda volver a cerrarlo.")
        return _redirect_to_closing(closing.date)

    def _handle_save_notes(self, request):
        closing = self._resolve_closing(request)
        if closing.is_closed:
            messages.error(request, "El cuadre ya está cerrado.")
            return _redirect_to_closing(closing.date)

        closing.notes = request.POST.get("notes", "").strip()
        closing.save(update_fields=["notes"])
        messages.success(request, "Notas guardadas.")
        return _redirect_to_closing(closing.date)


# ---------------------------------------------------------------------------
# El resto de las vistas no cambia — se incluyen completas para no romper imports
# ---------------------------------------------------------------------------

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
            Income.objects.filter(date=selected_date).aggregate(total=Sum("amount"))["total"] or 0
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
            Expense.objects.filter(date=selected_date).aggregate(total=Sum("amount"))["total"] or 0
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

        income_qs = Income.objects.select_related("business", "bank", "shift").filter(date=date)
        expense_qs = Expense.objects.select_related("business", "bank", "supplier").filter(date=date)
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

        return render(request, self.template_name, {
            "incomes": income_qs,
            "expenses": expense_qs,
            "businesses": Business.objects.all(),
            "suppliers": Supplier.objects.all(),
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
        })

    def post(self, request):
        kind = request.POST.get("_kind")
        form = IncomeForm(request.POST) if kind == "income" else ExpenseForm(request.POST)

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
        url = reverse("cash_closing:cash-flow") + f"?date={date}&tab={tab}"
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


class CashClosingHistoryView(View):
    template_name = "cash_closing/cash_closing_history.html"

    def get(self, request):
        closings_qs = CashClosing.objects.all().order_by("-date")
        paginator = Paginator(closings_qs, 20)
        page_obj = paginator.get_page(request.GET.get("page"))
        return render(request, self.template_name, {"page_obj": page_obj})


class BankAccountView(View):
    template_name = "cash_closing/bank_accounts.html"

    def get(self, request):
        from django.db.models import Sum

        selected_date = request.GET.get("date", str(localdate()))
        selected_biz = request.GET.get("business", "")

        banks = BankAccount.objects.filter(is_active=True)

        income_qs = Income.objects.filter(
            payment_method="deposit", date=selected_date
        ).select_related("business", "bank")

        expense_qs = Expense.objects.filter(
            payment_method="deposit", date=selected_date
        ).select_related("business", "bank")

        if selected_biz:
            income_qs = income_qs.filter(business_id=selected_biz)
            expense_qs = expense_qs.filter(business_id=selected_biz)

        bank_stats = []
        for bank in banks:
            day_in = income_qs.filter(bank=bank).aggregate(t=Sum("amount"))["t"] or 0
            day_out = expense_qs.filter(bank=bank).aggregate(t=Sum("amount"))["t"] or 0
            bank_stats.append({"bank": bank, "day_in": day_in, "day_out": day_out})

        total_in = income_qs.aggregate(t=Sum("amount"))["t"] or 0
        total_out = expense_qs.aggregate(t=Sum("amount"))["t"] or 0

        return render(request, self.template_name, {
            "bank_stats": bank_stats,
            "incomes": income_qs.order_by("-created_at"),
            "expenses": expense_qs.order_by("-created_at"),
            "businesses": Business.objects.all(),
            "selected_date": selected_date,
            "selected_business": selected_biz,
            "total_in": total_in,
            "total_out": total_out,
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