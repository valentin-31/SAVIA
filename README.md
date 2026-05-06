# SAVIA
### Sistema de Almacenamiento de Índices de Vegetación para Investigación Agronómica

Proyecto Integrador — Bases de Datos II · Universidad Nacional de Chilecito · 2026

---

## El problema

La producción vitivinícola es la actividad económica principal del departamento
Chilecito, La Rioja, con miles de hectáreas cultivadas entre los 900 y 1200 metros
sobre el nivel del mar. A pesar de su relevancia económica, estimar cuánto va a
producir un viñedo antes de la cosecha sigue siendo un proceso manual, tardío y
sin respaldo de datos históricos. Los productores no cuentan hoy con ninguna
herramienta que les permita anticipar el rendimiento con semanas de antelación.

El problema concreto es de infraestructura de datos. El satélite Sentinel-2
captura imágenes de cada parcela cada ~5 días con una resolución de 10 metros
por píxel. A partir de esas imágenes, Google Earth Engine puede calcular índices
espectrales como el NDVI, el EVI y el NDWI — métricas que reflejan la salud,
densidad y contenido hídrico de la vegetación a lo largo del ciclo vegetativo.
Esos datos existen y son públicos, pero no hay ningún sistema local que los
almacene por parcela de forma estructurada y consultable.

SAVIA resuelve ese problema. Es un módulo de acceso a datos que almacena el
historial satelital de cada viñedo en MongoDB, lo expone mediante una interfaz
Python con semántica del dominio vitícola, y sienta las bases para que un modelo
de aprendizaje automático pueda aprender a predecir el rendimiento a partir de
la evolución temporal de los índices espectrales.

---
## ¿Qué es SAVIA?

SAVIA es una capa de persistencia para datos satelitales agrícolas. Toma las
imágenes del satélite Sentinel-2 procesadas en Google Earth Engine, extrae los
índices espectrales relevantes (NDVI, EVI, NDWI) y los almacena por parcela en
MongoDB de forma estructurada y consultable.

El sistema está orientado a investigadores y técnicos que necesiten construir o
entrenar modelos de predicción de rendimiento agrícola. No incluye el modelo de
machine learning ni una interfaz de usuario final — su propósito es proveer una
base de datos local, ordenada y eficiente sobre la cual esas capas puedan
construirse.

---
## Arquitectura

```
Sentinel-2 (GEE) → seed.py → MongoDB (Docker) → VinedoDAO → Modelo ML
```

- **MongoDB**: almacena parcelas con historial satelital embebido y campañas de cosecha
- **VinedoDAO**: abstrae todas las operaciones en métodos con semántica vitícola
- **demo.ipynb**: demuestra el DAO en acción con gráficos de series temporales

---

## Estructura del proyecto

```
SAVIA/
├── db_models/
│   ├── parcela.py       # Documento principal con historial embebido
│   ├── observacion.py   # Subdocumento de captura satelital
│   └── campana.py       # Registro de cosecha por temporada
├── dao.py               # Clase VinedoDAO — interfaz principal
├── config_vars.py       # Variables de conexión desde .env
├── setup_db.py          # Inicialización de BD e índices
├── seed.py              # Datos de prueba realistas
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
✓ Colección parcelas — índices creados
✓ Colección campanas — índices creados
✓ Base de datos 'vinedos_chilecito' lista
```
 
### 7. Cargar datos de prueba
```bash
python seed.py
```
 
Resultado esperado:
```
Iniciando carga de datos de prueba...
  ✓ Parcela insertada: Finca El Peñón (Nonogasta)
  ✓ Parcela insertada: Finca Los Sarmientos Norte (Los Sarmientos)
  ✓ Parcela insertada: Viña Famatina (Famatina)
  ✓ Parcela insertada: Finca Vichigasta Sur (Vichigasta)
Insertando observaciones satelitales...
  ✓ 13 observaciones → Finca El Peñón
  ✓ 13 observaciones → Finca Los Sarmientos Norte
Insertando campañas...
  ✓ Campaña insertada: Finca El Peñón 2023/2024
  ✓ Campaña insertada: Finca Los Sarmientos Norte 2023/2024
  ✓ Campaña insertada: Viña Famatina 2023/2024
✓ Seed completado.
```
 
