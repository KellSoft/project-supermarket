import io
import base64
import matplotlib
matplotlib.use("Agg")  # sin interfaz gráfica
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from datetime import date
from datetime import date as date_type
from collections import defaultdict
from django.db.models import Sum

from apps.purchases.models import Purchase
from apps.cash_closing.models import BankAccount, Expense, Income, PaymentMethod, Shift, CashClosing
from apps.businesses.models import Business


class ReportIndexView(View):
    def get(self, request):
        businesses = Business.objects.all()
        bank_accounts = BankAccount.objects.filter(is_active=True)
        shifts = Shift.objects.filter(is_active=True)
        return render(request, "reports/report_index.html", {
            "businesses": businesses,
            "bank_accounts": bank_accounts,
            "shifts": shifts,
            "selected_date": str(timezone.localdate()),
        })


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
        if product:
            purchases = purchases.filter(product__icontains=product)
        if start_date and end_date:
            purchases = purchases.filter(purchase_date__range=[start_date, end_date])

        purchases = list(purchases)
        total = sum(p.amount for p in purchases)
        filter_label = _build_filter_label(
            supplier=supplier, product=product, start_date=start_date, end_date=end_date
        )
        charts = _generate_purchase_charts(purchases)

        html_string = render_to_string(
            "reports/purchase_report.html",
            {
                "purchases": purchases,
                "filter_label": filter_label,
                "generated": date.today(),
                "total": total,
                "chart_proveedores": charts["proveedores"],
                "chart_productos": charts["productos"],
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
        charts = _generate_income_charts(incomes)

        html_string = render_to_string(
            "reports/income_report.html",
            {
                "incomes": incomes,
                "filter_label": filter_label,
                "generated": date.today(),
                "total": total,
                "business_name": business_name,
                "chart_por_negocio": charts["por_negocio"],
                "chart_por_metodo": charts["por_metodo"],
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
        charts = _generate_expense_charts(expenses)

        html_string = render_to_string(
            "reports/expense_report.html",
            {
                "expenses": expenses,
                "filter_label": filter_label,
                "generated": date.today(),
                "total": total,
                "business_name": business_name,
                "chart_por_negocio": charts["por_negocio"],
                "chart_por_proveedor": charts["por_proveedor"],
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


def _build_income_filter_label(
    business=None, start_date=None, end_date=None,
    payment_method=None, bank=None, shift=None,
):
    parts = []
    if business and business != "Todos los negocios":
        parts.append(f"Negocio: {business}")
    if start_date and end_date:
        parts.append(f"Período: {start_date} → {end_date}")
    if payment_method:
        parts.append(f"Método: {_get_payment_method_display(payment_method)}")
    if bank:
        try:
            bank_name = BankAccount.objects.get(pk=bank).name
        except BankAccount.DoesNotExist:
            bank_name = bank
        parts.append(f"Banco: {bank_name}")
    if shift:
        from apps.cash_closing.models import Shift
        try:
            shift_name = Shift.objects.get(pk=shift).name
        except Shift.DoesNotExist:
            shift_name = shift
        parts.append(f"Turno: {shift_name}")
    return " · ".join(parts) if parts else "Todos los registros"


def _build_expense_filter_label(
    business=None, start_date=None, end_date=None,
    supplier=None, payment_method=None, bank=None,
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
        try:
            bank_name = BankAccount.objects.get(pk=bank).name
        except BankAccount.DoesNotExist:
            bank_name = bank
        parts.append(f"Banco: {bank_name}")
    return " · ".join(parts) if parts else "Todos los registros"

def _generate_daily_charts(
    incomes, expenses, purchases, total_incomes, total_expenses, total_purchases
):
    charts = {}

    # Colores corporativos
    C_INCOME = "#1a7c4a"
    C_EXPENSE = "#1a3a7c"
    C_PURCHASE = "#c8421a"
    C_FAINT = "#999999"

    def fig_to_base64(fig):
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=150,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return encoded

    # ── GRÁFICA 1: Dona — distribución del día ──
    valores = [float(total_incomes), float(total_expenses), float(total_purchases)]
    etiquetas = ["Ingresos", "Egresos", "Compras"]
    colores = [C_INCOME, C_EXPENSE, C_PURCHASE]
    valores_filtrados = [
        (v, e, c) for v, e, c in zip(valores, etiquetas, colores) if v > 0
    ]

    if valores_filtrados:
        v, e, c = zip(*valores_filtrados)
        fig, ax = plt.subplots(figsize=(4, 3))
        wedges, texts, autotexts = ax.pie(
            v,
            labels=None,
            colors=c,
            autopct="%1.0f%%",
            startangle=90,
            wedgeprops={"linewidth": 1.5, "edgecolor": "white"},
            pctdistance=0.75,
        )
        for at in autotexts:
            at.set_fontsize(8)
            at.set_color("white")
            at.set_fontweight("bold")
        ax.legend(
            wedges,
            e,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.12),
            ncol=3,
            fontsize=7,
            frameon=False,
        )
        ax.set_title("Distribución del día", fontsize=9, fontweight="bold", pad=8)
        fig.patch.set_facecolor("white")
        charts["dona"] = fig_to_base64(fig)
    else:
        charts["dona"] = None

    # ── GRÁFICA 2: Barras — ingresos por negocio ──
    from collections import defaultdict

    income_by_biz = defaultdict(float)
    for i in incomes:
        income_by_biz[i.business.name] += float(i.amount)

    if income_by_biz:
        negocios = list(income_by_biz.keys())
        valores_biz = [income_by_biz[n] for n in negocios]

        fig, ax = plt.subplots(figsize=(5, max(2, len(negocios) * 0.8)))
        bars = ax.barh(
            negocios,
            valores_biz,
            color=C_INCOME,
            height=0.4,  # ← barra más delgada
            edgecolor="white",
        )
        ax.set_xlim(0, max(valores_biz) * 1.25)  # ← deja espacio a la derecha
        ax.tick_params(axis="y", labelsize=8)
        ax.tick_params(axis="x", labelsize=7)
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:,.0f}".replace(",", "."))
        )
        ax.set_facecolor("#f9fafb")  # ← fondo gris muy suave
        for bar, val in zip(bars, valores_biz):
            ax.text(
                bar.get_width() + max(valores_biz) * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}".replace(",", "."),
                va="center",
                fontsize=7,
                color=C_INCOME,
                fontweight="bold",
            )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.set_title("Ingresos por negocio", fontsize=9, fontweight="bold", pad=8)
        fig.patch.set_facecolor("white")
        plt.tight_layout()
        charts["ingresos_negocio"] = fig_to_base64(fig)
    else:
        charts["ingresos_negocio"] = None

    # ── GRÁFICA 3: Barras — compras por proveedor ──
    from collections import defaultdict

    purchase_by_supplier = defaultdict(float)
    for p in purchases:
        purchase_by_supplier[p.supplier] += float(p.amount)

    if purchase_by_supplier:
        proveedores = list(purchase_by_supplier.keys())
        valores_sup = [purchase_by_supplier[p] for p in proveedores]
        # ordenar de mayor a menor
        sorted_pairs = sorted(zip(valores_sup, proveedores), reverse=True)
        valores_sup, proveedores = zip(*sorted_pairs)

        fig, ax = plt.subplots(figsize=(5, max(2, len(proveedores) * 0.6)))
        bars = ax.barh(proveedores, valores_sup, color=C_PURCHASE, height=0.5)
        ax.tick_params(axis="y", labelsize=8)
        ax.tick_params(axis="x", labelsize=7)
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:,.0f}".replace(",", "."))
        )
        for bar, val in zip(bars, valores_sup):
            ax.text(
                bar.get_width() + max(valores_sup) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}".replace(",", "."),
                va="center",
                fontsize=7,
                color=C_PURCHASE,
            )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_title("Compras por proveedor", fontsize=9, fontweight="bold", pad=8)
        fig.patch.set_facecolor("white")
        plt.tight_layout()
        charts["compras_proveedor"] = fig_to_base64(fig)
    else:
        charts["compras_proveedor"] = None

    return charts


