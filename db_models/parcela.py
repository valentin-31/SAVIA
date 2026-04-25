from dataclasses import dataclass, field
from datetime import date
from db_models.observacion import Observacion


@dataclass
class Parcela:
    """
    Documento principal de la colección parcelas.
    Representa un viñedo con sus datos estáticos y su historial
    satelital embebido como lista de observaciones.
    """
    nombre: str
    cultivo: str
    zona: str
    geometria: dict
    variedad: str = ""
    superficie_ha: float = 0.0
    altitud_msnm: float = 0.0
    observaciones: list[Observacion] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convierte la parcela a dict serializable para MongoDB."""
        return {
            "nombre": self.nombre,
            "cultivo": self.cultivo,
            "zona": self.zona,
            "geometria": self.geometria,
            "variedad": self.variedad,
            "superficie_ha": self.superficie_ha,
            "altitud_msnm": self.altitud_msnm,
            "observaciones": [o.to_dict() for o in self.observaciones]
        }