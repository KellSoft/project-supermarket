from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('cash-closing/', include('cash_closing.urls')),
    path('purchases/', include('purchases.urls')),
    path('reports/', include('reports.urls')),
]