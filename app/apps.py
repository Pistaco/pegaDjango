from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        import app.signals  # noqa: F401
        
        from .domain.bus import bus
        from .domain.events import StockChanged, EnvioCreado, EnvioConfirmado
        from .domain.handlers import handle_stock_change, handle_envio_creado_notif, handle_envio_confirmado
        
        # Registro de Handlers
        bus.handle(StockChanged, handle_stock_change)
        bus.handle(EnvioCreado, handle_envio_creado_notif)
        bus.handle(EnvioConfirmado, handle_envio_confirmado)
