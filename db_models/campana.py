from dataclasses import dataclass
from datetime import date


@dataclass
class Campana:
    """
    Documento de la colección campañas.
    Registra el rendimiento real de una parcela en una temporada agrícola.

    Es el valor objetivo que el modelo de ML aprende a predecir
    a partir del historial satelital almacenado en observaciones.

    Se mantiene separado de parcelas porque su ciclo de vida es distinto:
    se agrega un documento nuevo al final de cada temporada sin
    modificar los datos estáticos de la parcela.

    Las notas del productor (heladas, granizo, sequías) son clave para
    explicar anomalías que el modelo no puede inferir solo con índices.
    """

    parcela_id: str
    temporada: str         # formato 2023/2024 — cruza el año calendario
    fecha_cosecha: date
    rendimiento_kg_ha: float
    notas: str = ""

    def to_dict(self) -> dict:
        """Convierte la campaña a dict serializable para MongoDB."""
        return {
            "parcela_id": self.parcela_id,
            "temporada": self.temporada,
            "fecha_cosecha": self.fecha_cosecha.isoformat(),
            "rendimiento_kg_ha": self.rendimiento_kg_ha,
            "notas": self.notas,
        }
