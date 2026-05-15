from pymongo import MongoClient, ASCENDING, GEOSPHERE
from config_vars import MONGO_URI, DB_NAME


def setup():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # -- parcelas ----------------------------------------------------------
    db["parcelas"].create_index([("geometria", GEOSPHERE)])
    db["parcelas"].create_index([("zona", ASCENDING)])
    db["parcelas"].create_index([("cultivo", ASCENDING)])
    print("✓ Colección parcelas — índices creados")

    # -- observaciones (antes embebidas, ahora colección propia) ----------
    # Índice compuesto parcela_id + fecha: cubre todas las consultas de
    # historial y rangos de fecha sin escanear la colección completa.
    db["observaciones"].create_index(
        [("parcela_id", ASCENDING), ("fecha", ASCENDING)]
    )
    print("✓ Colección observaciones — índices creados")

    # -- campañas ----------------------------------------------------------
    db["campanas"].create_index([("parcela_id", ASCENDING)])
    db["campanas"].create_index([("temporada", ASCENDING)])
    print("✓ Colección campanas — índices creados")

    # -- usuarios ----------------------------------------------------------
    # email único: garantiza que no haya dos cuentas con el mismo email.
    db["usuarios"].create_index([("email", ASCENDING)], unique=True)
    # parcelas_ids indexado para la consulta inversa get_usuarios_de_parcela.
    db["usuarios"].create_index([("parcelas_ids", ASCENDING)])
    print("✓ Colección usuarios — índices creados")

    client.close()
    print(f"\n✓ Base de datos '{DB_NAME}' lista")


if __name__ == "__main__":
    setup()
