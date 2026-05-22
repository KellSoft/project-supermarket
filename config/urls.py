from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("cash-closing/", include("apps.cash_closing.urls")),
    path("purchases/", include("apps.purchases.urls")),
    path("reports/", include("apps.reports.urls")),
]
