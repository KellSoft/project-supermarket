from django.apps import AppConfig

class CashClosingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cash_closing"

    def ready(self):
        import apps.cash_closing.signals  # noqa
