# T-444 · Cierre de la migración de workflows (D-129, D-130)

VERSIÓN: 1.0.0 · FECHA: 2026-11-22 · ESTADO: propuesta, solo diseño (sin implementar) · ANTERIOR: ninguna (fichero nuevo)

Base: `origin/main` @ `0cd77bed`. Lecturas: los 7 ficheros, `docs/PLAN.md` (D-129, D-130, D-135, D-142, D-144, D-145,
D-149, D-155, D-159, D-164), diseño T-378 1.1.4 (§9, §11, §13), `.claude/rules/workflows.md`, las PR #888, #913, #938 y #956,
y el ruleset `proteger-main` (API, 22-11). Los recuentos de referencias excluyen `legacy/`, `docs/registro/` y
`docs/REGISTRO_DE_CAMBIOS.md`.

## 1. Resumen

| # | Fichero (versión, líneas) | Nombre visible | Destino | PR | Fecha |
|---|---|---|---|---|---|
| 1 | `ejecucion-completa-proyecto.yml` (1.11.5, 1734) | P00 Campaña | Se retira: lo absorben P00 nueva (`p00-campana.yml` + `p00-cadena.yml`) y P10-P40 | R1 | Después del 29-11 |
| 2 | `gestor-campanas.yml` (1.11.3, 560) | P00 Campaña — Gestor | Se retira: botón y comprobación previa de P00 | R1 | Después del 29-11 |
| 3 | `activacion-por-eleccion.yml` (1.1.3, 116) | _P00 Campaña — Elección | Se retira: la expansión elección → territorios pasa a la comprobación previa de P00 | R1 | Después del 29-11 |
| 4 | `preparacion-legislatura-vigente.yml` (1.0.12, 437) | P00 Campaña — Legislatura | Se retira: P10 (P11 y P12) dentro de la cadena, con el par en R2 y en el cierre | R1 | Después del 29-11 |
| 5 | `_reutilizable-puerta-validacion.yml` (1.4.0, 197) | Interno · P40 Puerta de validación | Acción compuesta `.github/actions/puerta-validacion/action.yml` | R2 | Después de R1 |
| 6 | `auto-merge.yml` (1.3.2, 95) | _P90 Automático — Fusión automática | Fichero propio de P90 (D-135), solo cambia el nombre del fichero: `p90-fusion-automatica.yml` | R3 | Después del 29-11 y de decidir #888 |
| 7 | `revisor-pr.yml` (1.1.2, 137) | _P90 Automático — Revisor de PR | Fichero propio de P90 (D-144 a), solo cambia el nombre del fichero: `p90-revisor-pr.yml` | R3 | Ídem |

Después viene R4, el paso 10 (documentación renumerada, T-383, D-142), y por último la limpieza de ejecuciones de D-155
(la hace el Operador, con frase).

Las PR #913, #938 y #956 **no chocan** con R1, R2 ni R3: no borran ni editan ninguno de los 7 ficheros, y dependen de dos
de ellos. `p00-cadena.yml` llama 4 veces a la puerta reutilizable. `p00-campana.yml` lleva el mismo `name:` que la 00 vieja
(«P00 Campaña»). **Por eso R1 y R2 van detrás de esas tres PR.** La única PR abierta que toca alguno de los 7 es **#888**
(T-379 2a, en pausa por D-164). Modifica `auto-merge.yml`, `ejecucion-completa-proyecto.yml` y
`preparacion-legislatura-vigente.yml` (`environment: registro`), así que choca con R1 y R3 (pregunta 4).

## 2. Condiciones comunes

- Una PR por familia, con `no-automerge` y en borrador hasta la revisión. La fusiona el propietario, o el Coordinador
  con su frase. Cada fichero borrado va a `legacy/workflows/<nombre>_v<versión>_<fecha>.yml` con `git mv`, y cada fichero
  tocado sube VERSIÓN y deja su ANTERIOR.
