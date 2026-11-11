# Arquitectura de enaho2027

## Visión general

```
Navegador (Vue 3)  ──HTTP/JSON──▶  API Django REST  ──▶  Base de monitoreo nueva (lectura/escritura)
                                         │
                                         └──solo lectura──▶  Base del sistema actual ENAHO2019_BDMONITOREO
                                                              (procedimientos y usuarios del monitoreo actual)
```

- **Monolito modular**: un solo proyecto Django con una app por módulo del menú.
- **La base del sistema actual no se modifica.** Solo se lee, desde un único punto
  (`apps/comun/sistema_actual.py`), con una lista blanca de procedimientos y parámetros
  enlazados. Los usuarios entran con su mismo usuario y contraseña del sistema actual
  (`apps/comun/autenticacion.py`); la contraseña no se copia.
- **Migración progresiva (Strangler Fig).** Cada módulo empieza leyendo los procedimientos
  actuales y luego pasa a tablas resumen propias, sin cambiar la API ni el frontend.

## Backend

```
backend/
├── config/                 Configuración (settings por entorno, rutas, router de bases)
│   ├── settings/base.py    Común. Todo lo sensible viene del .env
│   ├── settings/dev.py     Desarrollo
│   ├── settings/local.py   Datos y usuarios reales del sistema actual + SQLite propio
│   ├── settings/demo.py    Demo sin SQL Server (SQLite + datos de ejemplo)
│   ├── settings/test.py    Pruebas automáticas
│   ├── settings/prod.py    Producción (cookies seguras, cabeceras)
│   └── db_routers.py       Impide escribir o migrar en la base del sistema actual
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
| `repositorios.py` | De dónde salen los datos (sistema actual, monitoreo o demo) | Sí | No |
| `servicios.py` | Reglas del caso de uso | No | No |
| `views.py` | Endpoints: valida filtros, aplica permisos, responde JSON o Excel | No | Sí |

Para cambiar la fuente de datos de un módulo se cambia una variable del `.env`
(`FUENTE_COBERTURA=sistema_actual | monitoreo | demo`).

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
| GET | `/api/v1/cobertura/{tnr}/` | Pantalla de tasa de no respuesta (`tnr-total`, `tnr-parcial`): vistas, textos, gráficos |
| GET | `/api/v1/cobertura/{tnr}/{vista}/` | Filas de una vista (`departamentos`, `odei`, `odei-mes`); `sede`, `usuario`, `conglomerado` para bajar de nivel; `&formato=xlsx` |
| GET | `/api/v1/cobertura/{tnr}/mapa/` | Mapa de calor por departamento |
| GET | `/api/v1/cobertura/tnr-estrato/{anual,mensual,hogar}/` | TNR según estrato (`tipo`, `estrato`, `odei`, `conglomerado`, rango de meses y periodos, `excluir`; hogar: `odei`, `mes`); `&formato=xlsx` |

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

### Pantallas de tasa de no respuesta (diseño igual al sistema actual)

TNR total y TNR parcial repiten en el sistema actual ~2.500 líneas de JavaScript casi
iguales cada una. Aquí comparten todo:

- Backend: `apps/cobertura/tasas_no_respuesta.py` (motor: filtros, alcance por ODEI,
  consulta, modo demo) y una configuración por pantalla (`tnr_total.py`, `tnr_parcial.py`)
  con sus procedimientos, orden de parámetros, prefijo de columnas (`tnr2026` /
  `tnrp_2026`), textos, colores y filtros extra. El Excel con el diseño del reporte
  actual está en `excel_tnr.py`.
- Frontend: `views/cobertura/TasaNoRespuestaView.vue` recibe el código de la pantalla y
  toma de `/cobertura/{tnr}/` lo que cambia. Las columnas de años y meses salen de los
  datos (`composables/tablaTnr.js`): no hay que tocar código al cambiar de año.

La TNR según estrato tiene otra estructura (cuatro pestañas: gráfico por estrato,
anual, por mes y hogares), por eso tiene su propio módulo (`tnr_estrato.py`,
`excel_estrato.py`) y vista (`TnrEstratoView.vue`, `composables/tablaEstrato.js`).

Para agregar otra pantalla con el mismo esquema (p. ej. TNR por estrato): crear su
configuración en el backend, sumarla a `VISTAS_PROPIAS` en `router/index.js` y marcarla
`migrada: true` en el menú.

## Cómo migrar una pantalla nueva

1. Backend: agregar el indicador en `apps/<modulo>/indicadores.py` con su procedimiento y el
   orden de parámetros (tomarlo del código del procedimiento, no del sistema anterior).
2. Agregar una prueba en `apps/<modulo>/tests/` con un repositorio falso.
3. Frontend: en `config/menu.js`, agregar `indicador: '<codigo>'` a la pantalla.
4. Validar que los números coincidan con el sistema actual para los mismos filtros.

## Decisiones pendientes

- Cuándo dejar de validar contra las cuentas del sistema actual (y si se integra con el
  directorio del INEI).
- Licencia de gráficos: se usa ECharts (libre). Highcharts requiere licencia.
- Formato exacto de periodo y mes, y validación del rango (se confirma con los procedimientos).
- Columnas que devuelve cada procedimiento, para definir qué grafica cada indicador.
- Servidor de producción (IIS, Nginx o contenedor) y HTTPS.
