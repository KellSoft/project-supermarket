from django.urls import path
from . import views

app_name = "cash_closing"

urlpatterns = [
    path("", views.CashFlowView.as_view(), name="cash-flow"),
    path("ingresos/", views.IncomeListView.as_view(), name="income-list"),
    path("ingresos/crear/", views.IncomeCreateView.as_view(), name="income-create"),
    path("ingresos/<int:pk>/eliminar/",views.IncomeDeleteView.as_view(),name="income-delete",),
    path("egresos/", views.ExpenseListView.as_view(), name="expense-list"),
    path("egresos/crear/", views.ExpenseCreateView.as_view(), name="expense-create"),
    path("egresos/<int:pk>/eliminar/",views.ExpenseDeleteView.as_view(),name="expense-delete",),
    path("cuadre/", views.CashClosingView.as_view(), name="cash-closing"),
    path("cuadre/historial/",views.CashClosingHistoryView.as_view(),name="cash-closing-history",),
    path("bancos/", views.BankAccountView.as_view(), name="bank-accounts"),
]
