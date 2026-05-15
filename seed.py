from datetime import date
from dao import SaviaDAO
from db_models import Cliente, Usuario, Parcela, Observacion, Campana, Alerta, Reporte


def seed():
    """
    Carga datos de prueba realistas para el departamento Chilecito.
    Cubre las siete colecciones del sistema.

    Seguro para correr múltiples veces — limpia los datos existentes
    antes de insertar para evitar duplicados.
    """
    dao = SaviaDAO()

    print("Limpiando datos existentes...")
    dao._clientes.delete_many({})
    dao._usuarios.delete_many({})
    dao._parcelas.delete_many({})
    dao._observaciones.delete_many({})
    dao._campanas.delete_many({})
    dao._alertas.delete_many({})
    dao._reportes.delete_many({})

    print("\nIniciando carga de datos de prueba...\n")

    # -----------------------------------------------------------------------
    # Clientes
    # -----------------------------------------------------------------------
    print("Insertando clientes...")

    cliente_condor = Cliente(
        nombre="Bodega El Cóndor",
        cuit="30-12345678-9",
        tipo="bodega",
        plan="profesional",
        fecha_alta=date(2024, 3, 1),
        contacto={"email": "admin@elcondor.com", "telefono": "03825-420000"},
        direccion={"localidad": "Nonogasta", "provincia": "La Rioja", "pais": "Argentina"},
    )
    id_condor = dao.registrar_cliente(cliente_condor)
    print(f"  ✓ Cliente: Bodega El Cóndor")

    cliente_sarmientos = Cliente(
        nombre="Finca Los Sarmientos",
        cuit="20-87654321-3",
        tipo="productor_independiente",
        plan="basico",
        fecha_alta=date(2024, 4, 15),
        contacto={"email": "contacto@lossarmientos.com", "telefono": "03825-430000"},
        direccion={"localidad": "Los Sarmientos", "provincia": "La Rioja", "pais": "Argentina"},
    )
    id_sarmientos = dao.registrar_cliente(cliente_sarmientos)
    print(f"  ✓ Cliente: Finca Los Sarmientos")

    # -----------------------------------------------------------------------
    # Usuarios
    # -----------------------------------------------------------------------
    print("\nInsertando usuarios...")

    dao.registrar_usuario(Usuario(
        cliente_id=id_condor,
        nombre="Ana Gómez",
        email="ana@elcondor.com",
        rol="admin",
        fecha_alta=date(2024, 3, 1),
    ))
    print(f"  ✓ Usuario: Ana Gómez (admin — Bodega El Cóndor)")

    dao.registrar_usuario(Usuario(
        cliente_id=id_condor,
        nombre="Marcos Díaz",
        email="marcos@elcondor.com",
        rol="operador",
        fecha_alta=date(2024, 3, 5),
    ))
    print(f"  ✓ Usuario: Marcos Díaz (operador — Bodega El Cóndor)")

    id_usuario_sarmientos = dao.registrar_usuario(Usuario(
        cliente_id=id_sarmientos,
        nombre="Lucía Pérez",
        email="lucia@lossarmientos.com",
        rol="visor",
        fecha_alta=date(2024, 4, 15),
    ))
    print(f"  ✓ Usuario: Lucía Pérez (visor — Finca Los Sarmientos)")

    # -----------------------------------------------------------------------
    # Parcelas
    # -----------------------------------------------------------------------
    print("\nInsertando parcelas...")

    parcelas_data = [
        {
            "cliente_id": id_condor,
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
                    [-67.4821, -29.0134],
                ]],
            },
        },
        {
            "cliente_id": id_condor,
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
                    [-67.5198, -28.9876],
                ]],
            },
        },
        {
            "cliente_id": id_sarmientos,
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
                    [-67.5012, -29.0201],
                ]],
            },
        },
        {
            "cliente_id": id_sarmientos,
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
                    [-67.4654, -29.0432],
                ]],
            },
        },
    ]

    ids_parcelas = {}
    for data in parcelas_data:
        parcela = Parcela(
            cliente_id=data["cliente_id"],
            nombre=data["nombre"],
            cultivo=data["cultivo"],
            zona=data["zona"],
            geometria=data["geometria"],
            variedad=data["variedad"],
            superficie_ha=data["superficie_ha"],
            altitud_msnm=data["altitud_msnm"],
        )
        pid = dao.registrar_parcela(parcela)
        ids_parcelas[data["nombre"]] = pid
        print(f"  ✓ Parcela: {data['nombre']} ({data['zona']})")

    # -----------------------------------------------------------------------
    # Observaciones
    # -----------------------------------------------------------------------
    print("\nInsertando observaciones satelitales...")

    # Formato: (fecha, ndvi, evi, ndwi, nubosidad_pct)
    series = {
        "Finca El Peñón": [
            (date(2023, 9,  5),  0.31, 0.22, 0.09, 3.2),
            (date(2023, 9,  20), 0.38, 0.27, 0.11, 7.1),
            (date(2023, 10,  5), 0.45, 0.33, 0.14, 2.8),
            (date(2023, 10, 20), 0.52, 0.39, 0.16, 5.4),
            (date(2023, 11,  4), 0.61, 0.46, 0.19, 1.9),
            (date(2023, 11, 19), 0.68, 0.51, 0.21, 8.3),
            (date(2023, 12,  4), 0.71, 0.54, 0.23, 4.1),
            (date(2023, 12, 19), 0.69, 0.52, 0.22, 6.7),
            (date(2024,  1,  3), 0.65, 0.49, 0.20, 3.5),
            (date(2024,  1, 18), 0.58, 0.44, 0.17, 2.1),
            (date(2024,  2,  2), 0.47, 0.35, 0.13, 9.8),
            (date(2024,  2, 17), 0.38, 0.28, 0.10, 4.6),
            (date(2024,  3,  3), 0.29, 0.21, 0.08, 1.3),
        ],
        "Finca Los Sarmientos Norte": [
            (date(2023, 9,  6),  0.29, 0.20, 0.08, 5.1),
            (date(2023, 9,  21), 0.35, 0.25, 0.10, 3.8),
            (date(2023, 10,  6), 0.43, 0.31, 0.13, 6.2),
            (date(2023, 10, 21), 0.50, 0.37, 0.15, 2.4),
            (date(2023, 11,  5), 0.58, 0.44, 0.18, 4.7),
            (date(2023, 11, 20), 0.64, 0.48, 0.20, 1.6),
            (date(2023, 12,  5), 0.68, 0.51, 0.22, 7.3),
            (date(2023, 12, 20), 0.66, 0.50, 0.21, 3.9),
            (date(2024,  1,  4), 0.61, 0.46, 0.19, 5.5),
            (date(2024,  1, 19), 0.53, 0.40, 0.16, 2.8),
            (date(2024,  2,  3), 0.44, 0.33, 0.12, 8.1),
            (date(2024,  2, 18), 0.35, 0.26, 0.09, 4.3),
            (date(2024,  3,  4), 0.27, 0.19, 0.07, 1.8),
        ],
        "Viña Famatina": [
            (date(2023, 9,  7),  0.33, 0.24, 0.10, 2.5),
            (date(2023, 9,  22), 0.40, 0.29, 0.12, 4.1),
            (date(2023, 10,  7), 0.49, 0.36, 0.15, 3.3),
            (date(2023, 10, 22), 0.57, 0.43, 0.18, 6.8),
            (date(2023, 11,  6), 0.65, 0.49, 0.21, 1.4),
            (date(2023, 11, 21), 0.72, 0.55, 0.24, 5.2),
            (date(2023, 12,  6), 0.75, 0.57, 0.25, 3.7),
            (date(2023, 12, 21), 0.73, 0.56, 0.24, 7.9),
            (date(2024,  1,  5), 0.68, 0.51, 0.22, 2.6),
            (date(2024,  1, 20), 0.60, 0.45, 0.19, 4.0),
            (date(2024,  2,  4), 0.50, 0.38, 0.15, 1.7),
            (date(2024,  2, 19), 0.41, 0.30, 0.11, 6.3),
            (date(2024,  3,  5), 0.31, 0.23, 0.09, 2.9),
        ],
    }

    for nombre_parcela, observaciones in series.items():
        pid = ids_parcelas[nombre_parcela]
        for fecha, ndvi, evi, ndwi, nubosidad in observaciones:
            obs = Observacion(
                parcela_id=pid,
                fecha=fecha,
                ndvi=ndvi,
                evi=evi,
                ndwi=ndwi,
                nubosidad_pct=nubosidad,
            )
            dao.registrar_observacion(obs)
        print(f"  ✓ {len(observaciones)} observaciones → {nombre_parcela}")

    # -----------------------------------------------------------------------
    # Campañas
    # -----------------------------------------------------------------------
    print("\nInsertando campañas...")

    campanas_data = [
        {
            "nombre": "Finca El Peñón",
            "temporada": "2023/2024",
            "fecha_cosecha": date(2024, 2, 28),
            "rendimiento_kg_ha": 8400,
            "notas": "Sin eventos climáticos adversos. Riego controlado desde noviembre.",
        },
        {
            "nombre": "Finca Los Sarmientos Norte",
            "temporada": "2023/2024",
            "fecha_cosecha": date(2024, 3, 5),
            "rendimiento_kg_ha": 7200,
            "notas": "Helada leve en octubre. Recuperación normal.",
        },
        {
            "nombre": "Viña Famatina",
            "temporada": "2023/2024",
            "fecha_cosecha": date(2024, 2, 20),
            "rendimiento_kg_ha": 9100,
            "notas": "Temporada excelente. Sin incidentes.",
        },
    ]

    for data in campanas_data:
        campana = Campana(
            parcela_id=ids_parcelas[data["nombre"]],
            temporada=data["temporada"],
            fecha_cosecha=data["fecha_cosecha"],
            rendimiento_kg_ha=data["rendimiento_kg_ha"],
            notas=data["notas"],
        )
        dao.registrar_campana(campana)
        print(f"  ✓ Campaña: {data['nombre']} {data['temporada']} — {data['rendimiento_kg_ha']} kg/ha")

    # -----------------------------------------------------------------------
    # Alertas
    # -----------------------------------------------------------------------
    print("\nInsertando alertas...")

    pid_sarmientos = ids_parcelas["Finca Los Sarmientos Norte"]

    dao.registrar_alerta(Alerta(
        parcela_id=pid_sarmientos,
        fecha=date(2024, 1, 19),
        tipo="estres_hidrico",
        indice="NDWI",
        valor_detectado=0.16,
        umbral=0.18,
    ))
    print("  ✓ Alerta: estrés hídrico — Finca Los Sarmientos Norte")

    dao.registrar_alerta(Alerta(
        parcela_id=ids_parcelas["Finca Vichigasta Sur"],
        fecha=date(2024, 2, 10),
        tipo="ndvi_bajo",
        indice="NDVI",
        valor_detectado=0.28,
        umbral=0.35,
    ))
    print("  ✓ Alerta: NDVI bajo — Finca Vichigasta Sur")

    # -----------------------------------------------------------------------
    # Reportes
    # -----------------------------------------------------------------------
    print("\nInsertando reportes...")

    dao.generar_reporte(Reporte(
        cliente_id=id_condor,
        nombre="Resumen NDVI — Temporada 2023/2024",
        tipo="resumen_indices",
        periodo={"desde": "2023-09-01", "hasta": "2024-03-31"},
        parcelas_incluidas=[
            ids_parcelas["Finca El Peñón"],
            ids_parcelas["Viña Famatina"],
        ],
        fecha_generacion=date(2024, 4, 1),
        generado_por=id_usuario_sarmientos,
        resumen={
            "ndvi_promedio": 0.54,
            "parcelas_en_alerta": 0,
            "observaciones_procesadas": 26,
        },
    ))
    print("  ✓ Reporte: Resumen NDVI — Bodega El Cóndor")

    dao.cerrar()
    print("\n✓ Seed completado.")


if __name__ == "__main__":
    seed()
