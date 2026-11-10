# T-162 · Propuesta para gastar menos minutos en la CI `pruebas` (D-46)

Solo propuesta documental: no se toca ningún workflow ni test. Fecha de los datos: 10-11-2026.

## 1. Datos (REST `gh api`, sin /timing)

Fuente: runs de `pruebas-plataforma.yml` creados del 27-10 al 10-11 (1.512 runs) y sus jobs (`recoger_runs.py`,
`analisis_runs.py`). Minutos = duración de cada job redondeada al minuto (así factura Actions). Días sin runs: 4, 5 y 6 de
noviembre. La actividad se concentra tras la 1.6.0 (T-50, 7-11), así que **la base es la última semana (3-10 nov): 1.068 runs,
25.083 min**, frente al tope de 15.000. Es una semana punta (ensembles, campañas); otra más tranquila gastará menos.

| Parte (3-10 nov) | min | % |
|---|---:|---:|
| Pasos «Verificar evidencia…» (tests de los 5 grupos) | 13.860 | 55 % |
| Paso «Construir entorno reproducible» (`docker build` ×5 por run) | 4.193 | 17 % |
| Resto de la matriz (checkout, GerryChain, descubrimiento, subida) | ~3.700 | 15 % |
| `guardian` | 957 | 4 % |
| `pruebas` (agregador; incluye runs antiguos de antes de la 1.6.0) | 2.400 | 10 % |

Por origen del run:

| Origen | runs | min | % |
|---|---:|---:|---:|
| Push a `main` de bots de datos (`chore: registrar/sincronizar/archivo…`, autor github-actions) | 372 | 9.561 | 38 % |
| Push a `main` «registro: numerar» (bot de registro) | 184 | 4.652 | 19 % |
| Push a `main` de personas/Claude (fusiones de PR) | 166 | 3.869 | 15 % |
| Runs de PR en verde | 208 | 4.754 | 19 % |
| Runs de PR en rojo | 39 | 1.029 | 4 % |
| Runs de PR cancelados | 86 | 1.130 | 5 % |

Hallazgos:
1. **El 72 % del gasto son pushes a `main`, y el 57 % lo producen bots** que solo registran datos o numeran el registro.
   Cada uno ejecuta la suite completa (~23 min facturables por run).
2. Los pushes llegan en ráfagas: 655 de 722 runs de push tuvieron otro push en los 12 min siguientes (~16.500 min). Con
   `concurrency` por SHA no se cancela ninguno.
3. `docker build` se repite 5 veces por run (una por grupo): 17 % del total, y la imagen solo cambia en el `COPY . /app`.
4. En PR ya hay `cancel-in-progress` (86 runs cancelados) y 2,1 runs por PR de media.
5. Duración de pared: mediana 8,8 min, p90 16,5 min (la 1.6.0 ya la bajó; aquí solo importan los minutos facturados).

## 2. Garantía de no debilitar

- El check obligatorio sigue siendo el job final `pruebas` (necesita todos los jobs; falla si alguno no es `success`).
- Toda **PR** sigue pasando la suite completa antes de fusionarse (las opciones 1-4 no tocan eso). La única opción que lo
  sustituiría (opción 6, selección por rutas) queda condicionada a una prueba de cobertura y va la última.
- `main` sigue verde por la regla del propietario: las opciones sobre push mantienen la suite completa en el tip de `main`
  y una vez al día.

## 3. Opciones

Ahorros sobre la base de 25.083 min/semana. Son estimaciones; los solapes se tratan en §4.

