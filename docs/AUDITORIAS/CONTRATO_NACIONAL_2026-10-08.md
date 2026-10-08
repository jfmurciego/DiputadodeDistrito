# Recuperación del contrato de distritos nacionales

**Versión:** 1.0.0
**Nombre:** Evidencia nacional y bloqueo institucional
**Fecha:** 2026-10-08
**Alcance:** frente Distritos nacionales; diagnóstico y compatibilidad local
**Estado:** diagnóstico; no es un contrato aprobado ni habilita generación
**Cambios:** inventario de reglas acreditadas, incógnitas y componentes reutilizables
**Motivo:** separar la distritación de la Nación de la campaña autonómica
**Origen:** encargo del Director; documento nuevo, sin predecesor
**Base examinada:** `2d8508a04f9b54efa05dbb0c2ee7f1d60f81dfce`, rama `codex/distritos-nacionales`; worktree inicialmente limpio y base efectiva igual a `main` local.

## Resultado y fuentes

No se ha localizado en esta base un contrato ejecutable de distritación de la Nación. Sí existe un contrato territorial común que admite ámbito nacional. No se reconstruye ninguna decisión institucional a partir de los parámetros autonómicos.

Fuentes locales examinadas:

- `../AGENTS.md`, secciones 1, 3 y 9: el frente nacional construye la división de la Nación española; no permite trasladar K ni restricciones autonómicas.
- `docs/CONTRATO_TERRITORIO.md`, versión 1.2.0, secciones 1–8: identidad, unidad mínima, fuentes, K y reparto, restricciones y pruebas deben declararse; un bootstrap no habilita generación.
- `docs/POLITICA_K_LIMITES_Y_ESQUEMA.md`, versión 1.0.0: K requiere decisión previa independiente del resultado; el origen histórico no registrado no es regla para una implantación nueva.
- `docs/ARQUITECTURA_MULTI_TERRITORIO.md` y `docs/ARQUITECTURA_DEL_PROCEDIMIENTO.md`: motor común y separación entre cálculo territorial y electoral.
- `docs/POLITICA_TOPOLOGIA_TERRITORIAL.md` y `configuracion/politica_topologia_territorial_2025.yaml`: evidencia topológica existente y tratamiento declarado de discontinuidades; no acreditan un reparto nacional.
- `configuracion/catalogo_territorios_espana_2025.yaml` y `configuracion/politica_generacion_territorial_2025.yaml`: 19 entradas autonómicas/ciudades autónomas; ninguna entrada de la Nación. Los K son tamaños de las cámaras respectivas, incluidas las asambleas de Ceuta y Melilla.
- `docs/SALIDAS_CHATGPT/HITOS/2026-09-12_H005_BOOTSTRAP_NACIONAL.md`: observación M01–M03 por territorios, no partición nacional.
- `docs/PREINSCRIPCION_OSF.md`: estudio de Aragón, con campos pendientes; no especificación nacional. Las capturas locales de `fuentes/normativa/` corresponden a Andalucía y Extremadura, no al Congreso.

Contraste normativo mediante lectura web del BOE el 2026-10-08, sin adquisición de datasets ni incorporación de documentos externos al repositorio:

