# Plan de migración de los identificadores internos a AUTnn / NACnn (2026-11-10)

Solo documentación. No se migra nada, no se toca código, claves ni workflows y no se lanza nada. Se ejecutaría en el corte 5.0.0 (decisión D-45), nunca antes.
Entradas: `configuracion/notacion_territorial.csv` (71 filas: AUT01-19 = CODAUTO, NAC01-52 = CPRO) y `docs/INVENTARIO_IMPACTO_NOTACION_AUT_NAC.md`.

## 0. Resumen
- Idea: id nuevo = código de la tabla maestra en minúsculas (`aut01`, `nac01`; las 350: sufijo, §6). El id viejo se conserva como alias de lectura hasta el final de la transición.
- El corte 5.0.0 regenera todo de todos modos (D-45): las huellas y los checkpoints se invalidan **por el corte**, no por la migración. Lo que no puede invalidarse son las fuentes y los datos oficiales con sha256 y el histórico.
- Orden: de la capa más reversible a la menos reversible. Hay un único punto de no retorno real: borrar las claves antiguas (R2, registro del visor, URL públicas).
- Recomendación del inventario, que sigue en pie: si el beneficio es solo de cara al exterior, basta la capa visible (etiqueta) y no migrar. Este plan es para si el propietario decide migrar.

## 1. Orden de migración por capas
Cada capa termina con su prueba de equivalencia (§4) y no empieza hasta que la anterior esté en verde. Hasta la capa 6 el id viejo sigue funcionando.

| Capa | Qué | Cómo | Reversible |
|---|---|---|---|
| 1. Datos y catálogo | `catalogo_territorios_espana_2025.yaml` (`territory_id`, `parent_territory_id`), `notacion_territorial.csv`, `territorios/<id>/` (122 carpetas) y `meta.territory_id` | Añadir al catálogo `id_legacy` (id viejo) y `notacion` (AUTnn/NACnn); resolutor único `resolver_id(x)` que acepta cualquiera de los dos y devuelve el nuevo. Después renombrar carpetas con `git mv` (conserva historia) | Sí (git revert), mientras no se haya regenerado nada |
| 2. Contratos y políticas | `configuracion/` (19 ficheros: registro electoral, preparación de legislatura, política, elecciones generales, `ensemble/<id>.json`, f10), `ddd_core/*_contract.py` (`expected_territory_id`), `herramientas/` (12 ficheros con ids literales, claves `ES-<ámbito>-<unidad>-<fecha>`) | Contratos aceptan ambos ids y normalizan al nuevo; las claves de elección se emiten con el nuevo y se leen con ambos | Sí |
| 3. Workflows y Gestor | input `territory_id` (tipo `choice`) de la 00 y demás, test que compara opciones con el catálogo, `gestor_campana_nacional.py`, `gestor-campanas.yml`, `generar_estado_operativo.py` | Las opciones del `choice` pasan a ser los ids nuevos; durante la transición se admite el viejo vía el resolutor (normalizar en el primer paso). Los lanzamientos por API con id viejo siguen funcionando | Sí, salvo runs lanzados con el id nuevo (se resuelven por alias) |
| 4. Visor y datos abiertos | `visor/` (app, v2, nacional), `web/`, `datos_abiertos/<id>/` (52 carpetas), `INDEX.json`, `index.html`, `datos/composicion|distritos|resultados` y sus manifiestos | Publicar las carpetas nuevas **a la vez** que las viejas (copia con mismo contenido, sha256 iguales) y que el visor lea el nuevo id con respaldo al viejo. Redirecciones o ficheros puente en las URL viejas | Sí mientras convivan las dos |
| 5. Archivo ARC y claves de R2 | `orchestracion/archivo_r2.json` (campo `territorio`), claves `r2://ddd-research-archive/<id>/<run>/…`, ARC-E, ARC-C, ARC-P | Copiar a la clave nueva, verificar sha256 objeto a objeto, escribir en `archivo_r2.json` el par (clave nueva, clave vieja) y **no borrar** la vieja. ARC-C (14 días) no se migra: caduca solo | Sí hasta borrar las claves viejas |
| 6. Histórico y registro de publicaciones | `publicaciones_visor.json` (197 productos, id `m06-<id>-<run>`; solo adición), `estado_operativo.json`, `catalogo_procedencia.json`, `publicado/dashboard/`, `legacy/`, registro de cambios, auditorías, tests/fixtures | Registro: **solo se añaden** entradas con id nuevo; las viejas quedan como están y el campo `alias_de` enlaza ambas. Histórico (`legacy/`, registro, auditorías): no se toca. Tests y fixtures: reescribir literales (105 ficheros); `raiz_congelada_aee8215e` se regenera | Registro: sí (se retira lo añadido) |
| 7. Retirada de alias (fin) | Quitar el respaldo al id viejo, borrar claves antiguas de R2 y carpetas viejas de `datos_abiertos` | Solo tras un ciclo completo sin lecturas por id viejo (contador en el resolutor) | **No** (punto de no retorno 2, §5) |

