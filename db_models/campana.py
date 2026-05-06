from  dataclasses import dataclass
from datetime import date


@dataclass
class Campana:
    """
    Documento de la colección campañas.
    Registra el rendimiento real de una parcela en una temporada agrícola.
    Es el valor que el modelo de ML aprende a predecir.
    Separado de parcelas porque crece de forma independiente —
    se agrega un documento nuevo al final de cada temporada.
    """

    parcela_id: str
    temporada: str
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
