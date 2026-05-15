from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from bson import ObjectId
from datetime import date
from db_models import Parcela, Observacion, Campana, Usuario
from config_vars import MONGO_URI, DB_NAME


class VinedoDAO:
    """
    Módulo de acceso a datos para el sistema SAVIA.
    Abstrae todas las operaciones sobre MongoDB en métodos
    con semántica del dominio vitícola.

    Colecciones gestionadas:
      - parcelas      : datos estáticos y geográficos de cada viñedo
      - observaciones : serie temporal satelital (colección separada)
      - campanas      : rendimiento real por temporada agrícola
      - usuarios      : productores y técnicos con acceso al sistema
    """

    def __init__(self):
        self._client = MongoClient(MONGO_URI)
        self._db = self._client[DB_NAME]
        self._parcelas: Collection = self._db["parcelas"]
        self._observaciones: Collection = self._db["observaciones"]
        self._campanas: Collection = self._db["campanas"]
        self._usuarios: Collection = self._db["usuarios"]

    def cerrar(self):
        """Cierra la conexión con MongoDB."""
        self._client.close()

    # ------------------------------------------------------------------ #
    #  PARCELAS                                                            #
    # ------------------------------------------------------------------ #

    def insertar_parcela(self, parcela: Parcela) -> str:
        """
        Inserta una parcela nueva en la colección.
        Devuelve el id generado por MongoDB.
        """
        resultado = self._parcelas.insert_one(parcela.to_dict())
        return str(resultado.inserted_id)

    def get_parcela(self, parcela_id: str) -> dict | None:
        """
        Recupera una parcela por su id.
        Devuelve el documento sin observaciones embebidas.
        Para obtener el historial usar get_observaciones().
        """
        return self._parcelas.find_one({"_id": ObjectId(parcela_id)})

    def get_parcelas_por_zona(self, zona: str) -> list[dict]:
        """Devuelve todas las parcelas de una zona geográfica."""
        return list(self._parcelas.find({"zona": zona}))

    def get_parcelas_por_cultivo(self, cultivo: str) -> list[dict]:
        """Devuelve todas las parcelas por tipo de cultivo."""
        return list(self._parcelas.find({"cultivo": cultivo}))

    def get_parcelas_cerca_de(
        self, lat: float, lon: float, radio_km: float
    ) -> list[dict]:
        """
        Devuelve parcelas dentro del radio indicado desde (lat, lon).
        Usa $nearSphere sobre el índice 2dsphere.
        Resultados ordenados de menor a mayor distancia.
        """
        return list(
            self._parcelas.find(
                {
                    "geometria": {
                        "$nearSphere": {
                            "$geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat],
                            },
                            "$maxDistance": radio_km * 1000,
                        }
                    }
                },
                {
                    "nombre": 1, "zona": 1, "cultivo": 1,
                    "variedad": 1, "superficie_ha": 1,
                    "altitud_msnm": 1, "geometria": 1,
                },
            )
        )

    def get_parcelas_en_bbox(
        self,
        sw_lat: float, sw_lon: float,
        ne_lat: float, ne_lon: float,
    ) -> list[dict]:
        """
        Devuelve parcelas dentro del rectángulo geográfico
        definido por las esquinas suroeste y noreste.
        Usa $geoWithin sobre el índice 2dsphere.
        """
        bbox_polygon = {
            "type": "Polygon",
            "coordinates": [[
                [sw_lon, sw_lat],
                [ne_lon, sw_lat],
                [ne_lon, ne_lat],
                [sw_lon, ne_lat],
                [sw_lon, sw_lat],
            ]],
        }
        return list(
            self._parcelas.find(
                {"geometria": {"$geoWithin": {"$geometry": bbox_polygon}}},
                {
                    "nombre": 1, "zona": 1, "cultivo": 1,
                    "variedad": 1, "superficie_ha": 1,
                    "altitud_msnm": 1, "geometria": 1,
                },
            )
        )

    # ------------------------------------------------------------------ #
    #  OBSERVACIONES  (colección separada, referenciada por parcela_id)   #
    # ------------------------------------------------------------------ #

    def agregar_observacion(
        self, parcela_id: str, observacion: Observacion
    ) -> str:
        """
        Inserta una observación satelital en la colección observaciones.
        La vincula a su parcela mediante parcela_id.
        Devuelve el id del documento insertado.

        Antes: $push sobre el array embebido en parcelas.
        Ahora: insert_one en colección propia → sin límite de crecimiento.
        """
        doc = observacion.to_dict()
        doc["parcela_id"] = parcela_id
        resultado = self._observaciones.insert_one(doc)
        return str(resultado.inserted_id)

    def get_observaciones(
        self,
        parcela_id: str,
        desde: date = None,
        hasta: date = None,
    ) -> list[dict]:
        """
        Devuelve el historial de observaciones de una parcela.
        Si se especifican desde y/o hasta, filtra por rango de fechas.
        Ordenado cronológicamente.
        """
        filtro: dict = {"parcela_id": parcela_id}

        if desde or hasta:
            filtro["fecha"] = {}
            if desde:
                filtro["fecha"]["$gte"] = desde.isoformat()
            if hasta:
                filtro["fecha"]["$lte"] = hasta.isoformat()

        return list(
            self._observaciones
            .find(filtro)
            .sort("fecha", ASCENDING)
        )

    def get_ndvi_promedio_por_zona(
        self, zona: str, temporada: str
    ) -> list[dict]:
        """
        Calcula el NDVI promedio de todas las parcelas de una zona
        para una temporada agrícola dada.
        Ej: zona="Nonogasta", temporada="2023/2024"

        Pipeline actualizado: ahora hace $lookup entre parcelas
        y observaciones en lugar de $unwind sobre array embebido.
        """
        y1, y2 = temporada[:4], temporada[-4:]
        pipeline = [
            {"$match": {"zona": zona}},
            {
                "$lookup": {
                    "from": "observaciones",
                    "localField": "_id_str",
                    "foreignField": "parcela_id",
                    "as": "obs",
                    "pipeline": [
                        {"$match": {
                            "fecha": {
                                "$gte": f"{y1}-09-01",
                                "$lte": f"{y2}-03-31",
                            }
                        }}
                    ],
                }
            },
            {"$unwind": "$obs"},
            {
                "$group": {
                    "_id": "$zona",
                    "ndvi_promedio": {"$avg": "$obs.ndvi"},
                    "total_observaciones": {"$sum": 1},
                }
            },
        ]
        return list(self._parcelas.aggregate(pipeline))

    # ------------------------------------------------------------------ #
    #  CAMPAÑAS                                                            #
    # ------------------------------------------------------------------ #

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
            .sort("temporada", ASCENDING)
        )

    # ------------------------------------------------------------------ #
    #  USUARIOS                                                            #
    # ------------------------------------------------------------------ #

    def insertar_usuario(self, usuario: Usuario) -> str:
        """
        Registra un nuevo usuario en el sistema.
        Devuelve el id generado por MongoDB.
        El campo email debe ser único (índice creado en setup_db.py).
        """
        resultado = self._usuarios.insert_one(usuario.to_dict())
        return str(resultado.inserted_id)

    def get_usuario_por_email(self, email: str) -> dict | None:
        """
        Recupera un usuario por su email.
        Usado en el flujo de autenticación.
        """
        return self._usuarios.find_one({"email": email})

    def get_usuario(self, usuario_id: str) -> dict | None:
        """Recupera un usuario por su id."""
        return self._usuarios.find_one({"_id": ObjectId(usuario_id)})

    def vincular_parcela(self, usuario_id: str, parcela_id: str) -> bool:
        """
        Asocia una parcela a un usuario.
        Usa $addToSet para evitar duplicados en la lista parcelas_ids.
        Relación N a N: múltiples usuarios pueden compartir una parcela.
        """
        resultado = self._usuarios.update_one(
            {"_id": ObjectId(usuario_id)},
            {"$addToSet": {"parcelas_ids": parcela_id}},
        )
        return resultado.modified_count == 1

    def desvincular_parcela(self, usuario_id: str, parcela_id: str) -> bool:
        """
        Elimina la asociación entre un usuario y una parcela.
        No elimina la parcela ni sus datos.
        """
        resultado = self._usuarios.update_one(
            {"_id": ObjectId(usuario_id)},
            {"$pull": {"parcelas_ids": parcela_id}},
        )
        return resultado.modified_count == 1

    def get_parcelas_de_usuario(self, usuario_id: str) -> list[dict]:
        """
        Devuelve todas las parcelas asociadas a un usuario.
        Resuelve la relación N a N haciendo $lookup desde usuarios
        hacia parcelas por la lista parcelas_ids.
        """
        pipeline = [
            {"$match": {"_id": ObjectId(usuario_id)}},
            {
                "$lookup": {
                    "from": "parcelas",
                    "localField": "parcelas_ids",
                    "foreignField": "_id_str",
                    "as": "parcelas",
                }
            },
            {"$unwind": "$parcelas"},
            {"$replaceRoot": {"newRoot": "$parcelas"}},
        ]
        return list(self._usuarios.aggregate(pipeline))

    def get_usuarios_de_parcela(self, parcela_id: str) -> list[dict]:
        """
        Devuelve todos los usuarios que tienen acceso a una parcela.
        Consulta inversa de la relación N a N.
        """
        return list(
            self._usuarios.find(
                {"parcelas_ids": parcela_id},
                {"nombre": 1, "email": 1, "rol": 1},
            )
        )
