import json
from django.views import View
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from apps.purchases.models import Purchase
from apps.cash_closing.models import Income, Expense
from apps.businesses.models import Business


class DashboardView(View):
    def get(self, request):
        today = timezone.localdate()
        last_30 = today - timedelta(days=29)

        # Gráfica ingresos vs egresos ult 30 días
        incomes_by_day = (
            Income.objects.filter(date__range=[last_30, today])
            .annotate(day=TruncDate("date"))
            .values("day")
            .annotate(total=Sum("amount"))
            .order_by("day")
        )
        expenses_by_day = (
            Expense.objects.filter(date__range=[last_30, today])
            .annotate(day=TruncDate("date"))
            .values("day")
            .annotate(total=Sum("amount"))
            .order_by("day")
        )

        days = [(last_30 + timedelta(days=i)) for i in range(30)]
        income_map = {r["day"]: float(r["total"]) for r in incomes_by_day}
        expense_map = {r["day"]: float(r["total"]) for r in expenses_by_day}

        chart1_labels = [d.strftime("%d/%m") for d in days]
        chart1_incomes = [income_map.get(d, 0) for d in days]
        chart1_expenses = [expense_map.get(d, 0) for d in days]

        # ── Gráfica 2: Ingresos vs Egresos por negocio ──
        businesses = Business.objects.all()
        chart2_labels = [b.name for b in businesses]
        chart2_incomes = [
            float(
                Income.objects.filter(business=b).aggregate(t=Sum("amount"))["t"] or 0
            )
            for b in businesses
        ]
        chart2_expenses = [
            float(
                Expense.objects.filter(business=b).aggregate(t=Sum("amount"))["t"] or 0
            )
            for b in businesses
        ]

        # ── Gráfica 4: Top proveedores por monto ──
        top_suppliers = (
            Purchase.objects.values("supplier")
            .annotate(total=Sum("amount"))
            .order_by("-total")[:8]
        )
        chart4_labels = [r["supplier"] for r in top_suppliers]
        chart4_values = [float(r["total"]) for r in top_suppliers]

        # ── Gráfica 7: Ingresos por negocio este mes ──
        chart7_labels = chart2_labels
        chart7_values = [
            float(
                Income.objects.filter(
                    business=b, date__year=today.year, date__month=today.month
                ).aggregate(t=Sum("amount"))["t"]
                or 0
            )
            for b in businesses
        ]
        today_income = (
            Income.objects.filter(date=today).aggregate(t=Sum("amount"))["t"] or 0
        )
        today_expense = (
            Expense.objects.filter(date=today).aggregate(t=Sum("amount"))["t"] or 0
        )
        today_purchases = (
            Purchase.objects.filter(purchase_date=today).aggregate(t=Sum("amount"))["t"]
            or 0
        )

        context = {
            "chart1_labels": json.dumps(chart1_labels),
            "chart1_incomes": json.dumps(chart1_incomes),
            "chart1_expenses": json.dumps(chart1_expenses),
            "chart2_labels": json.dumps(chart2_labels),
            "chart2_incomes": json.dumps(chart2_incomes),
            "chart2_expenses": json.dumps(chart2_expenses),
            "chart4_labels": json.dumps(chart4_labels),
            "chart4_values": json.dumps(chart4_values),
            "chart7_labels": json.dumps(chart7_labels),
            "chart7_values": json.dumps(chart7_values),
            "today_income": int(today_income),
            "today_expense": int(today_expense),
            "today_purchases": int(today_purchases),
        }
        return render(request, "dashboard/index.html", context)