### Opción 1 · Push a `main` de bots: solo `guardian`, suite completa por la noche
Cambio: en `on.push`, un job previo clasifica el commit (`git diff --name-only HEAD^ HEAD`); si solo toca rutas de bots
(`orchestracion/**`, `configuracion/catalogo_*.yaml`, `datos/**`, `publicado/**`, `docs/registro/**`,
`docs/REGISTRO_DE_CAMBIOS.md`, `README.md`, `legacy/docs/**`) la matriz `suite` se salta y `pruebas` pasa si `guardian` pasa.
Más un `schedule` diario (1 run completo, ~23 min = ~160 min/semana).
- Ahorro: 9.561 + 4.652 − (556 runs × ~1,5 min) ≈ **13.400 min/semana** (−53 %).
- Riesgos: hay tests «sobre estado vivo» (catálogo, `estado_operativo.json`, registro) que un commit de bot podría
  romper sin que se vea hasta la noche. Mitigación: lista de rutas revisada con `grep` de lo que leen los tests y
  revertir una ruta de la lista si algún test falla en el run nocturno; el nocturno avisa en rojo. Reglas de numeración:
  el job `guardian` ya comprueba `registro`.
- Esfuerzo: medio (≈40 líneas de YAML + un test de la lista de rutas + test_workflow_safety).

### Opción 2 · Cancelar pushes superados en `main`
Cambio: `concurrency` en push con grupo por referencia (`ddd-pruebas-main`) y `cancel-in-progress: true` (en PR queda
como está). Solo el tip de ráfaga se prueba completo; los commits intermedios quedan «cancelados».
- Ahorro: de ~16.500 min de ráfagas, cada run cancelado gasta de media la mitad antes de caer: **≈ 7.000-8.000 min/semana**
  (estimación; no medible sin probarlo). Se solapa con la 1 (los pushes de bot son la mayoría de las ráfagas).
