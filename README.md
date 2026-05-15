# SAVIA
### Sistema de Almacenamiento de Índices de Vegetación para Investigación Agronómica

Proyecto Integrador — Bases de Datos II · Universidad Nacional de Chilecito · 2026

---

## El problema

La producción vitivinícola es la actividad económica principal del departamento Chilecito, La Rioja, con miles de hectáreas cultivadas entre los 900 y 1200 metros sobre el nivel del mar. A pesar de su relevancia económica, estimar cuánto va a producir un viñedo antes de la cosecha sigue siendo un proceso manual, tardío y sin respaldo de datos históricos. Los productores no cuentan hoy con ninguna herramienta que les permita anticipar el rendimiento con semanas de antelación.

El problema concreto es de infraestructura de datos. El satélite Sentinel-2 captura imágenes de cada parcela cada ~5 días con una resolución de 10 metros por píxel. A partir de esas imágenes, Google Earth Engine puede calcular índices espectrales como el NDVI, el EVI y el NDWI — métricas que reflejan la salud, densidad y contenido hídrico de la vegetación a lo largo del ciclo vegetativo. Esos datos existen y son públicos, pero no hay ningún sistema local que los almacene por parcela de forma estructurada y consultable.

SAVIA resuelve ese problema. Es un módulo de acceso a datos que almacena el historial satelital de cada viñedo en MongoDB, lo expone mediante una interfaz Python con semántica del dominio vitícola, y sienta las bases para que un modelo de aprendizaje automático pueda aprender a predecir el rendimiento a partir de la evolución temporal de los índices espectrales.

---

## ¿Qué es SAVIA?

SAVIA es una capa de persistencia para datos satelitales agrícolas. Toma las imágenes del satélite Sentinel-2 procesadas en Google Earth Engine, extrae los índices espectrales relevantes (NDVI, EVI, NDWI) y los almacena por parcela en MongoDB de forma estructurada y consultable.

El sistema está orientado a investigadores, técnicos y productores que necesiten construir o entrenar modelos de predicción de rendimiento agrícola. No incluye el modelo de machine learning ni una interfaz de usuario final — su propósito es proveer una base de datos local, ordenada y eficiente sobre la cual esas capas puedan construirse.

---

## Arquitectura

```
Sentinel-2 (GEE) → seed.py → MongoDB (Docker) → SaviaDAO → Modelo ML
```

- **MongoDB**: 7 colecciones organizadas en tres grupos — tenancy (clientes, usuarios), datos operativos (parcelas, observaciones, campañas) y salidas del sistema (alertas, reportes)
- **SaviaDAO**: abstrae todas las operaciones en métodos con semántica vitícola. El filtro `cliente_id` se aplica siempre en las colecciones operativas para garantizar el aislamiento entre organizaciones
- **demo.ipynb**: demuestra el DAO en acción con gráficos de series temporales

---

## Estructura del proyecto

```
SAVIA/
├── db_models/
│   ├── __init__.py
│   ├── cliente.py       # Organización que accede al sistema (bodega, cooperativa)
│   ├── usuario.py       # Persona que opera en nombre de un cliente
│   ├── parcela.py       # Viñedo con datos geográficos estáticos
│   ├── observacion.py   # Captura satelital individual (Sentinel-2)
│   ├── campana.py       # Registro de cosecha y rendimiento por temporada
│   ├── alerta.py        # Evento detectado sobre un índice espectral
│   └── reporte.py       # Documento generado con métricas del período
├── dao.py               # Clase SaviaDAO — interfaz principal con MongoDB
├── config_vars.py       # Variables de conexión desde .env
├── setup_db.py          # Inicialización de BD e índices
├── seed.py              # Datos de prueba realistas (limpia y recarga)
├── demo.ipynb           # Notebook de demostración
├── docker-compose.yml   # MongoDB 7.0 en contenedor
└── libs.txt             # Dependencias del proyecto
```

---

## Instalación

