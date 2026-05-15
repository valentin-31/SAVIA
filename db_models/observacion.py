from dataclasses import dataclass
from datetime import date


@dataclass
class Observacion:
    """
    Documento de la colección observaciones.
    Representa una captura de Sentinel-2 procesada para una parcela.

    A diferencia del modelo anterior, ya no es un subdocumento embebido
    dentro de parcelas: cada observación es un documento independiente
    vinculado mediante parcela_id.

    La colección tiene un índice compuesto sobre {parcela_id, fecha}
    que hace eficientes las consultas de rango temporal —
    el patrón de acceso más frecuente durante el entrenamiento del modelo.

    Las observaciones con nubosidad_pct > 20 se descartan durante
    el procesamiento en GEE antes de llegar a esta colección.
    """

    parcela_id: str
    fecha: date
    ndvi: float
    evi: float
    ndwi: float
    nubosidad_pct: float
    fuente: str = "Sentinel-2"

    def to_dict(self) -> dict:
        """Convierte la observación a dict serializable para MongoDB."""
        return {
            "parcela_id": self.parcela_id,
            "fecha": self.fecha.isoformat(),
            "ndvi": self.ndvi,
            "evi": self.evi,
            "ndwi": self.ndwi,
            "nubosidad_pct": self.nubosidad_pct,
            "fuente": self.fuente,
        }
