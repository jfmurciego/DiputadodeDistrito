# N08 — Aprobación institucional y promoción controlada del contrato

Estado del expediente: **APPROVED_BY_OWNER para siete reglas generales**.
Estado de la implementación en esta PR: **CANDIDATO_EN_REVISION**.
Fecha: 2026-10-13. Acta: `ACTA_APROBACION.json` (`N08-OWNER-20261013-7RULES`).

El archivo `PROPUESTA_DECISIONES.json` conserva su estado histórico
`NOT_APPROVED` porque registra la propuesta **antes de la decisión**.
El acta posterior es la evidencia de la aprobación expresada por el propietario.
No se retrodata ni modifica la propuesta histórica.

## Contrato 0.4 candidato

Se aprueban como reglas institucionales generales:

- CUSEC INE 2025 completa como unidad mínima indivisible.
- Contigüidad física con frontera compartida lineal positiva en los polígonos originales, sin fabricar pasarelas ni mezclar provincias.
- Centro operativo `P_i/K_i`, tolerancia ordinaria ±15 %, con ratios `0.85 / 1.15 / 0.15`. La referencia 120.000 sigue siendo la utilizada para calcular el K institucional.
- Municipios completos si son compatibles con las restricciones; cortes imprescindibles solo por CUSEC completas, minimizados como prioridad secundaria.
- Islas, enclaves y discontinuidades físicas conservan su identidad real; cualquier discontinuidad excepcional de distrito requiere evidencia y decisión *nominal*, no una autorización de clase.

Estos siete valores pasan al objeto `decisions` del contrato candidato
`territorios/congreso/contrato_congreso_2026.json` con `APPROVED` y
`decision_id=N08-OWNER-20261013-7RULES`.

Se conserva sin alterar la decisión N06 `K=407` y las cuotas por unidad de
origen. Las 52 unidades administrativas no son 52 circunscripciones
uninominales: los 407 distritos son la unidad de representación.

## Cambios técnicos

El validador `ddd_core/congreso_contract.py` extiende el esquema cerrado
exactamente a `decisions.population_limits.value`, rechazando:

- Campos adicionales, omitidos o mal tipados.
- `bool`, `NaN`, infinito, ratios negativos o incoherentes con la tolerancia.
- Una política con `APPROVED` pero sin valor o sin `decision_id`.
- Discrepancia entre `minimum_unit` superior y la decisión anidada.

No introduce un valor por defecto en el motor ni toma configuraciones del
gestor de los 19 territorios autonómicos.

## Bloqueos que sobreviven a la aprobación

**No hay excepciones individualizadas aprobadas.** El registro está vacío.
Siguen sin acreditación nominal las discontinuidades municipales, componentes
de islas y enclaves, y posibles desviaciones poblacionales excepcionales.

`production_blockers()` conserva la exigencia nacional 52/52.
`validate_production_admission()` y `execution_authorization()` no habilitan
la producción. `generation_authorized=false`, y no hay orden de ejecutar.

### Linaje de productos N08

El producto
`docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto/manifest.json`
contiene un `contract_sha256` correspondiente al contrato anterior.
**Este SHA es evidencia histórica y no debe sobrescribirse** con el SHA del
contrato candidato 0.4. El expediente de Cáceres PR #256 permanece veraz para
la versión de contrato bajo la que se ejecutó.

Para comprobar íntegramente los **26 hashes históricos** se han conservado
las copias exactas de los tres archivos que evolucionaron:

- `legacy/n08_caceres_20261012/congreso_contract_v1_1.py`
- `legacy/n08_caceres_20261012/contrato_congreso_2026_v0_3.json`
- `legacy/n08_caceres_20261012/test_preflight_caceres_n08_v1.py`

La regresión de Cáceres contrasta las rutas históricas contra estas copias,
sin modificar los registros del manifiesto. Asimismo, las pruebas sobre la
puerta histórica usan explícitamente el contrato antiguo para justificar
`WAIT_OWNER` de aquel momento; la aprobación N08 nueva se prueba por
separado, sin corregir retrospectivamente el pasado.

Actualizar el contrato cambia su identidad, por lo que los validadores que
requieran coincidencia exacta con el contrato original deben mantenerse
fail-closed hasta que exista:

1. Acreditación de equivalencia de fuentes, K y restricciones aplicables.
2. Nueva vinculación explícita del contrato aprobado con producto N08, con
   manifiesto de transición **nuevo**, sin modificar los anteriores.
3. Pruebas completas de los consumidores de las puertas y auditoría independiente.
4. Confirmación de que el nuevo expediente sigue `generation_authorized=false`.

La presente PR **no efectúa ninguna renovación de ese linaje** ni convierte
los fixtures M05/M06 en resultados reales.

## Condición de integración

CI verde y revisión independiente del HEAD exacto. La aprobación de las
siete reglas **no equivale a autorizar el merge**, el ensayo real M04–M06,
la acreditación de excepciones o la publicación de distritos.
