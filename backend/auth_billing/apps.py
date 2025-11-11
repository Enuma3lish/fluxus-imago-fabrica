from django.apps import AppConfig


class AuthBillingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_billing'
    verbose_name = 'Authentication & Billing'

    def ready(self):
        import auth_billing.signals
