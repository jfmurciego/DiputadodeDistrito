# DDD F10 — Evidencia geométrica INE 2023/2025/2026 (2026-10-17)

**Naturaleza:** incremento de evidencia oficial reproducible, no promoción ni cambio de contrato.
**Rama:** `chatgpt/fuentes-wfs-20261017`. **Test suite:** GitHub Actions **39024733631, SUCCESS** en HEAD `4ff7bd9512e077d60a3f13736083497954670953`. Los valores se imprimen con los marcadores `DDD_F10_VALENCIA_2023_WFS_GEOMETRY_RESULT` y `DDD_F10_ARAGON_INE_SPATIAL_CANDIDATES` en el log de la suite.

## 1. Comunidad Valenciana (INE WFS `Secciones_2023`)

Tres features `TIPO=SECCIONADO`, `CPRO=46`, CUSEC `4617201001`, `4619401008`, `4619401013`; respuestas originales conservadas en `INE_WFS_VALENCIA_2023_TRES_CUSEC.geojson`. Todas estas **tres** geometrías son individualmente válidas; esto no certifica las 3.503 geometrías de la comunidad ni sustituye el expediente F10 previo.

El cálculo directo de Shapely en el **CRS fuente EPSG:25830** devuelve para los dos pares `intersects=true, touches=true, intersection.area=0`, sin superposición interior. Tras transformar **separadamente las geometrías** con `pyproj Transformer.from_crs(25830,3035)`, la intersección poligonal calculada en EPSG:3035 es:

| Pair | Fuente 25830 | Reproyección 3035 | Límite contrato |
|---|---:|---:|---:|
| 4617201001 / 4619401008 | 0 m² | 11.622500827 m² | 1 m² |
| 4617201001 / 4619401013 | 0 m² | 11.901114392 m² | 1 m² |

**Interpretación:** el solapamiento de esos dos pares en el fichero oficial WFS preservado surge **después** de la reproyección y la representación con segmentos rectos, no aparece como solapamiento del original. Esto respalda una hipótesis de artefacto computacional del método reproyectado que exige validación adicional en el consumidor. El contrato M02 de Valencia actualmente declara `working_crs=EPSG:3035` y `max_precision_overlap_area_m2=1`; según esas reglas hoy el resultado continúa **BLOCKED_GEOMETRY**.

**No** cambiar automáticamente el CRS de admisión, el límite, la geometría, ni conceder excepción; el cambio en el procedimiento de aceptación, si se justifica mediante una prueba general que preserve topología e identidad, es **decisión contractual reservada**, junto con revisión independiente. La comprobación debe repetirse sobre el **snapshot protegido anterior** antes de afirmar que todos los solapes valencianos responden a la misma causa. Los tres WFS de esta entrega no constituyen la reparación de los tres `SECCIONADO` inválidos restantes del WFS provincial alternativo.

## 2. Aragón (2025→2026)

Fuente: INE WFS 2.0.0, capas `Secciones_2025` y `SU.VectorStatisticalUnit` (etiqueta 2026), filtro `CUMUN` y `TIPO=SECCIONADO`. Los cuatro GeoJSON oficiales de los municipios `50025` y `22213` se preservan sin modificación en el mismo directorio de este informe. Por código:

- Municipio 50025: tres secciones 2025, cuatro 2026, `5002501003` nueva. Su geometría 2026 se superpone a `5002501002` 2025 en **87.8507318%** y a `5002501001` 2025 en **12.1492682%**, total de superficie del código nuevo cubierta por las antiguas **100%**.
- Municipio 22213: tres secciones 2025, dos 2026; `2221301003` desaparece. La geometría 2025 queda cubierta al **100%** por `2221301002` de 2026.

Esto acredita coincidencia geométrica y la dirección espacial del cambio, **NO** transferencia de votos: para 5002501003 hay dos secciones 2025 afectadas, por lo que no existe correspondencia biunívoca automática. La conservación de votos y la adscripción del resultado electoral a 2025 siguen requiriendo documento de la administración electoral o regla posterior expresamente aprobada.

## 3. Andalucía y Castilla y León — Identidades

`IDENTIDADES_INE_2025_2026_F10.json` contiene los resultados de las consultas oficiales a las ocho provincias andaluzas y ocho municipios afectados por Aragón/Castilla y León. Recuentos INE Andalucía 2025=6029 y 2026=6045, con 25 altas y 9 bajas. El dataset electoral SIEL de 2026 declara **6044**, diferencia **1** frente a la capa INE anual consultada. No asumir que la edición anual equivale al censo electoral del 17/05/2026.

Los nueve CUSEC conflictivos de Aragón y Castilla y León están contrastados individualmente en WFS de 2025 y 2026. Para Castilla y León faltan las relaciones administrativas/atribución electoral verificadas de cinco códigos `electoral-only` y dos `map-only`; los votos CERA permanecen separados.

## 4. Estado tras esta entrega

- `SOURCE_ACCREDITED` para las identidades observadas directamente en WFS bajo las dos ediciones, **solo** en el alcance descrito.
- `CROSSWALK_ACCREDITED`: **NO** para Aragón, Andalucía ni Castilla y León.
- `EXCEPTION_APPROVED`: **NO**.
- F10 puertas anteriores **sin elevar**.
- `generation_authorized=false`; ninguna producción ni publicación.

**Pruebas:** `tests/test_valencia_wfs_2023_diagnostico.py` y `tests/test_ine_wfs_aragon_multiyear_diagnostico.py`.

