# SAVIA
### Sistema de Almacenamiento de Índices de Vegetación con Inteligencia Agrícola

Proyecto Integrador — Bases de Datos II · Universidad Nacional de Chilecito · 2026

---

## El problema

La producción vitivinícola es la actividad económica principal del departamento
Chilecito, La Rioja. Estimar el rendimiento de los viñedos antes de la cosecha
es un proceso manual y tardío, sin herramientas que permitan anticiparlo con
semanas de antelación.

Este módulo es la capa de persistencia de una tesis de grado que busca predecir
el rendimiento usando imágenes satelitales de Sentinel-2 e índices espectrales
como el NDVI, aplicando aprendizaje automático.

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

### 1. Requisitos
- Python 3.12+
- Docker Desktop

### 2. Clonar el repositorio
```bash
git clone <url-del-repo>
cd SAVIA
```

### 3. Entorno virtual
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -r libs.txt
```

### 4. Levantar MongoDB
```bash
docker compose up -d
```

### 5. Inicializar la base de datos
```bash
python setup_db.py
```

### 6. Cargar datos de prueba
```bash
python seed.py
```

### 7. Ejecutar el notebook
```bash
jupyter notebook demo.ipynb
```

---

## Uso del DAO

```python
from dao import VinedoDAO
from db_models import Parcela, Observacion
from datetime import date

dao = VinedoDAO()

# Consultar parcelas por zona
parcelas = dao.get_parcelas_por_zona("Nonogasta")

# Agregar observación satelital
dao.agregar_observacion(parcela_id, observacion)

# Serie temporal con filtro de fechas
obs = dao.get_observaciones(parcela_id, desde=date(2023, 12, 1))

# NDVI promedio por zona
resultado = dao.get_ndvi_promedio_por_zona("Nonogasta", "2023/2024")

dao.cerrar()
```

---

## Colecciones MongoDB

**parcelas** — datos estáticos del viñedo + historial satelital embebido

**campanas** — rendimiento real por temporada (ground truth para el modelo ML)