### 8. Ejecutar el notebook de demostración
```bash
jupyter notebook demo.ipynb
```
 
---

## Uso del DAO

`VinedoDAO` es la única interfaz entre el sistema y MongoDB.
Todos los métodos reciben parámetros del dominio vitícola — nunca queries en crudo.

```python
from dao import VinedoDAO
from db_models import Parcela, Observacion, Campana
from datetime import date

dao = VinedoDAO()

# --- Insertar una parcela ---
parcela = Parcela(
    nombre="Finca El Peñón",
    cultivo="vid",
    variedad="Torrontés Riojano",
    zona="Nonogasta",
    superficie_ha=3.8,
    altitud_msnm=1050,
    geometria={"type": "Polygon", "coordinates": [[...]]}
)
pid = dao.insertar_parcela(parcela)  # devuelve el id generado por MongoDB

# --- Consultar parcelas ---
parcelas = dao.get_parcelas_por_zona("Nonogasta")     # lista de documentos
parcelas = dao.get_parcelas_por_cultivo("vid")        # lista de documentos
parcela  = dao.get_parcela(pid)                       # documento único o None

# --- Agregar observación satelital ---
obs = Observacion(
    fecha=date(2024, 1, 5),
    ndvi=0.71,
    evi=0.54,
    ndwi=0.18,
    nubosidad_pct=4.0
)
dao.agregar_observacion(pid, obs)  # True si se insertó, False si el id no existe

# --- Consultar serie temporal ---
# Sin filtro: devuelve todo el historial de la parcela
observaciones = dao.get_observaciones(pid)

# Con filtro: devuelve solo el rango de fechas indicado
verano = dao.get_observaciones(pid, desde=date(2023, 12, 1), hasta=date(2024, 2, 28))

# --- Agregación por zona ---
# Devuelve el NDVI promedio de todas las parcelas de una zona en una temporada
# Útil para comparar zonas antes de entrenar el modelo
resultado = dao.get_ndvi_promedio_por_zona("Nonogasta", "2023/2024")
# → [{"_id": "Nonogasta", "ndvi_promedio": 0.4957, "total_observaciones": 14}]

# --- Campañas ---
campana = Campana(
    parcela_id=pid,
    temporada="2023/2024",
    fecha_cosecha=date(2024, 2, 28),
    rendimiento_kg_ha=8400,
    notas="Sin eventos climáticos adversos."
)
dao.insertar_campana(campana)
historial = dao.get_campanas(pid)  # lista ordenada por temporada ascendente

dao.cerrar()
```
---

## Colecciones MongoDB

### parcelas
Documento central del sistema. Almacena los datos geográficos del viñedo
y su historial satelital completo como array embebido.
Una sola consulta trae todo el historial sin joins ni operaciones adicionales.

| Campo | Tipo | Descripción |
|---|---|---|
| nombre | String | Identificador de la parcela |
| cultivo | String | Tipo de cultivo (vid, olivo, nogal) |
| variedad | String | Cepa cultivada (Torrontés, Malbec) |
| zona | String | Sector geográfico del departamento |
| geometria | GeoJSON | Polígono de la parcela en WGS84 |
| observaciones | Array | Historial satelital embebido |

### campanas
Registra el rendimiento real por temporada agrícola.
Es el ground truth que el modelo de aprendizaje automático aprende a predecir.
Se mantiene separada de `parcelas` porque crece de forma independiente —
un documento nuevo por temporada, sin modificar los datos del viñedo.

| Campo | Tipo | Descripción |
|---|---|---|
| parcela_id | String | Referencia a la parcela |
| temporada | String | Año agrícola (ej: 2023/2024) |
| fecha_cosecha | Date | Fecha efectiva de cosecha |
| rendimiento_kg_ha | Float | Kilos cosechados por hectárea |
| notas | String | Eventos climáticos u observaciones |
