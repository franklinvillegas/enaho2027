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
| GET | `/api/v1/cobertura/{tnr}/` | Pantallas con vistas por departamento / ODEI / ODEI y mes (`tnr-total`, `tnr-parcial`, `problemas-marco`, `informacion-indirecta`): vistas, textos, gráficos |
| GET | `/api/v1/cobertura/{tnr}/{vista}/` | Filas de una vista (`departamentos`, `odei`, `odei-mes`); `sede`, `usuario`, `conglomerado` para bajar de nivel; `&formato=xlsx` |
| GET | `/api/v1/cobertura/{tnr}/mapa/` | Mapa de calor por departamento |
| GET | `/api/v1/cobertura/informacion-indirecta/absolutos/` | Valores absolutos por encuestador de una sede (`sede`, `solo_activos`, rango) |
| GET | `/api/v1/cobertura/reportes/{pantalla}/{vista}/` | Control de visitas, omisión por capítulos, omisiones GPS y tipo de entrevista (ver abajo) |
| GET | `/api/v1/calidad/reportes/{pantalla}/{vista}/?indicador=` | Indicadores de calidad (ver abajo) |
| POST | `/api/v1/excel/` | Excel de la tabla que la pantalla ya muestra (sin volver a consultar la base) |
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

TNR total, TNR parcial, problemas de marco e información indirecta repiten en el sistema actual ~2.000–2.500
líneas de JavaScript casi iguales cada una. Aquí comparten todo:

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

### Control de visitas, omisión por capítulos, omisiones GPS y tipo de entrevista

Estas cuatro pantallas tienen tablas con encabezados agrupados (años × dos medidas,
capítulos × años, meses × capítulos...). Comparten:

- Backend: `apps/cobertura/reportes.py` — por pantalla y vista, el procedimiento y el orden
  de parámetros (lista blanca), el alcance por ODEI y el modo demo. Una sola ruta:
  `/cobertura/reportes/{pantalla}/{vista}/`.

  | Pantalla | Vistas → procedimiento |
  |---|---|
  | `control-visitas` | `departamentos` → cobertura_controlVisitas_dep · `odei` → enaho2016_visitas_odei_anio · `odei-mes` → enaho2016_visitas_odei_mes · `casos` → cobertura_controlVisitas_casos |
  | `omision-capitulos` | `grafico` → enaho2015_calidad_ind02 · `anio` → ENAHO2020_CALIDAD_OMISIONCAPITULOS_ANIO · `mes` → ENAHO2020_CALIDAD_OMISIONCAPITULOS_MES · `mapa` → enaho2015_omision_capitulo_map |
  | `omisiones-gps` | `resumen` → enaho2016_geo_omisiones · `viviendas` → enaho2015_cobertura_ind01_2 |
  | `tipo-entrevista` | `departamentos` → cobertura_tipoEntrevista_dep · `odei` → enaho2021_tipoEntrevista_odei · `odei-mes` → enaho2021_tipoEntrevista_odeiMes |

- Excel genérico: `apps/comun/excel_tabla.py` (`POST /api/v1/excel/`). La pantalla envía la
  tabla tal como la dibuja (encabezados con celdas combinadas, filas, celdas en rojo) y el
  backend solo arma el .xlsx con el diseño del reporte. Sirve para cualquier pantalla futura.
- Frontend: una vista genérica `views/reportes/ReporteView.vue` + la tabla
  `components/reportes/TablaReporte.vue`. Lo propio de cada pantalla está en
  `config/reportesCobertura/<pantalla>.js`: vistas, pestañas, filtros, qué consultar,
  cómo se arma la tabla (`tabla(filas, ctx)`), gráficos y textos. Los años y meses salen
  de los datos o del año en curso: no hay que tocar código al cambiar de año.
- Grupos de columnas que se abren y cierran (± en omisión por capítulos): la celda de
  encabezado lleva `alternar` y `columnasCerrado`; las celdas del grupo llevan `grupo`.

Mejoras respecto al sistema actual:
- El detalle de viviendas de omisiones GPS llamaba mal al procedimiento (faltaba el año);
  aquí la llamada va completa, y cada vivienda con GPS tiene el enlace "Ver mapa".
- Una consulta a la vez y sin repetir la misma; ventana de espera que bloquea la pantalla.
- El Excel exporta exactamente lo que se ve (con los grupos abiertos o cerrados).

### Indicadores de calidad

En el sistema actual las siete pantallas de calidad (vivienda y hogar, demográficos,
consumo de alimentos, programas sociales, educación, salud, empleo) repiten ~2.500–7.600
líneas de JavaScript cada una, y casi todos sus indicadores usan el mismo esquema de
procedimientos: `enaho2017_calidad_{indicador}{tipo}` (tipo 1 departamentos, 2 ODEI, 3 ODEI y
por mes).

- Backend `apps/calidad/`: `indicadores.py` declara qué indicadores tiene cada pantalla
  (lista cerrada: el nombre del procedimiento nunca se arma con un valor sin validar) y
  registra los procedimientos en la lista blanca; `servicios.py` arma los parámetros en el
  orden y formato de la pantalla actual (encuestador "" = todos, mes "0" = sin filtro) y
  tiene los datos de demostración. Ruta única `/calidad/reportes/{pantalla}/{vista}/?indicador=`.
- Frontend: la misma vista genérica de reportes, con el combo de indicadores. Lo común de
  las pantallas de calidad está en `config/reportesCalidad/indicadorCalidad.js` (tablas por
  año y por mes, gráfico de barras o líneas, cuadro de objetivo y fórmula); cada pantalla
  solo lista sus indicadores con sus textos (`viviendaHogar.js`, `programasSociales.js`).
- "Visualizar casos" (balance del hogar, indicadores 11 y 12 de vivienda y hogar) llama a
  `calidad_viviendaHogar_detalleBalanceHogar`.

Migradas: vivienda y hogar, programas sociales. Pendientes: demográficos (pirámide de
edad), consumo de alimentos (precios IPC, kilos, canasta), educación (tasa de asistencia
escolar por dominio), salud (razones de no asistencia) y empleo (PET, ninis, etnicidad):
usan el mismo esquema más algunos indicadores con procedimiento propio.

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
