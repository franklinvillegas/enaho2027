# enaho2027 — Monitoreo ENAHO

Reingeniería del sistema de monitoreo de la Encuesta Nacional de Hogares.

- **backend/**: Python 3.14, Django 6.1, Django REST Framework. Solo expone la API (JSON).
- **frontend/**: Vue 3, Vite, Vuetify, Pinia, Vue Router, ECharts y Leaflet.

Se reescribe desde cero siguiendo los seis módulos del sistema actual, y se pone en
producción módulo por módulo. El primero es **Indicadores de cobertura** (piloto).

## Requisitos

- Python 3.14
- Node.js 22 o superior
- Para conectarse a SQL Server: [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)

## Levantarlo en modo demo (sin SQL Server ni VPN)

El modo demo usa SQLite para los usuarios y **datos de ejemplo inventados** para los
indicadores. Sirve para trabajar el frontend desde cualquier PC.

```bash
# Backend (terminal 1)
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (en Linux/Mac: source .venv/bin/activate)
pip install -r requirements/dev.txt
python manage.py migrate --settings=config.settings.demo
python manage.py createsuperuser --settings=config.settings.demo
python manage.py runserver --settings=config.settings.demo

# Frontend (terminal 2)
cd frontend
npm install
npm run dev
```

Abrir http://localhost:5173 e ingresar con el usuario creado. Para que el menú muestre
módulos, el usuario debe tener `permisos` = 1 o 2 (el superusuario ve todo).

## Levantarlo con SQL Server (oficina)

1. Copiar `backend/.env.example` a `backend/.env` y completar las dos conexiones:
   - **Base de monitoreo**: base nueva y propia del sistema (usuarios, registro de uso,
     y luego las tablas resumen).
   - **Base de captura**: `ENAHO2014_BDCAPTURA`, **solo lectura**. Idealmente una réplica.
2. `python manage.py migrate` (crea las tablas solo en la base de monitoreo).
3. `python manage.py runserver`.

## Pruebas y calidad

```bash
cd backend && pytest && ruff check .
cd frontend && npm test && npm run build
```

## Documentación

- API interactiva (Swagger): http://localhost:8000/api/docs/
- Arquitectura y convenciones: [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md)
- Diagnóstico, catálogo de pantallas y piloto: documento "Reingeniería del Monitoreo ENAHO".
