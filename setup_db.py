from pymongo import MongoClient, GEOSPHERE, ASCENDING
from config_vars import MONGO_URI, DB_NAME


def setup():
    """
    Inicializa la base de datos SAVIA.
    Crea las siete colecciones con sus índices.
    Seguro para correr múltiples veces — no rompe datos existentes.
    """
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Colección: clientes
    clientes = db["clientes"]
    clientes.create_index([("cuit", ASCENDING)], unique=True)
    clientes.create_index([("activo", ASCENDING)])
    print("--OK-- Colección clientes — índices creados")

    # Colección: usuarios
    usuarios = db["usuarios"]
    usuarios.create_index([("email", ASCENDING)], unique=True)
    usuarios.create_index([("cliente_id", ASCENDING)])
    print("--OK-- Colección usuarios — índices creados")

    # Colección: parcelas
    parcelas = db["parcelas"]
    parcelas.create_index([("geometria", GEOSPHERE)])
    parcelas.create_index([("cliente_id", ASCENDING)])
    parcelas.create_index([("zona", ASCENDING)])
    parcelas.create_index([("cultivo", ASCENDING)])
    print("--OK-- Colección parcelas — índices creados")

    # Colección: observaciones
    # El índice compuesto {parcela_id, fecha} es el más importante del sistema:
    # todas las consultas de historial satelital durante el entrenamiento del
    # modelo lo usan. Se marca unique=True para evitar duplicados de la misma
    # fecha para la misma parcela.
    observaciones = db["observaciones"]
    observaciones.create_index(
        [("parcela_id", ASCENDING), ("fecha", ASCENDING)],
        unique=True,
    )
    print("--OK-- Colección observaciones — índices creados")

    # Colección: campañas
    campanas = db["campanas"]
    campanas.create_index([("parcela_id", ASCENDING)])
    campanas.create_index([("temporada", ASCENDING)])
    print("--OK-- Colección campañas — índices creados")

    # Colección: alertas
    alertas = db["alertas"]
    alertas.create_index([("parcela_id", ASCENDING)])
    alertas.create_index([("estado", ASCENDING)])
    alertas.create_index([("fecha", ASCENDING)])
    print("--OK-- Colección alertas — índices creados")

    # Colección: reportes
    reportes = db["reportes"]
    reportes.create_index([("cliente_id", ASCENDING)])
    reportes.create_index([("fecha_generacion", ASCENDING)])
    print("--OK-- Colección reportes — índices creados")

    client.close()
    print(f"\n--OK-- Base de datos '{DB_NAME}' lista.")


if __name__ == "__main__":
    setup()
