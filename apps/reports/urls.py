from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path(
        'purchases/',
        views.PurchaseReportView.as_view(),
        name='purchase_report'
    ),
]