from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts' 

    # ✅ Registrar signals
    def ready(self):
        """Registrar los signals al iniciar la aplicación."""
        import accounts.signals
