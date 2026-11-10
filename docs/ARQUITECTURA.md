# Arquitectura de enaho2027

## Visión general

```
Navegador (Vue 3)  ──HTTP/JSON──▶  API Django REST  ──▶  Base de monitoreo (lectura/escritura)
                                         │
                                         └──solo lectura──▶  Base de captura ENAHO2014_BDCAPTURA
```

- **Monolito modular**: un solo proyecto Django con una app por módulo del menú.
- **La base de captura no se modifica.** Solo se lee, desde un único punto
  (`apps/comun/captura.py`), con una lista blanca de procedimientos y parámetros enlazados.
- **Migración progresiva (Strangler Fig).** Cada módulo empieza leyendo los procedimientos
  actuales y luego pasa a tablas resumen propias, sin cambiar la API ni el frontend.

## Backend

```
backend/
├── config/                 Configuración (settings por entorno, rutas, router de bases)
│   ├── settings/base.py    Común. Todo lo sensible viene del .env
│   ├── settings/dev.py     Desarrollo
│   ├── settings/demo.py    Demo sin SQL Server (SQLite + datos de ejemplo)
│   ├── settings/test.py    Pruebas automáticas
│   ├── settings/prod.py    Producción (cookies seguras, cabeceras)
│   └── db_routers.py       Impide escribir o migrar en la base de captura
└── apps/
    ├── comun/              Usuarios, acceso por cargo, filtros, registro de uso, Excel
    ├── cobertura/          PILOTO
    ├── operacion_campo/    Pendiente
    ├── reportes_campo/     Pendiente
    ├── calidad/            Pendiente
    ├── valores_monetarios/ Pendiente (oculto en el sistema actual: confirmar)
    └── seguimiento_monitor/Pendiente
```

### Capas dentro de cada módulo

| Archivo | Responsabilidad | Conoce SQL | Conoce HTTP |
|---|---|---|---|
| `indicadores.py` | Catálogo: qué indicadores hay y qué procedimiento usa cada nivel | No | No |
| `repositorios.py` | De dónde salen los datos (captura, monitoreo o demo) | Sí | No |
| `servicios.py` | Reglas del caso de uso | No | No |
| `views.py` | Endpoints: valida filtros, aplica permisos, responde JSON o Excel | No | Sí |

Para cambiar la fuente de datos de un módulo se cambia una variable del `.env`
(`FUENTE_COBERTURA=captura | monitoreo | demo`).

### Seguridad

- Toda la API está cerrada por defecto; cada vista declara su permiso de módulo.
- Las reglas de acceso por cargo viven en `apps/comun/acceso.py` (antes estaban repartidas
  en el menú HTML). El frontend las recibe en `/api/v1/auth/yo/`.
- Un usuario de una ODEI solo puede consultar su ODEI, aunque pida otra.
- Parámetros validados con expresiones regulares y enlazados al ejecutar el SQL.
- Errores de base de datos: detalle en el log, mensaje genérico al usuario.
- Sesión de Django por cookie (HttpOnly) + token CSRF; intentos de login limitados.

### API (v1)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/auth/csrf/` | Entrega la cookie CSRF |
| POST | `/api/v1/auth/login/` | Inicia sesión |
| POST | `/api/v1/auth/logout/` | Cierra sesión |
| GET | `/api/v1/auth/yo/` | Usuario en sesión y módulos permitidos |
| GET | `/api/v1/catalogos/odeis/` | ODEI que el usuario puede consultar |
| POST | `/api/v1/registro-uso/` | Registra ingreso o salida de una pantalla |
| GET | `/api/v1/cobertura/indicadores/` | Indicadores de cobertura disponibles |
| GET | `/api/v1/cobertura/indicadores/{codigo}/` | Datos (`?nivel=&odei=&periodo_inicio=...`, `&formato=xlsx`) |
| GET | `/api/v1/cobertura/indicadores/{codigo}/mapa/` | Datos para el mapa |

Documentación completa: `/api/docs/`.

## Frontend

```
frontend/src/
├── api/            Cliente HTTP (sesión + CSRF) y un archivo por módulo
├── config/menu.js  Menú: módulos y pantallas (las migradas tienen `indicador`)
├── router/         Rutas generadas desde el menú + guardia de sesión y permisos
├── stores/         Pinia: sesión del usuario
├── layouts/        Barra superior y menú lateral
├── composables/    useIndicador (filtros, consulta, Excel, mapa, registro de uso)
├── components/indicador/  Filtros, Gráfico, Tabla y Mapa reutilizables
└── views/          Login, Inicio, En construcción y vistas por módulo
```

Una sola vista (`views/cobertura/IndicadorCoberturaView.vue`) sirve para todos los
indicadores de cobertura; solo cambia el código del indicador.

## Cómo migrar una pantalla nueva

1. Backend: agregar el indicador en `apps/<modulo>/indicadores.py` con su procedimiento y el
   orden de parámetros (tomarlo del código del procedimiento, no del sistema anterior).
2. Agregar una prueba en `apps/<modulo>/tests/` con un repositorio falso.
3. Frontend: en `config/menu.js`, agregar `indicador: '<codigo>'` a la pantalla.
4. Validar que los números coincidan con el sistema actual para los mismos filtros.

## Decisiones pendientes

- Cómo se migran las cuentas de usuario del sistema actual (y si se integra con el
  directorio del INEI).
- Licencia de gráficos: se usa ECharts (libre). Highcharts requiere licencia.
- Formato exacto de periodo y mes, y validación del rango (se confirma con los procedimientos).
- Columnas que devuelve cada procedimiento, para definir qué grafica cada indicador.
- Servidor de producción (IIS, Nginx o contenedor) y HTTPS.