- Riesgos: el check de un SHA intermedio queda sin resultado; la fusión segura (#457, #460) usa el check-run del SHA de
  la PR, no el del push, así que no se ve afectada. Una ráfaga que acaba en rojo no dice qué commit lo rompió (hay que
  bisecar).
- Esfuerzo: bajo (3 líneas). Un fallo del tip se investiga con `diagnosticar-run`.

### Opción 3 · Construir la imagen una vez (caché de capas) 
Cambio: `docker/build-push-action` + `cache-from/to: type=gha` (las capas pesadas — apt y pip de los dos `requirements.lock` —
no cambian), o un job `imagen` que la construye y la pasa a los 5 grupos con `docker save`/`load` como artefacto.
Con caché, el paso pasa de ~0,9 a ~0,3 min por grupo.
- Ahorro: 4.193 → ~1.300 ≈ **2.900 min/semana** sobre la base; proporcional a los runs que queden (≈1.400 tras la 1).
- Riesgos: caché envenenada o obsoleta (mitigar con la clave = hash de `Dockerfile` + locks); el artefacto de 1-2 GB
  cuesta tiempo de transferencia y almacenamiento (por eso se prefiere la caché gha); `docker build --pull` pierde el
  pull de la base (fijarla por digest, que ya es lo recomendable).
- Esfuerzo: bajo-medio. Tocar `Dockerfile` activa la regla `workflows.md` (legacy + cabecera).

### Opción 4 · Fallo rápido y borradores
(a) `fail-fast: true` solo en `pull_request` (`fail-fast: ${{ github.event_name == 'pull_request' }}`): al fallar un grupo
se cancelan los demás; PR en rojo = 1.029 min → ahorro ≈ 400. (b) No ejecutar la suite en PR en borrador
(`if: github.event.pull_request.draft == false` y activar `ready_for_review`): ahorro estimado 10-15 % de los runs de PR
(≈ 600-900), pero el check `pruebas` aparecería «pendiente» en borradores, aceptable porque un borrador no se fusiona.
- Ahorro total ≈ **1.000-1.300 min/semana**.
- Riesgos: (a) se pierde la lista completa de fallos en un solo run; (b) las PR `no-automerge` creadas en borrador
  (skill implementador) pasan por «listo» antes de fusionar: la suite correría entonces.
- Esfuerzo: bajo.

### Opción 5 · Menos PR encadenadas y rebases (proceso)
Cada `synchronize` (push, merge de `main` en la rama, rebase) cuesta ~23 min. 2,1 runs por PR. Pautas: una PR por causa
(ya), no actualizar la rama con `main` salvo conflicto real, agrupar los commits antes de empujar, no usar la actualización
automática de rama. Ahorro ≈ **600-1.000 min/semana** (10-15 % de los runs de PR). Sin riesgo para la CI; esfuerzo: pauta en
`CLAUDE.md`/skill implementador.

### Opción 6 · Selección de tests por rutas modificadas en PR (la de mayor riesgo)
Mapa fichero modificado → tests afectados (a partir de importaciones y de `tests/tiempos_ci.json`, o con `coverage` por
test) para correr solo esos en PR, y la suite completa en el push a `main`.
- Ahorro: PR ≈ 6.900 min; si en el 60 % de las PR basta un subconjunto del 30 %, ≈ **2.900 min/semana**, solapado con 3 y 4.
- Riesgos: es la única que puede debilitar la CI por PR (tests que leen ficheros sin importarlos: catálogos, docs,
  `legacy/`). Exigencia para activarla: demostrar sin pérdida de cobertura reproduciendo el último mes de PR (por cada PR
  fusionada, que el subconjunto contenga todos los tests que fallarían con su diff) y mantener la suite completa en `main`
  y en el nocturno. Hasta que exista esa prueba **no se propone activarla**.
- Esfuerzo: alto.

### Descartadas
- Quitar la matriz de 5 grupos o reducirla a 3: no baja minutos (el trabajo es el mismo) y sube la pared.
- Self-hosted runners: fuera de alcance (coste y mantenimiento).
- Quitar tests lentos de PR: debilita la CI.

## 4. Orden recomendado y efecto acumulado (base 25.083 min/semana)

| Paso | Opción | Esfuerzo | Ahorro propio | Gasto tras aplicarla |
|---|---|---|---:|---:|
| 1 | 2 · cancelar pushes superados | bajo | ~7.500 | ~17.600 |
| 2 | 1 · pushes de bots solo `guardian` + nocturno | medio | ~7.000 adicionales (los pushes de bot que quedan tras la 2) | ~10.600 |
| 3 | 3 · caché de imagen | bajo-medio | ~1.500 adicionales (menos runs que construir) | ~9.100 |
| 4 | 4 · fail-fast PR y borradores | bajo | ~1.000 | ~8.100 |
| 5 | 5 · pautas de proceso | ninguno | ~600 | ~7.500 |
| — | 6 · selección por rutas | alto | no se recomienda por ahora | — |

Con 1-5 la semana punta bajaría de ~25.000 a ~7.500-9.000 min (por debajo del tope de 15.000 con margen). Los pasos 1 y 2
son lo que más pesa; el 1 es el más barato de hacer. Los solapes no son medibles hasta aplicar el paso: tras cada uno,
repetir `analisis_runs.py` una semana y reajustar.

## 5. Coordinación y siguientes pasos
- Todas las opciones tocan `pruebas-plataforma.yml` (y la 3, el `Dockerfile`): compartido con T-149 (#603). Implementar
  después de que T-149 cierre, en PR aparte por opción (VERSIÓN + copia en `legacy/workflows/`).
- Tests a ajustar al implementar: `test_workflow_safety` (sin botón manual; el `schedule` no es botón), `test_design_a_catalogo`.
- Pendiente de decisión del propietario (vía Planificador): opción 1 (se admite que un commit de bot solo pase `guardian`
  hasta el nocturno) y opción 2 (se admite que los commits intermedios de una ráfaga en `main` queden sin suite).
- Limitaciones de los datos: la API corta a 1.000 resultados por consulta (se pidió por medios días); los minutos son de
  jobs redondeados, no facturación exacta; el reparto por origen se infiere del autor del commit.
