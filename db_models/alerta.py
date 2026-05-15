from dataclasses import dataclass
from datetime import date


@dataclass
class Alerta:
    """
    Documento de la colección alertas.
    Registra un evento detectado automáticamente cuando un índice
    espectral cae por debajo del umbral configurado para la parcela.

    El ciclo de vida completo queda registrado en el campo estado:
    activa → resuelta | ignorada

    Tipos de alerta:
    - ndvi_bajo        : vegetación con estrés severo o pérdida de masa foliar
    - estres_hidrico   : NDWI por debajo del umbral, déficit hídrico probable
    - anomalia_temporal: valor fuera del rango histórico para esa fecha

    El campo umbral registra el valor de referencia al momento de generar
    la alerta, permitiendo auditar por qué se disparó incluso si el umbral
    cambia después.
    """

    parcela_id: str
    fecha: date
    tipo: str              # ndvi_bajo | estres_hidrico | anomalia_temporal
    indice: str            # NDVI | EVI | NDWI
    valor_detectado: float
    umbral: float
    estado: str = "activa" # activa | resuelta | ignorada

    def to_dict(self) -> dict:
        """Convierte la alerta a dict serializable para MongoDB."""
        return {
            "parcela_id": self.parcela_id,
            "fecha": self.fecha.isoformat(),
            "tipo": self.tipo,
            "indice": self.indice,
            "valor_detectado": self.valor_detectado,
            "umbral": self.umbral,
            "estado": self.estado,
        }
