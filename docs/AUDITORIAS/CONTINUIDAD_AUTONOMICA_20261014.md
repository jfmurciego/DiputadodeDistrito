# Continuidad autonómica — 2026-10-14

## Identidad y preservación

- Rama: `codex/distritos-autonomicos`.
- HEAD: `42163cd8cebd120db9ab9fd1329c32ccdd87cf36`.
- Worktree: conserva el conjunto de cambios previos A2 y AUTO-01. No se limpiaron ni se reemplazaron.
- No se creó commit ni se alteraron datos territoriales de producción.
- `git diff --check`: PASS. `git write-tree` no pudo crear el lock en el repositorio común fuera de las rutas escribibles; no se usó para mutar el índice.

## Avances

### AUTO-01 — identidad de unidades del preflight

La corrección local v1.1.1 bloquea IDs nulos, vacíos o duplicados normalizados antes de construir el mapa de unidades. La reproducción `auto01_before_after.py` volvió a mostrar `READY` con v1.1.0 al colapsar dos filas y `BLOCKED` con v1.1.1. La suite topológica ejecutada en esta sesión pasó: 33 tests y 4 subtests; también pasó la batería transversal final descrita abajo. Se reutiliza el dictamen independiente previo `GO_ACOTADO`; el revisor no ejecutó pruebas, por lo que el PASS de tests corresponde al ejecutor.

### OPT-01 — completitud de candidatos M02

El defecto confirmado era el truncamiento de `STRtree` bbox hits a los 50 centroides más cercanos en `iter_edges()`. El fixture sintético de 114 polígonos produce la arista real `LBIG—RBIG` con enumeración exhaustiva, pero la v7.3.2 con límite 50 la omite. En el worktree se implementó M02 v7.3.3: ordena y procesa todos los hits, conserva el predicado geométrico exacto y mantiene `max_candidates` solo por compatibilidad de configuración. Se archivó el predecesor antes del cambio.

Evidencia nueva en `docs/AUDITORIAS/A-OPT-01_M02_20261014/`:

- `benchmark.py`: reproducción local de v7.3.2, v7.3.3 con límite 50, v7.3.3 sin límite y prototipo exacto STRtree.
- `benchmark.json`: 5 repeticiones por variante, hashes del módulo, Python 3.13.12, GeoPandas 1.1.2 y Shapely 2.1.2.
- `tests/test_m02_candidate_completeness.py`: comparación contra el predecesor archivado y comprobación de determinismo.

El resultado final tuvo cero aristas omitidas en v7.3.3 y coincidió con el modo exhaustivo; el prototipo STRtree produjo el mismo conjunto. Revisión independiente del cambio: `GO` tras corregir la versión mostrada por el CLI. No es una validación territorial: falta el M01 auténtico de Aragón con SHA-256 esperado `5f939e8daae23ebc4e430966311cfecb5aedceaaa5882b62fbc480f2bb52215f`.

El cambio funcional invalida evidencia pre-M04 que fija el blob anterior de M02. La regresión de Islas Baleares ahora exige explícitamente planificar reacreditación y no reutilizar el preflight ligado al blob `254ab944f8e76dd51d76917d69deb7fe7e035ba6`. No se relaja el gate. Para validar los territorios que reutilicen esa evidencia se necesitarán sus entradas autenticadas y una revalidación autorizada.

## Regresiones ejecutadas

Entorno de pruebas: `/usr/local/Caskroom/miniforge/base/bin/pytest`; `PATH` antepuesto con Miniforge y `TMPDIR=/private/tmp` para evitar Python 2.7 y la divergencia `/var` frente a `/private/var` del entorno del sistema.

- M02, preflight topológico, M03, persistencia/evidencia pre-M04, M04, reparador M05 y contratos de fuente: **128 passed, 45 subtests passed**.
- Componentes físicos de partición: **7 passed, 4 subtests passed**.
- Benchmark sintético de completitud: predecesor omite `LBIG—RBIG`; v7.3.3 con `max_candidates=50` no omite; coincide con exhaustivo.
- `git diff --check`: PASS.

Barrido global `tests/` con `PYTHONPATH=tests:.`: **1309 passed, 9 skipped, 1029 subtests passed y 8 failed** antes de adaptar la expectativa de reutilización insular afectada por el nuevo blob M02. Los ocho fallos quedaron clasificados: dos tests de GerryChain no pueden importar `gerrychain`; dos tests del lanzador compartido reproducen `bad substitution` en `procedimiento.sh` línea 46; un test de documentación refleja el desfase preexistente entre M05 v7.8.0 del código local A2 y M05 v7.7.2 del documento; dos tests Rioja fallan por la guarda de identidad (`REPAIR_CODE_DIFFERS_FROM_RUN`); y un test de Baleares/Canarias aún esperaba reutilización del preflight anterior. Esta última expectativa se actualizó para exigir reacreditación fail-closed y su grupo dirigido pasó (**36 passed, 4 subtests**). No se repitió la suite completa después de ese cambio de test.

