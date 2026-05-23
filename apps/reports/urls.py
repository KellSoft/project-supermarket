from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportIndexView.as_view(), name='report_index'),
    path('compras/', views.PurchaseReportView.as_view(), name='purchase_report'),
    path('ingresos/', views.IncomeReportView.as_view(), name='income_report'),
    path('egresos/', views.ExpenseReportView.as_view(), name='expense_report'),
    path('diario/', views.DailyReportView.as_view(), name='daily_report'),
    path('cuadre-caja/', views.CashClosingReportView.as_view(), name='cash_closing_report'),
]