### Requisitos previos
- Python 3.12 o superior — [python.org/downloads](https://www.python.org/downloads/)
- Docker Desktop corriendo — [docker.com](https://www.docker.com/products/docker-desktop/)
- Git — [git-scm.com](https://git-scm.com/)

Verificá que estén instalados antes de continuar:
```bash
python --version   # debe mostrar 3.12+
docker ps          # debe mostrar una tabla (aunque vacía)
git --version      # debe mostrar la versión instalada
```

### 1. Clonar el repositorio
```bash
git clone https://github.com/valentin-31/SAVIA.git
cd SAVIA
```

### 2. Crear el entorno virtual
```bash
python -m venv .venv
```

Activarlo:
```bash
# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate
```

Cuando el entorno está activo, el prompt muestra `(.venv)` al inicio.

### 3. Instalar dependencias
```bash
pip install -r libs.txt
```

### 4. Configurar variables de entorno
Crear un archivo `.env` en la raíz del proyecto con el siguiente contenido:
```
MONGO_URI=mongodb://localhost:27017
DB_NAME=vinedos_chilecito
```
Este archivo no se sube al repositorio — está excluido por `.gitignore`.

### 5. Levantar MongoDB
```bash
docker compose up -d
```

Verificar que el contenedor esté corriendo:
```bash
docker ps
# debe aparecer savia_mongo con STATUS "Up"
```

### 6. Inicializar la base de datos
```bash
python setup_db.py
```

Resultado esperado:
```
--OK-- Colección clientes — índices creados
--OK-- Colección usuarios — índices creados
--OK-- Colección parcelas — índices creados
--OK-- Colección observaciones — índices creados
--OK-- Colección campañas — índices creados
--OK-- Colección alertas — índices creados
--OK-- Colección reportes — índices creados

--OK-- Base de datos 'vinedos_chilecito' lista.
```

### 7. Cargar datos de prueba
```bash
python seed.py
```

> El seed limpia los datos existentes antes de insertar. Es seguro correrlo múltiples veces.

Resultado esperado:
```
Limpiando datos existentes...

Iniciando carga de datos de prueba...

Insertando clientes...
  ✓ Cliente: Bodega El Cóndor
  ✓ Cliente: Finca Los Sarmientos

Insertando usuarios...
  ✓ Usuario: Ana Gómez (admin — Bodega El Cóndor)
  ✓ Usuario: Marcos Díaz (operador — Bodega El Cóndor)
  ✓ Usuario: Lucía Pérez (visor — Finca Los Sarmientos)

Insertando parcelas...
  ✓ Parcela: Finca El Peñón (Nonogasta)
  ✓ Parcela: Viña Famatina (Famatina)
  ✓ Parcela: Finca Los Sarmientos Norte (Los Sarmientos)
  ✓ Parcela: Finca Vichigasta Sur (Vichigasta)

Insertando observaciones satelitales...
  ✓ 13 observaciones → Finca El Peñón
  ✓ 13 observaciones → Finca Los Sarmientos Norte
  ✓ 13 observaciones → Viña Famatina

Insertando campañas...
  ✓ Campaña: Finca El Peñón 2023/2024 — 8400 kg/ha
  ✓ Campaña: Finca Los Sarmientos Norte 2023/2024 — 7200 kg/ha
  ✓ Campaña: Viña Famatina 2023/2024 — 9100 kg/ha

Insertando alertas...
  ✓ Alerta: estrés hídrico — Finca Los Sarmientos Norte
  ✓ Alerta: NDVI bajo — Finca Vichigasta Sur

Insertando reportes...
  ✓ Reporte: Resumen NDVI — Bodega El Cóndor

✓ Seed completado.
```

### 8. Ejecutar el notebook de demostración
```bash
jupyter notebook demo.ipynb
```

---

## Uso del DAO

`SaviaDAO` es la única interfaz entre el sistema y MongoDB.
Todos los métodos reciben parámetros del dominio vitícola — nunca queries en crudo.
El parámetro `cliente_id` se aplica en todas las consultas operativas para garantizar el aislamiento entre organizaciones.

```python
from dao import SaviaDAO
from db_models import Cliente, Usuario, Parcela, Observacion, Campana, Alerta, Reporte
from datetime import date

dao = SaviaDAO()

# --- Clientes ---
cliente = Cliente(
    nombre="Bodega El Cóndor",
    cuit="30-12345678-9",
    tipo="bodega",           # bodega | productor_independiente | cooperativa
    plan="profesional",      # basico | profesional | enterprise
    fecha_alta=date.today(),
    contacto={"email": "admin@elcondor.com", "telefono": "03825-420000"},
    direccion={"localidad": "Nonogasta", "provincia": "La Rioja", "pais": "Argentina"},
)
cliente_id = dao.registrar_cliente(cliente)
dao.suspender_cliente(cliente_id)   # desactiva sin borrar datos
dao.reactivar_cliente(cliente_id)   # reactiva el acceso

# --- Usuarios ---
usuario = Usuario(
    cliente_id=cliente_id,
    nombre="Ana Gómez",
    email="ana@elcondor.com",
    rol="admin",             # admin | operador | visor
    fecha_alta=date.today(),
)
usuario_id = dao.registrar_usuario(usuario)
dao.get_usuarios_por_cliente(cliente_id)       # lista de usuarios activos
dao.get_usuario_por_email("ana@elcondor.com")
dao.desactivar_usuario(usuario_id)             # revoca acceso sin borrar registro

# --- Parcelas ---
parcela = Parcela(
    cliente_id=cliente_id,
    nombre="Finca El Peñón",
    cultivo="vid",
    variedad="Torrontés Riojano",
    zona="Nonogasta",
    superficie_ha=3.8,
    altitud_msnm=1050,
    geometria={"type": "Polygon", "coordinates": [[...]]}
)
parcela_id = dao.registrar_parcela(parcela)
dao.get_parcelas_por_zona(cliente_id, "Nonogasta")
dao.get_parcelas_por_cultivo(cliente_id, "vid")

# Consultas geográficas (requieren índice 2dsphere)
dao.get_parcelas_cerca_de(cliente_id, lat=-29.0, lon=-67.49, radio_km=8)
dao.get_parcelas_en_bbox(cliente_id, sw_lat=-29.03, sw_lon=-67.52,
                                     ne_lat=-28.98, ne_lon=-67.46)

# --- Observaciones satelitales ---
obs = Observacion(
    parcela_id=parcela_id,
    fecha=date(2024, 1, 5),
    ndvi=0.71, evi=0.54, ndwi=0.18,
    nubosidad_pct=4.0
)
dao.registrar_observacion(obs)

dao.get_observaciones(parcela_id)                          # historial completo
dao.get_observaciones(parcela_id,                          # filtrado por rango
                      desde=date(2023, 9, 1),
                      hasta=date(2024, 3, 31))

# NDVI promedio de una zona en una temporada (aggregation pipeline con $lookup)
dao.get_ndvi_promedio_por_zona(cliente_id, zona="Nonogasta", temporada="2023/2024")
# → [{"_id": "Nonogasta", "ndvi_promedio": 0.68, "total_observaciones": 412}]

# --- Campañas ---
campana = Campana(
    parcela_id=parcela_id,
    temporada="2023/2024",
    fecha_cosecha=date(2024, 2, 28),
    rendimiento_kg_ha=8400,
    notas="Sin eventos climáticos adversos."
)
dao.registrar_campana(campana)
dao.get_campanas(parcela_id)   # historial ordenado por temporada

# Rendimiento promedio histórico por zona (aggregation pipeline con $lookup)
dao.get_rendimiento_promedio_por_zona(cliente_id, zona="Nonogasta")
# → [{"_id": "2023/2024", "rendimiento_promedio": 7850.0, "parcelas": 4}]

# --- Alertas ---
alerta = Alerta(
    parcela_id=parcela_id,
    fecha=date(2024, 1, 10),
    tipo="estres_hidrico",     # ndvi_bajo | estres_hidrico | anomalia_temporal
    indice="NDWI",
    valor_detectado=0.09,
    umbral=0.15,
)
alerta_id = dao.registrar_alerta(alerta)
dao.get_alertas_activas_por_parcela(parcela_id)
dao.resolver_alerta(alerta_id)   # activa → resuelta
dao.ignorar_alerta(alerta_id)    # activa → ignorada

# --- Reportes ---
reporte = Reporte(
    cliente_id=cliente_id,
    nombre="Resumen NDVI — Temporada 2023/2024",
    tipo="resumen_indices",    # resumen_indices | comparativa_parcelas | estado_general
    periodo={"desde": "2023-09-01", "hasta": "2024-03-31"},
    parcelas_incluidas=[parcela_id],
    fecha_generacion=date.today(),
    generado_por=usuario_id,
    resumen={"ndvi_promedio": 0.68, "parcelas_en_alerta": 1,
             "observaciones_procesadas": 412},
)
reporte_id = dao.generar_reporte(reporte)
dao.get_reportes_por_cliente(cliente_id)   # ordenados por fecha descendente
dao.marcar_reporte_visto(reporte_id)       # generado → visto

dao.cerrar()
```

---

## Colecciones MongoDB

El sistema organiza sus siete colecciones en tres grupos según su función.

### Grupo 1 — Tenancy

#### clientes
Registra las organizaciones que acceden al sistema. El `_id` generado por MongoDB se propaga como `cliente_id` a todas las colecciones operativas, garantizando el aislamiento lógico entre organizaciones (patrón shared-database + cliente_id).

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| nombre | String | Razón social o nombre de la bodega | Sí |
| cuit | String | CUIT del cliente. Único en la colección | Sí |
| tipo | String | `bodega` · `productor_independiente` · `cooperativa` | Sí |
| plan | String | `basico` · `profesional` · `enterprise` | Sí |
| fecha_alta | Date | Fecha de registro en el sistema | Sí |
| activo | Boolean | Permite suspender el acceso sin borrar datos | Sí |
| contacto | Objeto | Subdocumento `{email, telefono}` | No |
| direccion | Objeto | Subdocumento `{localidad, provincia, pais}` | No |

#### usuarios
Registra las personas que operan en nombre de un cliente. Un cliente puede tener múltiples usuarios con distintos roles. El `email` es único en toda la colección y funciona como identificador de inicio de sesión.

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| cliente_id | ObjectId | Referencia al cliente propietario | Sí |
| nombre | String | Nombre completo del usuario | Sí |
| email | String | Correo de inicio de sesión. Único en la colección | Sí |
| rol | String | `admin` · `operador` · `visor` | Sí |
| fecha_alta | Date | Fecha de creación del usuario | Sí |
| activo | Boolean | Permite revocar el acceso sin borrar el registro | Sí |

---

### Grupo 2 — Datos operativos

#### parcelas
Documento central del sistema. Almacena los datos geográficos estáticos de cada viñedo. Las observaciones satelitales **no** se almacenan embebidas — viven en su propia colección y se vinculan mediante `parcela_id`.

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| cliente_id | ObjectId | Referencia al cliente propietario | Sí |
| nombre | String | Nombre o identificador de la parcela | Sí |
| cultivo | String | Tipo de cultivo: `vid`, `olivo`, `nogal` | Sí |
| variedad | String | Cepa cultivada: Torrontés, Malbec, Bonarda... | No |
| superficie_ha | Float | Superficie en hectáreas | No |
| altitud_msnm | Int | Metros sobre el nivel del mar | No |
| zona | String | Sector geográfico del departamento | Sí |
| geometria | GeoJSON | Polígono de la parcela en WGS84 | Sí |

#### observaciones
Colección independiente que almacena el historial satelital. Cada documento representa una captura de Sentinel-2 procesada para una parcela. Cuenta con un índice compuesto único sobre `{ parcela_id, fecha }` para consultas de rango temporal eficientes.

> **Por qué colección separada:** Sentinel-2 entrega una imagen cada ~5 días. En tres años eso representa ~200 observaciones por parcela. Almacenarlas como array embebido dentro del documento de la parcela generaba un crecimiento ilimitado que degrada el rendimiento de lectura y puede superar el límite de 16 MB por documento de MongoDB.

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| parcela_id | String | Referencia a la parcela | Sí |
| fecha | Date | Fecha de la imagen satelital (YYYY-MM-DD) | Sí |
| ndvi | Float | Normalized Difference Vegetation Index | Sí |
| evi | Float | Enhanced Vegetation Index | Sí |
| ndwi | Float | Normalized Difference Water Index | Sí |
| nubosidad_pct | Float | % de nubosidad (0-100). Se descartan observaciones > 20% | Sí |
| fuente | String | Satélite de origen. Por defecto: `Sentinel-2` | Sí |

#### campañas
Registra el rendimiento real por temporada agrícola. Es el *ground truth* que el modelo de aprendizaje automático aprende a predecir. Se mantiene separada de `parcelas` porque crece de forma independiente — un documento nuevo por temporada, sin modificar los datos del viñedo.

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| parcela_id | String | Referencia a la parcela | Sí |
| temporada | String | Año agrícola en formato `2023/2024` | Sí |
| fecha_cosecha | Date | Fecha efectiva de cosecha | Sí |
| rendimiento_kg_ha | Float | Kilos cosechados por hectárea. Valor objetivo del modelo | Sí |
| notas | String | Eventos climáticos u observaciones del productor | No |

---

### Grupo 3 — Salidas del sistema

#### alertas
Registra eventos detectados automáticamente cuando un índice espectral supera un umbral configurado. El ciclo de vida completo queda registrado en el campo `estado`: `activa → resuelta | ignorada`.

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| parcela_id | String | Referencia a la parcela que disparó la alerta | Sí |
| fecha | Date | Fecha en que se detectó la condición | Sí |
| tipo | String | `ndvi_bajo` · `estres_hidrico` · `anomalia_temporal` | Sí |
| indice | String | Índice que disparó la alerta: `NDVI` · `EVI` · `NDWI` | Sí |
| valor_detectado | Float | Valor del índice en la fecha de detección | Sí |
| umbral | Float | Valor de referencia configurado para la parcela | Sí |
| estado | String | `activa` · `resuelta` · `ignorada` | Sí |

#### reportes
Almacena documentos generados con métricas del estado satelital de una o varias parcelas en un período. A diferencia de las colecciones operativas, los reportes cuelgan del cliente directamente ya que pueden cubrir múltiples parcelas. El campo `resumen` es un snapshot calculado al momento de generación y no se recalcula.

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| cliente_id | String | Referencia al cliente propietario | Sí |
| nombre | String | Nombre descriptivo del reporte | Sí |
| tipo | String | `resumen_indices` · `comparativa_parcelas` · `estado_general` | Sí |
| periodo | Objeto | Subdocumento `{desde, hasta}` en formato ISO | Sí |
| parcelas_incluidas | Array | Lista de `parcela_id` incluidos en el reporte | Sí |
| fecha_generacion | Date | Fecha en que se generó el reporte | Sí |
| generado_por | String | Referencia al usuario que lo solicitó | Sí |
| estado | String | `generado` · `enviado` · `visto` | Sí |
| resumen | Objeto | Snapshot con métricas calculadas al momento de generación | No |

---

## Índices

| Colección | Campo(s) | Tipo | Propósito |
|---|---|---|---|
| clientes | `cuit` | Único | Identificación fiscal, evita duplicados |
| clientes | `activo` | Ascendente | Filtrar clientes activos/suspendidos |
| usuarios | `email` | Único | Autenticación e identificación |
| usuarios | `cliente_id` | Ascendente | Listar usuarios de una organización |
| parcelas | `geometria` | 2dsphere | Consultas espaciales ($nearSphere, $geoWithin) |
| parcelas | `cliente_id` | Ascendente | Aislamiento por organización |
| parcelas | `zona` | Ascendente | Filtro por zona geográfica |
| parcelas | `cultivo` | Ascendente | Filtro por tipo de cultivo |
| observaciones | `parcela_id + fecha` | Compuesto único | Consultas de rango temporal. Evita duplicados |
| campañas | `parcela_id` | Ascendente | Historial de cosechas por parcela |
| campañas | `temporada` | Ascendente | Ordenamiento por temporada |
| alertas | `parcela_id` | Ascendente | Alertas activas de una parcela |
| alertas | `estado` | Ascendente | Filtrar por ciclo de vida |
| alertas | `fecha` | Ascendente | Ordenamiento cronológico |
| reportes | `cliente_id` | Ascendente | Reportes de una organización |
| reportes | `fecha_generacion` | Ascendente | Ordenamiento por fecha |