Una primera batería amplia (antes de fijar `PATH`/`TMPDIR`) reportó fallos ambientales por invocar Python 2.7 y por normalización de `/var`; ambos desaparecieron al usar el entorno compatible. Dos tests de GerryChain quedaron sin validar porque Miniforge no tiene instalado `gerrychain`; no se instalaron dependencias. Una prueba de reutilización de Baleares inicialmente falló porque la evidencia pre-M04 está ligada al blob previo de M02; se actualizó a la expectativa fail-closed y pasó.

## Bloqueos de datos acreditados

- Cataluña, run `37453376100`: preflight `ERROR_TECHNICAL`, `PRE_GENERATION_PERSISTENCE`, `CAP_PRE_M04_EVIDENCE`. El manifiesto no contiene la excepción concreta. No está el paquete de fuente con digest `e904289f179ee4fe552f0bb7dae11b8822d2deecf918eb036bf52a0614e97ee0` ni el log runtime. No se atribuye una causa al código actual.
- Murcia, run `37344628042`: `BLOCKED` en `TERRITORY_GRAPH`, `provinces=1, municipalities=0`. Faltan el paquete de fuente y geometrías M01/M02 con digest de paquete `71883ee809b295739904929a967808468cc650dd33785ae7d87eb6f410880534`. El diagnóstico de Murcia de run `34688393979` pertenece a otra entrada/ejecución y no se usa para reparar ésta.
- Tremp/Llívia: no está la geometría auténtica del run `37215025861`; no se reinterpreta el contacto puntual ni se inventa una arista.
- Baleares/Canarias: hay evidencia de preflight y configuración de componentes, y pasan pruebas locales; no se encontraron los paquetes geométricos para ejecutar nuevas validaciones territoriales. Baleares requiere además reacreditación por el cambio M02.
- País Vasco: el repo conserva config, recibo y manifiesto del run `37458584767`, pero no el checkpoint M05/M03 ni entradas completas para probar una nueva estrategia global. No se repitió la búsqueda histórica agotada.
- A2: se preserva sin modificación; sus trabajos experimentales existentes no se convierten en PASS. A3 sigue bloqueada.

## Matriz y siguiente cola

Consultar `CONTINUIDAD_AUTONOMICA_20261014.json`. Prioridad ejecutable restante: conseguir acceso autorizado a los insumos faltantes antes de validar CAT-02, MUR-01, Tremp/Llívia, M02 real, islas o País Vasco. Mientras falten, avanzar solo en regresiones unitarias independientes y tareas autonómicas que no dependan de la evidencia ausente. No lanzar fases, territorios, fuentes ni workflows.

## Actualización de cierre de sesión — 2026-10-14

Se inventariaron todos los JSON del repositorio que contienen `m02_git_blob_sha1`: son 13 fichas `generation_preflight_2025.json`. Ninguna corresponde al blob Git de la implementación M02 v7.3.3 de este worktree (`git hash-object modulos/02_construir_adyacencias.py` = `a055259813c023394d9dd5c4877e6eb4d1ab99be`). Once fichas usan `254ab944f8e76dd51d76917d69deb7fe7e035ba6`; Comunidad Valenciana y Galicia usan `2f8256d6a82920c3145fad330c4862af60bff30a`. La evidencia pre-M04 enlazada a esas fichas debe tratarse como no acreditada para la nueva implementación, hasta reacreditarla con entradas auténticas. No se ejecutó ninguna fase territorial.

La revisión independiente M02 concluyó `GO` sobre el cambio local y las regresiones sintéticas, incluidas las actualizaciones de expectativa que exigen reacreditación insular. El alcance no cubre una ejecución territorial real. No se encontró el M01 auténtico de Aragón requerido por SHA-256 ni los paquetes de Cataluña, Murcia o islas descritos arriba.

La última batería amplia de pruebas sigue siendo la documentada: 128 pruebas y 45 subtests pertinentes PASS; suite total con ocho fallos antes de la adaptación insular, con solo la expectativa insular cambiada y verificada después por una prueba enfocada. No se afirma que la suite completa haya pasado. El worktree continúa en `codex/distritos-autonomicos`, HEAD `42163cd8cebd120db9ab9fd1329c32ccdd87cf36`, con los 38 paths modificados/no seguidos preexistentes conservados. No se creó commit ni se ejecutaron operaciones remotas o generación territorial.

### Seguimiento de disponibilidad de Aragón — 2026-10-15

