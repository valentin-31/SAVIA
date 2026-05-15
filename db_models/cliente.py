from dataclasses import dataclass, field
from datetime import date


@dataclass
class Cliente:
    """
    Documento de la colección clientes.
    Representa una organización que accede al sistema:
    bodega, productor independiente o cooperativa.

    El campo cliente_id generado por MongoDB se propaga a todas
    las colecciones operativas (parcelas, reportes) para garantizar
    el aislamiento lógico entre organizaciones.
    """

    nombre: str
    cuit: str
    tipo: str          # bodega | productor_independiente | cooperativa
    plan: str          # basico | profesional | enterprise
    fecha_alta: date
    activo: bool = True
    contacto: dict = field(default_factory=dict)   # {email, telefono}
    direccion: dict = field(default_factory=dict)  # {localidad, provincia, pais}

    def to_dict(self) -> dict:
        """Convierte el cliente a dict serializable para MongoDB."""
        return {
            "nombre": self.nombre,
            "cuit": self.cuit,
            "tipo": self.tipo,
            "plan": self.plan,
            "fecha_alta": self.fecha_alta.isoformat(),
            "activo": self.activo,
            "contacto": self.contacto,
            "direccion": self.direccion,
        }