def _generate_purchase_charts(purchases):
    import io, base64
    from collections import defaultdict

    charts = {}
    C_PURCHASE = "#c8421a"

    def fig_to_base64(fig):
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=150,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return encoded

    # ── Gráfica 1: Top proveedores ──
    by_supplier = defaultdict(float)
    for p in purchases:
        by_supplier[p.supplier] += float(p.amount)

    if by_supplier:
        pairs = sorted(by_supplier.items(), key=lambda x: x[1], reverse=True)[:8]
        proveedores, valores = zip(*pairs)
        fig, ax = plt.subplots(figsize=(8, max(3, len(proveedores) * 0.9)))
        bars = ax.barh(
            list(proveedores),
            list(valores),
            color=C_PURCHASE,
            height=0.4,
            edgecolor="white",
        )
        ax.set_xlim(0, max(valores) * 1.25)
        ax.set_facecolor("#f9fafb")
        ax.tick_params(axis="y", labelsize=8)
        ax.tick_params(axis="x", labelsize=7)
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:,.0f}".replace(",", "."))
        )
        for bar, val in zip(bars, valores):
            ax.text(
                bar.get_width() + max(valores) * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}".replace(",", "."),
                va="center",
                fontsize=7,
                color=C_PURCHASE,
                fontweight="bold",
            )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.set_title("Top proveedores", fontsize=9, fontweight="bold", pad=8)
        fig.patch.set_facecolor("white")
        plt.tight_layout()
        charts["proveedores"] = fig_to_base64(fig)
    else:
        charts["proveedores"] = None

    # ── Gráfica 2: Top productos ──
    by_product = defaultdict(float)
    for p in purchases:
        by_product[p.product] += float(p.amount)

    if by_product:
        pairs = sorted(by_product.items(), key=lambda x: x[1], reverse=True)[:8]
        productos, valores = zip(*pairs)
        fig, ax = plt.subplots(figsize=(8, max(3, len(productos) * 0.9)))
        bars = ax.barh(
            list(productos),
            list(valores),
            color="#1a3a7c",
            height=0.4,
            edgecolor="white",
        )
        ax.set_xlim(0, max(valores) * 1.25)
        ax.set_facecolor("#f9fafb")
        ax.tick_params(axis="y", labelsize=8)
        ax.tick_params(axis="x", labelsize=7)
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:,.0f}".replace(",", "."))
        )
        for bar, val in zip(bars, valores):
            ax.text(
                bar.get_width() + max(valores) * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}".replace(",", "."),
                va="center",
                fontsize=7,
                color="#1a3a7c",
                fontweight="bold",
            )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.set_title("Top productos", fontsize=9, fontweight="bold", pad=8)
        fig.patch.set_facecolor("white")
        plt.tight_layout()
        charts["productos"] = fig_to_base64(fig)
    else:
        charts["productos"] = None

    return charts


