# F10 — expediente de cierre técnico y decisión final

**Fecha:** 2026-10-12
**Base remota comprobada:** `main@e14c27368d57ebd4674b476fe5da10c4d66b7d90`
**Base de árbol local verificable:** `c609b3bdcf3a8911e85fcd38aeae73d8c6f00c43` (segundo padre de e14; tree idéntico `7d2c309e72c3311edd8d64ae5937bb4ecfbdd3f3`)
**Rama local aislada:** `codex/f10-cierre-integral`
**Estado F10:** `PENDING`; no se asigna `CLOSED` ni PASS conjunto.

## Dictamen

**FINAL_OWNER_DECISION_REQUIRED, con una dependencia técnica externa explícita.** Se ejecutaron validaciones actuales y se agotaron las comprobaciones locales posibles con las evidencias del checkout. La acreditación de población valenciana 2023 está completa para el universo objetivo; no hay geometría admisible que permita cerrar su puerta territorial. Las tres correspondencias electorales 2025/2026 y la fuente granular definitiva de Extremadura carecen de evidencia oficial compatible suficiente en los expedientes revisados. Además, el catálogo oficial OGC API del INE ahora enumera `Secciones_2026`, candidato nuevo para el cotejo geométrico; no se pudieron recuperar sus features desde este entorno: `urllib` falla por DNS (`Errno 8`) y el lector web no puede abrir las rutas dinámicas de `items`. Por tanto, no se afirma agotada esa comprobación técnica. El Plan Maestro y el controlador `ddd auto` viven fuera del árbol escribible de este encargo, por lo que no se pueden registrar allí fichas ejecutables ni realizar una ejecución autónoma real sin modificar esa instalación. No se declara autonomía demostrada.

## Estado derivado reproducido

La orden `ddd auto --status --f10 --f10-root /private/tmp/DDD-f10-operacion-cierre-20261012 --plan /Users/macbookpro/Desarrollo/DDD-control/planes/ddd-maestro-vivo-20261011` devuelve `NO_READY` y reproduce:

| Puerta | Estado derivado |
|---|---:|
| Adquisición territorial | 18 CLOSED / 1 BLOCKED |
| Admisibilidad electoral | 15 ADMISSIBLE / 4 BLOCKED |
| Admisibilidad conjunta | 14 PASS / 5 BLOCKED |
| Producción | 19 NOT_AUTHORIZED_BY_F10 |
| F10 formal | PENDING |

Los trabajos de Andalucía, Aragón, Castilla y León y Extremadura aparecen `READY_LOCAL`, con `task_spec_registered=false` y `selectable=false`; Valencia queda `WAIT_OWNER` por falta de nueva evidencia oficial o decisión del propietario. Esto es diagnóstico de disponibilidad, no ejecución.

## Bloqueos y evidencia por frente

### Comunidad Valenciana

**P1 población: resuelto para identidad y cobertura del universo objetivo.** La evidencia de #253 diferencia exactamente 3.503 CUSEC con observación válida, que conservan 5.216.195 habitantes, de 46 filas poblacionales vacías que no pertenecen al universo de secciones 2023 exigible. La misma investigación atribuye los 360 registros extra del WFS a unidades `DISTRITO`, no `SECCIONADO`; filtrado el tipo de unidad, el universo queda en 1.823 CUSEC. No se imputaron ceros ni población.

**P2 geometría: bloqueado.** En EPSG:3035 los pares `4617201001/4619401008` y `4617201001/4619401013` se solapan en 11,8277092397 m² y 12,1112377964 m², ambos sobre el máximo contractual de 1 m². La normalización de consenso que preserva fronteras presenta cero cambios de solapamiento; por tanto, no se trata de un artefacto de reproyección/procesamiento. La alternativa REST Censo consultada mantiene el defecto; la alternativa WFS lo reduce levemente pero continúa sobre el umbral y, antes de separar distritos, incluye otras seis geometrías inválidas. No se encontró fe de erratas o versión oficial corregida ni mecanismo contractual específico para exceptuar esos pares. Las geometrías originales y alternativas permanecen intactas.