- [Constitución, artículo 68](https://www.boe.es/buscar/act.php?id=BOE-A-1978-31229#a68): tamaño del Congreso entre 300 y 400; circunscripción provincial, un diputado por cada ciudad autónoma y representación proporcional.
- [LOREG, artículos 161–162](https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672#acientosesentayuno): 350 escaños; dos iniciales por provincia y uno por cada ciudad autónoma. Los 248 restantes se distribuyen por población provincial mediante cocientes enteros y mayores fracciones; la convocatoria fija el reparto.

Estas normas acreditan el sistema electoral del Congreso, no una partición DDD uninominal. Tomar únicamente su tamaño institucional o reproducir su reparto son decisiones diferentes que deben quedar registradas. No se ha seleccionado convocatoria ni reparto legal de referencia.

## Reglas: acreditación e incógnitas

| Dimensión | Acreditado | Pendiente para el contrato DDD nacional |
| --- | --- | --- |
| Ámbito | La Nación española es un ámbito distinto de las comunidades, según el encargo y AGENTS. | Identificador, universo geográfico exacto y cobertura verificable de sus unidades, incluidos archipiélagos, Ceuta y Melilla. |
| Unidad mínima | El contrato común exige unidad indivisible y clave estable; las implantaciones actuales usan secciones censales. | Decisión nacional sobre unidad mínima y atomicidad; no se acredita por analogía con Aragón. |
| K institucional | La LOREG fija 350 escaños del Congreso. | Adoptar explícitamente ese tamaño como K DDD, o identificar otra decisión institucional documentada. No sumar K autonómicos. |
| Población | El sistema legal reparte por población provincial; el contrato común exige fuentes, año y checksum. | Año y edición compatibles de población/geometría, universo, totales acreditados y target nacional o por partición. |
| Contigüidad | El contrato común exige declararla; existe preflight físico/operativo. | Regla nacional, criterio de adyacencia y acreditaciones aplicables. No inferirlos de un valor por defecto. |
| Disciplina administrativa | El sistema legal utiliza provincias; el contrato común exige barreras, reparto y atomicidad explícitos. | Mantener o sustituir reparto legal, barreras provinciales/autonómicas, indivisibilidad municipal y tratamiento de ciudades grandes. |
| Discontinuidades | Existen herramientas para componentes físicos y evidencia administrativa; la legislación trata separadamente Ceuta y Melilla. | Cuotas y excepciones nacionales de islas, enclaves/exclaves y ciudades autónomas, con autoridad y evidencia. No reutilizar automáticamente excepciones de suelo autonómicas. |
| Equilibrio | El contrato común publica perfil general 0.80/1.75/0.12, que debe declararse expresamente. | Su aplicación nacional y target de referencia; cualquier excepción exige expediente previo. |

## Estado real y reutilización

`herramientas/gestor_campana_nacional.py` coordina ejecuciones por entrada territorial y sus resultados. `tests/test_materializacion_contratos_nacionales.py` prueba la materialización de los contratos de esas entradas. Ninguno acredita una división única de la Nación ni una agregación válida de mapas autonómicos.

`herramientas/materializar_contrato_generacion.py` exige una entrada única del catálogo y una política correspondiente antes de materializar K. `ddd_core/territory_contract.py` exige coincidencia de catálogo, YAML y módulos. El valor por defecto `scope=national` del cargador `ddd_core/config.py` es metadato de configuración, no una decisión institucional ni una prueba de cobertura.

| Componente | Reutilización posible sin cambiar su semántica | Límite comprobado |
| --- | --- | --- |
| `ddd_core.territorial_validation` | Interpretación estricta de población; comprobación de claves y geometrías. | No selecciona universo, edición ni unidad mínima. |
| `ddd_core.config` y `ddd_core.territory_contract` | Carga, límites explícitos, trazabilidad y coherencia contractual. | La admisión usa catálogo español, códigos provinciales y contrato completo; no acredita por sí sola las decisiones nacionales. |
| `ddd_core.topology_preflight` y M02–M03 | Diagnóstico de contactos y componentes; contraste de evidencias antes del cálculo. | Las acreditaciones dependen de fuente y ámbito; los roles operativos son provincia/municipio. No convierte proximidad en autorización de arista. |
| M04 y `ddd_core.m04_partition_contract` | Potencial reutilización con cuotas y barreras compatibles. | El validador impone un único código provincial por distrito y cuotas exactas; no es neutral ante distritos interprovinciales. |
| M05–M06 y separación M07–M08 | Optimización, consolidación y agregación electoral posterior sobre un contrato compatible. | No se ha probado compatibilidad nacional de extremo a extremo; faltan contrato, fixtures y baseline nacional. |

Dependencias declaradas: un futuro contrato nacional necesita fuentes acreditadas del frente Fuentes oficiales y capacidades del motor compartido con Distritos autonómicos. Este incremento no copia cambios de esos frentes ni altera sus contratos, código, catálogo o resultados.

## Incremento local y evidencia

El incremento conseguido es este expediente contractual, con una comprobación económica de componentes existentes. No se implementa un validador nacional que complete reglas ausentes ni se declara un producto nacional funcional.

Pruebas sobre el código de la base, usando Python 3.11 local:

- `python3 -m unittest discover -s tests -p test_m04_engine_contract.py`: **PASS**, 3 pruebas de identidad, entrypoints y composición del motor canónico; no ejecutan generación.
- Comprobación sintética reproducible siguiente: **PASS**, 9 casos de población y 3 de contacto. El umbral de 1 m es un parámetro del fixture, no una regla nacional aprobada.
- `python3 -m unittest discover -s tests -p test_territory_contract_admission.py` y `test_catalogo_territorios_espana.py`: **NO EJECUTADAS**, fallo de importación por `ModuleNotFoundError: yaml`.
- `python3 -m unittest discover -s tests -p test_territorial_data_boundaries.py`: **NO EJECUTADA**, fallo de importación por `ModuleNotFoundError: geopandas`.

Los fallos de importación son ambientales y anteriores a este documento; no demuestran regresión productiva. No se instalaron dependencias. No se ejecutaron suite completa, CI, módulos territoriales ni optimizadores.

```sh
python3 - <<'PY'
from ddd_core.territorial_validation import parse_population_value, TerritorialDataError
from ddd_core.topology_preflight import evaluate_topology_preflight
for raw, expected in [(0, 0), (123, 123), ('1.234', 1234), ('1,234', 1234)]:
    assert parse_population_value(raw) == expected
for raw in [None, True, -1, 1.5, 'desconocida']:
    try:
        parse_population_value(raw)
    except TerritorialDataError:
        pass
    else:
        raise AssertionError(raw)
units = {k: {'province': '01', 'municipality': '001', 'multipart': False} for k in ['a', 'b']}
for length, decision in [(0.0, 'NEEDS_POLICY'), (0.5, 'NEEDS_POLICY'), (10.0, 'READY')]:
    report = evaluate_topology_preflight(units=units, contacts=[{'u': 'a', 'v': 'b', 'shared_border_m': length}], bridges=[], min_shared_border_m=1.0, productive_continental=True)
    assert report['decision'] == decision, report
print('PASS: 9 casos de población y 3 casos de frontera sintéticos')
PY
```

Política de versiones 1.3.0: documento nuevo con versión, nombre, fecha, alcance, estado, cambios, motivo y origen; no sustituye ningún fichero existente, por lo que no hay predecesor que preservar en `legacy/`. El registro del incremento queda en este expediente y su commit local. No hay cambio funcional ni de comportamiento territorial: las obligaciones de CI, run y regresiones territoriales del procedimiento de cambio funcional no se presentan como cumplidas ni se activan mediante una modificación del motor. Una implementación posterior debe evaluarlas antes de editar código. No se promueve ni certifica ningún producto.

La revisión con `ddd-revisor` debe limitarse a este expediente y a la evidencia indicada; su dictamen no equivaldrá a aprobación del contrato nacional pendiente.

## Bloqueo y alternativas para el Director

**Bloqueo preciso:** falta la decisión nacional ex ante que vincule tamaño institucional, reparto/barreras, unidad mínima, población de referencia y discontinuidades. El contrato común enumera esos requisitos, pero no los resuelve para la Nación. Por ello no se puede validar honestamente un YAML nacional de producción.

Alternativas, sin adoptar ninguna:

1. Aportar un contrato o estudio nacional ya aprobado que no figure en esta base, con su autoridad y versión; contrastarlo y materializar una prueba de admisión local.
2. Aprobar un contrato DDD nacional que tome sólo el tamaño institucional del Congreso y declare una política propia de reparto, barreras y componentes. No basta con indicar K=350.
3. Aprobar un contrato que conserve además el reparto legal de una convocatoria identificada, especificando qué significa subdividir cada circunscripción en distritos DDD y cómo trata discontinuidades y equilibrio.

El siguiente incremento, una vez exista esa decisión, será un fixture mínimo y pruebas positivas/negativas de admisión nacional, antes de cualquier generación. No se propone rediseñar el motor ni agregar los distritos autonómicos.