## 2. Alias y compatibilidad durante la transición
- Una sola función de resolución (`resolver_id`) en `ddd_core`, con la tabla `id_legacy → id_nuevo` generada desde el catálogo; todos los consumidores la usan. Prohibido comparar ids con literales fuera de ella.
- Escritura con el id nuevo, lectura con ambos. El resolutor cuenta los accesos por id viejo; la capa 7 solo se hace cuando el contador está en cero durante un ciclo completo.
- Colisión: ningún id nuevo puede coincidir con uno viejo (los nuevos son `aut\d\d` / `nac\d\d`; ningún id viejo lo es). Test que lo comprueba.
- Registro del visor (solo adición): cada producto nuevo lleva `alias_de: <id viejo>`; el visor busca por el nuevo y, si no lo halla, por el viejo.
- URL públicas: mantener las rutas viejas como redirección o fichero puente al menos un ciclo de publicación y una versión de `INDEX.json` que liste ambas (citas y enlaces externos).
- `pilot_code` (`C01`…`C52`, `Rnn`) no cambia: ya coincide con `C`/`R` + CPRO y sirve de comprobación cruzada.

## 3. Qué huellas y hashes cambian
**Cambian (y se asumen, porque el corte 5.0.0 regenera todo):**
- Huella M05/N08 y checkpoints M04/M05: el id entra en el contrato y el motor lee `meta.territory_id` (`modulos/05_optimizar_distritos.py` lo usa también para localizar `territorios/<id>/config`). Todo checkpoint previo queda inválido; 00 «Generar desde fuente territorial acreditada» (o «Desde el principio») por territorio, 71 ejecuciones más las 350 si se regeneran.
- Hash del catálogo, de cada contrato de territorio, de `INDEX.json`, de los manifiestos de `datos/` (rutas con id) y de `archivo_r2.json`.
- Claves de elección y de producto que incluyen el id (`m06-<id>-<run>`).
- El par territorial-electoral queda incompatible (`TERRITORIAL_READY_PAIR_INCOMPATIBLE`) hasta repreparar: electoral con reutilizar=false → legislatura `prepare_one` → 00 «Reutilizar».

**No debe invalidarse (comprobar antes y después, bit a bit):**
- Fuentes oficiales y sus sha256: ZIP nacional de Interior (release `fuente-infoelectoral-02202307`), CSV de escaños 2023 (BOE-A-2023-18907), `fuentes/ine_codigos_territoriales_2026-11-10/`, cartografía y censo. No contienen el id del proyecto; si alguna huella de fuente lo contuviera, es un defecto a corregir antes del corte.
- Contenido de los productos publicados (GeoJSON M06, ZIP M08): el sha256 del contenido no cambia; cambia solo la ruta/clave.
- Histórico inmutable: `legacy/`, `docs/REGISTRO_DE_CAMBIOS.md`, `docs/AUDITORIAS/`.
- Umbrales, K, suelo, techo, atomicidad: no son parte de la migración (decisión del propietario aparte).
- A verificar al empezar (no comprobado aquí): si el id entra en la semilla aleatoria de M04/M05. Si entra, el resultado del motor cambiaría con el id y la equivalencia bit a bit solo valdría congelando la semilla explícita; la prueba A de §4 lo detecta.

