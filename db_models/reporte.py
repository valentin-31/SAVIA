from dataclasses import dataclass, field
from datetime import date


@dataclass
class Reporte:
    """
    Documento de la colección reportes.
    Almacena un resumen generado del estado satelital de una o varias
    parcelas en un período determinado.

    A diferencia de las colecciones operativas, los reportes cuelgan
    del cliente directamente y no de una parcela individual,
    ya que pueden cubrir múltiples parcelas de la misma organización.

    El campo resumen es un snapshot calculado al momento de generación:
    no se recalcula aunque lleguen nuevas observaciones después.
    Esto garantiza que el reporte refleje exactamente lo que el
    cliente vio en ese momento.

    Tipos de reporte:
    - resumen_indices      : NDVI/EVI/NDWI promedio por parcela en el período
    - comparativa_parcelas : ranking de parcelas por índice seleccionado
    - estado_general       : consolidado de alertas y rendimiento esperado
    """

    cliente_id: str
    nombre: str
    tipo: str                       # resumen_indices | comparativa_parcelas | estado_general
    periodo: dict                   # {desde: str (ISO), hasta: str (ISO)}
    parcelas_incluidas: list[str]   # lista de parcela_id como strings
    fecha_generacion: date
    generado_por: str               # usuario_id como string
    estado: str = "generado"        # generado | enviado | visto
    resumen: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convierte el reporte a dict serializable para MongoDB."""
        return {
            "cliente_id": self.cliente_id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "periodo": self.periodo,
            "parcelas_incluidas": self.parcelas_incluidas,
            "fecha_generacion": self.fecha_generacion.isoformat(),
            "generado_por": self.generado_por,
            "estado": self.estado,
            "resumen": self.resumen,
        }
