# T-393 · Diseño: cómo entra el histórico por época en la resolución de territorios

VERSIÓN: 1.0.0 · FECHA: 2026-11-17 · ESTADO: propuesta para el Planificador y el propietario (D-150)
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS (revisor, FAIL de #873@cbf4bd6a, 4 bloqueantes): `election_id` y `meta.territory_id` corregidos (§0.1, §2); citas de lo que aún no está en `main` con PR y SHA (§1); cifras declaradas provisionales y derivadas (§3); la expansión de P00 a 52 ids pasa a decisión del propietario (§7); evidencia de `validate` sin run (§5); riesgos añadidos (§8); base `origin/main` f559cea8.
MOTIVO: D-150 (alta de los territorios-elección `<t>_hAAAA_MM`); sustituye la opción A (implementar ya) por diseño al detalle, por orden del Planificador (D-149: prioridad a T-375/T-376).
Solo documento: sin cambios en `ddd_core/`, `herramientas/`, catálogos ni workflows. Base: `origin/main` f559cea8 (los hallazgos H1-H4 se midieron sobre e2702b25; `catalogo_preparacion.py` no ha cambiado desde entonces).

## 0. Resumen y recomendación

1. **Identidad:** `nac22_h2019_11` es un **id propio** (identidad lógica: fila del catálogo, `run_name`, artefactos y checkpoints), con **carpeta física la de la provincia** (`territorios/nac22/`), como ya hace T-365. **No cambia** `meta.territory_id` (sigue `nac22`) **ni** `election_id` (sigue `{t}_{fecha}` = `nac22_2019-11-10`; `contrato_historico_epoca.py` l. 302 y 500): el id `_h` es el `run_name` y la clave del catálogo, no un campo nuevo del manifiesto. No hay filas nuevas en el catálogo maestro.
2. **Catálogo de preparación:** 260 filas `<t>_hAAAA_MM` (52 × 5), **generadas** desde los 5 contratos por una herramienta idempotente y fijadas por test; solo las provincias generables entran con `territory_declared: true`; el resto, `false` con su causa.
3. **YAML materializado al vuelo** (no versionado): `contract_path` declara la ruta futura; `validate` comprueba el contrato JSON (sha256) y, si el YAML existe, lo valida entero.
4. **Producto disponible:** nace en `false`; lo ponen a `true` P20 (M06) y P30 (M08 + `PUERTA` PASS) al registrarse, igual que en las ediciones vigentes.
5. **P00:** `elección = AAAA-MM` expandiría el grupo a `<t>_hAAAA_MM` (una elección por campaña, 52 ≤ 256), pero choca con D-148 y D-137: **decisión del propietario** (§7); la traducción `2019-11 → rojo` del §2 de T-378 pasa a «histórico».
6. Implementación detrás de T-377, con turno exclusivo (§6). Un prototipo local de `territorio_ids` (16 tests en verde) confirma que la parte de ids es pequeña; el trabajo grande está en `catalogo_preparacion.py`.

## 1. Evidencia: por qué hoy no entra (4 hallazgos del `validate`, `catalogo_preparacion.py` sobre e2702b25)

| # | Hallazgo | Dónde |
|---|---|---|
| H1 | `validate` exige una fila del `territory_id` en el catálogo **maestro** (`catalogo_territorios_espana_2025.yaml`) con el mismo nombre: «ausente del catálogo territorial maestro». No hay ids `_h`. | `validate_repository`, bucle de `data["territories"]` |
| H2 | `territorial_contract_complete: true` exige `contract_path` existente («contrato completo sin fichero materializado»); el YAML `_hAAAA_MM` está en `.gitignore` (T-365) y la CI no lo tiene. | `validate_repository`; `.gitignore` l. 19 |
| H3 | `validate` compara `meta.year` con la **clave de edición** (el contrato histórico trae `2019`, no `2019-11`). Además `territorio_ids.resolver_id/mismo_territorio` no conocen `_h` (`IdTerritorioDesconocido`). | `validate_repository`; `ddd_core/territorio_ids.py` |
| H4 | `rows_for(electoral_application)` exige `territorial_product_available` y `electoral_source_prepared` true; para el histórico no hay run ni producto. Marcarlos true sin evidencia sería falso. | `rows_for` |

Otros hechos que condicionan: `ddd_core/territory_contract.py` 1.5.0 ya compara K con el contrato de su elección (`meta.historico_epoca`) y exige `run_name = <t>_h<AAAA_MM>`; `meta.territory_id` sigue siendo `nacNN`. En `main` **no** están `p30_resolver.py` ni los cambios de P10: `p30_resolver.py` acepta `<t>_hAAAA_MM` en **#866@16c15eb0** (T-376, sin fusionar) y P10 pasa el id tal cual en **#874** (T-375, rama `t375-p10-fuentes`, cabeza 8785a6c, sin fusionar; §9). Si cambian antes de fusionarse, la implementación lo recoge al rebasar. `herramientas/clave_eleccion.py` dice que «cada elección histórica necesita su propio territory_id (catálogo, checkpoints y artefactos van por territory_id)».

## 2. (1) Id propio frente a «variante de nacNN con edición AAAA-MM»

| | A. Id propio `nac22_h2019_11` (recomendada) | B. Fila `nac22`, edición `'2019-11'` |
|---|---|---|
| Catálogo de preparación | fila nueva por elección | edición nueva en la fila existente (`lookup(nac22,'2019-11')` ya funciona) |
| Catálogo maestro | sin cambios (se resuelve a la fila de la provincia) | sin cambios |
| Artefactos y checkpoints | `ddd-source-package-nac22_h2019_11-…`: nunca chocan con los de 2025 | mismo `territory_id` `nac22` con otra edición: obliga a revisar todo consumidor que filtre solo por `territory_id` (T-199: `resultados_ligeros`, `generar_datos_abiertos`, `generar_hemiciclo`, `legislatura_vigente`) |
| Coherencia con lo hecho | `run_name` de T-365 y `clave_eleccion.py` lo usan en `main`; `p30_resolver` lo acepta en #866@16c15eb0 (sin fusionar) | habría que deshacer el id en P30 |
| Riesgo | cada consumidor debe aceptar el id (lista de §6) | el histórico se cuela en lo «vigente» de `nac22` |

**Decisión propuesta: A**, con una regla de borde: el id `_h` se descompone con `base_y_eleccion(x) → ("nac22", "2019-11")`; carpeta, K y nombre salen de la provincia; `variantes()` incluye el id propio; `mismo_territorio(nac22_h2019_11, nac22)` es **False** (no son el mismo territorio-elección; `territory_contract` sigue comparando con `meta.territory_id = nac22`). Ven el id `_h`: catálogo, resolutores (`p30_resolver`, `resolver_eleccion_vigente`), artefactos y checkpoints. No lo ven el manifiesto (`election_id`, `kind: historico_epoca`) ni los receipts de M07/M08, que siguen con `nacNN` + fecha.

Reglas de forma (fallan cerrado con `IdTerritorioDesconocido`): `^nac\d\d_h\d{4}_\d{2}$` en minúsculas; solo Congreso (`aut01_h…` no existe: el histórico es de las generales); exige `configuracion/historico_epoca/contrato_AAAA_MM.json` y que la provincia figure en él. Prototipo local (no entregado): `territorio_ids` 1.2.0, 3 tests nuevos + `test_t220_renombrado` y `test_t338` en verde.

## 3. (2) Filas del catálogo y su clave de edición

- **Catálogo maestro:** sin filas nuevas. `catalogo_preparacion.validate` resuelve el id `_h` a la fila de su provincia (H1) y el nombre de la fila de preparación es el visible: `Congreso Huesca (2019-11)`.
- **Catálogo de preparación:** `territory_id: nac22_h2019_11`, `name: Congreso Huesca (2019-11)`, **clave de edición = `'2019-11'`** (no `'2019'`: hay dos elecciones en 2019). `validate` compara `meta.year` con `edicion[:4]` solo para filas con `meta.historico_epoca` (H3). `default_edition` no cambia.
- **Estados:** `territory_declared: true` y `READY_INITIAL` solo si `estado == LISTA` y `secciones_sin_seccionado == []` (D-126; `materializar` falla cerrado si no). Generables con los contratos de `main` (#865, T-389): 2011-11 **39**, 2015-12 **27**, 2016-06 **33**, 2019-04 **35**, 2019-11 **46** (corrigen las del README de T-365). **Son provisionales**: T-364b/T-396 (D-153, según el Coordinador; aún no consta en `docs/PLAN.md` de `main`) asignará las secciones sin geometría a su sucesora y cambiará `secciones_sin_seccionado` y los estados. Por eso ni la herramienta de filas ni su test fijan cifras: derivan el estado de cada fila del contrato vigente y el test compara fila a fila. Resto: `territory_declared: false` y `PENDING_INCORPORATION`; la causa (`BLOQUEADA_RELLENO`, `BLOQUEADA_SIN_DATO`, `secciones_sin_seccionado`) la da el contrato, no se copia.
- **Generación, no mano:** `herramientas/catalogo_historico_epoca.py` (nuevo, idempotente) escribe las filas desde los contratos; un test compara filas y contratos (K, estado, sha256 del contrato). Los robots que reescriben el catálogo (`contratos.md`) obligan a rebasar: la herramienta reinserta solo las `_h`.

## 4. (3) `contract_path` con YAML materializado al vuelo

- `contract_path: territorios/nac22/config/nac22_h2019_11.yaml` (la ruta que escribe `materializar`) y un campo nuevo `historico_epoca: {eleccion, contrato, contrato_sha256}`.
- `validate`: si hay `historico_epoca`, comprueba el contrato JSON (existe, sha256, provincia, K) **en lugar de** exigir el fichero (H2); si el YAML existe, lo valida con las reglas actuales (+ H3). `territorial_contract_complete: true` sigue exigiendo `contract_level` del YAML cuando existe.
- Quién materializa: el primer paso de P10/P20 (`materializar` + `validate_production_contract`) con las fuentes bajadas y verificadas por sha256 contra el contrato. Falla cerrado ante cualquier diferencia (hoy ya ocurre). El YAML vive solo en el runner.
- Contrato base cambiante: si un robot reescribe `nacNN_2025.yaml`, `materializar` falla por huella y hay que regenerar el contrato (T-365 §5.3): la herramienta de filas lo detecta antes (test).

## 5. (4) Qué cuenta como producto disponible del histórico

| Campo del catálogo | Verdadero cuando | Quién lo escribe |
|---|---|---|
| `territorial_sources_prepared` | P10 prepara el paquete y deja su receipt (`validate` exige declaración y, si hay `receipt_path`, el receipt) | P10 al registrar |
| `territorial_contract_complete` | contrato de la elección válido y provincia generable | la herramienta de filas (derivable del contrato) |
| `territorial_product_available` | existe M06 del `<t>_hAAAA_MM` con su receipt (run P20) | P20 al registrar |
| `electoral_source_prepared` | paquete electoral de esa elección con `evidence.electoral_source` (`ddd.catalog-evidence/1.0`, con `run_id` y artefacto: `validate` lo exige) | preparación electoral al registrar |
| `electoral_product_available` | M08 + `PUERTA_<t>_<AAAA_MM>.json` PASS (M07 sin asignar ≤ 0,1 %, contraste BOE, K = escaños) | P30 al registrar |

Consecuencia (H4): una fila nace `READY_INITIAL` con producto `false`; «Verificar elegibilidad del territorio» de P30 pasa solo **después** de P20, como en lo vigente, y falla cerrado con un id inexistente. Nada se marca `true` sin run. **Sin run solo es verdadero `territorial_contract_complete`**, y cada fila lleva como `territorial_source_declaration` el contrato JSON de su elección: `validate` lo acepta en filas con `historico_epoca` (comprueba sha256, provincia y que `territorio` es la base del id) en lugar del `fuentes_oficiales.yaml` de las ediciones vigentes. El estado de salida es `READY_INITIAL` con producto y fuentes a `false`.

## 6. (6) Lista exacta de ficheros y tests (implementación, tras T-377, turno exclusivo)

| Fichero | Cambio |
|---|---|
| `ddd_core/territorio_ids.py` (1.2.0, legacy) | `_epoca`, `base_y_eleccion`; `territorio`, `resolver_id`, `etiqueta` aceptan `_h` (§2) |
| `herramientas/catalogo_preparacion.py` | `validate` y `lookup/resolve` con id `_h` (H1-H3, §4) |
| `herramientas/catalogo_historico_epoca.py` (nuevo) | genera las 260 filas |
| `configuracion/catalogo_preparacion.yaml` | +260 filas (robots: rebasar) |
| `herramientas/contrato_historico_epoca.py` | `materializar` también para el id `_h` (sin cambio de formato del YAML) |
| P10/P20/P30 (`p30_resolver.py`, resolutores de T-375/T-377) | aceptar el id; sin cambios si ya usan `territorio_ids` |
| `herramientas/clave_eleccion.py` | solo si P00 expande por elección (§7) |

Tests: ids (válidos, inexistentes, forma, solo Congreso, `mismo_territorio`, `variantes`); catálogo (`validate` verde con las 260 filas, rojo con contrato alterado, año ≠ elección, id sin contrato); filas = contratos (K, estado, sha256); `resolve --mode electoral_application` falla cerrado sin producto y con id inexistente; materializar con fuentes sintéticas + `validate_production_contract` (patrón de `test_t365_historico_epoca`); `test_t220_renombrado` y `test_t338` sin cambios.

## 7. (5)(7) P00 con `elección = AAAA-MM` y contraste con T-378 §2/§8

- **Expansión (DECISIÓN DEL PROPIETARIO, no se da por buena):** `elección = 2019-11` + grupo `congreso` → 52 ids `nacNN_h2019_11`. Choca con D-148 (P20 y P30 admiten **un territorio por ejecución**; varios en paralelo solo con P00, cadena de un territorio, D-143) y con D-137 (P30 sin campo «elección» hasta el histórico). Alternativas: (i) P00 expande y lanza una cadena por id (compatible con D-148 si cada cadena es un territorio, pero exige que P20/P30 acepten el id `_h` y D-137 se corrija); (ii) el botón de P00 no expande: acepta solo una lista de ids `_h` explícita; (iii) el histórico queda fuera de P00 y va por P10/P20/P30 sueltos, un id cada vez. Recomendación: (i), a confirmar. `lista de códigos` admite `nac22` y lo traduce. Con `aut11`: rojo «sin elección en 2019-11» (T-378 §2, listas mixtas).
- **Semáforo:** verde = fila declarada y fuentes verificadas; ámbar = fila declarada con aviso (p. ej. 2011-11); rojo = `territory_declared: false`, con la causa del contrato (`BLOQUEADA_RELLENO`…). La campaña se niega entera solo si ninguno queda en verde o ámbar (T-378 §2).
- **§8 de T-378 (límites):** coincide: «una elección por campaña» (52 jobs ≤ 256; 15 en paralelo, 5 libres para la CI). No cambia el tope de 20 jobs ni el reloj: el piloto nac22 2019-11 tarda ~15 s en local (T-365 §4).
- **Qué hay que cambiar en T-378 (§2 y §14):** la fila «Elección» deja de poner en rojo todo `AAAA-MM` ≠ vigente/ensayo; la prueba `2019-11 → rojo «elección no soportada»` pasa a «→ histórico» (con provincias generables en verde y las demás en rojo con causa); el ensayo `2026-11` no cambia. El cierre del histórico **no escribe en `main`** hasta que exista el registro del histórico en el visor (P43, T-395, según el Coordinador; T-355/#830 está cerrada y sustituida: no es bloqueo de este diseño), y `Publicar = sí` se rechaza con aviso en histórico.
- **D-150 (4):** la validación de P00 incluye el piloto `nac22_h2019_11`, que ya pasa la puerta en local (T-365 §4); no depende de las 260 filas, sí de §2-§4 para un solo id.
- **Pendiente del propietario, no de este diseño:** secciones con población sin geometría (T-365 §5.1) y los 46 municipios con aviso de T-364: bloquean provincias, no el diseño.

## 8. Riesgos

1. Las filas generadas chocan con los robots que reescriben el catálogo: fusionar rápido, rebasando con la herramienta.
2. Un consumidor que filtre por `territory_id` sin elección verá filas nuevas: lista de T-199 en §2; la prueba de barrido va con control positivo y negativo.
3. Si se elige B (variante de `nacNN`), desaparecen H1 y los ids nuevos, pero entran los consumidores de T-199 sin separar el histórico del vigente: más riesgo para el visor (T-355).
4. 260 filas nuevas en `data['territories']`: todo consumidor que itere el catálogo (dashboard, `rows_for`, `resolver_*`, generadores) verá filas con `edition` `AAAA-MM`; barrido de consumidores con control positivo y negativo antes de fusionar.
5. La CI no puede ejercer `validate` sobre el YAML ignorado: solo ejerce el contrato JSON y la fila. La prueba del YAML va con fuentes sintéticas (`materializar` + `validate_production_contract`), no con el real.
6. Los robots reescriben `nacNN_2025.yaml`: cambia su sha256 y el contrato histórico (`contrato_base.sha256`) deja de casar; `materializar` falla cerrado y hay que regenerar los 5 contratos. La herramienta de filas lo detecta antes y el test la ejecuta sobre el árbol real.
7. Huellas M04/M05 sin cambios: ninguna pieza de este diseño está en el cierre de imports de M05 (T-365 §2). Sin 00 nueva.

## 9. Respuesta de T-375 (P10, #874)

P10 no impone ruta de contrato ni llama nada nuevo: pasa el id tal cual (el regex del botón admite `nac22_h2019_11`) a `catalogo_preparacion.py lookup --territory <id> --edition <E>` y a `resolver_eleccion_vigente.py --for-preparation`, que ya existen dentro de los reutilizables. La edición no la decide P10 para los ids de época: la fija el llamador. Por tanto la clave `'2019-11'` (§3) es decisión de catálogo y resolutores, y P10 no la bloquea; en `plan` solo usa `lookup --edition 2025` para el nombre del grupo de exclusión y, si falla, usa el código con `::warning::`.
T-375 no toca `catalogo_preparacion.py` ni `territorio_ids.py`; sí toca `clave_eleccion.py` y los dos `generar_provincias_congreso*` en #874: la implementación de §6 debe rebasar sobre ella (la fila de `clave_eleccion.py` pasa a «tras #874»).
