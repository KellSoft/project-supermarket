from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from datetime import date

from apps.purchases.models import Purchase
from apps.cash_closing.models import Expense, Income
from apps.businesses.models import Business


class ReportIndexView(View):
    def get(self, request):
        businesses = Business.objects.all()
        return render(request, "reports/report_index.html", {"businesses": businesses})


class PurchaseReportView(View):
    def get(self, request):
        businesses = Business.objects.all()
        return render(
            request, "reports/purchase_report_filters.html", {"businesses": businesses}
        )

    def post(self, request):
        purchases = Purchase.objects.all()

        supplier = request.POST.get("supplier")
        product = request.POST.get("product")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        if supplier:
            purchases = purchases.filter(supplier__icontains=supplier)

        product = request.POST.get("product")
        if product:
            purchases = purchases.filter(product__icontains=product)

        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        if start_date and end_date:
            purchases = purchases.filter(purchase_date__range=[start_date, end_date])

        filter_label = _build_filter_label(supplier, product, start_date, end_date)

        purchases = list(purchases)
        total = sum(p.amount for p in purchases)
        filter_label = _build_filter_label(
            supplier=supplier, product=product, start_date=start_date, end_date=end_date
        )

        html_string = render_to_string(
            "reports/purchase_report.html",
            {
                "purchases": purchases,
                "filter_label": filter_label,
                "generated": date.today(),
                "total": total,
            },
        )

        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="reporte_compras.pdf"'
        return response


class IncomeReportView(View):
    def get(self, request):
        businesses = Business.objects.all()
        return render(request, "reports/report_index.html", {"businesses": businesses})

    def post(self, request):
        incomes = Income.objects.select_related("business").all()

        business_id = request.POST.get("business")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        payment_method = request.POST.get("payment_method")
        bank = request.POST.get("bank")
        shift = request.POST.get("shift")

        business_name = "Todos los negocios"

        if business_id:
            incomes = incomes.filter(business_id=business_id)
            try:
                business_name = Business.objects.get(pk=business_id).name
            except Business.DoesNotExist:
                pass

        if start_date and end_date:
            incomes = incomes.filter(date__range=[start_date, end_date])

        if payment_method:
            incomes = incomes.filter(payment_method=payment_method)

        if bank:
            incomes = incomes.filter(bank=bank)

        if shift:
            incomes = incomes.filter(shift=int(shift))

        incomes = list(incomes)
        total = sum(i.amount for i in incomes)
        filter_label = _build_income_filter_label(
            business=business_name,
            start_date=start_date,
            end_date=end_date,
            payment_method=payment_method,
            bank=bank,
            shift=shift,
        )

        html_string = render_to_string(
            "reports/income_report.html",
            {
                "incomes": incomes,
                "filter_label": filter_label,
                "generated": date.today(),
                "total": total,
                "business_name": business_name,
            },
        )

        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="reporte_ingresos.pdf"'
        return response


class ExpenseReportView(View):
    def get(self, request):
        businesses = Business.objects.all()
        return render(request, "reports/report_index.html", {"businesses": businesses})

    def post(self, request):
        expenses = Expense.objects.select_related("business").all()

        business_id = request.POST.get("business")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        supplier = request.POST.get("supplier")
        payment_method = request.POST.get("payment_method")
        bank = request.POST.get("bank")

        business_name = "Todos los negocios"

        if business_id:
            expenses = expenses.filter(business_id=business_id)
            try:
                business_name = Business.objects.get(pk=business_id).name
            except Business.DoesNotExist:
                pass

        if start_date and end_date:
            expenses = expenses.filter(date__range=[start_date, end_date])

        if supplier:
            expenses = expenses.filter(supplier__icontains=supplier)

        if payment_method:
            expenses = expenses.filter(payment_method=payment_method)

        if bank:
            expenses = expenses.filter(bank=bank)

        expenses = list(expenses)
        total = sum(e.amount for e in expenses)
        filter_label = _build_expense_filter_label(
            business=business_name,
            start_date=start_date,
            end_date=end_date,
            supplier=supplier,
            payment_method=payment_method,
            bank=bank,
        )

        html_string = render_to_string(
            "reports/expense_report.html",
            {
                "expenses": expenses,
                "filter_label": filter_label,
                "generated": date.today(),
                "total": total,
                "business_name": business_name,
            },
        )

        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="reporte_egresos.pdf"'
        return response


