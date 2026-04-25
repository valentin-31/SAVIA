
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId
from datetime import date
from db_models import Parcela, Observacion, Campana
from config_vars import MONGO_URI, DB_NAME


class VinedoDAO:
    """
    Módulo de acceso a datos para el sistema SAVIA.
    Abstrae todas las operaciones sobre MongoDB en métodos
    con semántica del dominio vitícola.
    Los métodos reciben parámetros del dominio (zona, fecha, ndvi)
    — nunca queries de MongoDB en crudo.
    """

    def __init__(self):
        self._client = MongoClient(MONGO_URI)
        self._db = self._client[DB_NAME]
        self._parcelas: Collection = self._db["parcelas"]
        self._campanas: Collection = self._db["campanas"]

    def cerrar(self):
        """Cierra la conexión con MongoDB."""
        self._client.close()

    def insertar_parcela(self, parcela: Parcela) -> str:
        """
        Inserta una parcela nueva en la coleccion
        Recibe un objeto Parcela y devuelve el id generado por MongoDB.
        """

        resultado = self._parcelas.insert_one(parcela.to_dict())
        return str(resultado.inserted_id)

    def get_parcela(self, parcela_id: str) -> dict | None:
        """
        Recupera una parcela por su id
        Devuelve el documento completo incluyendo el historial
        de observaciones embebido, o None si no existe
        """

        resultado = self._parcelas.find_one(
            {"_id": ObjectId(parcela_id)}
        )

        return resultado

    def get_parcelas_por_zona(self, zona: str) -> list[dict]:
        """
        Devuelve todas las parcelas de una zona geografica
        Ej: zona="Nonogasta", zona="Los Sarmientos"
        """

        return list(self._parcelas.find({"zona": zona}))

    def get_parcelas_por_cultivo(self, cultivo: str) -> list[dict]:
        """
        Devuelve todas las parcelas por tipo de cultivo
        Ej: cultivo="vid", cultivo="olivo"
        """
        return list(self._parcelas.find({"cultivo": cultivo}))

    def agregar_observacion(self, parcela_id: str, observacion: Observacion) -> bool:
        """
        Agrega una observación satelital al historial de una parcela.
        Usa $push para insertar en el array embebido sin reescribir
        el documento completo.
        """

        resultado = self._parcelas.update_one(
            {"_id": ObjectId(parcela_id)},
            {"$push": {"observaciones": observacion.to_dict()}},
        )

        return resultado.modified_count == 1

    def get_observaciones(self, parcela_id: str,
                          desde: date = None,
                          hasta: date = None) -> list[dict]:
        """
        Devuelve el historial de observaciones de una parcela
        Si se especifican desde y/o hasta, filtra por rango de fechas
        """

        parcela = self._parcelas.find_one(
            {"_id": ObjectId(parcela_id)},
            {"observaciones": 1}
        )

        if not parcela:
            return []

        observaciones = parcela.get("observaciones", [])

        if desde:
            observaciones = [
                o for o in observaciones
                if o["fecha"] >= desde.isoformat()
            ]
        if hasta:
            observaciones = [
                o for o in observaciones
                if o["fecha"] <= hasta.isoformat()
            ]

        return observaciones

    def get_ndvi_promedio_por_zona(self, zona: str, temporada: str) -> list[dict]:
        """
        Calcula el NDVI promedio de todas las parcelas de una zona
        para una temporada agrícola dada.
        Ej: zona="Nonogasta", temporada="2023/2024"
        """

        pipeline = [
            {"$match": {"zona": zona}},
            {"$unwind": "$observaciones"},
            {"$match": {
                "observaciones.fecha": {
                    "$gte": temporada[:4] + "-09-01",
                    "$lte": temporada[-4:] + "-03-31"
                }
            }},
            {"$group": {
                "_id": "$zona",
                "ndvi_promedio": {"$avg": "$observaciones.ndvi"},
                "total_observaciones": {"$sum": 1}
            }}
        ]

        return list(self._parcelas.aggregate(pipeline))

    def insertar_campana(self, campana: Campana) -> str:
        """
        Registra los datos de cosecha de una temporada agrícola.
        Devuelve el id generado por MongoDB.
        """
        resultado = self._campanas.insert_one(campana.to_dict())
        return str(resultado.inserted_id)

    def get_campanas(self, parcela_id: str) -> list[dict]:
        """
        Devuelve el historial completo de cosechas de una parcela.
        Ordenado por temporada de forma ascendente.
        """
        return list(
            self._campanas
            .find({"parcela_id": parcela_id})
            .sort("temporada", 1)
        )