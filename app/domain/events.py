from dataclasses import dataclass
from typing import Any, Optional

@dataclass(frozen=True)
class Event:
    pass

@dataclass(frozen=True)
class StockChanged(Event):
    producto_id: int
    bodega_id: int
    cantidad_delta: int  # Positivo para ingreso, negativo para retiro
    razon: str

@dataclass(frozen=True)
class EnvioCreado(Event):
    envio_id: int

@dataclass(frozen=True)
class EnvioConfirmado(Event):
    envio_id: int

@dataclass(frozen=True)
class ArchivoSubidoEliminado(Event):
    path: str
