from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("cuentas/", include("apps.accounts.urls")),
    path("flujo-caja/", include("apps.cash_closing.urls")),
    path("compras/", include("apps.purchases.urls")),
    path("reportes/", include("apps.reports.urls")),
    path("favicon.ico", RedirectView.as_view(url="/static/mana-logo.jpeg")),
]