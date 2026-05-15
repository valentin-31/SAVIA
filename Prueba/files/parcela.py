from dataclasses import dataclass


@dataclass
class Parcela:
    """
    Documento de la colección parcelas.
    Representa un viñedo con sus datos estáticos y geográficos.

    Las observaciones satelitales ya NO se almacenan embebidas.
    Viven en la colección 'observaciones' y se vinculan mediante
    el campo parcela_id en cada documento de esa colección.

    Colección: parcelas
    """
    nombre: str
    cultivo: str
    zona: str
    geometria: dict
    variedad: str = ""
    superficie_ha: float = 0.0
    altitud_msnm: float = 0.0

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
        }
