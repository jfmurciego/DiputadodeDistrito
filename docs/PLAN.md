<!--
Nombre: Plan de trabajo DDD
Versión: 1.0.0
Fecha: 2026-11-01
Alcance: Cola de tareas para chats implementadores y operadores
Estado: candidato
Cambios/motivo: Alta del plan (sesión planificadora)
Anterior: —
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
- D-3. Publicación en el visor de las 27 provincias completas además de Huesca: ¿ahora o al cerrar la elección entera?

## 3. Cola de tareas

### T-01 · Revisar el log del Mac y el estado de las 51 provincias
- Objetivo: tabla única provincia → último run 00, fase alcanzada, PARADA sí/no y causa (anotaciones del check-run).
- Rol: operador. Modelo: Sonnet.
- Ficheros afectados: solo este `docs/PLAN.md` (tabla en T-02); ninguno de código.
- Entrada: el propietario pega `grep -E "PARADA|ERROR|OK" ~/lanzar_resto.log` en el chat.
- Criterio de aceptación: las 51 clasificadas en {completa, M06 sin electoral, PARADA con causa, sin lanzar};
  causas agrupadas (M02 puentes, población, conectividad, otro); coincide con `estado_operativo.json`.
- Prueba local exigida: ninguna (solo lectura con `gh api .../check-runs/<job>/annotations`).
- Dependencias: ninguna.

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

### T-03 · PR de activación por elección
- Objetivo: activar, preparar electoral (03) y ejecutar 00 por elección entera, no por provincia. Clave
  `ES / nacional / provincia (INE o matrícula) / fecha`, preparada para el histórico de legislaturas
  (varias elecciones nacionales y autonómicas coexistiendo).
- Rol: implementador. Modelo: Opus.
- Ficheros afectados: `preparacion-legislatura-vigente.yml`, `preparacion-resultados-electorales.yml`,
  `ejecucion-completa-proyecto.yml`, catálogo de preparación/maestro, `herramientas/` de activación,
  esquema de clave y sus tests. Coordinar con cualquier sesión que toque workflows o catálogo.
- Criterio de aceptación: una sola activación + una 03 + un 00 cubren las 52 provincias de la elección
  2023-07-23; las autonómicas siguen funcionando con la misma clave; la clave admite INE y matrícula y
  resuelve a un único canónico (D-2); dos elecciones distintas no colisionan en catálogo ni checkpoints.
- Prueba local exigida: suite completa + test nuevo de resolución de claves (INE ↔ matrícula) y de
  expansión elección → provincias + simulación en seco del 00 por elección.
- Dependencias: D-2. Puede avanzar en paralelo a T-02 (sin lanzar).

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
