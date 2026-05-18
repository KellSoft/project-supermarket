from django.urls import path
from .views import (
    IncomeListView,
    IncomeCreateView,
    IncomeDeleteView,
    CashExpenseListView,
    CashExpenseCreateView,
    CashExpenseDeleteView,
)

app_name = "cash_closing"

urlpatterns = [
    path("incomes/", IncomeListView.as_view(), name="income_list"),
    path("incomes/create/", IncomeCreateView.as_view(), name="income_create"),
    path("incomes/<int:pk>/delete/", IncomeDeleteView.as_view(), name="income_delete"),
    path("expenses/", CashExpenseListView.as_view(), name="expense_list"),
    path("expenses/create/", CashExpenseCreateView.as_view(), name="expense_create"),
    path(
        "expenses/<int:pk>/delete/",
        CashExpenseDeleteView.as_view(),
        name="expense_delete",
    ),
]
