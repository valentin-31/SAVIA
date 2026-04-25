from dataclasses import dataclass, field
from datetime import date


@dataclass
class Observacion:
    """
    Subdocumento que representa una captura de Sentinel-2 procesada.
    Se almacena embebido dentro del documento de una parcela.
    Cada instancia corresponde a una fecha de imagen satelital.
    """
    fecha: date
    ndvi: float
    evi: float
    ndwi: float
    nubosidad_pct: float
    fuente: str = "Sentinel-2"

    def to_dict(self) -> dict:
        """Convierte la observación a dict serializable para MongoDB."""
        return {
            "fecha": self.fecha.isoformat(),
            "ndvi": self.ndvi,
            "evi": self.evi,
            "ndwi": self.ndwi,
            "nubosidad_pct": self.nubosidad_pct,
            "fuente": self.fuente
        }