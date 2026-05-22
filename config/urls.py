from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("cuentas/", include("apps.accounts.urls")),
    path("flujo-caja/", include("apps.cash_closing.urls")),
    path("compras/", include("apps.purchases.urls")),
    path("reportes/", include("apps.reports.urls")),
]