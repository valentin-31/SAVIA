from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from bson import ObjectId
from datetime import date

from db_models import Cliente, Usuario, Parcela, Observacion, Campana, Alerta, Reporte
from config_vars import MONGO_URI, DB_NAME


class SaviaDAO:
    """
    Módulo de acceso a datos para el sistema SAVIA.
    Abstrae todas las operaciones sobre MongoDB en métodos
    con semántica del dominio vitícola-satelital.

    Cubre las siete colecciones del sistema:
        clientes, usuarios, parcelas, observaciones,
        campañas, alertas, reportes.

    Los métodos reciben parámetros del dominio (zona, temporada, ndvi)
    — nunca queries de MongoDB en crudo. El filtro cliente_id se aplica
    siempre en las colecciones operativas para garantizar el aislamiento
    entre organizaciones (modelo shared-database + cliente_id).
    """

    def __init__(self):
        self._client = MongoClient(MONGO_URI)
        self._db = self._client[DB_NAME]

        self._clientes: Collection = self._db["clientes"]
        self._usuarios: Collection = self._db["usuarios"]
        self._parcelas: Collection = self._db["parcelas"]
        self._observaciones: Collection = self._db["observaciones"]
        self._campanas: Collection = self._db["campanas"]
        self._alertas: Collection = self._db["alertas"]
        self._reportes: Collection = self._db["reportes"]

    def cerrar(self):
        """Cierra la conexión con MongoDB."""
        self._client.close()

    # -----------------------------------------------------------------------
    # Colección: clientes
    # -----------------------------------------------------------------------

    def registrar_cliente(self, cliente: Cliente) -> str:
        """
        Registra una organización nueva en el sistema.
        Devuelve el cliente_id generado por MongoDB, que debe propagarse
        a todas las colecciones operativas que pertenezcan a este cliente.

        Ejemplo
        -------
        cliente = Cliente(
            nombre="Bodega El Cóndor",
            cuit="30-12345678-9",
            tipo="bodega",
            plan="profesional",
            fecha_alta=date.today(),
            contacto={"email": "admin@elcondor.com", "telefono": "03825-000000"},
            direccion={"localidad": "Nonogasta", "provincia": "La Rioja", "pais": "Argentina"},
        )
        cliente_id = dao.registrar_cliente(cliente)
        """
        resultado = self._clientes.insert_one(cliente.to_dict())
        return str(resultado.inserted_id)

    def get_cliente(self, cliente_id: str) -> dict | None:
        """
        Recupera los datos de una organización por su id.
        Devuelve el documento completo o None si no existe.
        """
        return self._clientes.find_one({"_id": ObjectId(cliente_id)})

    def suspender_cliente(self, cliente_id: str) -> bool:
        """
        Desactiva el acceso de un cliente sin eliminar sus datos históricos.
        Devuelve True si el documento fue modificado.
        """
        resultado = self._clientes.update_one(
            {"_id": ObjectId(cliente_id)},
            {"$set": {"activo": False}},
        )
        return resultado.modified_count == 1

    def reactivar_cliente(self, cliente_id: str) -> bool:
        """
        Reactiva un cliente previamente suspendido.
        Devuelve True si el documento fue modificado.
        """
        resultado = self._clientes.update_one(
            {"_id": ObjectId(cliente_id)},
            {"$set": {"activo": True}},
        )
        return resultado.modified_count == 1

    # -----------------------------------------------------------------------
    # Colección: usuarios
    # -----------------------------------------------------------------------

    def registrar_usuario(self, usuario: Usuario) -> str:
        """
        Registra un usuario nuevo en nombre de un cliente.
        El campo email debe ser único en toda la colección.
        Devuelve el usuario_id generado por MongoDB.

        Ejemplo
        -------
        usuario = Usuario(
            cliente_id=cliente_id,
            nombre="Ana Gómez",
            email="ana@elcondor.com",
            rol="operador",
            fecha_alta=date.today(),
        )
        usuario_id = dao.registrar_usuario(usuario)
        """
        resultado = self._usuarios.insert_one(usuario.to_dict())
        return str(resultado.inserted_id)

    def get_usuarios_por_cliente(self, cliente_id: str) -> list[dict]:
        """
        Devuelve todos los usuarios activos de una organización.
        Ordenados alfabéticamente por nombre.
        """
        return list(
            self._usuarios
            .find({"cliente_id": cliente_id, "activo": True})
            .sort("nombre", ASCENDING)
        )

    def get_usuario_por_email(self, email: str) -> dict | None:
        """
        Recupera un usuario por su email de inicio de sesión.
        Devuelve el documento completo o None si no existe.
        """
        return self._usuarios.find_one({"email": email})

    def desactivar_usuario(self, usuario_id: str) -> bool:
        """
        Revoca el acceso de un usuario sin eliminar su registro.
        Devuelve True si el documento fue modificado.
        """
        resultado = self._usuarios.update_one(
            {"_id": ObjectId(usuario_id)},
            {"$set": {"activo": False}},
        )
        return resultado.modified_count == 1

    # -----------------------------------------------------------------------
    # Colección: parcelas
    # -----------------------------------------------------------------------

    def registrar_parcela(self, parcela: Parcela) -> str:
        """
        Registra un viñedo nuevo con sus datos estáticos y geometría.
        El cliente_id dentro del objeto Parcela garantiza que la parcela
        queda asociada a la organización correcta.
        Devuelve el parcela_id generado por MongoDB.

        Ejemplo
        -------
        parcela = Parcela(
            cliente_id=cliente_id,
            nombre="Finca El Peñón",
            cultivo="vid",
            variedad="Torrontés Riojano",
            zona="Nonogasta",
            superficie_ha=3.8,
            altitud_msnm=1050,
            geometria={
                "type": "Polygon",
                "coordinates": [[
                    [-67.4821, -29.0134],
                    [-67.4798, -29.0134],
                    [-67.4798, -29.0158],
                    [-67.4821, -29.0158],
                    [-67.4821, -29.0134],
                ]]
            }
        )
        parcela_id = dao.registrar_parcela(parcela)
        """
        resultado = self._parcelas.insert_one(parcela.to_dict())
        return str(resultado.inserted_id)

    def get_parcela(self, parcela_id: str) -> dict | None:
        """
        Recupera los datos estáticos de una parcela por su id.
        No incluye el historial de observaciones — para eso
        usar get_observaciones(parcela_id).
        Devuelve el documento o None si no existe.
        """
        return self._parcelas.find_one({"_id": ObjectId(parcela_id)})

    def get_parcelas_por_zona(self, cliente_id: str, zona: str) -> list[dict]:
        """
        Devuelve todas las parcelas de un cliente en una zona geográfica.
        Ej: zona="Nonogasta", zona="Los Sarmientos"

        El filtro cliente_id garantiza que solo se devuelven parcelas
        de la organización correspondiente.
        """
        return list(
            self._parcelas.find({"cliente_id": cliente_id, "zona": zona})
        )

    def get_parcelas_por_cultivo(self, cliente_id: str, cultivo: str) -> list[dict]:
        """
        Devuelve todas las parcelas de un cliente por tipo de cultivo.
        Ej: cultivo="vid", cultivo="olivo", cultivo="nogal"
        """
        return list(
            self._parcelas.find({"cliente_id": cliente_id, "cultivo": cultivo})
        )

    def get_parcelas_cerca_de(
        self,
        cliente_id: str,
        lat: float,
        lon: float,
        radio_km: float,
    ) -> list[dict]:
        """
        Devuelve las parcelas de un cliente dentro del radio indicado
        desde el punto (lat, lon), ordenadas de menor a mayor distancia.

        Usa $nearSphere sobre el índice 2dsphere del campo geometria.

        Parámetros
        ----------
        cliente_id : organización propietaria de las parcelas
        lat        : latitud del punto de referencia en grados decimales
        lon        : longitud del punto de referencia en grados decimales
        radio_km   : radio máximo de búsqueda en kilómetros

        Ejemplo
        -------
        # Parcelas dentro de 8 km del centro de Chilecito
        parcelas = dao.get_parcelas_cerca_de(
            cliente_id=cliente_id,
            lat=-29.0, lon=-67.49, radio_km=8,
        )
        """
        return list(
            self._parcelas.find(
                {
                    "cliente_id": cliente_id,
                    "geometria": {
                        "$nearSphere": {
                            "$geometry": {
                                "type": "Point",
                                # GeoJSON: longitud siempre va primero
                                "coordinates": [lon, lat],
                            },
                            "$maxDistance": radio_km * 1000,
                        }
                    },
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
        cliente_id: str,
        sw_lat: float,
        sw_lon: float,
        ne_lat: float,
        ne_lon: float,
    ) -> list[dict]:
        """
        Devuelve las parcelas de un cliente dentro del rectángulo
        geográfico definido por las esquinas suroeste (sw) y noreste (ne).

        Usa $geoWithin + $geometry con un Polygon GeoJSON —
        compatible con el índice 2dsphere creado en setup_db.py.

        Parámetros
        ----------
        cliente_id : organización propietaria de las parcelas
        sw_lat / sw_lon : esquina suroeste
        ne_lat / ne_lon : esquina noreste

        Ejemplo
        -------
        # Área que cubre el sector Nonogasta–Los Sarmientos
        parcelas = dao.get_parcelas_en_bbox(
            cliente_id=cliente_id,
            sw_lat=-29.03, sw_lon=-67.52,
            ne_lat=-28.98, ne_lon=-67.46,
        )
        """
        # El anillo del polígono debe cerrarse: primer punto = último punto.
        # Orden: suroeste → sureste → noreste → noroeste → suroeste
        bbox_polygon = {
            "type": "Polygon",
            "coordinates": [[
                [sw_lon, sw_lat],  # suroeste
                [ne_lon, sw_lat],  # sureste
                [ne_lon, ne_lat],  # noreste
                [sw_lon, ne_lat],  # noroeste
                [sw_lon, sw_lat],  # cierre del anillo
            ]],
        }

        return list(
            self._parcelas.find(
                {
                    "cliente_id": cliente_id,
                    "geometria": {"$geoWithin": {"$geometry": bbox_polygon}},
                },
                {
                    "nombre": 1, "zona": 1, "cultivo": 1,
                    "variedad": 1, "superficie_ha": 1,
                    "altitud_msnm": 1, "geometria": 1,
                },
            )
        )

    # -----------------------------------------------------------------------
    # Colección: observaciones
    # -----------------------------------------------------------------------

    def registrar_observacion(self, observacion: Observacion) -> str:
        """
        Inserta una observación satelital de Sentinel-2 en la colección
        dedicada. El campo parcela_id vincula la observación con su parcela.

        La colección tiene un índice compuesto sobre {parcela_id, fecha}
        definido en setup_db.py, que hace eficientes las consultas
        de rango temporal durante el entrenamiento del modelo.

        Ejemplo
        -------
        obs = Observacion(
            parcela_id=parcela_id,
            fecha=date(2024, 1, 5),
            ndvi=0.71, evi=0.54, ndwi=0.18,
            nubosidad_pct=4,
        )
        dao.registrar_observacion(obs)
        """
        resultado = self._observaciones.insert_one(observacion.to_dict())
        return str(resultado.inserted_id)

    def get_observaciones(
        self,
        parcela_id: str,
        desde: date = None,
        hasta: date = None,
    ) -> list[dict]:
        """
        Devuelve el historial satelital de una parcela.
        Si se especifican desde y/o hasta, filtra por rango de fechas.
        Los resultados vienen ordenados cronológicamente.

        Es el método central del sistema: el pipeline de entrenamiento
        del modelo llama a este método para obtener la serie temporal
        de cada parcela durante el ajuste de parámetros.

        Parámetros
        ----------
        parcela_id : identificador de la parcela
        desde      : fecha de inicio del rango (inclusive), opcional
        hasta      : fecha de fin del rango (inclusive), opcional

        Ejemplo
        -------
        # Historial completo
        obs = dao.get_observaciones(parcela_id)

        # Solo la temporada 2023/2024 (sep 2023 – mar 2024)
        obs = dao.get_observaciones(
            parcela_id,
            desde=date(2023, 9, 1),
            hasta=date(2024, 3, 31),
        )
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
        self,
        cliente_id: str,
        zona: str,
        temporada: str,
    ) -> list[dict]:
        """
        Calcula el NDVI promedio de todas las parcelas de un cliente
        en una zona geográfica para una temporada agrícola dada.

        Usa un $lookup para cruzar parcelas con observaciones —
        necesario porque las observaciones ya no están embebidas.
        El filtro de fechas cubre sep del primer año a mar del segundo,
        que corresponde al ciclo vegetativo de la vid en Chilecito.

        Parámetros
        ----------
        cliente_id : organización propietaria de las parcelas
        zona       : sector geográfico (ej: "Nonogasta")
        temporada  : año agrícola en formato "2023/2024"

        Ejemplo
        -------
        resultado = dao.get_ndvi_promedio_por_zona(
            cliente_id=cliente_id,
            zona="Nonogasta",
            temporada="2023/2024",
        )
        # [{"_id": "Nonogasta", "ndvi_promedio": 0.68, "total_observaciones": 412}]
        """
        anio_inicio = temporada[:4]
        anio_fin = temporada[-4:]

        pipeline = [
            # 1. Solo parcelas del cliente en la zona solicitada
            {"$match": {"cliente_id": cliente_id, "zona": zona}},

            # 2. Traer las observaciones de cada parcela
            {"$lookup": {
                "from": "observaciones",
                "localField": "_id",     # _id en parcelas es ObjectId
                "foreignField": "parcela_id",  # string en observaciones
                "as": "obs",
                # pipeline interno para filtrar por fecha antes de unir
                "pipeline": [
                    {"$match": {"$expr": {"$and": [
                        {"$gte": ["$fecha", anio_inicio + "-09-01"]},
                        {"$lte": ["$fecha", anio_fin + "-03-31"]},
                    ]}}},
                ],
            }},

            # 3. Expandir el array de observaciones — una fila por obs
            {"$unwind": "$obs"},

            # 4. Agrupar por zona y calcular el promedio
            {"$group": {
                "_id": "$zona",
                "ndvi_promedio": {"$avg": "$obs.ndvi"},
                "total_observaciones": {"$sum": 1},
            }},
        ]

        return list(self._parcelas.aggregate(pipeline))

    # -----------------------------------------------------------------------
    # Colección: campañas
    # -----------------------------------------------------------------------

    def registrar_campana(self, campana: Campana) -> str:
        """
        Registra los datos de cosecha reales de una temporada agrícola.
        Es el valor objetivo del modelo: sin campañas históricas
        no hay entrenamiento supervisado posible.
        Devuelve el id generado por MongoDB.

        Ejemplo
        -------
        campana = Campana(
            parcela_id=parcela_id,
            temporada="2023/2024",
            fecha_cosecha=date(2024, 2, 28),
            rendimiento_kg_ha=8400,
            notas="Sin eventos climáticos adversos. Riego controlado desde noviembre.",
        )
        dao.registrar_campana(campana)
        """
        resultado = self._campanas.insert_one(campana.to_dict())
        return str(resultado.inserted_id)

    def get_campanas(self, parcela_id: str) -> list[dict]:
        """
        Devuelve el historial completo de cosechas de una parcela,
        ordenado cronológicamente por temporada.
        """
        return list(
            self._campanas
            .find({"parcela_id": parcela_id})
            .sort("temporada", ASCENDING)
        )

    def get_rendimiento_promedio_por_zona(
        self,
        cliente_id: str,
        zona: str,
    ) -> list[dict]:
        """
        Calcula el rendimiento promedio histórico (kg/ha) de todas las
        parcelas de un cliente en una zona, agrupado por temporada.

        Útil para comparar el rendimiento real contra la predicción
        del modelo una vez que está entrenado.

        Ejemplo
        -------
        resultado = dao.get_rendimiento_promedio_por_zona(
            cliente_id=cliente_id, zona="Nonogasta"
        )
        # [{"_id": "2022/2023", "rendimiento_promedio": 7850.0, "parcelas": 4}, ...]
        """
        pipeline = [
            # 1. Solo parcelas del cliente en la zona
            {"$match": {"cliente_id": cliente_id, "zona": zona}},

            # 2. Traer campañas de cada parcela
            {"$lookup": {
                "from": "campanas",
                "localField": "_id",
                "foreignField": "parcela_id",
                "as": "campanas",
            }},

            {"$unwind": "$campanas"},

            # 3. Agrupar por temporada
            {"$group": {
                "_id": "$campanas.temporada",
                "rendimiento_promedio": {"$avg": "$campanas.rendimiento_kg_ha"},
                "parcelas": {"$sum": 1},
            }},

            {"$sort": {"_id": ASCENDING}},
        ]

        return list(self._parcelas.aggregate(pipeline))

    # -----------------------------------------------------------------------
    # Colección: alertas
    # -----------------------------------------------------------------------

    def registrar_alerta(self, alerta: Alerta) -> str:
        """
        Registra un evento de alerta detectado sobre una parcela.
        El estado inicial es siempre "activa".
        Devuelve el id generado por MongoDB.

        Ejemplo
        -------
        alerta = Alerta(
            parcela_id=parcela_id,
            fecha=date(2024, 1, 10),
            tipo="estres_hidrico",
            indice="NDWI",
            valor_detectado=0.09,
            umbral=0.15,
        )
        dao.registrar_alerta(alerta)
        """
        resultado = self._alertas.insert_one(alerta.to_dict())
        return str(resultado.inserted_id)

    def get_alertas_activas_por_parcela(self, parcela_id: str) -> list[dict]:
        """
        Devuelve todas las alertas activas de una parcela,
        ordenadas por fecha descendente (la más reciente primero).
        """
        return list(
            self._alertas
            .find({"parcela_id": parcela_id, "estado": "activa"})
            .sort("fecha", -1)
        )

    def resolver_alerta(self, alerta_id: str) -> bool:
        """
        Marca una alerta como resuelta.
        Devuelve True si el documento fue modificado.
        """
        resultado = self._alertas.update_one(
            {"_id": ObjectId(alerta_id)},
            {"$set": {"estado": "resuelta"}},
        )
        return resultado.modified_count == 1

    def ignorar_alerta(self, alerta_id: str) -> bool:
        """
        Marca una alerta como ignorada (descartada por el operador).
        Devuelve True si el documento fue modificado.
        """
        resultado = self._alertas.update_one(
            {"_id": ObjectId(alerta_id)},
            {"$set": {"estado": "ignorada"}},
        )
        return resultado.modified_count == 1

    # -----------------------------------------------------------------------
    # Colección: reportes
    # -----------------------------------------------------------------------

    def generar_reporte(self, reporte: Reporte) -> str:
        """
        Almacena un reporte generado para un cliente.
        El campo resumen es un snapshot calculado externamente —
        el DAO lo persiste tal como llega, sin recalcular.
        Devuelve el id generado por MongoDB.

        Ejemplo
        -------
        reporte = Reporte(
            cliente_id=cliente_id,
            nombre="Resumen NDVI - Temporada 2024",
            tipo="resumen_indices",
            periodo={"desde": "2023-09-01", "hasta": "2024-03-31"},
            parcelas_incluidas=[parcela_id_1, parcela_id_2],
            fecha_generacion=date.today(),
            generado_por=usuario_id,
            resumen={
                "ndvi_promedio": 0.68,
                "parcelas_en_alerta": 1,
                "observaciones_procesadas": 412,
            },
        )
        dao.generar_reporte(reporte)
        """
        resultado = self._reportes.insert_one(reporte.to_dict())
        return str(resultado.inserted_id)

    def get_reportes_por_cliente(self, cliente_id: str) -> list[dict]:
        """
        Devuelve todos los reportes de un cliente,
        ordenados por fecha de generación descendente.
        """
        return list(
            self._reportes
            .find({"cliente_id": cliente_id})
            .sort("fecha_generacion", -1)
        )

    def marcar_reporte_visto(self, reporte_id: str) -> bool:
        """
        Actualiza el estado del reporte a 'visto' cuando el cliente
        accede al documento por primera vez.
        Devuelve True si el documento fue modificado.
        """
        resultado = self._reportes.update_one(
            {"_id": ObjectId(reporte_id)},
            {"$set": {"estado": "visto"}},
        )
        return resultado.modified_count == 1
