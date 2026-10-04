# Normalización geométrica territorial

## Propósito

La preparación territorial conserva la respuesta oficial sin modificar y, cuando la política común lo permite, produce un derivado geométrico trazable. La capacidad no contiene reglas por territorio, año ni identificador seccional.

La política ejecutable está en `configuracion/politica_normalizacion_geometrica.yaml`. Su huella SHA-256 se incorpora a la evidencia de cada ejecución.

## Etapas y atribución del defecto

1. **Raw oficial**. Para OGC live se preservan los bytes HTTP exactos por provincia antes de JSON, Shapely o GeoPandas. Para snapshots se conserva la identidad y huella de la copia verificada.
2. **Raw decodificado**. Se identifica cada geometría por sección, tipo, motivo GEOS, huella canónica y CRS. Un defecto aquí se atribuye a la fuente decodificada, no a la materialización.
3. **Normalización derivada**. Sólo se aplican métodos admitidos por la política.
4. **Materialización**. El derivado se escribe a Shapefile y se relee. Identidad, atributos, CRS, geometría y tipos se vuelven a validar. Un defecto nuevo aquí se atribuye a `POST_SHAPEFILE_WRITE_READBACK`.

El raw nunca se sobrescribe.

## Política de aceptación automática

Se admiten tres clases de operación:

- eliminación de componentes `MultiPolygon` exactamente duplicados;
- eliminación de anillos interiores exactamente duplicados;
- auto-intersecciones sólo cuando `make_valid(linework)` y `make_valid(structure)` producen el mismo conjunto poligonal válido y la frontera del raw se conserva exactamente como conjunto.

`make_valid()` por sí solo no constituye evidencia suficiente. Si los dos algoritmos discrepan, si aparece un componente no poligonal, si cambia la frontera, si la clase de invalidez no está admitida o si la prueba no es concluyente, el caso permanece bloqueado.

No se permiten snapping, puentes, relleno de fronteras, eliminación de secciones, allowlists ni excepciones por territorio.

## Tolerancias y unidades

La tolerancia semántica de aceptación es **nula**: `numeric_acceptance_tolerance: null`. No se ajusta ningún umbral para los incidentes observados.

Las magnitudes métricas de diagnóstico se calculan en **ETRS89 / LAEA Europe (EPSG:3035)**, con metros y metros cuadrados. Esas magnitudes documentan el cambio; no sustituyen las pruebas topológicas exactas ni actúan como umbrales de aprobación.

El área de una geometría inválida no se usa como prueba de equivalencia porque su interpretación puede no ser fiable. Para auto-intersecciones se exige evidencia adicional independiente: consenso entre algoritmos válidos y conservación exacta de frontera.

## Validaciones de conjunto

La decisión común comprueba:

- identidad y número de secciones;
- atributos no geométricos y cobertura provincial;
- población, si está embebida como atributo; cuando población y geometría son fuentes separadas, la compatibilidad sigue en la puerta territorial existente;
- geometrías nulas o vacías y tipos resultantes;
- validez del derivado;
- solapes de área entre secciones;
- contactos de las secciones modificadas con sus vecinas;
- número de componentes;
- identidad tras escritura/lectura del Shapefile y equivalencia de CRS.

### Huecos

La fuente de secciones no aporta una máscara territorial autoritativa independiente. Por tanto, esta etapa **no afirma** que todo hueco global sea erróneo ni que pueda distinguir un hueco legítimo de uno ilegítimo sólo a partir del mismo seccionado. La evidencia registra esta comprobación como `LIMITED`.

Lo que sí exige la aceptación es que una reparación no cambie la frontera fuente ni los contactos de las secciones afectadas. Una comprobación global de huecos contra una máscara administrativa independiente deberá incorporarse cuando ese contrato exista; hasta entonces no se presenta como validación superada.

## Evidencia durable

Cada derivación genera `.ddd-sources/geometry_normalization/<source_id>_<year>.json` con:

- identidad de las respuestas raw y sus SHA-256, o identidad del snapshot;
- política y SHA-256 de la política;
- versiones de GeoPandas, Shapely, GEOS, pyproj y pyogrio;
- identificadores afectados, diagnóstico antes/después, método y parámetros;
- huella del derivado;
- decisión de validación;
- cambios espaciales/topológicos y limitaciones explícitas;
- resultado de la validación posterior a materialización.

El inventario y el manifiesto de procedencia existentes enlazan a esta evidencia mediante `derivation`.

## Incidentes del 3–4 de octubre de 2026

Los siete runs históricos con 13 geometrías inválidas se recuperaron sin relanzar adquisiciones. Sus artefactos diagnósticos conservan conteos y URLs, pero no los bytes OGC de seccionado ni el diagnóstico por feature. En consecuencia, para esos 13 slots históricos no es posible reconstruir honestamente CUSEC, motivo GEOS ni hash raw a partir de los artefactos existentes.

Esa ausencia se mantiene como evidencia de limitación, no se rellena mediante una nueva descarga ni mediante inferencia. La capacidad común evita que vuelva a ocurrir en futuras preparaciones.