def _generate_income_charts(incomes):
    from collections import defaultdict

    charts = {}
    C_INCOME = "#1a7c4a"
    C_DEPOSIT = "#1a3a7c"

    def fig_to_base64(fig):
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=150,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return encoded

    # ── Gráfica 1: Ingresos por negocio ──
    by_biz = defaultdict(float)
    for i in incomes:
        by_biz[i.business.name] += float(i.amount)

    if by_biz:
        pairs = sorted(by_biz.items(), key=lambda x: x[1], reverse=True)
        negocios, valores = zip(*pairs)
        fig, ax = plt.subplots(figsize=(8, max(3, len(negocios) * 0.9)))
        bars = ax.barh(
            list(negocios), list(valores), color=C_INCOME, height=0.4, edgecolor="white"
        )
        ax.set_xlim(0, max(valores) * 1.25)
        ax.set_facecolor("#f9fafb")
        ax.tick_params(axis="y", labelsize=8)
        ax.tick_params(axis="x", labelsize=7)
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:,.0f}".replace(",", "."))
        )
        for bar, val in zip(bars, valores):
            ax.text(
                bar.get_width() + max(valores) * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}".replace(",", "."),
                va="center",
                fontsize=7,
                color=C_INCOME,
                fontweight="bold",
            )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.set_title("Ingresos por negocio", fontsize=9, fontweight="bold", pad=8)
        fig.patch.set_facecolor("white")
        plt.tight_layout()
        charts["por_negocio"] = fig_to_base64(fig)
    else:
        charts["por_negocio"] = None

    # ── Gráfica 2: Ingresos por método de pago ──
    by_method = defaultdict(float)
    for i in incomes:
        label = i.get_payment_method_display()
        by_method[label] += float(i.amount)

    if by_method:
        pairs = sorted(by_method.items(), key=lambda x: x[1], reverse=True)
        metodos, valores = zip(*pairs)
        colores = [C_INCOME if "fectivo" in m else C_DEPOSIT for m in metodos]
        fig, ax = plt.subplots(figsize=(8, max(2, len(metodos) * 0.9)))
        bars = ax.barh(
            list(metodos), list(valores), color=colores, height=0.4, edgecolor="white"
        )
        ax.set_xlim(0, max(valores) * 1.25)
        ax.set_facecolor("#f9fafb")
        ax.tick_params(axis="y", labelsize=8)
        ax.tick_params(axis="x", labelsize=7)
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:,.0f}".replace(",", "."))
        )
        for bar, val, color in zip(bars, valores, colores):
            ax.text(
                bar.get_width() + max(valores) * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}".replace(",", "."),
                va="center",
                fontsize=7,
                color=color,
                fontweight="bold",
            )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.set_title(
            "Ingresos por método de pago", fontsize=9, fontweight="bold", pad=8
        )
        fig.patch.set_facecolor("white")
        plt.tight_layout()
        charts["por_metodo"] = fig_to_base64(fig)
    else:
        charts["por_metodo"] = None

    return charts