## 4. Pruebas de equivalencia
Prueba = misma entrada con id viejo y con id nuevo, y comparar.
- **A. Motor (bit a bit):** un territorio por tipo (Álava, Huesca, Cádiz, Madrid, uno insular, Ceuta) con la misma semilla: asignación municipio→distrito y GeoJSON M06 idénticos byte a byte; solo difiere el id. Si no lo son, parar: la semilla depende del id.
- **B. Datos publicados:** sha256 de cada fichero de `datos_abiertos/<id_nuevo>/` = el de `<id_viejo>/`; mismo recuento (52 carpetas, 197 productos).
- **C. Archivo R2:** por cada objeto copiado, sha256 clave nueva = sha256 clave vieja; lista completa de pares en `archivo_r2.json`.
- **D. Catálogo:** 71 + 49 entradas, una por id nuevo; tabla `id_legacy → id_nuevo` biyectiva; `pilot_code` y `province_codes` intactos; cada `nac` coincide con CPRO y cada `aut` con CODAUTO de la tabla maestra.
- **E. Resolutor:** test de las 120 entradas en ambos sentidos y de un id inexistente (error claro); test de no colisión.
- **F. Contratos y Gestor:** el Gestor en modo `plan` (sin lanzar) produce el mismo plan con ids viejos y nuevos, salvo etiquetas.
- **G. Visor:** carga de cada territorio por URL vieja y por URL nueva; mismo contenido.
- **H. Suite completa** (`unittest`) en verde en cada capa; la CI en verde en la PR y en `main` antes de fusionar (regla del propietario).

## 5. Puntos de no retorno y reversión
| Punto | Qué lo hace irreversible | Reversión antes / después |
|---|---|---|
| 1. Regenerar con id nuevo (corte 5.0.0) | Checkpoints y huellas viejos inutilizados; los artefactos de Actions caducan (14 días) | Antes: `git revert` de capas 1-3 y vuelta a los checkpoints. Después: regenerar con el id viejo (otras 71 ejecuciones). Hacer el corte tras congelar etiqueta/rama `pre-5.0.0` |
| 2. Capa 7 (borrar claves viejas de R2, carpetas y rutas públicas) | Pérdida de enlaces y claves | Antes: nada que revertir. Después: solo restaurando desde la copia (por eso §1 exige copia, no movimiento) |
| 3. Publicar el nuevo `INDEX.json` y retirar el viejo | Enlaces externos y citas | Mantener ambos un ciclo |
- Plan de reversión general: cada capa es una PR; revertirla restituye el estado anterior mientras el alias siga activo. Antes de la capa 5 se guarda un inventario (`id_clave_vieja, sha256`) de R2; antes de la capa 7, copia fuera de línea del registro y de `INDEX.json`.
- Una capa que falle una prueba de §4 se revierte entera; no se arregla sobre la marcha (límite: dos ciclos de reparación por causa).

## 6. Variantes de 350 distritos (49 ids sin código propio)
Hoy `congreso350_<prov>` (`pilot_code` Rnn, `parent_territory_id: congreso_<prov>`). Hereda el NAC de su provincia; Baleares, Las Palmas y Santa Cruz de Tenerife no tienen variante.
- **Propuesta:** sufijo `-350`: `NAC01-350` para Álava, y así hasta `NAC52-350` (49 ids; en minúsculas `nac01-350`). Razones: el prefijo `NACnn` sigue siendo la clave de provincia (agrupar y ordenar por provincia es trivial), el sufijo dice qué variante es, y es extensible (`-NNN` para otra variante) sin gastar códigos. Alternativa: campo `variante` en el catálogo con `nac01` único y clave compuesta (`nac01`, `350`); más limpio en modelo de datos, más invasivo en claves y rutas.
- Cruce: `Rnn` ↔ `NACnn-350` ↔ `parent`=`NACnn`; el test de catálogo verifica los 49 pares.
- **La decide el propietario** (sufijo, campo `variante` u otro).

