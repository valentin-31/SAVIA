from dataclasses import dataclass, field
from datetime import date


@dataclass
class Usuario:
    """
    Documento de la colección usuarios.
    Representa a un productor o técnico con acceso al sistema.

    La relación con parcelas es N a N: un usuario puede tener
    varias parcelas, y una parcela puede ser compartida por
    varios usuarios. Esa relación se resuelve mediante la lista
    parcelas_ids, que contiene los ObjectId de cada parcela
    asociada al usuario.

    Colección: usuarios
    """
    nombre: str
    email: str
    contrasena_hash: str
    rol: str = "productor"           # productor | tecnico | admin
    parcelas_ids: list = field(default_factory=list)
    fecha_registro: str = ""

    def to_dict(self) -> dict:
        """Convierte el usuario a dict serializable para MongoDB."""
        return {
            "nombre": self.nombre,
            "email": self.email,
            "contrasena_hash": self.contrasena_hash,
            "rol": self.rol,
            "parcelas_ids": self.parcelas_ids,
            "fecha_registro": self.fecha_registro
                               or date.today().isoformat(),
        }
