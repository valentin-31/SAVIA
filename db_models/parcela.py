from dataclasses import dataclass


@dataclass
class Parcela:
    """
    Documento de la colección parcelas.
    Representa un viñedo con sus datos estáticos y su geometría geográfica.

    Las observaciones satelitales ya no se embeben aquí:
    viven en su propia colección y se vinculan mediante parcela_id.
    Esto permite que la serie temporal crezca de forma independiente
    sin modificar el documento de la parcela.

    El campo cliente_id garantiza que la parcela pertenece a una
    organización específica y habilita el aislamiento multi-tenant.
    """

    cliente_id: str
    nombre: str
    cultivo: str
    zona: str
    geometria: dict        # GeoJSON Polygon en WGS84
    variedad: str = ""
    superficie_ha: float = 0.0
    altitud_msnm: float = 0.0

    def to_dict(self) -> dict:
        """Convierte la parcela a dict serializable para MongoDB."""
        return {
            "cliente_id": self.cliente_id,
            "nombre": self.nombre,
            "cultivo": self.cultivo,
            "zona": self.zona,
            "geometria": self.geometria,
            "variedad": self.variedad,
            "superficie_ha": self.superficie_ha,
            "altitud_msnm": self.altitud_msnm,
        }