def _build_filter_label(
    supplier=None, product=None, business=None, start_date=None, end_date=None
):
    parts = []
    if business and business != "Todos los negocios":
        parts.append(f"Negocio: {business}")
    if supplier:
        parts.append(f"Proveedor: {supplier}")
    if product:
        parts.append(f"Producto: {product}")
    if start_date and end_date:
        parts.append(f"Período: {start_date} → {end_date}")
    return " · ".join(parts) if parts else "Todos los registros"


def _get_payment_method_display(value):
    choices = {"cash": "Efectivo", "deposit": "Consignación"}
    return choices.get(value, value)


def _get_bank_display(value):
    choices = {
        "agrario": "Banco Agrario",
        "bancolombia": "Bancolombia",
        "bogota": "Banco de Bogotá",
    }
    return choices.get(value, value)


def _build_income_filter_label(
    business=None,
    start_date=None,
    end_date=None,
    payment_method=None,
    bank=None,
    shift=None,
):
    parts = []
    if business and business != "Todos los negocios":
        parts.append(f"Negocio: {business}")
    if start_date and end_date:
        parts.append(f"Período: {start_date} → {end_date}")
    if payment_method:
        parts.append(f"Método: {_get_payment_method_display(payment_method)}")
    if bank:
        parts.append(f"Banco: {_get_bank_display(bank)}")
    if shift:
        parts.append(f"Turno: {shift}")
    return " · ".join(parts) if parts else "Todos los registros"


def _build_expense_filter_label(
    business=None,
    start_date=None,
    end_date=None,
    supplier=None,
    payment_method=None,
    bank=None,
):
    parts = []
    if business and business != "Todos los negocios":
        parts.append(f"Negocio: {business}")
    if start_date and end_date:
        parts.append(f"Período: {start_date} → {end_date}")
    if supplier:
        parts.append(f"Proveedor: {supplier}")
    if payment_method:
        parts.append(f"Método: {_get_payment_method_display(payment_method)}")
    if bank:
        parts.append(f"Banco: {_get_bank_display(bank)}")
    return " · ".join(parts) if parts else "Todos los registros"


class DailyReportView(View):

    def get(self, request):
        selected_date = request.GET.get("date", str(timezone.localdate()))
        businesses = Business.objects.all()
        return render(
            request,
            "reports/report_index.html",
            {
                "businesses": businesses,
                "selected_date": selected_date,
            },
        )

    def post(self, request):
        selected_date = request.POST.get("date") or str(timezone.localdate())

        purchases = list(Purchase.objects.filter(purchase_date=selected_date))
        incomes = list(
            Income.objects.filter(date=selected_date).select_related("business")
        )
        expenses = list(
            Expense.objects.filter(date=selected_date).select_related("business")
        )

        total_purchases = sum(p.amount for p in purchases)
        total_incomes = sum(i.amount for i in incomes)
        total_expenses = sum(e.amount for e in expenses)
        balance = total_incomes - total_expenses

        html_string = render_to_string(
            "reports/daily_report.html",
            {
                "selected_date": selected_date,
                "generated": date.today(),
                "purchases": purchases,
                "incomes": incomes,
                "expenses": expenses,
                "total_purchases": total_purchases,
                "total_incomes": total_incomes,
                "total_expenses": total_expenses,
                "balance": balance,
            },
        )

        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="reporte_diario_{selected_date}.pdf"'
        )
        return response
