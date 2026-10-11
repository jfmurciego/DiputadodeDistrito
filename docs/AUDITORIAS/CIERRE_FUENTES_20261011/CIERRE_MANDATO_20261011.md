# Fuentes Oficiales — checkpoint del mandato de finalización

**Versión:** 1.0.0 — Revalidación de acreditaciones F10

**Fecha:** 2026-10-11

**Estado:** candidato para revisión; F10 no cerrado

**Alcance:** reanudación del Plan Maestro `ddd-maestro-20261008`; no modifica sus estados

**Predecesor:** nuevo checkpoint de ejecución; sin predecesor publicado
**Origen:** commit `27a462618df0ab7d2452e77673fc2214fd0e0d45`, árbol `de46b96c6595f6a602531c17e6dd8858c3e7626e`

## Resultado ejecutado

La evidencia de F04 satisface materialmente los criterios documentados en `docs/AUDITORIAS/F04_F10_20261009/ENTREGA_F04.md` y la aceptación técnica `docs/AUDITORIAS/F04_F10_20261009/continuacion/REVISION_F04_ACEPTADA.md`: 242 entradas de manifiesto y su overlay pasan hashes; la matriz contiene los 19 territorios; los cinco candidatos F04 validan paquete, receipt local e informe de compatibilidad con identidad coherente. El verificador emitió `F04.technical_criterion=SATISFIED`, `formal_status=PENDING` y `approval_recorded=false`. La transición formal queda propuesta a Work, no registrada aquí. F09 permanece PASS.

Se volvió a reproducir desde este checkout la verificación de transferencia. El ZIP entregado conserva SHA-256 `d44f79be353f6c5df469189d47cce9667d451da21a1b60c0eef28f2b34afd66c`. Los cinco artefactos, paquetes interiores, informes congelados e identidades 2025/2025 pasan; se preparan receipts auténticos en la salida temporal, fuera del catálogo. La identidad y SHA del paquete, informe e identidad de compatibilidad por territorio están en `transferencia-autentica-20261011/validacion.json` y se reproducen en `transferencia-autentica-20261011/receipts-pendientes/`.

| Territorio | Run / artefacto | SHA-256 del ZIP exterior | Identidad territorial 2025/2025 | Validación territorial | Situación canónica |
|---|---:|---|---|---|---|
| Andalucía | 38082966768 / 11682006744 | `cc70f801d5a26a522458da05a5fde15e1876071cf1738d07c90429ca2057a056` | `057a38a77a6e2163a962022d73387fe0588f3efda1b969b30c737538544ef1f2` | Paquete e informe PASS | BLOCKED para 2025/2026; receipt no registrado |
| Aragón | 38093067883 / 11685591675 | `35adcbfcf41619c3e54219714aefac5b4885fae0ccd08ae5fcf9930e0528db51` | `e93472693aea78e48318bdf65a612c72d5bd1cd559b472b12ce0cfeb251b83ac` | Paquete e informe PASS | BLOCKED para 2025/2026; receipt no registrado |
| Castilla y León | 38091055890 / 11684448799 | `1f9d6a7c0362b157d2bb300a4c1eca037eb7a07fa52fec53ad550d46752351bd` | `155b35accd76c2f82cb21c298fda55b2df0fe122a7059df1c6068fbfb3e26b5e` | Paquete e informe PASS | BLOCKED para 2025/2026; receipt no registrado |
| Comunidad Valenciana | 38091132175 / 11684204844 | `528d2bfb2a7096120528fe5407473d13138551380278cfaa2a2928e521f57c5d` | `f50c038b9e79935c6fc0327df0d4f40d0315dbae70bff5215c32ce4b48e2cd28` | Paquete e informe PASS | BLOCKED para 2023/2023; receipt no registrado |
| Extremadura | 38091144559 / 11684599346 | `b4241708cbc7eb1fcf3dd7b6298152392731975106bbddaf6d8ae03bc3fcd8dc` | `70d7a964b7b837555ce03d5874c5fa04a74a80d5d724947b89fa9107684fd084` | Paquete e informe PASS; puerta #179 PASS en scratch | BLOCKED como consumidor canónico hasta registrar receipt; fuente electoral `BLOCKED_PROVISIONAL` |

En Extremadura, la reproducción de `validate_territorial_receipt` devolvió PASS para run `38091144559`, identidad `70d7a964…84fd084`, con el SHA del catálogo antes/después idéntico (`dc3bf7662d22c7b854df7821defbc6f2d9121607131351d48341fba1056d8693`). El ensayo fue aislado, sin registro ni promoción, y no evaluó la fuente electoral.