- En cada PR, revisor independiente, CI verde en la PR y «main en verde» antes de fusionar.
- Ninguna PR lanza nada. Las pruebas reales de §3 las lanza el Operador con frase del propietario.
- Las listas fijadas se ajustan en la misma PR (regla de workflows): `test_t397_nombres_workflows`,
  `test_design_a_matriz_sintetica` (lista de `workflow_dispatch`), `test_design_a_catalogo`,
  `test_codauto_preparation_contract` y `test_workflow_safety`.

## 3. Por fichero

### 3.1 `ejecucion-completa-proyecto.yml` (la 00)

- **Destino.** Se retira. Sus jobs ya llaman a P10/P20/P30/P40/P70 y a la puerta. La cadena equivalente es
  `p00-cadena.yml`: plan → P11 → puerta 01 → P12 → P20 → puerta 02 → puerta 03 → P30 → puerta 04. El manifiesto y el
  estado van al cierre de `p00-campana.yml` (3c, #956).
- **Qué la llama hoy:**
  - Workflows: `gestor-campanas.yml` (`uses:`, l. 464). Ella misma se encadena por `dispatches`: otra 00 «Reutilizar»
    (l. 1720) y `prepare_one` (l. 1695). `activacion-por-eleccion.yml` la lanza a través del plan de `clave_eleccion.py`.
    `p90-automatico.yml` la escucha por nombre (`workflow_run` «P00 Campaña», l. 38); tras R1 la recoge `p00-campana.yml`,
    que lleva el mismo nombre.
  - Herramientas (7):
    - `legislatura_vigente.py` (`WF_00`) y `metricas_proceso.py` (`WF_00`);
    - `clave_eleccion.py` (tabla `completa`);
    - `generar_provincias_congreso.py` y `generar_provincias_congreso_350.py` (`WORKFLOWS`: reescriben las opciones del
      selector);
    - `descargar_artefacto.py` y `campana_estado.py` (solo texto de mensajes).
  - Tests: 48 módulos.
  - Otros: skill `lanzar-00`, `CLAUDE.md` (sección «Ejecución 00»), `README.md`, 13 documentos en `docs/`,
    `documentacion_publica/evidencias/source-index.json` y 3 ficheros de `evals/oro` (históricos, no se tocan).
- **Equivalencia.**
  1. Test de inventario: cada job de la 00 tiene su destino (job o paso de `p00-cadena`/`p00-campana`/P10-P70) o «retirado»
     con su motivo, en una tabla versionada que el test cruza con el YAML de `legacy/`. Si sale un job nuevo sin destino,
     el test falla.
  2. Test D-142 limitado al código: ningún workflow, herramienta, test ni skill vivo cita el fichero borrado.
  3. La lista de `workflow_dispatch` queda en los 9 P.
  4. Prueba real previa (condición de T-378 §11): al menos una campaña real de P00 completa en verde antes de fusionar R1.
- **Fecha.** Después del 29-11. Esa noche va con la 00 actual (D-145 C), y R1 entra después de fusionar #913, #938 y #956
  y de la primera campaña real de P00.
- **Riesgo: alto.** Desaparece el plan B, la vía de reutilizar checkpoints M04 y la de recuperar un territorio suelto. Lo
  mitiga la prueba real previa. Además, `legacy/` conserva el fichero, y una PR de reversión lo devuelve en minutos.
  Métricas: `metricas_proceso.py` pierde la serie de la 00 si solo lee `p00-campana.yml` (pregunta 3).

### 3.2 `gestor-campanas.yml` (Gestor)

- **Destino.** Se retira. El botón pasa a P00 y el plan a la comprobación previa con semáforo (T-378 §9).
  `herramientas/gestor_campanas_2.py` y `legislatura_vigente.py` solo los usa el Gestor: van a `legacy/` con sus tests,
  salvo las funciones que reutilice P00 (inventario en R1).
- **Qué lo llama hoy:**
  - nada por `uses:` ni por `dispatches`: es un botón;
  - herramientas: `legislatura_vigente.py` (`WF_GESTOR`);
  - 14 tests, la skill `lanzar-campana`, `README.md`, 12 documentos y los datos generados
    `orchestracion/metricas_proceso.json` y `dashboard/metricas_proceso.json`.
- **Equivalencia.** La misma tabla de §3.1, con las opciones del botón: cada opción del Gestor va a una opción de P00
  (territorios, elección, modo y publicar) o sale como retirada. También el test de §3.1.2.
- **Fecha y riesgo.** Después del 29-11, en R1. Riesgo medio: lo que cuenta es la trazabilidad de las métricas.

### 3.3 `activacion-por-eleccion.yml` (Elección)

- **Destino.** Se retira. `clave_eleccion.py` sigue (expande la elección a territorios), pero pierde la tabla
  `DISPATCH` (`activar`, `completa`), porque P00 no lanza nada por fuera (D-130).
- **Qué lo llama hoy:**
  - botón;
  - `clave_eleccion.py` (docstring y tabla);
  - 5 tests (`test_clave_eleccion`, `test_codauto_preparation_contract`, `test_design_a_matriz_sintetica`,
    `test_t397_nombres_workflows` y `tests/generar_equivalencias_5_0_0.py`);
  - 5 documentos.
- **Equivalencia.** Para cada elección del catálogo, la lista de territorios de `clave_eleccion.py` sin `DISPATCH` es
  igual a la de hoy. Se comprueba con los valores literales de `test_clave_eleccion` y un control negativo.
- **Fecha y riesgo.** Después del 29-11, en R1. Riesgo bajo.

### 3.4 `preparacion-legislatura-vigente.yml` (Legislatura)

- **Destino.** Se retira. P11 y P12 corren dentro de la cadena. El artefacto `ddd-prepared-source-pair` (l. 306)
  desaparece: el par va a R2 y al cierre (T-378 §5). `registrar_par` sale del inventario de la app (T-378 §10).
- **Qué lo llama hoy:**
  - workflows: la 00 por `dispatches` (l. 1695);
  - herramientas: `clave_eleccion.py` (tabla `activar`), `comprobar_paquete_electoral_remoto.py` (texto de remedio) y
    los dos `generar_provincias_congreso*.py` (`WORKFLOWS`);
  - 12 tests, la skill `lanzar-00`, `CLAUDE.md` (pasos 1-3 de `TERRITORIAL_READY_PAIR_INCOMPATIBLE`), 9 documentos y
    `evals/oro` (histórico).
- **Equivalencia.** La tabla de §3.1 (operaciones `prepare_one` y lote → P10 en la cadena), más un test de que
  `comprobar_paquete_electoral_remoto.py` da un remedio que existe.
- **Fecha y riesgo.** Después del 29-11, en R1. Riesgo medio: la receta de CLAUDE.md para un par incompatible deja de
  valer el día de R1. Por eso R4 va justo detrás, o el remedio se cambia en la misma R1 (pregunta 2).

### 3.5 `_reutilizable-puerta-validacion.yml` (puerta)

- **Destino.** Acción compuesta `.github/actions/puerta-validacion/action.yml` (D-129: nada «Interno»; T-378 §13 PR 2,
  sin hacer). Mismas entradas (9) y salidas (5). Los secretos de R2 pasan a ser entradas, que el caller lee en el `env`
  del paso (regla de R2).
- **Qué la llama hoy:**
  - workflows: la 00 (5 `uses:`, desaparecen con R1), `p70-archivo.yml` (job `validar_m08`, l. 609) y, en #913/#956,
    `p00-cadena.yml` (4 `uses:`), además de la ruta en `paths` de `gestor-campanas.yml`;
  - herramientas: `campana_estado.py` (cita líneas del fichero en `ARTIFACT_EGRESS_QUOTA`);
  - 15 tests y 6 fixtures; 6 documentos.
- **Diferencias que hay que cubrir.**
  1. El job lo pone el caller: `runs-on`, `permissions: contents: read, actions: read`, el checkout de
     `inputs.source_ref || github.sha` y el `upload-artifact`.
  2. El nombre del check pasa de «`<job>` / Puerta de validación» a «`<job>`».
     `herramientas/generar_estado_operativo.py` usa etiquetas propias, no ese nombre: hay que comprobarlo en R2.
- **Equivalencia.**
  1. Los bloques `run:` de la acción son idénticos byte a byte a los del reutilizable de `legacy/`. El test los extrae y
     los compara.
  2. Mismas salidas, y la misma decisión con los fixtures actuales de la puerta.
  3. Cada caller declara los mismos permisos y el mismo `source_ref`.
  4. Prueba real: una P70 que pase por `validar_m08` (con simulación si la acción lo admite) y la primera P00 en «solo
     comprobar» tras la fusión.
- **Fecha y riesgo.** Después de R1. Así la PR solo toca P70 y `p00-cadena`, y no 10 llamadas de un fichero que se va a
  borrar. Riesgo medio: la puerta decide si una cadena sigue. Un permiso o un checkout mal puesto rompe todas las
  campañas, y eso solo se ve en un run real.

### 3.6 `auto-merge.yml` y 3.7 `revisor-pr.yml` (mecanismo de fusión)

- **Destino.** Siguen en ficheros propios: son la excepción permanente de D-135 y D-144 (a). Por dos motivos no pueden ir
  dentro de `p90-automatico.yml`:
  - GitHub rechaza un `workflow_run` que se nombra a sí mismo, y fusionar desde el run de la PR ejecutaría su código con
    la app;
  - `labeled`/`ready_for_review` en el workflow de `pruebas` crea un `pruebas` skipped que el ruleset da por cumplido.

  Lo único que cambia es el **nombre del fichero**: `p90-fusion-automatica.yml` y `p90-revisor-pr.yml`. Los nombres
  visibles (D-159) no cambian.
- **Qué los llama hoy:**
  - `auto-merge.yml`: nadie por `uses:` ni por nombre (es un disparador). Herramienta: `decidir_auto_merge.py`
    (docstring). 4 tests: `test_auto_merge`, `test_t366_p90_equivalencia`, `test_corte_5_0_0_equivalencias` y
    `test_t397_nombres_workflows`. También la skill `operador`, `.claude/rules/workflows.md`, `docs/PLAN.md`,
    `docs/INVENTARIO_WORKFLOWS_RETIRADOS.md` y 13 documentos.
  - `revisor-pr.yml`: nadie. 3 tests (`test_agentes_ci`, `test_t366_p90_equivalencia` y `test_t397_nombres_workflows`),
    `.claude/rules/workflows.md` y 11 documentos.
- **Lo que no se toca** (lo garantiza un test de equivalencia sobre el YAML cargado, comparado con la copia de `legacy/`
  y con control negativo):
  - el `name:`;
  - `on:` (en auto-merge, `workflow_run` de «P90 Automático» con `types: [completed]`; en el revisor, los 5 tipos);
  - `permissions` de workflow y de job;
  - `concurrency`, con los mismos grupos `ddd-auto-merge-<sha>` y `ddd-revisor-pr-<n>`, para que un run viejo y uno
    nuevo del mismo SHA nunca corran a la vez;
  - todos los `if:`, incluido `workflow_run.path == '.github/workflows/p90-automatico.yml'`;
  - los ids y nombres de job: **`veredicto`** sigue siendo el job del revisor, y `pruebas` sigue en `p90-automatico.yml`,
    que R3 no toca;
  - los pasos, byte a byte.
- **Estado del ruleset `proteger-main` (id 26311854), leído el 22-11:**
  - exige solo `veredicto` (integración 15368);
  - **no tiene regla `pull_request`: ninguna aprobación obligatoria**;
  - salta la regla siempre para el rol 5 (administrador) y para la integración 5568103 (la app de registro).

  Conclusiones:
  - **D-144 (b) sigue pendiente**: `pruebas` no es check obligatorio.
  - Exigir una aprobación no protegería nada mientras la app y el administrador puedan saltarse la regla: la garantía real
    es `decidir_auto_merge.py` (`pruebas` en success sobre el HEAD exacto y de la suite que dispara, PR no borrador, sin
    `no-automerge`, del repositorio y hacia `main`).

  El test de equivalencia de R3 ejecuta `decidir_auto_merge.py` con fixtures: debe rechazar el borrador, `no-automerge`,
  `pruebas` en failure o de otra suite, y el fork.
- **Fusión de R3.** En borrador y con `no-automerge`: la fusión automática no la toca. **Solo la fusiona el propietario,
  con su frase en el chat que fusiona** (el clasificador lo exige en los cambios del mecanismo de fusión). Al pasar a
  lista, la propia PR ejecuta ya `p90-revisor-pr.yml` desde su referencia de merge. Con `revisar-ia`, ese run debe dar
  el check `veredicto`. Es la primera prueba.
- **Prueba real tras fusionar:**
  1. La primera PR de solo docs, sin etiqueta, se fusiona sola con un run de «_P90 Automático — Fusión automática» cuyo
     `path` es `p90-fusion-automatica.yml`.
  2. Una PR con `revisar-ia` deja su comentario `veredicto`.
  3. Una PR con `no-automerge` no se fusiona.

  Si 1 falla, la reversión es una PR que devuelve los dos nombres, y mientras tanto se fusiona a mano.
- **Fecha.** Después del 29-11 (antes no se gana nada y se arriesga la fusión en la semana clave), y después de decidir
  #888, que edita `auto-merge.yml`.
- **Riesgo: medio.** Si el mecanismo falla, se para la fusión de todas las PR, pero sin fusionar nada indebido: todas las
  condiciones son fallo cerrado. Queda un riesgo residual: GitHub registra cada fichero como un workflow nuevo, y el viejo
  queda en la lista con sus ejecuciones hasta la limpieza de D-155.

## 4. Orden y dependencias

1. **29-11**: noche electoral con la 00 actual (D-145 C). Antes no entra nada de T-444.
2. Fusión de #913 → #938 → #956 (T-379) y primera campaña real de P00 en verde (T-378 §11).
3. **R1**: retirada de la familia P00 vieja (§3.1-§3.4).
4. **R2**: puerta → acción compuesta (§3.5), con P00 «solo comprobar» como prueba real.
5. **R3**: renombrado de los dos ficheros de fusión (§3.6-§3.7). Es independiente de R1 y R2, pero va después de #888.
6. **R4 = paso 10** (§5).
7. Limpieza de ejecuciones de los workflows retirados (D-155): la hace el Operador, con frase del propietario.

## 5. Paso 10: documentación renumerada (T-383, D-142)

Se reescribe solo el texto vivo. Lo histórico (`docs/ESTUDIOS`, `docs/AUDITORIAS`, `docs/registro`, `evals/oro`) no se
toca.

- `CLAUDE.md`:
  - «Ejecución 00» y «Visor» en notación P (P00 nueva, sus modos y la receta del par incompatible con P10 en la cadena);
  - la lección de la 00 que se encadena y se cuela pasa a legacy;
  - `auto-merge` → «la fusión automática de P90»;
  - el texto sigue por debajo de 100 líneas.
- `.claude/rules/workflows.md`: rutas nuevas de los dos ficheros de fusión. Las lecciones de la 00 vieja pasan a legacy
  con nota.
- Skills:
  - `lanzar-00` y `lanzar-campana` se funden en `lanzar-p00`;
  - `publicar-visor` pasa a `publicar-p40`;
  - la skill `operador`, con la ruta de la fusión automática.
- `docs/ARQUITECTURA/`: 4 a 6 documentos por fichero.
- `docs/ARQUITECTURA/EQUIVALENCIAS_D129.md`: una fila por cada uno de los 7 (viejo → destino → PR).
- `README.md`.
- `docs/INVENTARIO_WORKFLOWS_RETIRADOS.md`: los 4 de R1, la puerta y los 2 nombres de fichero de R3, con su id de
  workflow (de la API, en solo lectura).
- Test (D-142): falla si un documento vivo cita un workflow que no existe en `.github/workflows/`. En CI no hay `.git`,
  así que usa `os.walk`.

## 6. Riesgos transversales

- **Ventana R1 → R4.** Las skills y CLAUDE.md citan ficheros que ya no existen, y un Operador podría intentar lanzar la
  00. Se evita con R4 inmediata o con un aviso mínimo en la propia R1 (pregunta 2).
- **Tests con estado vivo.** Varios de los 48+14+12 módulos leen el catálogo o `datos_abiertos`
  (`.claude/rules/workflows.md`). Al llevarlos a legacy, hay que comprobar que no queda ninguna fixture huérfana.
- **`test_t220_renombrado`** rechaza ids viejos en ficheros nuevos, también en las tablas de inventario: se usan ids
  `nacNN/autNN`.

## 7. Preguntas al propietario

1. **¿R1 se fusiona solo tras una campaña real de P00 en verde, o basta la validación de aut11 desde la rama?**
   Recomiendo una campaña real (lo que dice T-378 §11): R1 quita el plan B.
2. **¿El paso 10 va en una PR aparte (R4, como manda D-142) o el mínimo operativo entra en R1?** Ese mínimo son
   CLAUDE.md «Ejecución 00», las skills `lanzar-00` y `lanzar-campana`, y el remedio de
   `comprobar_paquete_electoral_remoto.py`. Recomiendo meter el mínimo en R1 y dejar el resto en R4: así no queda ninguna
   ventana con instrucciones rotas.
3. **Métricas: ¿`metricas_proceso.py` sigue contando las ejecuciones históricas de la 00 junto a las de P00, o la serie
   empieza de cero?** Recomiendo que lea las dos (la 00 por su id de workflow, que sigue en la API) y separe P00 nueva por
   «· campaña ·».
4. **#888 (2a, en pausa por D-164) edita `auto-merge.yml` y dos ficheros de R1. ¿Se cierra, o se reactiva antes de R1 y
   R3?** Recomiendo decidirlo antes de R1. Si sigue en pausa más allá de R1, que se cierre y se rehaga sobre los ficheros
   nuevos: rebasarla sobre ficheros borrados es más caro.
5. **R3: ¿se renombran los ficheros de fusión a `p90-*.yml` o se quedan como están?** Funcionalmente es lo mismo, porque
   los nombres visibles ya son «_P90…». Recomiendo renombrar, después del 29-11, con la prueba real de §3.6. Si prefiere
   riesgo cero en el mecanismo de fusión, la otra opción es dejarlos y declararlos P90 solo en EQUIVALENCIAS_D129.
6. **D-144 (b): ¿se añade ya `pruebas` a los checks obligatorios del ruleset, que hoy solo exige `veredicto`?** Recomiendo
   hacerlo en una acción aparte, después de R3: primero se comprueba que P90 crea `pruebas` en las PR de solo docs.
   Con eso basta. Una aprobación obligatoria no protegería nada mientras la app y el administrador puedan saltarse la
   regla. La cambia el propietario, o el Operador con su frase.
7. **R2: ¿acción compuesta (D-129) o se mantiene el reutilizable con otro nombre?** Recomiendo la acción compuesta,
   después de R1, con el test de bloques idénticos y la prueba real de P70 + P00 «solo comprobar».