Una búsqueda adicional en las rutas locales de desarrollo y temporales confirmó que no existe `aragon_2025_m01_secciones_poblacion.geojson.zip`. Sí existe el manifiesto de productos de `gh-34599224954-1`: su `PRODUCTOS.json` (SHA-256 `2fa6157330545a54bac8396904097489a4f574ae2f07bf2c47d7c2abffb828e2`) registra tamaño 4.123.522 bytes y SHA-256 `5f939e8daae23ebc4e430966311cfecb5aedceaaa5882b62fbc480f2bb52215f`. El manifiesto de ejecución (SHA-256 de archivo no recalculado aquí) también vincula el run al commit `f9ca44ff005043f630fce39334d34726d8bf55c5` y registra el hash de su módulo M02 histórico. La identidad esperada del insumo está por tanto confirmada en el registro del run, pero no se puede validar M02 v7.3.3 con sus geometrías: el producto no está disponible y no se reconstruyó M01.

### Procedimiento compatible con Bash 3 — 2026-10-15

Se acreditó y corrigió un fallo del procedimiento común: `/bin/bash` 3.2 no implementa `readarray`, usado por `procedimiento.sh` 2.9.1 para capturar directorios del contrato. En la prueba encadenada, la ejecución fallaba antes de los módulos. `procedimiento.sh` 2.9.2 ahora captura esas dos rutas con sustitución de comando y valida su separación; no cambia selección de estrategia ni ejecuta módulos territoriales reales. El predecesor se conservó byte por byte como `legacy/procedimiento/procedimiento_v2.9.1.sh` (SHA-256 `15760024420f21ba8963bb75f94ac8a6663012cfcc9b7a5d5b62947a21711cb4`). El script actual tiene SHA-256 `7858a254232b372eff691e8719b67cac11867db13949baa782b9dee68d7dea4a`. Los tests de encadenamiento, tramos, limpieza operativa, reanudación y módulo pasaron: **20 passed**; `bash -n` con Bash 3.2 y `git diff --check`: PASS.

La suite activa completa, ejecutada después de la corrección principal y antes de reforzar la guarda que valida la salida del resolver, dio **1312 passed, 9 skipped, 1029 subtests y 5 failed**. Los cinco fallos quedaron identificados: dos por la dependencia GerryChain no instalada; uno por el desfase preexistente entre el M05 local experimental y su documento contractual; y dos porque la guarda Rioja detecta que el reparador preservado no coincide con el hash del run histórico. Tras la guarda final se repitieron todas las pruebas afectadas del procedimiento (20 PASS); no se repitió la suite completa. La revisión independiente del lanzador concluyó `GO_ACOTADO`, con alcance limitado al cambio Bash.

Se instaló GerryChain 1.0.0 y rustworkx 0.18.1 en `/private/tmp/ddd-gerrychain-test-site`, sin modificar dependencias del repo ni el entorno base. Con ese `PYTHONPATH`, las dos pruebas antes bloqueadas pasan. La suite completa se repitió y el log reproducible está en `CONTINUIDAD_AUTONOMICA_20261015_full_suite_gerrychain.log`: **1319 passed, 4 skipped, 1029 subtests y 3 failed**. Los tres fallos son: (1) el contrato documental M05 declara v7.7.2 mientras el worktree conserva una versión experimental v7.8.0; (2–3) el replay de La Rioja requiere el SHA-256 de reparador `1c87809aefaa015307288f1d1491815ba3bbeafd70ddef8800fad9916cc874b8`, que coincide exactamente con el archivo histórico `legacy/core/m05_population_repair_v1.6.0_2026-10-09.py`, mientras el reparador de trabajo es `064a32bce09aeafa4ecfd4e0d88e358f9e0cdf820e2dd805caee15180e58a602`. Se conservó la guarda; no se forzó una reproducción con código distinto ni se alteró el contrato M05 para hacer pasar el test. El entorno temporal usa Python 3.13 y no representa el lock productivo de GerryChain para Python 3.11; valida esas pruebas sintéticas, no el runtime de producción.

En comprobación estrictamente de solo lectura, el checkout activo `DDD-orquestador-auto` contiene copias de los manifiestos Cataluña/Murcia con hashes idénticos a los del worktree autonómico (`67de8f84…` y `8c23f0a1…`). Sus carpetas de recibo solo contienen `receipt.json` y `fuentes_oficiales.yaml`; no hay paquete fuente, log de runtime ni geometrías. No se ejecutó ni modificó ese checkout. El hallazgo no desbloquea CAT-02 ni MUR-01.

