import logging
from typing import Dict, List, Type, Callable, Any
from .events import Event

logger = logging.getLogger(__name__)

class MessageBus:
    def __init__(self):
        self._handlers: Dict[Type[Event], List[Callable]] = {}

    def handle(self, event_type: Type[Event], handler: Callable):
        """Registra un manejador para un tipo de evento específico."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: Event):
        """Publica un evento y dispara todos sus manejadores registrados."""
        handlers = self._handlers.get(type(event), [])
        if not handlers:
            logger.debug(f"No hay manejadores registrados para {type(event).__name__}")
            return
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error procesando {type(event).__name__} en {handler.__name__}: {str(e)}")
                # Opcional: Re-lanzar si estamos en transacción atómica crítica
                raise e

# Instancia global del bus
bus = MessageBus()