## 7. Duplicados AUT / NAC (ids distintos en dos ámbitos)
Un mismo territorio físico tiene dos códigos y dos ids. Son ámbitos distintos y **no se fusionan**: autonómica y Congreso tienen contratos, K, resultados y registros distintos.

| Territorio | AUT (id viejo) | NAC (id viejo) |
|---|---|---|
| Madrid | AUT13 `madrid` | NAC28 `congreso_madrid` |
| Asturias | AUT03 `principado_de_asturias` | NAC33 `congreso_asturias` |
| Cantabria | AUT06 `cantabria` | NAC39 `congreso_cantabria` |
| La Rioja | AUT17 `la_rioja` | NAC26 `congreso_la_rioja` |
| Navarra | AUT15 `comunidad_foral_de_navarra` | NAC31 `congreso_navarra` |
| Murcia | AUT14 `region_de_murcia` | NAC30 `congreso_murcia` |
| Ceuta | AUT18 `ceuta` | NAC51 `congreso_ceuta` |
| Melilla | AUT19 `melilla` | NAC52 `congreso_melilla` |
| Baleares (no estaba en la lista de la orden) | AUT04 `illes_balears` | NAC07 `congreso_baleares` |

- Con el prefijo la ambigüedad desaparece (el ámbito va en el código); el riesgo está en el alias: el id viejo `madrid` (autonómico) no debe resolverse nunca a `nac28`. La tabla `id_legacy` es por id exacto y el test E lo verifica.
- Baleares: es también uniprovincial y tiene dos ids distintos, igual que los ocho de la orden (nueve en total). Además `illes_balears` es el único id viejo en lengua no española; el id nuevo lo corrige de paso (nombre público: «Islas Baleares»).
- Ceuta y Melilla: dos ámbitos con la misma ciudad (AUT18/NAC51, AUT19/NAC52); el código NAC es siempre el CPRO, no el de la comunidad.
- Datos: `datos_abiertos/<id>/` tiene carpetas separadas por ámbito, de modo que no hay colisión de rutas.

## 8. Riesgos y esfuerzo
| Riesgo | Efecto | Mitigación |
|---|---|---|
| Id viejo suelto en algún sitio (literal en `herramientas/` o test) | Fallo silencioso o territorio no hallado | Resolutor único, contador de accesos al id viejo, búsqueda de literales como puerta de la capa 7 |
| Semilla dependiente del id | Resultado distinto | Prueba A antes de empezar |
| Registro de solo adición | No se reescribe lo viejo | Alias `alias_de` y entradas nuevas |
| Claves R2 y URL públicas | Enlaces rotos | Copiar, no mover; redirecciones |
| Caducidad de artefactos (14 días) y par electoral incompatible | Cadena de repreparaciones | Ordenar el corte: territorial → electoral → legislatura → 00 |
| Colisiones AUT/NAC | Resolución al ámbito equivocado | Tabla por id exacto, tests |
| Coste de producción: 71 (+49 si se regeneran las 350) ejecuciones de la 00 y la publicación | Presupuesto | Dentro del corte 5.0.0, que ya regenera todo; sin coste adicional si se hace a la vez |

Esfuerzo (orden de magnitud, sin ejecuciones productivas): capa 1: 1 PR (catálogo, resolutor, carpetas); capa 2: 1-2 PR (contratos, políticas, herramientas); capa 3: 1 PR; capa 4: 1-2 PR; capa 5: 1 PR + script de copia verificada; capa 6: 1-2 PR (registro, tests); capa 7: 1 PR. En total unas 8-10 PR y los 71 (+49) lanzamientos del corte, que se hacen igualmente.

## 9. Decisiones que quedan al propietario
1. Migrar o quedarse con la capa visible (recomendación vigente: no migrar).
2. Sufijo de las 350 (`-350` propuesto) o campo `variante`.
3. Si el id nuevo va en minúsculas (`nac01`) o con el código tal cual (`NAC01`).
4. Cuántos ciclos de convivencia de alias antes de borrar lo viejo.