def _generate_expense_charts(expenses):
    from collections import defaultdict

    charts = {}
    C_EXPENSE = "#1a3a7c"
    C_SUPPLIER = "#c8421a"

    def fig_to_base64(fig):
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=150,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return encoded

    # ── Gráfica 1: Egresos por negocio ──
    by_biz = defaultdict(float)
    for e in expenses:
        name = str(e.business.name) if e.business and e.business.name else "Sin negocio"
        by_biz[name] += float(e.amount)

    if by_biz:
        pairs = sorted(by_biz.items(), key=lambda x: x[1], reverse=True)
        negocios, valores = zip(*pairs)
        fig, ax = plt.subplots(figsize=(8, max(3, len(negocios) * 0.9)))
        bars = ax.barh(
            list(negocios),
            list(valores),
            color=C_EXPENSE,
            height=0.4,
            edgecolor="white",
        )
        ax.set_xlim(0, max(valores) * 1.25)
        ax.set_facecolor("#f9fafb")
        ax.tick_params(axis="y", labelsize=8)
        ax.tick_params(axis="x", labelsize=7)
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:,.0f}".replace(",", "."))
        )
        for bar, val in zip(bars, valores):
            ax.text(
                bar.get_width() + max(valores) * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}".replace(",", "."),
                va="center",
                fontsize=7,
                color=C_EXPENSE,
                fontweight="bold",
            )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.set_title("Egresos por negocio", fontsize=9, fontweight="bold", pad=8)
        fig.patch.set_facecolor("white")
        plt.tight_layout()
        charts["por_negocio"] = fig_to_base64(fig)
    else:
        charts["por_negocio"] = None

    # ── Gráfica 2: Top proveedores ──
    by_supplier = defaultdict(float)
    for e in expenses:
        by_supplier[str(e.supplier) if e.supplier else "Sin proveedor"] += float(e.amount)

    if by_supplier:
        pairs = sorted(by_supplier.items(), key=lambda x: x[1], reverse=True)[:8]
        proveedores, valores = zip(*pairs)
        fig, ax = plt.subplots(figsize=(8, max(3, len(proveedores) * 0.9)))
        bars = ax.barh(
            list(proveedores),
            list(valores),
            color=C_SUPPLIER,
            height=0.4,
            edgecolor="white",
        )
        ax.set_xlim(0, max(valores) * 1.25)
        ax.set_facecolor("#f9fafb")
        ax.tick_params(axis="y", labelsize=8)
        ax.tick_params(axis="x", labelsize=7)
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:,.0f}".replace(",", "."))
        )
        for bar, val in zip(bars, valores):
            ax.text(
                bar.get_width() + max(valores) * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}".replace(",", "."),
                va="center",
                fontsize=7,
                color=C_SUPPLIER,
                fontweight="bold",
            )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.set_title("Top proveedores", fontsize=9, fontweight="bold", pad=8)
        fig.patch.set_facecolor("white")
        plt.tight_layout()
        charts["por_proveedor"] = fig_to_base64(fig)
    else:
        charts["por_proveedor"] = None

    return charts


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
        selected_date_str = request.POST.get("date") or str(timezone.localdate())
        selected_date = date_type.fromisoformat(selected_date_str)

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

        # ── Gráficas ──
        charts = _generate_daily_charts(
            incomes, expenses, purchases, total_incomes, total_expenses, total_purchases
        )

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
                "chart_dona": charts["dona"],
                "chart_ingresos_negocio": charts["ingresos_negocio"],
                "chart_compras_proveedor": charts["compras_proveedor"],
            },
        )

        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="reporte_diario_{selected_date}.pdf"'
        )
        return response

