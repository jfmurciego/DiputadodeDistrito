# F10 / N08 — Cuatro consultas institucionales listas para autorización de envío

**Fecha:** 2026-10-18. **Estado:** `DRAFT_NOT_SENT`. Cada apartado es un texto independiente. No implica una respuesta institucional, aceptación de excepción ni cambio de las puertas F10/N08. Requiere destinatario/canal real y firma aprobados por el propietario. No adjuntar datos personales.

## 1. Junta de Andalucía / unidad de resultados electorales SIEL

**Asunto:** Seccionado electoral efectivo 17/05/2026 y tratamiento de 2102502002 (Cortegana)

Solicitamos confirmación de la lista oficial de secciones y mesas utilizada para los resultados definitivos de las elecciones andaluzas de 17/05/2026 (convocatoria SIEL 202605), junto con su fecha y versión de referencia, y la correspondencia con las ediciones INE 2025/2026.

En las capas INE `TIPO=SECCIONADO` hemos identificado 6.029 secciones (2025) y 6.045 (2026), con 25 altas y 9 bajas. El producto electoral SIEL utilizado por nuestro expediente consta de 6.044 secciones y 4.157.539 votos a candidaturas conciliados. La identidad concreta presente en ambas ediciones del INE y ausente del nomenclátor `opciones/seccion` de SIEL es **2102502002**, Cortegana (Huelva), distrito 02, sección 002; SIEL devuelve solo `0001` para ese distrito. El producto territorial INE 2025 de nuestro estudio identifica esa sección con 558 habitantes y discontinuidad administrativa declarada.

Rogamos identificar documentalmente si en la convocatoria se integró en otra sección/mesa, si carecía de mesa propia, si existe error o una edición alternativa, y aportar el identificador auténtico y la relación electoral que justifica la atribución de resultados. Solicitamos también los cambios de sección con fecha de efecto para las restantes 34 identidades modificadas entre INE 2025 y 2026, o el organismo custodio de esa relación. No pretendemos asignar votos por inferencia geométrica.

**Evidencia DDD:** `ANDALUCIA_INE_6045_SIEL_6044_DIFERENCIA_NOMINAL.json`, `ANDALUCIA_SIEL_202605_IDENTIDADES_34.json`, `IDENTIDADES_INE_2025_2026_F10.json`.

## 2. Junta Electoral de Extremadura / juntas provinciales de Badajoz y Cáceres

**Asunto:** Acceso al escrutinio general definitivo por mesa/sección — Asamblea de Extremadura 21/12/2025

Solicitamos el conjunto oficial definitivo por provincia, municipio, distrito, sección y mesa, con candidaturas, votos blancos y nulos, identificación de CERA y otras categorías no geocodificables, y todas las correcciones respecto al avance provisional. En caso de no existir fichero granular, pedimos acceso a las actas auténticas o confirmación del nivel máximo disponible y del custodio oficial.

El acuerdo de 07/01/2026, publicado en DOE 8 de 14/01/2026 (`2026AC0001`), acredita 326.196 votos a candidaturas en Badajoz y 198.641 en Cáceres, total **524.837**. La reconciliación previa DDD de un conjunto provisional computa **522.418**, diferencia **2.419** que no se puede imputar de oficio. Se solicita específicamente aclaración documental de los códigos **1004201001** y **1012501001** y desglose de CERA, rectificaciones, actas y versión.

**Referencia oficial:** https://doe.juntaex.es/otrosFormatos/html.php?anio=2026&doe=80o&xml=2026AC0001

## 3. INE — cartografía digitalizada de secciones 2023 (Comunidad Valenciana)

**Asunto:** Semántica de contactos de frontera y precisión de reproyección para tres secciones 2023

Solicitamos confirmar la edición geométrica oficial de referencia 2023 y la existencia de rectificaciones, metadatos de precisión y criterios recomendados para evaluar contactos de frontera tras cambio de CRS entre las secciones **4617201001**, **4619401008** y **4619401013**.

Sobre una respuesta WFS `Secciones_2023` válida y preservada se ha calculado que ambos pares `touches=true` y `intersection.area=0` en **EPSG:25830**, mientras que al transformar geometrías con sus segmentos originales a EPSG:3035 aparecen intersecciones de **11,622500827 y 11,901114392 m²**. Al densificar en EPSG:25830 con tramos máximos de 50 m antes de proyectar, ambos solapamientos bajan a 0 m² en la muestra examinada. No se solicita cambiar la geometría oficial ni se afirma que exista un error administrativo de límites.

