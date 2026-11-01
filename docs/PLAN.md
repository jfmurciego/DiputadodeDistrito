<!--
Nombre: Plan de trabajo DDD
Versión: 1.0.7
Fecha: 2026-11-01
Alcance: Cola de tareas para chats implementadores y operadores
Estado: candidato
Cambios/motivo: 1.0.7: T-02 cierra Huelva y Valencia (Tareas hechas); Murcia y Álava siguen en curso.
  1.0.6: T-02b documentada: bloqueos de población M05 de Madrid, Málaga, Alicante y Barcelona
Anterior: legacy/docs/PLAN_v1.0.6_20261101.md
-->

# Plan de trabajo — Diputado de Distrito

## Reglas para todos los chats
- Un chat = una tarea. Coge la primera tarea libre de la cola cuyas dependencias estén en «Tareas hechas».
- Respeta `CLAUDE.md` (topónimos en español, mínimo consumo, coordinación entre sesiones, gobernanza VERSIÓN/legacy).
- El implementador pasa la suite local completa (`python -m pytest -q`) antes de abrir la PR.
- Fusiona el propietario. Nadie lanza ejecuciones productivas ni publica sin su permiso explícito.
- Nada de vigilar runs en el chat: los lanzamientos largos se hacen con scripts en el Mac del propietario
  (rama `lanzadores-mac`).
- Al terminar: mover la tarea a «Tareas hechas» con su PR o run y, si hubo lección cara, `/cierre-sesion`.
- Coordinación: el chat planificador («DDD Plan») lista, describe y asigna; no implementa. Cada chat le manda una
  línea (`send_message`) al abrir PR, lanzar run o cerrar tarea: «T-xx · qué · PR/run · siguiente · bloqueo», y le
  avisa antes de tocar ficheros compartidos (workflows, política, catálogo, `herramientas/`, `modulos/`,
  `ddd_core/`, este plan). Antes de lanzar, preguntar si otro chat ya lo hizo (01-11: Huelva/Valencia duplicadas).
- Las órdenes de lanzar o fusionar las confirma el propietario en el chat que ejecuta, no por mensaje entre sesiones.

## 1. Estado (2026-11-01 15:40)
- Autonómicas: 18/19 completas; Andalucía aparcada (T-07).
- Nacional (52): 38 completas (34 en el visor; La Rioja, Lugo, Santa Cruz de Tenerife y Tarragona republicándose,
  runs 41318666109/41318670798/41318675299/41318679581). Cantabria y Vizcaya con M06, sin electoral (T-04).
  12 PARADA en curso de resolución (T-02 y T-02b, abajo).