class CashClosingReportView(View):
    def get(self, request):
        businesses = Business.objects.all()
        return render(request, "reports/report_index.html", {"businesses": businesses})

    def post(self, request):
        selected_date_str = request.POST.get("date") or str(timezone.localdate())
        selected_date = date_type.fromisoformat(selected_date_str)

        try:
            closing = CashClosing.objects.get(date=selected_date)
        except CashClosing.DoesNotExist:
            closing = None

        incomes = list(Income.objects.filter(date=selected_date).select_related("business"))
        expenses = list(Expense.objects.filter(date=selected_date).select_related("business"))
        denominations = list(closing.denominations.all()) if closing else []

        total_income_cash = closing.total_income_cash if closing else 0
        total_expense_cash = closing.total_expense_cash if closing else 0
        expected_cash = closing.expected_cash if closing else 0
        difference = closing.difference if closing else 0
        physical_cash = closing.physical_cash if closing else 0
        opening_balance = closing.opening_balance if closing else 0

        html_string = render_to_string(
            "reports/cash_closing_report.html",
            {
                "selected_date": selected_date,
                "generated": date.today(),
                "closing": closing,
                "incomes": incomes,
                "expenses": expenses,
                "denominations": denominations,
                "total_income_cash": total_income_cash,
                "total_expense_cash": total_expense_cash,
                "expected_cash": expected_cash,
                "difference": difference,
                "physical_cash": physical_cash,
                "opening_balance": opening_balance,
            },
        )

        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="cuadre_caja_{selected_date}.pdf"'
        )
        return response

class BankReportView(View):
    def get(self, request):
        businesses = Business.objects.all()
        bank_accounts = BankAccount.objects.filter(is_active=True)
        return render(request, "reports/report_index.html", {
            "businesses": businesses,
            "bank_accounts": bank_accounts,
        })

    def post(self, request):
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        business_id = request.POST.get("business")
        bank_id = request.POST.get("bank")
        business_name = "Todos los negocios"

        income_qs = Income.objects.select_related("business", "bank").filter(
            payment_method=PaymentMethod.DEPOSIT
        )
        expense_qs = Expense.objects.select_related("business", "bank").filter(
            payment_method=PaymentMethod.DEPOSIT
        )

        if start_date and end_date:
            income_qs = income_qs.filter(date__range=[start_date, end_date])
            expense_qs = expense_qs.filter(date__range=[start_date, end_date])
        if business_id:
            income_qs = income_qs.filter(business_id=business_id)
            expense_qs = expense_qs.filter(business_id=business_id)
            try:
                business_name = Business.objects.get(pk=business_id).name
            except Business.DoesNotExist:
                pass
        if bank_id:
            income_qs = income_qs.filter(bank_id=bank_id)
            expense_qs = expense_qs.filter(bank_id=bank_id)

        incomes = list(income_qs.order_by("date"))
        expenses = list(expense_qs.order_by("date"))

        # Totales por banco
        banks = BankAccount.objects.filter(is_active=True)
        if bank_id:
            banks = banks.filter(pk=bank_id)

        bank_summary = []
        for bank in banks:
            total_in = sum(i.amount for i in incomes if i.bank_id == bank.pk)
            total_out = sum(e.amount for e in expenses if e.bank_id == bank.pk)
            bank_summary.append({
                "bank": bank,
                "total_in": total_in,
                "total_out": total_out,
                "net": total_in - total_out,
            })

        total_in_global = sum(i.amount for i in incomes)
        total_out_global = sum(e.amount for e in expenses)

        charts = _generate_bank_charts(incomes, expenses, banks)

        filter_label = _build_bank_filter_label(
            business=business_name,
            start_date=start_date,
            end_date=end_date,
            bank_id=bank_id,
            banks=banks,
        )

        html_string = render_to_string(
            "reports/bank_report.html",
            {
                "incomes": incomes,
                "expenses": expenses,
                "bank_summary": bank_summary,
                "total_in_global": total_in_global,
                "total_out_global": total_out_global,
                "net_global": total_in_global - total_out_global,
                "filter_label": filter_label,
                "generated": date.today(),
                "business_name": business_name,
                "start_date": start_date,
                "end_date": end_date,
                "chart_por_banco": charts["por_banco"],
                "chart_evolucion": charts["evolucion"],
            },
        )

        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="reporte_bancos.pdf"'
        return response