Rogamos confirmar el criterio institucional pertinente para distinguir la semántica de frontera real de la aproximación por segmentos lineales tras reproyección y la fecha/identidad de una eventual corrección oficial.

**Evidencia DDD:** `INE_WFS_VALENCIA_2023_TRES_CUSEC.geojson`, `tests/test_f10_valencia_reprojection_sensitivity.py`, GitHub Actions `39026274682`. La puerta de F10 sigue BLOCKED por su contrato M02 vigente.

## 4. CNIG / IGN — límites administrativos históricos de referencia 01/01/2025

**Asunto:** Acceso a límites oficiales de municipios/provincias a 01/01/2025 para acreditación independiente

Solicitamos referencia y acceso verificable a un conjunto histórico de límites provinciales y municipales vigente a **01/01/2025** —incluidos recintos, enclaves, componentes discontinuos y modificaciones de vigencia retroactiva—, con fuente jurídica o Registro Central de Cartografía, geometría, CRS, fechas y versión/hashes. El catálogo del Centro de Descargas consultado muestra archivos históricos 2023/2024 y ediciones actuales 2026, pero no una instantánea histórica titulada 2025, mientras su registro de novedades documenta varias actualizaciones en 2025. Solicitamos aclaración de qué versión permite una referencia efectiva al 01/01/2025.

La necesidad técnica afecta especialmente a **Burgos (CPRO09)** y **Palencia (CPRO34)**: el estudio de topología INE 2025 contiene respectivamente cuatro y tres componentes de grafo seccional frente a cuotas K=3 y K=1. No se afirma imposibilidad administrativa; se pide evidencia para clasificar discontinuidades reales frente a artefactos del seccionado y documentar posibles excepciones nominales de forma independiente.

**Referencia oficial:** https://centrodedescargas.cnig.es/CentroDescargas/limites-municipales-provinciales-autonomicos

---

**Criterio de aceptación:** no se promueve ninguna puerta basándose en estos borradores. Una respuesta debe conservarse íntegra y cotejarse contra la edición fuente, la identidad CUSEC, el contrato y el consumidor canónico; cualquier cambio contractual o excepción requiere decisión expresa de gobierno.


## 5. Addenda 19/10/2026 — INE Oficina del Censo Electoral: 18 cambios seccionales que requieren acreditación expresa

**Objeto concreto:** confirmar mediante expediente administrativo/callejero electoral/actos de modificación, fecha de eficacia y relación anterior→nueva de las **18 secciones oficiales SIEL 2026** siguientes. En el cotejo INE WFS 2025→2026 tienen cada una un predecesor geométrico dominante (>99,99% del área), pero no se ha hallado una relación directa `TRAM/CVAR=M` con ese predecesor en el extracto oficial ya auditado.

**Secciones electorales que precisan la relación documental (18):**

`1100602011`, `1101504017`, `1402110049`, `1814501010`, `2906702052`, `2906702053`, `2906707098`, `2906708077`, `2906708078`, `2906708079`, `2906708080`, `2906708081`, `2906711014`, `2906711015`, `4103804022`, `4103805032`, `4104701008`, `4108102019`.

**Impacto electoral medido:** estos 18 códigos acumulan **11.081 votos a candidaturas** de SIEL 202605. La otra cohorte de 7 altas contiene **4.344 votos** y sí presenta enlaces de modificación de tramos `M` con su candidato geométrico en los ficheros del INE. Esa relación de tramos no basta para atribuir resultados completos de secciones a la edición 2025.

Dos incidencias específicas requieren aclaración: `1102804011` figura en las variaciones con modificación y además un registro `B` fechado el 29/08/2025; y `2907001040` recibe variaciones de tramos tanto de `2907001018` (su candidato geométrico) como de `2907001010`. Solicitamos certificado de la identidad seccional en la elección 17/05/2026 y de su relación con la cartografía INE 2025 para evitar adjudicación arbitraria de electores o votos.

**Evidencia preservada:** `ANDALUCIA_SIEL_25_NUEVAS_TRAM_CRUCE_20261019.json`, `ANDALUCIA_SIEL_VOTOS_25_NUEVAS_20261019.json`, `ANDALUCIA_SIEL_25_NUEVAS_2026_VOTOS_20261019.csv`, `ANDALUCIA_CANDIDATOS_GEOMETRICOS_34_20261019.csv`. Originales de variaciones INE: ZIP SHA-256 `f2f8299b...` y `154b8eac...`. Snapshot electoral SIEL: run `37150399030` y huellas verificadas.

**Estado:** borrador sin enviar, `CROSSWALK_ACCREDITED=false`. Ningún voto trasladado a geografía 2025.
