import json
from django.views import View
from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from apps.cash_closing.models import Income, Expense
from apps.businesses.models import Business


def _to_float(val):
    return float(val or 0)


class DashboardView(View):
    def get(self, request):
        today = timezone.localdate()
        last_30 = today - timedelta(days=29)
        days = [(last_30 + timedelta(days=i)) for i in range(30)]

        # ── Gráfica 1: Ingresos vs Egresos últimos 30 días ──
        income_map = dict(
            Income.objects.filter(date__range=[last_30, today])
            .values("date")
            .annotate(total=Sum("amount"))
            .values_list("date", "total")
        )
        expense_map = dict(
            Expense.objects.filter(date__range=[last_30, today])
            .values("date")
            .annotate(total=Sum("amount"))
            .values_list("date", "total")
        )

        chart1_labels = [d.strftime("%d/%m") for d in days]
        chart1_incomes = [_to_float(income_map.get(d)) for d in days]
        chart1_expenses = [_to_float(expense_map.get(d)) for d in days]

        # ── Gráficas 2 y 7: por negocio ──
        income_by_biz = dict(
            Income.objects.values("business_id")
            .annotate(t=Sum("amount"))
            .values_list("business_id", "t")
        )
        expense_by_biz = dict(
            Expense.objects.values("business_id")
            .annotate(t=Sum("amount"))
            .values_list("business_id", "t")
        )
        income_month_by_biz = dict(
            Income.objects.filter(date__year=today.year, date__month=today.month)
            .values("business_id")
            .annotate(t=Sum("amount"))
            .values_list("business_id", "t")
        )

        businesses = Business.objects.all()
        chart2_labels = [b.name for b in businesses]
        chart2_incomes = [_to_float(income_by_biz.get(b.id)) for b in businesses]
        chart2_expenses = [_to_float(expense_by_biz.get(b.id)) for b in businesses]
        chart7_labels = chart2_labels
        chart7_values = [_to_float(income_month_by_biz.get(b.id)) for b in businesses]

        # ── Métricas del día ──
        today_income = _to_float(
            Income.objects.filter(date=today).aggregate(t=Sum("amount"))["t"]
        )
        today_expense = _to_float(
            Expense.objects.filter(date=today).aggregate(t=Sum("amount"))["t"]
        )

        context = {
            "chart1_labels": json.dumps(chart1_labels),
            "chart1_incomes": json.dumps(chart1_incomes),
            "chart1_expenses": json.dumps(chart1_expenses),
            "chart2_labels": json.dumps(chart2_labels),
            "chart2_incomes": json.dumps(chart2_incomes),
            "chart2_expenses": json.dumps(chart2_expenses),
            "chart7_labels": json.dumps(chart7_labels),
            "chart7_values": json.dumps(chart7_values),
            "today_income": today_income,
            "today_expense": today_expense,
        }
        return render(request, "dashboard/index.html", context)