Evidencia y artefactos versionados: PR draft [#253](https://github.com/jfmurciego/DiputadodeDistrito/pull/253), rama `codex/f10-valencia-universo-2023`, HEAD `32e4397218c365af7b8de0df450dcde00339cc42`. La PR está `open/draft`; el compare actual con main da `ahead_by=7`, `behind_by=5` desde merge-base `34c8793cede82e1f82832c84fc43c6a990394905`, así que debe actualizarse y volver a validar antes de integrar. Evidencia: `docs/AUDITORIAS/F10_CIERRE_VALENCIA_20261012/evidencia_2023.json`; tests `tests.test_f10_valencia_2023_universe` (6/6 en la revisión independiente) y `tests.test_f10_valencia_independent_evidence`. Los hashes de varios artefactos cotejados por la revisión independiente incluyen población TSV `e8edd7b1…53906f21`, WFS ZIP `2f79e6cf…15aea4`, geometrías CPRO03 `b1ce66fc…ad7cb`, CPRO12 `886bb1ad…2ff3`, CPRO46 `4e0597c12…da58`, REST Censo Valencia `2dee7414…47d5ac`. Algunos originales protegidos 65034 no estaban disponibles en esta sesión para volver a calcular su digest; se preservan los hashes declarados en el expediente, sin alegar una nueva revalidación de sus bytes.

**Desbloqueo mínimo:** fe de erratas/representación corregida del INE, con identidad de edición y cobertura exactas, o una decisión contractual expresa de Work que defina el tratamiento de estos dos pares. No se recomienda una excepción automática ni un cambio de tolerancia; ambas opciones cambiarían el contrato de admisión.

### Andalucía, Aragón y Castilla y León — Electoral

La decisión de referencia territorial #250 `configuracion/decisiones/f10_referencia_territorial_2025_2026.json` (SHA-256 `f9b8e9c0887318c2caae72234eeb321afd94e7de756a679e68d7566dbb373caa`) aprueba población/seccionado territorial 2025/2025 y deja el crosswalk electoral 2025/2026 pendiente. No se reutilizan correspondencias poblacionales descartadas ni se infieren equivalencias por el solo código.

| Territorio | Hallazgo actual | Bloqueo mínimo |
|---|---|---|
| Andalucía | SIEL/resultado definitivo conciliado con 4.157.539 votos y 6.044 secciones electorales. Receipt SHA-256 `d768c9e328d1772c0f15915114b83f9751edb629f7abdfe815efbab0451841a8`; artefacto declarado `4e075fd15d3f946c7ed54d373bf225f527bec35a3f70cf3140ff3589c08aa6ba`; configuración `4bb2e7532d43cb688f5b7dfea09e48bc9d64a11d0d18e26fd497d16b48c4e87a`. | Tabla oficial completa que relacione las 6.044 secciones del resultado con la referencia INE 2025. La conciliación de votos no acredita identidad territorial. |
| Aragón | Fuente electoral RTVE y receipt de resultados identificados. Contrato SHA `2a9c7bfb9005311989f3e5634d62479a4d7b81a0cabad456e4887a85eeaa406a`; datos `bd091a2a878afd3aa0e9bf2af52f2484e24d967020c56cee5b1e320c339aa94c`; receipt `6f4d86d59e3a6bd1a928432b05b8e2a9890b90f5a415cd160f8877ec973332ba`. | Resolver documentadamente `5002501003` (resultado-only, 608 votos) y `2221301003` (map-only) y demostrar el crosswalk completo. No asignar esos votos por aproximación. |
| Castilla y León | Fuente original y procedencia declaradas: 67.006 filas originales, 3.528 secciones electorales normalizadas; source SHA `a1ac5c54d7092a4ad9585a6c085cf87d210cb28dc83bbe707e69640a137a08cd`, normalizada SHA `603e0261adc11871cdc8345a847da9f9161894050a51dd334f9928a4e6d01d30`, procedencia `c219744c673f91712035c30edd9e8d018c181fc5184bc5dc9158296707f43752`. | Reconciliación declara 3.504 comunes, 24 electorales-only con 15.656 votos y 2 map-only; CSV normalizado referido por el contrato no está en el árbol revisado. Hace falta paquete reproducible y correspondencias oficiales para las excepciones. Reconciliación SHA `590f3f26f674fe340b714a34c901427cde247738e81bc9649dc82026bfe16fd9`. |

No se encontró una tabla oficial completa de equivalencias en los expedientes examinados. Como investigación técnica pendiente se identificó el [catálogo OGC API Features del INE](https://www.ine.es/geoserver/ogc/features/v1/collections?f=text/html), que lista `Secciones_2026` en EPSG:25830, junto a la [capa `Secciones_2025`](https://www.ine.es/geoserver/ogc/features/v1/collections/WMS_INE_SECCIONES_G01:Secciones_2025/queryables?f=text/html). La ruta de features 2026 no se pudo adquirir desde esta sesión: `urllib` devolvió `nodename nor servname provided, or not known` y el navegador web rechazó los endpoints dinámicos de `items`/`queryables`. La adquisición puntual no se repitió. Hay que recuperar ambas ediciones por el OGC API o shapefile oficial y cotejar, por provincia/municipio, CUSEC, tipo de unidad, relaciones geométricas y la edición aplicable a los resultados 2026. Una coincidencia geométrica solo será evidencia auxiliar; no acredita por sí sola atributos o votos en unidades distintas. No se efectuaron descargas repetidas ni asignaciones.

### Extremadura — Electoral

**BLOCKED_FINAL_GRANULAR_SOURCE.** El DOE `2026AC0001` publica el resultado definitivo a nivel de circunscripción, con 326.196 votos en Badajoz y 198.641 en Cáceres (524.837 total); esa resolución no satisface el mínimo de sección del contrato. La JEC separa ese acuerdo de listados CERA por país/consulado, que no aportan votos por sección/mesa. El portal público de Junta está declarado como fuente de descubrimiento; el repositorio de prensa granular requiere credenciales y está marcado provisional/no promocionable.

La evidencia previa desglosa la diferencia provisional/definitiva de 2.419 votos: 891 CERA de Badajoz, 994 de Cáceres y 534 votos de dos secciones de Cáceres con ceros explícitos (`1004201001`, `1012501001`). Copias de terceros no acreditan asignación oficial y presentan 13 conflictos con esos ceros. Los datos provisionales permanecen no promovidos. El bloqueo pide un fichero/colección oficial definitivo durable con granularidad contractual, incluidos CERA y las dos secciones; no se afirma que las actas administrativas no existan, solo que no se dispone de una fuente compatible autenticada en las fuentes públicas y artefactos revisados.

Hashes de evidencia: bloqueo `9de414bb0afaaafd5301f68cd1865b24fddad041a32140b1d2c6083929a667c5`; declaración de fuentes `14d8efff9c06de16e9db759cceeedddae2d48c8f971e0491e8bbf7a382053fc9`; contrato provisional `dadb240f464c5bb5ca1641185a65edc472a730c027d52d1a649a5ceb19a82c07`; reconciliación `256c39c0cbe3df034e1258b5832d552673137decddad22bd723210ee8f4be9e8`. Se preserva la evidencia del producto territorial histórico de Extremadura y su receipt territorial F10 independiente.

Fuentes oficiales consultadas: [acuerdo DOE 2026AC0001](https://doe.juntaex.es/otrosFormatos/html.php?anio=2026&doe=80o&xml=2026AC0001), [ficha de la Junta Electoral Central](https://www.juntaelectoralcentral.es/cs/Satellite?c=JECEleccion_C&childpagename=JEC%2FJEC_Layout&cid=1408442328847&p=1379061494795&pagename=jec%2Fwrapper%2FJEC_Wrapper&rendermode=preview), [guía electoral de la Junta](https://elecciones2025.juntaex.es/doc/Gu%C3%ADa%20para%20participar%20en%20las%20elecciones.pdf).

## Revisión de pruebas locales

En el checkout aislado con árbol idéntico a la base remota e14 se ejecutaron:

- `python3 -m unittest -v tests.test_f10_derived_doors tests.test_f10_2025_independent_territorial_receipts tests.test_independent_source_receipt tests.test_territorial_electoral_independence tests.test_f10_valencia_independent_evidence tests.test_f10_receipt_contract tests.test_f10_preparacion_aislada` — **44 tests PASS**.
- `python3 -m unittest -v tests.test_preparacion_legislatura_vigente tests.test_cyl_electoral_2026 tests.test_castilla_y_leon_electoral_reuse tests.test_adquisicion_electoral_especial tests.test_electoral_reconciliation` — **57 tests PASS**.
- `git diff --check` — PASS en el árbol previo al expediente.

Estos tests conservan la separación territorial/electoral, linajes históricos, fallos cerrados ante recibos/hashes corruptos y los bloqueos 2026 que no tienen aprobación. No ejecutan campañas.

## Persistencia y revisión

El expediente recibió revisión técnica independiente con dictamen **GO_ACOTADO documental**, sin errores materiales detectados. La revisión no certifica los bytes de artefactos que no estaban disponibles ni vuelve a ejecutar los tests; los resultados anteriores se atribuyen a sus respectivas ejecuciones.

El commit local del expediente es `66a106cc51025c5a7234c3e66ad640afee390972`, sobre `codex/f10-cierre-integral`, con diff documental único. La creación del ref remoto `codex/f10-cierre-final-20261012` desde main e14 se completó, pero la escritura del archivo fue rechazada por el conector GitHub (`MCP tool call requires approval, but approval policy is never`). La comparación confirma que el ref remoto sigue idéntico a main: no contiene el expediente; no se creó PR y no hay CI que reportar. El expediente permanece íntegro en el commit local para su publicación en una sesión con escritura remota habilitada.

## `ddd auto`: límite de piloto

La orden de estado F10 anterior es un modo de lectura. No hubo ejecución Codex autónoma: el controlador deriva cuatro actividades `READY_LOCAL`, pero las cuatro tienen `task_spec_registered=false`; ninguna es seleccionable. `--f10` es incompatible deliberadamente con `--run` y el Plan Maestro activo (`/Users/macbookpro/Desarrollo/DDD-control/planes/ddd-maestro-vivo-20261011`) y `auto-policy.json` están fuera de los directorios escribibles disponibles para este checkout. No se añadieron fichas falsamente ejecutables ni se editó la política externa. Para cumplir el piloto hace falta integrar las fichas/validadores en la instalación autorizada de `ddd auto` y el Plan Maestro, con permiso de escritura allí; hasta entonces no se debe llamar al sistema autónomo.

## Puertas separadas y conservación

- Territorial: 18 cerradas, Valencia bloqueada.
- Electoral: 15 admisibles, Andalucía/Aragón/Castilla y León/Extremadura bloqueadas.
- Conjunta: 14 PASS, cinco bloqueadas.
- Producción: no autorizada; cero campañas, `00`, M01–M08 productivos, generación o publicación.
- Linajes históricos, receipts territoriales independientes y hashes: sin cambios.

## Resoluciones y habilitaciones solicitadas a Work en la puerta final

1. Indicar al INE los dos pares valencianos con áreas medidas y solicitar una corrección/fe de erratas oficial. Mientras no exista, mantener Valencia bloqueada. Si se considera una excepción, decidir expresamente su alcance contractual sin afirmar que la geometría queda corregida.
2. Proveer para Andalucía, Aragón y Castilla y León una tabla oficial de correspondencias sección electoral 2026 ↔ sección INE 2025, o encargar su solicitud al organismo competente. No bastan uniones espaciales sin asignación demostrable.
3. Proveer para Extremadura el conjunto oficial definitivo granular —incluidos CERA— o actas de mesas autenticables que permitan reconstruirlo, con contrato de publicación y trazabilidad.
4. Autorizar cambios escribibles a la instalación del Plan Maestro/controlador para registrar fichas y ejecutar el piloto local; la autorización de este mandato no atraviesa el límite de filesystem impuesto a esta sesión.
5. Habilitar una sesión con salida a red al OGC API INE (o aportar el paquete oficial `Secciones_2025`/`Secciones_2026`) para completar el cotejo electoral. La capa `Secciones_2026` existe en el catálogo oficial, por lo que la indisponibilidad de sus features en esta sesión no demuestra ausencia de fuente.

**No es técnicamente defendible cambiar Valencia a CLOSED ni afirmar F10 completo antes de resolver esas puertas.** Mantener `PENDING`. No hay actualmente base para una transición final a `CLOSED`; el cotejo oficial 2025/2026 y la ejecución real en `ddd auto` siguen siendo tareas técnicas pendientes que requieren acceso externo/escribible.

## Continuidad F10 — 2026-10-13

Este apartado actualiza el estado del piloto sin reemplazar ni repetir este expediente. La
rama preservada `codex/f10-cierre-integral` permanece en `7d38c18121f6a12ce80394073a23eda88ca427f7`;
el contenido de este expediente se recuperó de ese commit. El trabajo del controlador está
preparado localmente en `codex/f10-auto-cards`, HEAD
`edc2ab6386a292ecc6a48c3dd23a642e995c9402`, base `origin/main@8ab547ddc2c777fdcdcf8466618518e1c6e3fe99`.
El árbol de validación `codex/fuentes-oficiales` integra esa rama localmente en
`26a39c4cc013730540d1899ccc5c480e919f7ea7`; no se ha publicado ni abierto PR para este
incremento.

Se incorporaron cuatro fichas ejecutables `READ_ONLY` al controlador existente, con
contratos, fuentes hash-pinned, instrucciones de límites, validadores deterministas,
dependencias territoriales explícitas y validación de las salidas del ejecutor. Las tareas
son Andalucía, Aragón, Castilla y León y Extremadura. Las verificaciones vuelven a calcular
las cifras y discrepancias fijadas en los expedientes; una salida debe citar todas las
entradas y declarar el código exacto del bloqueo contractual. La revisión independiente del
HEAD `edc2ab63…` fue `GO_ACOTADO`: cero findings bloqueantes de código/gobierno; el dictamen
no acredita ejecución autónoma ni cambia ninguna puerta electoral, territorial o productiva.
Los predecesores archivados de configuración, validador, tests y registro de cambios fueron
comparados byte a byte con sus versiones inmediatamente anteriores.

En ese HEAD se ejecutaron 109 pruebas focalizadas y de regresión de recibos, independencia
electoral/territorial, evidencia valenciana, preparación F10, Andalucía, Aragón, Castilla y
León y reconciliación electoral: **109 PASS**. `git diff --check`: **PASS**. El worktree de la
rama de fichas quedó limpio. El comando de materialización sobre las evidencias locales reales
produjo los cuatro overlays y el validador derivado mostró: adquisición territorial 18
CLOSED / 1 BLOCKED; admisibilidad electoral 15 ADMISSIBLE / 4 BLOCKED; admisibilidad conjunta
14 PASS / 5 BLOCKED; producción 19 NOT_AUTHORIZED_BY_F10; F10 PENDING. Los cuatro trabajos
registran `READY_LOCAL`, ficha comprobada y `selectable=true`; Valencia permanece
`WAIT_OWNER` y no seleccionable. El `ddd auto ... --dry-run --pilot --f10` seleccionó
Extremadura como ENABLED / READY_FOR_PILOT y mantuvo las puertas accept/integrate/produce
cerradas. Evidencia material y hashes de esta reproducción: directorio
`continuidad/ddd-auto-20261013/`.

Se intentó una única ejecución real local de `ddd auto` para
`F10-EXT-ELECTORAL-SOURCE`. El controlador la rechazó antes de invocar Codex con
`BLOCKED_BUDGET: preventive admission refused`; el presupuesto registrado declara
`available_tokens: 0`, `provider_quota: UNKNOWN` y falta/resolución imposible del presupuesto
local. La ejecución no produjo investigación ni informe autónomo. No se modificó ni eludió
la política de presupuesto. Por tanto, las fichas y la selección en dry-run están
implementadas y comprobadas, pero **la autonomía ejecutiva no está demostrada**. Para
continuar esa única tarea hace falta una autorización de presupuesto local vigente que cubra
`F10-EXT-ELECTORAL-SOURCE` y permita la invocación Codex; después deberá ejecutarse el piloto,
validarse y revisarse su resultado.

La actualización local preparada para #253 sigue sin publicarse. El commit de actualización
contra main vigente conocido, `17de33631ce85db128e7f17abec9fffd59a5949a`, tiene como base
`origin/main@8ab547ddc2c777fdcdcf8466618518e1c6e3fe99`; el remoto conserva el HEAD anterior
`32e4397218c365af7b8de0df450dcde00339cc42`. La operación de push ya falló por resolución DNS
de `github.com` en esta sesión y no se afirmó publicación. No se ha actualizado la PR #253,
creado una PR para las fichas ni ejecutado CI. El diff local de fichas queda preparado para
integración, pero necesita push y revisión/CI en GitHub. La actualización valenciana sigue
bloqueada por los dos solapamientos oficiales medidos por encima de 1 m² sin fe de erratas ni
mecanismo contractual admisible; la población/identidad se considera resuelta según #253,
pero la geometría impide certificar la pareja 2023/2023.

Hashes SHA-256 de artefactos de continuidad:

- `materializacion.json`: `6e8262178b34831fb2d846bf8bab27ec529f832cfeaceca20d97cb3a2ebbc2e5`
- `estado-derivado.json`: `abe6ce74d329f6fa320fab571b24ab5113087a6def5dac33992fe9e0e17ef6de`
- `ddd-auto-dry-run.log`: `b17cab870177dfe5376b1c2808ed01306f826819f8d30f47ec087ca2947ff346`
- `summary.json`: `8867038a0cb166bc8af198a245e3291c91ebbe7467e29c3585da2707e3b1fe8c`
- `result.json`: `6bb743b56827ca7050bdd1c353a87859a63a86844d0c82225c1e46a302593813`
- `executor-budget.json`: `3b4e255ef45b7543aba327a1ecf78a4cd4774fcdadcaf0d0790a3258674f138b`
- `input-manifest.json`: `bbd9f2cc7ee2373f02f117339c0b47fe11d7ffe2d948b8ac9b084dc3d0f30e43`

Estado de cierre: **F10 continúa PENDING; no declarar DONE ni READY_FOR_FINAL_REVIEW**.
Tareas técnicas no completadas: ejecutar realmente una ficha con presupuesto vigente; publicar
la actualización de #253 y las fichas, obtener CI sobre los HEAD publicados y completar la
revisión/iteración de esos HEAD. Bloqueos externos conservados: error de DNS para publicación
y acceso a servicios oficiales desde shell, ausencia de geometría valenciana corregida
oficialmente y falta de crosswalkes electorales/fuente definitiva granular de Extremadura.
Las decisiones reservadas al propietario siguen siendo las enumeradas en las secciones
anteriores de este expediente; esta actualización no las reemplaza ni las convierte en
excepciones.

## Continuidad F10 — verificación adicional 2026-10-13

El checkout local `codex/fuentes-oficiales` está en `e042dec6b321b004068a46b0e25f45deeabe760a`, sobre `origin/main@9295ac305d57fd4c84f0c5c1f077ae161600fc9d`, limpio antes de añadir esta continuación. La actualización valenciana se preserva aparte en `codex/f10-valencia-refresh`, HEAD `107f5894298e1af51ca6c3226b0020ea6d4caa80`, cuyo padre funcional es `18c58dc414b706a927895d155b6aaf3db8a4fcf9`. El HEAD local incluye la corrección de reproducibilidad revisada independientemente como `GO_ACOTADO`; no modifica la acreditación geométrica.

La herramienta `herramientas/auditar_filas_vacias_ine_65034.py` reconstruyó las filas seleccionadas directamente del ZIP oficial INE 65034 desde sus cuatro partes protegidas, comprobando el SHA-256 de cada parte y el ZIP concatenado. Luego recalculó la identidad de las 46 filas vacías contra Censo 2023, geometría INE `SECCIONADO` 2023 y las geometrías 2025 del ZIP protegido. Los resultados son 46/46 filas reproducidas, 46 fuera de Censo 2023 y seccionado 2023, 35 presentes y 11 ausentes en seccionado 2025. Los resultados por CUSEC y hashes están en `docs/AUDITORIAS/F10_CIERRE_VALENCIA_20261012/filas_vacias_65034_reproducidas.json` de la rama valenciana. No se asigna población.

Las cuatro fichas electorales ejecutaron su verificador local determinista contra las entradas fijadas y devolvieron `EVIDENCE_VERIFIED`; los informes están en `continuidad/f10-card-validations-20261013/`. Sus SHA-256 son:

- Andalucía: `cd609beb508e22431418f10fb0da2f0b693fa29de3f00982c1c531025fd9595c`.
- Aragón: `a073c857fdb539fc4e71b22134eed146acb36ff709b2fb065db23c12aad1828e`.
- Castilla y León: `620298a56112b750d7cc3f818f647af6997912b767358e12f384b20aa2158ccd`.
- Extremadura: `a4ee6bc79cc82662c14c3f43e852a6acc357c78784496efc421d813bd12d34a2`.

Las comprobaciones recalculan 6.044 secciones y 4.157.539 votos en Andalucía sin demostrar crosswalk; una excepción result-only de 608 votos y una unidad map-only en Aragón; 24 result-only, dos map-only y 15.656 votos sin asignar en Castilla y León; y 524.837 votos definitivos frente a 522.418 provisionales en Extremadura (diferencia 2.419). No se generaron resúmenes de ejecutor ni se falsificó una transición electoral: los cuatro bloqueos permanecen.

Para buscar un canal alternativo oficial se consultó el [catálogo OGC API Features del INE](https://ine.es/geoserver/ogc/features/v1/collections?f=text%2Fhtml) y la [guía oficial de seccionado](https://www.ine.es/geoserver/www/guias/OGC_API_Feature_Seccionado.pdf). El catálogo accesible informa que `SU.VectorStatisticalUnit` corresponde al seccionado del año en curso (2026) y CRS EPSG:25830; la guía describe esa capa como dinámica, con los años anteriores publicados en colecciones históricas `Secciones_$AÑO`. El web gateway pudo consultar metadatos pero expiró al pedir features; el shell sigue sin resolver `github.com`. Este intento no produjo datos geométricos ni hashes de payload y no acredita crosswalk alguno.

Las regresiones específicas `test_f10_ine_65034_empty_rows`, `test_f10_valencia_2023_universe`, `test_f10_valencia_independent_evidence` y `test_f10_2025_independent_territorial_receipts` dieron **16 PASS** en la rama valenciana, con `git diff --check` satisfactorio. La revisión independiente del auditor quedó `GO_ACOTADO`, ligada al commit funcional `18c58dc…`; su comentario de docstring se corrigió en el HEAD `107f589…` y fue confirmado por lectura rápida. En el checkout de fichas, `unittest discover -s tests -p 'test_f10*.py'` dio 37 pruebas PASS y dos errores de importación porque el entorno carece de `shapely`; esos errores impidieron la regresión amplia completa y no afectan a los tests focalizados mencionados.

La publicación sigue sin producirse. `git push` volvió a fallar por DNS. La escritura GitHub mediante `github_create_tree` fue rechazada por la revisión automática: “MCP tool call requires approval, but approval policy is never”. Por tanto #253 conserva el HEAD remoto `32e4397218c365af7b8de0df450dcde00339cc42`, base antigua en su metadata; no hay nuevo CI. No se intentó otra vía de mutación externa.

Estado actualizado: **F10 PENDING**. Las tareas locales de auditoría ejecutables quedan persistidas; siguen pendientes ejecutar de verdad una ficha `ddd auto` con presupuesto admisible, publicar/revisar los HEAD, resolver la geometría valenciana con evidencia oficial, obtener crosswalks electorales oficiales y hallar la fuente granular definitiva de Extremadura. La capa INE de seccionado 2026 constituye una fuente oficial identificada, pero su payload no pudo recuperarse en esta sesión.

Tras archivar el resumen anterior, se ejecutó otra regresión enfocada en fichas, puertas derivadas, recibos y separación territorial/electoral: **52 PASS**. La derivación canónica directa sobre las evidencias reales produjo otra vez 18 territorios territorialmente cerrados / 1 bloqueado, 15 puertas electorales admisibles / 4 bloqueadas, 14 conjuntos PASS / 5 bloqueados y 19 producciones `NOT_AUTHORIZED_BY_F10`. No se usó el resultado como prueba de ejecución autónoma. En este entorno, `ddd auto --status --front fuentes-oficiales --f10 --f10-root /private/tmp/DDD-fuentes-oficiales` se detuvo porque no está disponible el overlay `puertas_f10.v1.json` bajo el Plan Maestro externo; el intento real previo del controlador quedó rechazado por el presupuesto preventivo de cero tokens. Los cuatro informes deterministas archivados muestran `executor_summary: NOT_SUPPLIED` y no son entregas de ejecutor Codex.

La rama valenciana actual se basa en el merge local de `main@9295ac305d57fd4c84f0c5c1f077ae161600fc9d` y preserva la cadena anterior a #253. Antes del intento de publicación se comprobaron como ancestros tanto su HEAD remoto `32e4397218c365af7b8de0df450dcde00339cc42` como el `main` vigente. El comando exacto para reanudar el push desde ese worktree es `git push origin HEAD:refs/heads/codex/f10-valencia-universo-2023`; actualizará el head de la PR #253 por fast-forward si esos refs remotos siguen iguales.