La reproducción Python 3.11 adecuada se hizo usando el entorno local `ddd_aragon` (Python 3.11.14, GDAL/Pyogrio operativos) sin instalar paquetes en él; GerryChain 1.0.0 y rustworkx 0.18.1 se aportaron mediante el target temporal ya usado. Versiones GIS locales: GeoPandas 1.1.2, Pyogrio 0.12.1, PyProj 3.7.2, NumPy 2.4.2 y Shapely 2.1.2. Dio el mismo resultado que Python 3.13: **1319 passed, 4 skipped, 1029 subtests y los mismos 3 failed**. Log: `CONTINUIDAD_AUTONOMICA_20261015_full_suite_py311_gdal.log`. Un venv aparte instalado con el lock exacto intentó compilar Pyogrio 0.13.0 desde fuente y no pudo cargar `libgdal.38.dylib`; su suite reportó 101 fallos de setup GIS y se clasifica como entorno inválido, no como regresión. Ese venv fallido, creado en esta sesión, se retiró; su log `CONTINUIDAD_AUTONOMICA_20261015_full_suite_py311.log` se conserva.

### País Vasco PV-CUT-01 — 2026-10-15

Se localizó el expediente persistente `/Users/macbookpro/Desarrollo/DDD_PV_A2_G1_EVIDENCIAS`, que no estaba en las rutas examinadas en la auditoría anterior. Sus **146** archivos coinciden con el manifiesto; M03/M04/M05 oficiales pasan la prueba ZIP y coinciden con los hashes del expediente. Se reutilizaron, sin regenerar etapas, los M04/M03 auténticos del run `37458584767`.

Se preregistró una separación iterativa de cortes de conectividad sobre la relajación MILP: tope 120 s, 100.000 nodos acumulados, 12 resoluciones y 6 GiB virtuales. La primera implementación se invalidó al detectar que no fijaba cada unidad congelada dentro de distritos mixtos; se archivó como `result_pre_fix_invalid.json`. La segunda fija cada unidad y aborta ante cualquier excepción. Hubo 11 incumbentes factibles para las restricciones modeladas salvo conectividad; todos fueron rechazados por cortes porque aún tenían de dos a cuatro distritos desconectados. Se añadieron 72 cortes; los objetivos de reasignación fueron 2→5→6 unidades. La resolución final agotó el tiempo sin incumbent; 10 nodos, 120,122 s wall. No hay asignación candidata ni ejecución de M06/validadores. El resultado es `NEGATIVE_BOUNDED` para este mecanismo y límite, no infactibilidad global.

Se detectó un defecto instrumental: el campo RSS multiplicó por 1024 un `ru_maxrss` ya expresado en bytes en macOS; se excluye esa métrica de las conclusiones. El límite de memoria virtual sí fue aplicado. Las asignaciones intermedias tampoco se persistieron, por lo que no se presentan como candidatas auditadas. Código, preregistro e informes: `docs/AUDITORIAS/PAIS_VASCO_CUTS_20261015/`; copia persistente en `DDD_PV_A2_G1_EVIDENCIAS/experiment_08_connectivity_cuts/`, adenda SHA-256 `e94b5316e1aff1ad2318839ae8b766650dd7563bfc10eefe9c5dad479d2267d4`. Se solicitó revisión independiente del ensayo corregido; pendiente al corte de este informe.

La siguiente línea de mayor valor es diseñar un método que dirija compensaciones hacia conectividad y guarde cada incumbent y su auditoría; no repetir este modelo ni ampliar presupuesto automáticamente. CAT/MUR/Aragón/islas siguen bloqueados por sus entradas auténticas ausentes; no se lanzaron generaciones.

### País Vasco — actualización PV-CUT-02 — 2026-10-15

La revisión independiente de PV-CUT-01 determinó que el corte no enraizado podía eliminar una asignación conectada válida. Se reclasifica esa investigación como `NO_GO_ALGORITHM_INVALID_CUT`; sus incumbents y agotamiento no sirven como resultado negativo global. Se conserva el defecto inicial de pinning de unidades congeladas como evidencia histórica y no se reutilizan esos resultados.

Se preparó una corrección experimental con raíz binaria por distrito. Tres pruebas algebraicas pasan; el script fija todas las unidades congeladas y audita cada incumbent contra el grafo M03. Una invocación previa abortó antes del solver por una clave raíz no admisible; se corrigió antes de ejecutar la única búsqueda presupuestada. La corrida final llegó a 120,244 s, 10 resoluciones, 49 nodos y 42 cortes. Los 10 incumbents encontrados continuaban desconectados; el último solver llegó al límite. No hubo candidata, M06 ni validación oficial. Estado: `NEGATIVE_BOUNDED_REVIEW_PENDING`, no infactibilidad. Véase `docs/AUDITORIAS/PAIS_VASCO_CUTS_20261015/INFORME_ROOTED_02.md` y `MANIFEST_ROOTED_02.json`.

El experimento PV-EDGE-01 (priorización compacta) también agotó su supervisor de 130 s sin reporte ni asignación (`returncode=-15`); no equivale a infactibilidad y no se repite. La medida RSS histórica de CUT-01 fue inválida; PV-CUT-02 informa RSS bruto de Darwin en bytes. No hubo cambios al código productivo.
