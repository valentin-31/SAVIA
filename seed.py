from datetime import date
from dao import VinedoDAO
from db_models import Parcela, Observacion, Campana


def seed():
    dao = VinedoDAO()
    print("Iniciando carga de datos de prueba...")

    # --- PARCELAS ---
    parcelas_data = [
        {
            "nombre": "Finca El Peñón",
            "cultivo": "vid",
            "variedad": "Torrontés Riojano",
            "superficie_ha": 3.8,
            "altitud_msnm": 1050,
            "zona": "Nonogasta",
            "geometria": {
                "type": "Polygon",
                "coordinates": [[
                    [-67.4821, -29.0134],
                    [-67.4798, -29.0134],
                    [-67.4798, -29.0158],
                    [-67.4821, -29.0158],
                    [-67.4821, -29.0134]
                ]]
            }
        },
        {
            "nombre": "Finca Los Sarmientos Norte",
            "cultivo": "vid",
            "variedad": "Malbec",
            "superficie_ha": 5.2,
            "altitud_msnm": 980,
            "zona": "Los Sarmientos",
            "geometria": {
                "type": "Polygon",
                "coordinates": [[
                    [-67.5012, -29.0201],
                    [-67.4989, -29.0201],
                    [-67.4989, -29.0225],
                    [-67.5012, -29.0225],
                    [-67.5012, -29.0201]
                ]]
            }
        },
        {
            "nombre": "Viña Famatina",
            "cultivo": "vid",
            "variedad": "Syrah",
            "superficie_ha": 2.1,
            "altitud_msnm": 1120,
            "zona": "Famatina",
            "geometria": {
                "type": "Polygon",
                "coordinates": [[
                    [-67.5198, -28.9876],
                    [-67.5175, -28.9876],
                    [-67.5175, -28.9900],
                    [-67.5198, -28.9900],
                    [-67.5198, -28.9876]
                ]]
            }
        },
        {
            "nombre": "Finca Vichigasta Sur",
            "cultivo": "vid",
            "variedad": "Bonarda",
            "superficie_ha": 4.5,
            "altitud_msnm": 920,
            "zona": "Vichigasta",
            "geometria": {
                "type": "Polygon",
                "coordinates": [[
                    [-67.4654, -29.0432],
                    [-67.4631, -29.0432],
                    [-67.4631, -29.0456],
                    [-67.4654, -29.0456],
                    [-67.4654, -29.0432]
                ]]
            }
        },
    ]

    ids = {}
    for data in parcelas_data:
        parcela = Parcela(
            nombre=data["nombre"],
            cultivo=data["cultivo"],
            zona=data["zona"],
            geometria=data["geometria"],
            variedad=data["variedad"],
            superficie_ha=data["superficie_ha"],
            altitud_msnm=data["altitud_msnm"]
        )
        pid = dao.insertar_parcela(parcela)
        ids[data["nombre"]] = pid
        print(f"  ✓ Parcela insertada: {data['nombre']} ({data['zona']})")

    # --- OBSERVACIONES ---
    print("\nInsertando observaciones satelitales...")

    # Serie temporal para Finca El Peñón (ciclo completo sep-mar)
    observaciones_penon = [
        (date(2023, 9, 5),  0.31, 0.22, 0.09, 3.2),
        (date(2023, 9, 20), 0.38, 0.27, 0.11, 7.1),
        (date(2023, 10, 5), 0.45, 0.33, 0.14, 2.8),
        (date(2023, 10, 20),0.52, 0.39, 0.16, 5.4),
        (date(2023, 11, 4), 0.61, 0.46, 0.19, 1.9),
        (date(2023, 11, 19),0.68, 0.51, 0.21, 8.3),
        (date(2023, 12, 4), 0.71, 0.54, 0.23, 4.1),
        (date(2023, 12, 19),0.69, 0.52, 0.22, 6.7),
        (date(2024, 1, 3),  0.65, 0.49, 0.20, 3.5),
        (date(2024, 1, 18), 0.58, 0.44, 0.17, 2.1),
        (date(2024, 2, 2),  0.47, 0.35, 0.13, 9.8),
        (date(2024, 2, 17), 0.38, 0.28, 0.10, 4.6),
        (date(2024, 3, 3),  0.29, 0.21, 0.08, 1.3),
    ]

    pid = ids["Finca El Peñón"]
    for fecha, ndvi, evi, ndwi, nubosidad in observaciones_penon:
        obs = Observacion(fecha=fecha, ndvi=ndvi, evi=evi,
                          ndwi=ndwi, nubosidad_pct=nubosidad)
        dao.agregar_observacion(pid, obs)
    print(f"  ✓ {len(observaciones_penon)} observaciones → Finca El Peñón")

    # Serie temporal para Finca Los Sarmientos Norte
    observaciones_sarmientos = [
        (date(2023, 9, 6),  0.29, 0.20, 0.08, 5.1),
        (date(2023, 9, 21), 0.35, 0.25, 0.10, 3.8),
        (date(2023, 10, 6), 0.43, 0.31, 0.13, 6.2),
        (date(2023, 10, 21),0.50, 0.37, 0.15, 2.4),
        (date(2023, 11, 5), 0.58, 0.44, 0.18, 4.7),
        (date(2023, 11, 20),0.64, 0.48, 0.20, 1.6),
        (date(2023, 12, 5), 0.68, 0.51, 0.22, 7.3),
        (date(2023, 12, 20),0.66, 0.50, 0.21, 3.9),
        (date(2024, 1, 4),  0.61, 0.46, 0.19, 5.5),
        (date(2024, 1, 19), 0.53, 0.40, 0.16, 2.8),
        (date(2024, 2, 3),  0.44, 0.33, 0.12, 8.1),
        (date(2024, 2, 18), 0.35, 0.26, 0.09, 4.3),
        (date(2024, 3, 4),  0.27, 0.19, 0.07, 1.8),
    ]

    pid = ids["Finca Los Sarmientos Norte"]
    for fecha, ndvi, evi, ndwi, nubosidad in observaciones_sarmientos:
        obs = Observacion(fecha=fecha, ndvi=ndvi, evi=evi,
                          ndwi=ndwi, nubosidad_pct=nubosidad)
        dao.agregar_observacion(pid, obs)
    print(f"  ✓ {len(observaciones_sarmientos)} observaciones → Finca Los Sarmientos Norte")

    # --- CAMPAÑAS ---
    print("\nInsertando campañas...")

    campanas_data = [
        {
            "nombre": "Finca El Peñón",
            "temporada": "2023/2024",
            "fecha_cosecha": date(2024, 2, 28),
            "rendimiento_kg_ha": 8400,
            "notas": "Sin eventos climáticos adversos. Riego controlado desde noviembre."
        },
        {
            "nombre": "Finca Los Sarmientos Norte",
            "temporada": "2023/2024",
            "fecha_cosecha": date(2024, 3, 5),
            "rendimiento_kg_ha": 7200,
            "notas": "Helada leve en octubre. Recuperación normal."
        },
        {
            "nombre": "Viña Famatina",
            "temporada": "2023/2024",
            "fecha_cosecha": date(2024, 2, 20),
            "rendimiento_kg_ha": 9100,
            "notas": "Temporada excelente. Sin incidentes."
        },
    ]

    for data in campanas_data:
        campana = Campana(
            parcela_id=ids[data["nombre"]],
            temporada=data["temporada"],
            fecha_cosecha=data["fecha_cosecha"],
            rendimiento_kg_ha=data["rendimiento_kg_ha"],
            notas=data["notas"]
        )
        dao.insertar_campana(campana)
        print(f"  ✓ Campaña insertada: {data['nombre']} {data['temporada']}")

    dao.cerrar()
    print("\n✓ Seed completado.")


if __name__ == "__main__":
    seed()