## Identidades vigentes y adquisición

El contrato temporal vigente requiere Andalucía, Aragón y Castilla y León 2025/2026; Comunidad Valenciana 2023/2023; Extremadura 2025/2025. El inventario de reutilización no encontró paquete/receipt durable con identidad exacta para los cuatro primeros. Los paquetes auténticos 2025/2025 no se reasignaron a otra identidad. No se repitieron adquisiciones válidas de población ni se descargaron datos en esta sesión.

La comprobación puntual de DNS del productor oficial (`www.ine.es:443`) devolvió `gaierror: [Errno 8] nodename nor servname provided, or not known`. Por ello no se adquirieron las entradas ausentes. El primer paso ejecutable cuando se restablezca conectividad es usar `herramientas.adquirir_fuentes_oficiales.acquire` en modo `official_live`, edición de proyecto `2025`, población/seccionado `2025/2026` para Andalucía, Aragón y Castilla y León, y `2023/2023` para Comunidad Valenciana; aplicar las declaraciones territoriales existentes y mantener la salida en un área aislada. Validar cada paquete y generar el informe con `validate_compatibility_package(require_ready=True)` antes de construir o registrar cualquier receipt. No se ejecutó el workflow territorial.

## Regresión nacional y pruebas

La matriz offline reejecutada contra `/Users/macbookpro/Desarrollo/DDD-almacen/fuentes-preparadas` conserva el SHA-256 de `recovery-manifest.json` (`92c6acc0f29a4e1897de6c6f69bc025f0cf11722ebb4aa36e69a534b9ad3130c`) y arroja **14 PASS / 5 BLOCKED**. Los cinco bloqueos de consumidor son Andalucía, Aragón, Castilla y León, Comunidad Valenciana y Extremadura, porque ninguno tiene bytes acreditados por receipt registrado en el catálogo activo. Esto es independiente de que el receipt de Extremadura pase en scratch. La comprobación no ejecutó generación ni `00`, y la puerta electoral permanece separada.

Pruebas ejecutadas en este checkpoint:

- `verificar_transferencia.py --transfer <ZIP auténtico> --output <directorio nuevo>`: PASS, cinco receipts preparados, no registrados ni promovidos.
- `validar_extremadura_aislada.py --validated-root <salida completa> --scratch <directorio nuevo>`: PASS aislado; el primer intento con `--validated-root .../validated` falló por pasar el nivel de directorio incorrecto y no modificó datos.
- `/usr/local/Caskroom/miniforge/base/bin/python3 -m pytest -q tests/test_f10_receipt_contract.py tests/test_f10_preparacion_aislada.py tests/test_prepared_source_pair_execution.py -k 'not test_00_executes_real_territorial_reuse_route_without_preparing_source'`: **20 passed, 1 deselected, 56 subtests passed**. El caso que invoca `00` se excluyó expresamente.
- Regresión offline nacional: **14 PASS / 5 BLOCKED**, decisión general BLOCKED; cero receipts nuevos y cero promoción.

## Límites de este checkpoint

La escritura del Plan Maestro y el respaldo en `DDD-almacen` no están permitidos por las raíces escribibles de esta sesión; se conservan los ZIP originales en Downloads y el replay verificado bajo `/private/tmp`. El manifiesto del almacén se leyó sin modificación. No se ejecutaron adquisiciones por el fallo DNS. No se registraron receipts ni se promovieron fuentes. `gh auth status` detecta el token de `jfmurciego` inválido; por ello no es posible publicar la rama, abrir la PR ni obtener su CI hasta reautenticar el CLI. No se solicitaron credenciales ni se repitieron intentos de escritura externa.

La revisión independiente separada `GO_ACOTADO` sobre el HEAD/árbol de origen confirma la integridad y el alcance local del dossier, con cero defectos bloqueantes. No equivale a aceptación formal F04, cierre F10, registro canónico ni autorización de promoción.

**Estado de Fuentes Oficiales:** F04 técnicamente satisfecho, formalización PASS pendiente de registrar en el Plan Maestro; F09 PASS; F10 PENDING. **Dictamen: BLOCKED**, hasta que se habiliten DNS al INE, escritura autorizada al Plan Maestro y almacén, y autenticación GitHub para la integración autorizada. La acreditación productiva de cada identidad sigue pendiente hasta su adquisición, registro y validación; no se declara PASS por territorio con evidencia incompleta.
