from pymongo import MongoClient, GEOSPHERE, ASCENDING
from config_vars import MONGO_URI, DB_NAME
from db_models import parcela


def setup():
    """
    Inicializa la base de datos vinedos_chilecito.
    Crea las colecciones parcelas y campanas con sus índices.
    Seguro para correr múltiples veces — no rompe datos existentes.
    """
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Coleccion parcelas
    parcelas = db["parcela"]
    parcelas.create_index([("geometria", GEOSPHERE)])
    parcelas.create_index([("zona", ASCENDING)])
    parcelas.create_index([("cultivo", ASCENDING)])
    parcelas.create_index([("observaciones.fecha", ASCENDING)])
    print("--OK-- Colección parcelas — índices creados")

    # Coleccion campanas
    campanas = db["campanas"]
    campanas.create_index([("parcela_ide", ASCENDING)])
    campanas.create_index([("temporada", ASCENDING)])
    print("--OK-- Colección campanas — índices creados")


    client.close()
    print(f"--OK-- Base de Datos '{DB_NAME}'")

if __name__ == "__main__":
    setup()