## 2026-11-16 — T-376 — P30 Resultados electorales sustituye a la incorporación electoral y su reutilizable

**Causa.** D-137 (paso 7): un solo botón de incorporación electoral, sin parámetros técnicos y sin dos ficheros encadenados.

**Cambio.** Nuevo `.github/workflows/p30-resultados-electorales.yml` 1.0.0 («P30 Resultados electorales»), jobs `resolver` → `incorporar`. Sustituye a `incorporacion-resultados-electorales.yml` 2.0.8 y
`_reutilizable-incorporacion-electoral.yml` 1.3.0 (borrados; copias en `legacy/workflows/`). Los pasos de `preparar`, `incorporar` y `registrar` de antes van en el MISMO job: mismo comando, paso a paso; el registro
(checkout de `main` en `persistidor/`, credencial, archivo en origen, persistidor) corre solo tras el éxito y con `persistir`.
- Botón: solo `territorio` (UN código, p. ej. `aut12`); sin run id (producto territorial certificado y paquete electoral vigente desde el catálogo, como en manual); edición fijada en el código (2025).
- **D-148 (aplicado):** el botón admite UN territorio por ejecución, sin condición; varios en paralelo los da P00. Sin matriz ni `fromJSON`, y por tanto sin `namespace` de estado propio del botón (`ddd-state-<run>-M08` queda como hoy).
- `workflow_call` (entradas técnicas ocultas): la 00 (solo cambia `uses:`; 00 1.11.3) con las mismas entradas; su `artifact_namespace` se respeta tal cual. `data_edition` vacío = 2025; `persist_state` vacío/ausente = registra
  (el botón siempre registra); `territory_id` se usa tal cual (el grupo es el mismo texto que pasa la 00 a la 03).
- `herramientas/p30_resolver.py` (nuevo, `resolver`): código `autNN`/`nacNN` → id CANÓNICO (el código; también lo que llega por la llamada: nombre del catálogo, «12 Galicia» o código se resuelven al mismo id, y el grupo `ddd-electoral-prod-<id>` coincide con el de P10/T-375 y P20; desconocido → falla cerrado); rechaza varios, ids viejos, alias y `congreso350_*` (D-76). Errores `::error::P30_*` a stderr, rc 1.
- Concurrencia `ddd-electoral-prod-<territorio>` (cancel false, `queue: max`) pasa de workflow a job; registro y permisos (`contents: write`, `actions: read`) sin cambios; `resolver` solo `contents: read`.
- D-149/D-150: el resolutor acepta también `<t>_hAAAA_MM` (histórico por época; exige `configuracion/historico_epoca/contrato_AAAA_MM.json` y el territorio base válido; el id va tal cual al grupo y a la salida). LÍMITE: el catálogo (`catalogo_preparacion resolve/lookup`) no tiene filas para esos ids, así que el paso «Verificar elegibilidad del territorio» falla cerrado con ellos hasta que el catálogo/contratos de T-389 los admitan.
- Rutas: 00 (`uses:` y `paths`), `gestor-campanas.yml` 1.11.2 (`paths`), tupla `WORKFLOWS` de `generar_provincias_congreso.py` y `_350.py`; equivalencias del corte regeneradas.
- Revisión (B1): `tests/test_credencial_registro.py` toma el ÚLTIMO checkout anterior al primer paso que empuja (en P30 el del código va primero y el de `main` en `persistidor/` justo antes de la credencial), con control negativo.
  Con más de un checkout exige además que la credencial y los pasos que empujan compartan `working-directory` con el `path` del checkout elegido (control negativo sobre una copia del job de P30 con el directorio cambiado).

**Pruebas.** `tests/test_t376_p30_equivalencia.py`: copias congeladas (`tests/fixtures/t376_workflows/`, sha256; sin skipTest) → pasos de preparar/incorporar/registrar idénticos salvo las sustituciones declaradas, permisos, concurrencia, tiempos,
entradas, llamada de la 00, controles negativos, resolutor (CLI rc/stderr). ~20 ficheros de tests que citaban los dos ficheros viejos, actualizados.

**Lo que se pierde / cambia (declarado).** El botón ya no admite run id, edición, selector de lista ni varios territorios. Un job único: `timeout-minutes` 300 (240 de incorporar + el registro, antes job aparte sin límite propio);
un fallo del archivo en origen deja en rojo el mismo job. Las credenciales de R2 llegan solo a los dos pasos que las usaban. El grupo pasa a ser el id canónico (antes, el texto que llegaba): coincide con P10 (T-375, #874) y P20 (`ddd-p20-territorio-<id>`); mientras la 03 de `main` siga con el texto del selector, no excluirá con P30 (se cierra al fusionar T-375).

**No probado en Actions.** `concurrency`/`queue` a nivel de job con `needs.resolver.outputs`; `GITHUB_ENV` y `env.ARTIFACT_NAMESPACE` dentro de `with:`; checkout con `path: persistidor` + `working-directory` y el push desde la subcarpeta
(con los `includeIf` de checkout); `toJSON(inputs.persist_state)` = `null` del botón → persiste (como el botón viejo); la puerta 03→04 busca `ddd-puerta-electoral_source-<run>` sin `namespace`.

**Riesgos.** No se lanza nada (prueba real del Operador: botón con un territorio ya incorporado y, por separado, una 00 «Reutilizar»). Sin efectos en motor, huellas ni checkpoints. `herramientas/campana_estado.py` l. 77 y
`docs/ARQUITECTURA/CORTE_5_0_0.md` siguen citando el reutilizable borrado (fuera del turno de T-376).
