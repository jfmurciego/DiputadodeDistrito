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

La tolerancia semántica de aceptación de la **normalización** es **nula**: `numeric_acceptance_tolerance: null`. No se ajusta ningún umbral para los incidentes observados. Cuando el consumidor territorial ya declara una tolerancia de precisión para su propia semántica de adyacencia, esa regla puede reutilizarse exclusivamente en el control separado de admisibilidad de fuente y se registra como tal.

Las magnitudes métricas de diagnóstico se calculan en **ETRS89 / LAEA Europe (EPSG:3035)**, con metros y metros cuadrados. Esas magnitudes documentan el cambio; no sustituyen las pruebas topológicas exactas ni actúan como umbrales de aprobación.

El área de una geometría inválida no se usa como prueba de equivalencia porque su interpretación puede no ser fiable. Para auto-intersecciones se exige evidencia adicional independiente: consenso entre algoritmos válidos y conservación exacta de frontera.

## Dos controles distintos

La puerta común separa dos decisiones que no deben volver a confundirse.

### 1. Seguridad de la normalización

Responde únicamente a si la transformación conserva el producto fuente: identidad, atributos, cobertura declarada y topología. Los solapes y contactos se comparan **por pareja de secciones** antes/después mediante geometría exacta. Se clasifican solapes nuevos, aumentados, reducidos o desplazados y contactos añadidos, retirados o desplazados.

Un solape preexistente que permanece exactamente igual no es, por sí solo, un fallo de normalización. Tampoco queda automáticamente aceptado como defecto de fuente: pasa al segundo control.

Si una operación sobre el raw inválido no permite obtener un baseline fiable, el cálculo se registra como `PAIR_BASELINE_NOT_EVALUABLE`. Nunca se sustituye por cero. Sólo puede cerrarse con evidencia alternativa ya exigida por la política —prueba exacta de conjunto o consenso independiente de reparación con frontera fuente exacta—; en ausencia de esa evidencia la normalización queda bloqueada.

### 2. Admisibilidad del defecto de fuente

Responde a si un defecto que ya estaba en la fuente es compatible con el **consumidor territorial declarado**.

- Para `target_sectioning`, los solapes preexistentes se contrastan pareja por pareja con el contrato vigente de `modulo_02_construir_adyacencias`. Si el predicado es `contact`, la admisibilidad del defecto de precisión reutiliza exclusivamente el `max_precision_overlap_area_m2` ya declarado y lo mide en el `working_crs` efectivo del consumidor. Separadamente se reproduce el predicado completo de M02 —incluida `min_shared_border_m`— y se registra si la pareja produciría una arista (`GEOMETRIC_EDGE`) o no (`NO_EDGE_UNDER_DECLARED_CONSUMER`). Un solape submétrico puede por tanto ser admisible como defecto de precisión sin inventar una adyacencia. No se crea ni ajusta ninguna tolerancia en esta capa y el CRS diagnóstico global no se confunde con el CRS del consumidor.
- Para `population_sectioning_origin`, la geometría se consume conjuntamente con población y seccionado objetivo. La admisibilidad queda `DEFERRED_TO_CONSUMER_GATE`, pero el `READY` general de correspondencia no basta: `geometry_admissibility` debe ser `READY`. Cada pareja con defecto original debe quedar ligada a destinos geométricamente idénticos uno-a-uno, conservar exactamente la relación espacial tras el mapeo y corresponder a una pareja del seccionado objetivo ya admisible para su consumidor territorial. La procedencia INE o la mera ausencia de cambios no sustituyen esa evidencia.

El `decision` global permite materializar sólo cuando la normalización es segura y el segundo control permite staging. La ausencia de `declared_use` es fail-closed: puede existir `normalization_safety=READY`, pero `source_admissibility=NOT_EVALUATED` no produce `READY` global. Un `DEFERRED_TO_CONSUMER_GATE` no certifica la fuente: habilita únicamente llegar a la puerta obligatoria que debe emitir `geometry_admissibility=READY` o bloquearla.

## Validaciones de conjunto

La evidencia comprueba:

- identidad y número de secciones;
- atributos no geométricos y cobertura provincial;
- población, si está embebida como atributo;
- geometrías nulas o vacías y tipos resultantes;
- validez del derivado;
- solapes antes/después por pareja, con huella y área métrica diagnóstica;
- contactos antes/después por pareja, con huella y longitud métrica diagnóstica;
- limitaciones de baseline y evidencia alternativa, cuando exista;
- número de componentes;
- identidad tras escritura/lectura del Shapefile y equivalencia de CRS.

Las magnitudes métricas de la normalización siguen sin ser umbrales de aceptación. Sólo la admisibilidad de fuente puede reutilizar reglas ya existentes del consumidor territorial. El área de solape se usa únicamente contra el techo de precisión ya declarado; la frontera compartida se registra para evaluar por separado el efecto sobre la adyacencia. Procedencia, CRS, área, frontera compartida y efecto M02 quedan auditados por pareja.

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

Para pares cross-year esa referencia no es nominal: la puerta abre el `derivation.path` dentro del paquete congelado, verifica el SHA-256 declarado, valida `schema/source_id/source_year/decision`, exige que el bloque `derived` coincida con el ZIP de seccionado materializado (ruta, bytes y SHA-256) y usa `normalization` del JSON durable como fuente del audit. La copia inline de `content_checks.geometry_normalization` debe ser idéntica; cualquier ausencia o divergencia bloquea reutilización y compatibilidad.

## Incidentes del 3–4 de octubre de 2026

Los siete runs históricos con 13 geometrías inválidas se recuperaron sin relanzar adquisiciones. Sus artefactos diagnósticos conservan conteos y URLs, pero no los bytes OGC de seccionado ni el diagnóstico por feature. En consecuencia, para esos 13 slots históricos no es posible reconstruir honestamente CUSEC, motivo GEOS ni hash raw a partir de los artefactos existentes.

Esa ausencia se mantiene como evidencia de limitación, no se rellena mediante una nueva descarga ni mediante inferencia. La capacidad común evita que vuelva a ocurrir en futuras preparaciones.