def _build_bank_filter_label(business=None, start_date=None, end_date=None, bank_id=None, banks=None):
    parts = []
    if business and business != "Todos los negocios":
        parts.append(f"Negocio: {business}")
    if start_date and end_date:
        parts.append(f"Período: {start_date} → {end_date}")
    if bank_id and banks:
        bank = next((b for b in banks if str(b.pk) == str(bank_id)), None)
        if bank:
            parts.append(f"Banco: {bank.name}")
    return " · ".join(parts) if parts else "Todos los registros"


def _generate_bank_charts(incomes, expenses, banks):
    from collections import defaultdict

    charts = {}
    C_IN = "#1a7c4a"
    C_OUT = "#c8421a"

    def fig_to_base64(fig):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return encoded

    # ── Gráfica 1: Entradas vs Salidas por banco ──
    bank_names = [b.name for b in banks]
    ins  = [sum(i.amount for i in incomes  if i.bank_id == b.pk) for b in banks]
    outs = [sum(e.amount for e in expenses if e.bank_id == b.pk) for b in banks]

    if any(v > 0 for v in ins + outs):
        x = range(len(bank_names))
        fig, ax = plt.subplots(figsize=(8, max(3, len(bank_names) * 1.2)))
        width = 0.35
        bars_in  = ax.bar([i - width/2 for i in x], ins,  width, label="Entradas", color=C_IN,  edgecolor="white")
        bars_out = ax.bar([i + width/2 for i in x], outs, width, label="Salidas",  color=C_OUT, edgecolor="white")
        ax.set_xticks(list(x))
        ax.set_xticklabels(bank_names, fontsize=8)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:,.0f}".replace(",", ".")))
        ax.tick_params(axis="y", labelsize=7)
        ax.legend(fontsize=8, frameon=False)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_facecolor("#f9fafb")
        ax.set_title("Entradas vs Salidas por banco", fontsize=9, fontweight="bold", pad=8)
        fig.patch.set_facecolor("white")
        plt.tight_layout()
        charts["por_banco"] = fig_to_base64(fig)
    else:
        charts["por_banco"] = None

    # ── Gráfica 2: Evolución diaria (entradas - salidas) ──
    from collections import defaultdict
    daily_in  = defaultdict(float)
    daily_out = defaultdict(float)
    for i in incomes:
        daily_in[str(i.date)]  += float(i.amount)
    for e in expenses:
        daily_out[str(e.date)] += float(e.amount)

    all_dates = sorted(set(daily_in.keys()) | set(daily_out.keys()))

    if len(all_dates) > 1:
        vals_in  = [daily_in[d]  for d in all_dates]
        vals_out = [daily_out[d] for d in all_dates]
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(all_dates, vals_in,  color=C_IN,  linewidth=1.5, marker="o", markersize=4, label="Entradas")
        ax.plot(all_dates, vals_out, color=C_OUT, linewidth=1.5, marker="o", markersize=4, label="Salidas")
        ax.fill_between(all_dates, vals_in, alpha=0.08, color=C_IN)
        ax.fill_between(all_dates, vals_out, alpha=0.08, color=C_OUT)
        step = max(1, len(all_dates) // 8)
        ax.set_xticks(all_dates[::step])
        ax.set_xticklabels(all_dates[::step], rotation=30, fontsize=7)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:,.0f}".replace(",", ".")))
        ax.tick_params(axis="y", labelsize=7)
        ax.legend(fontsize=8, frameon=False)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_facecolor("#f9fafb")
        ax.set_title("Evolución diaria de movimientos bancarios", fontsize=9, fontweight="bold", pad=8)
        fig.patch.set_facecolor("white")
        plt.tight_layout()
        charts["evolucion"] = fig_to_base64(fig)
    else:
        charts["evolucion"] = None

    return charts