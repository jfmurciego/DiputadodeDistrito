<!--
Nombre: Plan de trabajo DDD
Versión: 1.0.3
Fecha: 2026-11-01
Alcance: Cola de tareas para chats implementadores y operadores
Estado: candidato
Cambios/motivo: D-2 confirmada (matrículas en español); T-01 hecha con tabla de PARADA
Anterior: legacy/docs/PLAN_v1.0.2_20261101.md
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

## 1. Estado (2026-11-01, `orchestracion/estado_operativo.json`)
- Autonómicas: 18/19 con cadena completa (M08); Andalucía aparcada (fuentes preparadas, sin generar).
- Nacional: 52 ámbitos en el estado (51 lanzados el 31-10 + Huesca, completa y publicada en el visor).
- Nacional completas (28): Albacete, Almería, Ávila, Cáceres, Castellón, Córdoba, La Coruña, Cuenca, Granada, Guadalajara, Huesca, Jaén, León, La Rioja, Lugo, Orense, Asturias, Salamanca, Santa Cruz de Tenerife, Segovia, Soria, Tarragona, Teruel, Toledo, Zamora, Zaragoza, Ceuta, Melilla.
- Nacional con M06 y sin electoral (11): Burgos, Ciudad Real, Gerona, Guipúzcoa, Lérida, Navarra, Palencia, Cantabria, Sevilla, Valladolid, Vizcaya. Sin generar (11): Álava, Alicante, Badajoz, Baleares, Barcelona, Cádiz, Madrid, Málaga, Murcia, Las Palmas, Pontevedra. Validación pendiente (2): Huelva, Valencia.
- No hay PR abiertas. Riesgo conocido: puentes municipales heredados 2024/2025 pueden romper M02 en algunas provincias.

## 2. Decisiones pendientes del propietario
- D-1. ¿Las 11 provincias con M06 sin electoral se completan ya por provincia (vía actual) o esperan a la
  activación por elección (T-03)? Recomendación: esperar a T-03 para no rehacer 03/00 por duplicado.
- D-2. Formato canónico de la clave de elección: número INE (`ES-NAC-22-20230723`) o matrícula (`ES-NAC-HU-20230723`).
  Recomendación: número INE como canónico y matrícula solo como alias de presentación.
  D-2 confirmada por el propietario: INE canónico; matrículas solo en español (PM, GE, OR…).
- D-3. Publicación en el visor de las 27 provincias completas además de Huesca: ¿ahora o al cerrar la elección entera?

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
- Dependencias: ninguna. Máxima prioridad.


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
- T-03 · Activación por elección: clave `ES-NAC|AUT-[unidad-]AAAAMMDD` (INE canónico, matrícula alias; D-2 según
  recomendación), workflow «Activación por Elección» (plan/activar/electoral/completa, filtro `solo`) y 00 v1.4.6
  con `lanzado_por_eleccion` · PR #376 · 2026-11-01
