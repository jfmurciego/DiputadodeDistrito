## 2026-11-16 — T-376 — P30 Resultados electorales sustituye a la incorporación electoral y su reutilizable

**Causa.** D-137 (paso 7): un solo botón de incorporación electoral, sin parámetros técnicos y sin dos ficheros encadenados.

**Cambio.** Nuevo `.github/workflows/p30-resultados-electorales.yml` 1.0.0 («P30 Resultados electorales»), jobs `resolver` → `incorporar` (matriz de un job por territorio). Sustituye a `incorporacion-resultados-electorales.yml` 2.0.8 y
`_reutilizable-incorporacion-electoral.yml` 1.3.0 (borrados; copias en `legacy/workflows/`). Los pasos de `preparar`, `incorporar` y `registrar` de antes van en el MISMO job por territorio (los resultados de una matriz no se
pueden pasar entre jobs): mismo comando, paso a paso; el registro (checkout de `main` en `persistidor/`, credencial, archivo en origen, persistidor) corre solo tras el éxito y con `persistir`.
- Botón: solo `territorios` (códigos, p. ej. `aut12,nac42`); sin run id (producto territorial certificado y paquete electoral vigente desde el catálogo, como en manual); edición fijada en el código (2025).
- `workflow_call` (entradas técnicas ocultas): la 00 (solo cambia `uses:`; 00 1.11.3) con las mismas entradas. `data_edition` vacío = 2025; `persist_state` vacío/ausente = registra (el botón siempre registra);
  `territory_id` se usa tal cual (el grupo `ddd-electoral-prod-<territorio>` es el mismo texto que pasa la 00 a la 03).
- `herramientas/p30_resolver.py` (nuevo): códigos → nombre del catálogo (matriz); varios territorios en una ejecución llevan `namespace` = id canónico en los nombres de artefactos M07/M08/certificación/informe
  (dos `ddd-state-<run>-M08` iguales chocarían); con uno queda vacío (como hoy). Errores `::error::P30_*` a stderr, rc 1.
- Concurrencia `ddd-electoral-prod-<territorio>` (cancel false, `queue: max`) pasa de workflow a job de la matriz; registro y permisos (`contents: write`, `actions: read`) sin cambios; `resolver` solo `contents: read`.
- Rutas: 00 (`uses:` y `paths`), `gestor-campanas.yml` 1.11.2 (`paths`), tupla `WORKFLOWS` de `generar_provincias_congreso.py` y `_350.py`; equivalencias del corte regeneradas (`generar_equivalencias_5_0_0.py`).

- D-148: no aplicada la restricción de un territorio por ejecución porque cada territorio es UN job (preparar+incorporar+registrar como pasos); la matriz es directa, sin reutilizable interno ni bucle. Consecuencia: varios territorios en una ejecución exigen
  un `namespace` de estado distinto (`ddd-state-<run>-M08-<id>`) y eso está sin probar en Actions.
- Revisión (B1): `tests/test_credencial_registro.py` toma ahora el ÚLTIMO checkout anterior al primer paso que empuja (en P30 el del código va primero y el de `main` en `persistidor/` justo antes de la credencial), con control negativo.
- El botón rechaza ids viejos, alias y `congreso350_*` (solo `autNN`/`nacNN`; D-76), con tests negativos.

**Pruebas.** `tests/test_t376_p30_equivalencia.py`: copias congeladas (`tests/fixtures/t376_workflows/`, sha256; sin skipTest) → pasos de preparar/incorporar/registrar idénticos salvo las sustituciones declaradas, permisos, concurrencia, tiempos,
entradas, llamada de la 00, controles negativos, resolutor (CLI rc/stderr). ~20 ficheros de tests que citaban los dos ficheros viejos, actualizados.

**Lo que se pierde / cambia (declarado).** El botón ya no admite run id, edición ni selector de lista. Un job único por territorio: `timeout-minutes` 300 (antes 240 + registrar sin límite propio) y el registro ya no es un job aparte
(un fallo del archivo en origen deja en rojo el mismo job). Las credenciales de R2 llegan solo a los dos pasos que las usaban (no al job).

**No probado en Actions.** Matriz con `fromJSON` + `concurrency`/`queue` a nivel de job; `GITHUB_ENV` y `env.ARTIFACT_NAMESPACE` dentro de `with:`; checkout con `path: persistidor` + `working-directory` y el push desde la subcarpeta (con los `includeIf` de checkout);
`toJSON(inputs.persist_state)` = `null` del botón → persiste (como el botón viejo); `matrix` en el nombre del job; varios territorios con `namespace` (consumidores del nombre de artefacto con sufijo); la puerta 03→04 busca `ddd-puerta-electoral_source-<run>` sin `namespace`.

**Concurrencia frente a la 03 manual (declarado).** El botón resuelve códigos al `name` del catálogo (aut12 → «Galicia»): excluye con la 00 y con la 03 encadenada (que pasan el mismo texto), pero NO con la 03 manual de `main`, cuyo selector es «12 Galicia». Se coordina con T-375 (P10) un nombre de grupo común; si no se logra queda como pérdida.
Timeout 300 min: se mantiene (240 de incorporar + el registro, que antes era un job aparte sin límite propio); un fallo del archivo en origen deja en rojo el mismo job.

**Riesgos.** No se lanza nada (prueba real del Operador: botón con un territorio ya incorporado y, por separado, una 00 «Reutilizar»). Sin efectos en motor, huellas ni checkpoints. `herramientas/campana_estado.py` l. 77 y `docs/ARQUITECTURA/CORTE_5_0_0.md`
siguen citando el reutilizable borrado (fuera del turno de T-376).
