from django.urls import path
from .views import IncomeListView, IncomeCreateView, IncomeDeleteView

app_name = 'cash_closing'

urlpatterns = [
    path('incomes/',
         IncomeListView.as_view(),   name='income_list'),

    path('incomes/create/',
         IncomeCreateView.as_view(), name='income_create'),

    path('incomes/<int:pk>/delete/',
         IncomeDeleteView.as_view(), name='income_delete'),
]