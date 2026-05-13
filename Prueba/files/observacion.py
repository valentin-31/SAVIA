from dataclasses import dataclass
from datetime import date


@dataclass
class Observacion:
    """
    Documento de la colección observaciones.

    Antes vivía embebido dentro del documento de una parcela.
    Ahora es una colección independiente referenciada por parcela_id.

    Justificación del cambio:
    Sentinel-2 entrega una imagen cada ~5 días. En tres años eso
    representa ~200 observaciones por parcela. Con múltiples parcelas
    y actualizaciones continuas, el array embebido crece sin límite,
    degrada el rendimiento de lectura del documento completo y supera
    el límite de 16 MB por documento de MongoDB a largo plazo.
    Separar observaciones en su propia colección permite:
      - Crecer ilimitadamente sin afectar el documento de la parcela.
      - Indexar por parcela_id + fecha para consultas de rango eficientes.
      - Agregar o filtrar observaciones sin tocar la parcela.

    Colección: observaciones
    """
    parcela_id: str          # ObjectId de la parcela a la que pertenece
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