- 00 en curso: Valencia 41318119259, Huelva 41318125504 (CRS #374), Cádiz 41321082489, Barcelona 41321084407
  (exención municipal #380). No reactivar el ruleset con 00 en marcha.
- PR abiertas: #381 (T-10). Ruleset `proteger-main` desactivado hasta cerrar T-10.

### Asignaciones vigentes
| Chat | Tarea | Alcance | Situación |
|---|---|---|---|
| T-01 | T-02b · PARADA por población M05 | Cádiz, Barcelona, Madrid, Málaga, Alicante, Pontevedra, Baleares, Las Palmas | Cádiz/Barcelona lanzadas; resto espera diagnóstico local; todo en contratos (no toca la política) |
| T-02 | T-02 · resto de PARADA | Murcia, Álava (Huelva y Valencia hechas) + script `subir_diagnostico_t02.sh` | Álava: 00 «Reutilizar» 41346917857 con M04 7.6.0 (#383) y #387; Murcia: M04 aísla Yecla (30043), espera grafo del Mac |
| T-03 | PR, fusiones y T-10 | Fusionar con `pruebas` en verde; robots con app propia | #381 abierta; espera que el propietario cree la app y los secretos |

### Ficheros con turno exclusivo
- `modulos/04_generar_semillas.py`, `ddd_core/m04_seed_engine.py`: chat T-02 (M04 multisección).
- 10 workflows de registro: chat T-03 (#381).
- `configuracion/politica_generacion_territorial_2025.yaml`: libre (nadie la necesita ahora).

## 2. Decisiones del propietario
### Pendientes
- D-1. Completar Cantabria y Vizcaya por provincia o esperar a la activación por elección (T-04).
- D-3. Publicación en el visor del resto de provincias completas: por lotes o al cerrar la elección.
- D-4. El cambio de M04 (T-02) invalida los checkpoints pre-M04 de los contratos con islas (Canarias, Islas
  Baleares, nacional Baleares, Las Palmas, Santa Cruz de Tenerife): las próximas 00 de esos territorios empiezan de cero.
  Visto bueno antes de que T-02 abra la PR.
- Crear la GitHub App `ddd-registro` y los secretos `DDD_REGISTRO_APP_ID`/`DDD_REGISTRO_APP_KEY` (pasos en T-10).

### Tomadas (01-11)
- D-2: INE canónico; matrículas como alias, en español.
- #380 Cádiz y Barcelona: exención municipal en contrato y lanzamiento de 00.
- Álava: arreglar M04 para transferir varias secciones fronterizas (no exención ni aparcar).
- Madrid y Málaga: se mantiene la regla «un municipio que cabe bajo el techo no se divide»; reparación de población
  más profunda en contrato; si no basta, documentar como bloqueadas.
- Alicante: reparación más profunda (contrato). Pontevedra: reparación más profunda; si no basta, exención municipal.
- Las Palmas: exención municipal en contrato (no de toda Gran Canaria, 35-C01).
- Baleares: reparación más profunda (el reparto por islas no es viable: Ibiza+Formentera 1,41 de la media).
- Republicar en el visor La Rioja, Lugo, Santa Cruz de Tenerife y Tarragona.
- Ruleset: `puerta_admision` fuera de checks obligatorios (solo corre si la PR toca contratos).

## 3. Cola de tareas
T-08 y T-09 se numeran al final pero van en la posición de la cola que les corresponde por prioridad.

### T-08 · Proteger `main` con CI obligatoria
- Objetivo: impedir fusionar sin «pruebas» en verde y con la rama al día con `main` (lo que ocurrió con #374).
- Rol: operador (lo aplica el propietario: requiere permisos de administrador). Modelo: Haiku.
- Ficheros afectados: ninguno; ajuste del repositorio (Settings → Branches o ruleset sobre `main`):
  check obligatorio `pruebas`, «Require branches to be up to date», sin push directo. Comprobar antes que
  los robots de registro (catálogo, `estado_operativo.json`, activos del visor) que escriben en `main`
  quedan exentos o pasan por PR; si no, la protección los bloquea.
- Criterio de aceptación: una PR con «pruebas» en rojo o pendiente no se puede fusionar; los robots siguen
  registrando sin fallos durante una ejecución 00.
- Prueba local exigida: ninguna; verificación con `gh api repos/jfmurciego/DiputadodeDistrito/branches/main/protection`
  (o rulesets) y una ejecución 00 posterior con registro correcto.
- Dependencias: T-10 para reactivar. Máxima prioridad.
- Estado (2026-11-01): ruleset `proteger-main` (id 26311854) creado con PR obligatoria, check `pruebas` y rama
  al día (`puerta_admision` retirado: solo corre si la PR toca contratos y dejaba las demás en espera eterna).
  **Desactivado**: la app GitHub Actions no se puede añadir a los exentos y los robots de registro
  (`git push origin main` en 00, generación, operación, publicación del sitio y orquestación) quedarían bloqueados.
  Se reactiva al cerrar T-10.


### T-10 · Robots de registro con token propio (desbloquea T-08)
- Objetivo: que los workflows que hacen `git push origin main` lo hagan con un token de GitHub App propia
  (o PAT de grano fino) que pueda figurar como exenta en el ruleset, para reactivar `proteger-main`.
- Rol: implementador (workflows) + propietario (crear la app o el PAT y el secreto). Modelo: Opus.
- Ficheros afectados: `.github/workflows/ejecucion-completa-proyecto.yml`, `orquestacion-durable.yml`,
  `_reutilizable-generacion-territorial.yml`, `_reutilizable-operacion-territorial.yml`,
  `_reutilizable-publicar-sitio.yml` (paso de checkout/push con el token del secreto). Workflows compartidos:
  avisar a las demás sesiones antes.
- Criterio de aceptación: con el ruleset activo y la app exenta, una 00 registra en `main` sin
  «rule violations»; una PR sin `pruebas` en verde no se puede fusionar.
- Prueba local exigida: suite completa (incluye tests de gobernanza de workflows) + `actionlint` si está disponible.
- Dependencias: el propietario crea la GitHub App o PAT y el secreto. No reactivar el ruleset con 00 en curso.

### Resultado de T-01 (2026-11-01, `estado_operativo.json` de las 11:06 + anotaciones y logs de los jobs)
- Completas (32): Albacete, Almería, Ávila, Cáceres, Castellón, Ciudad Real, Córdoba, La Coruña, Cuenca, Gerona,
  Granada, Guadalajara, Huesca, Jaén, León, La Rioja, Lugo, Orense, Asturias, Palencia, Salamanca,
  Santa Cruz de Tenerife, Segovia, Sevilla, Soria, Tarragona, Teruel, Toledo, Zamora, Zaragoza, Ceuta, Melilla.
  En Huesca, La Rioja, Lugo, Santa Cruz de Tenerife y Tarragona el último run falló solo en 05 (visor), sin efecto en M08.
- M06 sin electoral (8): Badajoz, Burgos, Guipúzcoa, Lérida, Navarra, Cantabria, Valladolid, Vizcaya
  (lanzadas con alcance territorial; `main` registra después ejecuciones completas de Badajoz, Burgos, Lérida,
  Navarra y Valladolid: confirmar en el próximo estado operativo).
- PARADA (12), por causa:

| Causa | Provincia | Run | Detalle |
|---|---|---|---|
| Población (M05 `POPULATION_HARD_BLOCK`) | Alicante | 41293667422 | hard=1, desviación máx. 0,36 |
| | Barcelona | 41244711464 | hard=2, 0,30 |
| | Cádiz | 41243953699 | hard=2, 0,18 |
| | Madrid | 41244835816 | hard=1, 0,56 |
| | Málaga | 41293427148 | hard=1, 0,38 |
| | Pontevedra | 41293311168 | hard=1, 0,25 |
| | Baleares | 41250230577 | hard=2, 0,67 (con #370; revisar `component_districts`/exenciones) |
| | Las Palmas | 41250283081 | hard=1, 0,46 (con #370; techo 1,40 insuficiente o reparto no aplicado) |
| Población (M04, estructural) | Álava | 41240137880 | residual de Vitoria (01059) 0,72 bajo suelo; sin sección transferible |
| Conectividad (pre-M04) | Murcia | 41293548832 | «grafo territorial no supera conectividad administrativa», ya con #371 |
| Geometría fuente (01) | Huelva | 41292468775 | `GEOMETRY_INVALID_AUDITED`: secciones INE con huecos interiores sin máscara de cobertura |
| | Valencia | 41293787892 | ídem |

### T-02 · Diagnosticar y relanzar las PARADA
- Objetivo: corregir la causa de cada grupo de PARADA (empezando por M02 con puentes heredados 2024/2025,
  Huelva y Valencia) y dejar un script de relanzamiento para el Mac.
- Rol: implementador (corrección) + operador (relanzamiento por script). Modelo: Opus.
- Ficheros afectados: probablemente `herramientas/generar_provincias_congreso.py`, contratos
  `territorios/congreso_*/config/`, `particiones_insulares_2025.json`,
  `configuracion/politica_generacion_territorial_2025.yaml`; script en rama `lanzadores-mac`.
  Avisar antes de tocar `herramientas/`, `modulos/`, `ddd_core/` o la política.
- Criterio de aceptación: cada provincia PARADA llega al menos a M06 validado en un run nuevo; ninguna
  regresión en las 28 completas.
- Prueba local exigida: suite completa + diagnóstico local de M02/M04/M05 por provincia afectada con el grafo
  subido a `diagnostico/…` (ver `CLAUDE.md`, «Diagnóstico local»).
- Dependencias: T-01. Una PR por causa, no por provincia.

### T-02b · Bloqueos de población M05 (2026-11-01)
Runs 00 de las 16:40 (reparación profunda: profundidad 6, conjunto 3, 500.000 candidatos, 300 s). La reparación no mejoró ningún exceso: el bloqueo es estructural (municipios enteros indivisibles bajo el techo, regla del propietario).

| Provincia | Run | Distrito | Población | Límite | Exceso | Municipios enteros |
|---|---|---|---|---|---|---|
| Madrid | 41327479240 | 52 | 181.853 | techo 133.943 | +47.909 | Pozuelo (28115, 88.504), Boadilla (28022, 64.635) y 28181 (28.714) |
| Málaga | 41327483858 | 10 | 161.454 | techo 134.376 | +27.078 | 29054 (85.136) y 29025 (76.318) |
| Alicante | 41327488604 | 12 | 156.889 | techo 132.268 | +24.620 | trozo de 03065 (119.050) y 03121 (37.839) |
| Barcelona | 41327510776 | 31 | 150.148 | techo 133.339 | +16.809 | 08015 (112.242) y 08194 (37.906); el distrito 40 (08073) va exento del suelo |

**Estado: BLOQUEADAS por estructura.** Quedan para un futuro estudio de motor. Palancas descartadas: bajar `municipality_atomicity_limit_ratio` (contradice la regla de no partir un municipio que cabe bajo el techo) y subir el techo (Barcelona 31 está a 1,29 de la media).

Resueltas por decisión del propietario: Cádiz (techo 116 % solo en Cádiz, política 1.7.3, distrito 8 a 1,159 de la media), Pontevedra (exención municipal 36008), Las Palmas (exención municipal 35012). Baleares: techo 127 % solo en Baleares (política 1.7.3; distrito 5 de Mallorca a 1,261 de la media, la reparación profunda no lo mejoró).

### T-09 · Huella de puentes heredados antes de M02
- Objetivo: comprobación previa que detecte puentes municipales heredados de 2024/2025 que ya no casan con el
  inventario municipal y la geometría vigentes, y bloquee con mensaje claro antes de lanzar M02 (evita PARADA).
- Rol: implementador. Modelo: Opus.
- Ficheros afectados: `herramientas/generar_provincias_congreso.py` (o nueva herramienta de comprobación en
  `herramientas/`), paso previo del workflow que lanza M02, tests nuevos en `tests/`. Avisar antes de tocar
  `herramientas/` y workflows.
- Criterio de aceptación: para cada provincia nacional, informe de puentes (válido / municipio inexistente /
  municipios no colindantes ni enlazables / código INE cambiado); las provincias que pararon en M02 por
  puentes (T-01/T-02) salen marcadas; las 28 completas salen limpias.
- Prueba local exigida: suite completa + ejecución de la comprobación sobre todos los contratos
  `territorios/congreso_*` + test con un puente roto sintético.
- Dependencias: T-01 (causas de PARADA). Va detrás de T-02 en prioridad; si T-02 corrige puentes, se apoya en ello.

### T-04 · Completar electoral de las provincias con M06
- Objetivo: llevar las 11 provincias con M06 (y las que salgan de T-02) a M08 con la activación por elección.
- Rol: operador. Modelo: Sonnet.
- Ficheros afectados: ninguno de código; script de lanzamiento en `lanzadores-mac`.
- Criterio de aceptación: 52/52 provincias nacionales con «Cadena completa validada» en el estado operativo.
- Prueba local exigida: ninguna (lanzamiento); comprobación del estado con `generar_estado_operativo.py`.
- Dependencias: T-02, T-03, D-1, permiso explícito del propietario.

### T-05 · Renombrado visible a «nacional»
- Objetivo: en visor, dashboard, informes y textos públicos, «nacional» en lugar de «congreso»; sin
  «circunscripción» en lo visible; topónimos en español. Los identificadores internos (`congreso_*`) no cambian.
- Rol: implementador. Modelo: Sonnet.
- Ficheros afectados: `herramientas/generar_estado_operativo.py`, plantillas del visor, generadores de
  nombres visibles (`display_name`), documentos públicos.
- Criterio de aceptación: `grep -ri "congreso\|circunscripci"` sobre las salidas visibles (visor, dashboard,
  `estado_operativo.json` campos `name`/`display_name`) sin coincidencias; claves internas intactas.
- Prueba local exigida: suite completa + regenerar estado operativo y visor en local y revisar el grep.
- Dependencias: ninguna (mejor tras T-03 si toca los mismos generadores).

### T-06 · Gestor de Campañas con provincias
- Objetivo: el selector del Gestor admite las elecciones nacionales por provincia además de las 19 autonómicas.
- Rol: implementador. Modelo: Sonnet (Opus si exige cambiar el modelo de datos).
- Ficheros afectados: módulo/plantillas del Gestor de Campañas y su catálogo de ámbitos.
- Criterio de aceptación: el selector lista las 52 provincias con nombre en español y etiqueta «nacional»;
  abrir una provincia completa carga sus distritos y resultados.
- Prueba local exigida: suite completa + prueba del selector con una provincia (Huesca).
- Dependencias: T-03 (clave de elección), T-05. Prioridad secundaria.

### T-07 · Andalucía (al final)
- Objetivo: generar y validar distritos de Andalucía y completar su cadena.
- Rol: implementador + operador. Modelo: Opus.
- Ficheros afectados: contrato de Andalucía, política (`population_limits`, exenciones), lanzador del Mac.
- Criterio de aceptación: Andalucía con «Cadena completa validada»; 19/19 autonómicas.
- Prueba local exigida: suite completa + diagnóstico local M04/M05 con el grafo de Andalucía.
- Dependencias: T-04 terminada.

## 4. Tareas hechas
<!-- Formato: T-xx · resumen · PR #nnn / run nnnnnnnnnn · fecha -->
- T-01 · Clasificación de las 52 provincias y causas de PARADA (tabla antes de T-02) · 2026-11-01
- T-02 (Huelva y Valencia) · CRS de M02 EPSG:25830 como el autonómico; Huelva además solape 2 m². Cadena
  completa 01→04: Huelva 41318125504 (02) + par 41335075779 + 00 41335929678; Valencia 41318119259 (02) + par
  41335082275 + 00 41335936727 · PR #374 · 2026-11-01
- T-03 · Activación por elección: clave `ES-NAC|AUT-[unidad-]AAAAMMDD` (INE canónico, matrícula alias; D-2 según
  recomendación), workflow «Activación por Elección» (plan/activar/electoral/completa, filtro `solo`) y 00 v1.4.6
  con `lanzado_por_eleccion` · PR #376 · 2026-11-01
