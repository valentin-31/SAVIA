from dataclasses import dataclass
from datetime import date


@dataclass
class Usuario:
    """
    Documento de la colección usuarios.
    Representa a una persona que opera el sistema en nombre de un cliente.

    Un cliente puede tener múltiples usuarios con distintos niveles de acceso:
    - admin    : gestión completa (alta de parcelas, usuarios, etc.)
    - operador : carga de datos y campañas
    - visor    : solo lectura, orientado al dueño de la finca

    El campo email es único en toda la colección y funciona
    como identificador de inicio de sesión.
    """

    cliente_id: str
    nombre: str
    email: str
    rol: str           # admin | operador | visor
    fecha_alta: date
    activo: bool = True

    def to_dict(self) -> dict:
        """Convierte el usuario a dict serializable para MongoDB."""
        return {
            "cliente_id": self.cliente_id,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol,
            "fecha_alta": self.fecha_alta.isoformat(),
            "activo": self.activo,
        }
