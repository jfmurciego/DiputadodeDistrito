# Congreso DDD — propuesta de siete decisiones institucionales

**Expediente N08-7-DECISIONS-20261013. Estado: `NOT_APPROVED`.**
Referencia: `main@c1449aa65fd391b77314441a6567163c1af92fe1`.
No modifica ni sustituye `territorios/congreso/contrato_congreso_2026.json`.
Ninguna política se considera aprobada por abrir o fusionar esta PR.
`generation_authorized=false`.

## Distinción institucional necesaria

Las **52 provincias y ciudades autónomas** son unidades **administrativas de origen y cálculo de cuota**, no circunscripciones uninominales. Los **407 distritos electorales** resultantes son las circunscripciones uninominales, cada una representada por un diputado. K=407 procede de la decisión N06 aprobada y no se revisa aquí. La referencia política de 120.000 habitantes gobierna el cálculo de K, pero no reemplaza la media provincial `P_i/K_i` como centro operativo propuesto.

## Paquete recomendado — siete votos explícitos

| Decisión del contrato | Propuesta institucional | Puerta de seguridad |
|---|---|---|
| `minimum_unit` | **CUSEC oficial íntegra de 2025**. Una sección pertenece a un único distrito, incluso si es MultiPolygon | Nunca fraccionar electores ni imputar población por superficie de sus partes |
| `contiguity` | **Contacto físico mediante frontera lineal positiva** entre polígonos originales; ni puntos ni pseudoaristas | Las excepciones geográficas exigen acto individual expreso y jamás se fabrican puentes |
| `population_limits` | **±15 % de `P_i/K_i`**, límites duros ordinarios; no ±15 % de 120.000 fijo | Fuera de intervalo únicamente con excepción nominativa aprobada; K intacto |
| `municipal_indivisibility` | **Preservar municipios cuando sea posible; admitir cortes necesarios por CUSEC completa** y minimizarlos después de restricciones duras | Ni indivisibilidad absoluta ni troceo arbitrario de una sección |
| `islands` | Conservar islas e islotes como componentes reales; **agrupación electoral discontinua solo si hay excepción nominal** | Sin puentes sobre agua ni cruzar fronteras provinciales |
| `enclaves` | Conservar el municipio en su provincia administrativa; **acreditar cada enclave y su posible excepción** | Valle de Villaverde no se conecta por Vizcaya |
| `physical_discontinuities` | Registro de excepciones por edición, geometría, CUSEC y componentes, con caducidad verificable | La sección multipartes no funciona como pasarela artificial |

La propuesta tiene **reglas generales**, no una lista de excepciones ya autorizadas. El registro `approved_cases=[]` es intencionadamente vacío.

## Equilibrio poblacional: definición ejecutable, pendiente de aprobación

Para cada origen administrativo `i`, con población oficial `P_i` y cuota aprobada `K_i`:

- Centro territorial: `T_i=P_i/K_i`.
- Suelo ordinario entero: `ceil(17 P_i/(20 K_i))`.
- Techo ordinario entero: `floor(23 P_i/(20 K_i))`.
- Valores propuestos para el consumidor `hard_limits`: `population_floor_ratio=0.85`, `population_cap_ratio=1.15`, `target_tolerance_ratio=0.15`.
- La comparación y el redondeo se harán con aritmética exacta; no se corregirán violaciones duras calificándolas como tolerancia.

En municipios o partes geográficamente excepcionales, **no existe excepción numérica automática**. La excepción debe identificar distrito/componente, valor y fundamento; en caso contrario la salida sigue `BLOCKED`.

**Consecuencia para K=1:** la media provincial es toda su población; Ávila, Soria, Ceuta o Melilla pueden quedar fuera de la banda fija respecto a 120.000 sin infringir por ello la banda provincial propuesta. El desvío respecto de la referencia política debe informarse; esto no suprime la necesidad de revisar la geografía.

## Impacto nacional realmente observado

Fuente: `docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/FACTIBILIDAD_OPCIONES.json`, opción `basis=provincial_mean`, `tolerance=3/20`.

| Condición necesaria examinada | Resultado |
|---|---|
| Unidades bloqueadas por aritmética de componentes seccionales con ±15 % | **16 de 52** |
| Provincias con componentes físicos de partes estrictamente superiores a su K | **9 de 52** |
| Unidades incompatibles con municipio absolutamente indivisible por tamaño o número | **31 de 52** |
| Municipios cuya población supera el techo propuesto | **48** |
| Secciones individuales superiores al techo propuesto | **0** |

Las 16 unidades del primer grupo son `06, 07, 09, 13, 17, 28, 31, 34, 35, 36, 38, 39, 43, 46, 47, 48`. Las nueve del segundo grupo son `04, 07, 09, 15, 17, 27, 30, 34, 36`. Los dos conjuntos miden **condiciones distintas**, y no se suman.

Comparación de las seis opciones observadas:

| Centro | Banda | Bloqueos aritméticos de componentes | Incompatibilidad municipal absoluta |
|---|---:|---:|---:|
| 120.000 fijo | ±10 % | 24 | 33 |
| 120.000 fijo | ±15 % | 22 | 33 |
| 120.000 fijo | ±20 % | 19 | 31 |
| Media provincial | ±10 % | 16 | 33 |
| **Media provincial** | **±15 %** | **16** | **31** |
| Media provincial | ±20 % | 16 | 31 |

**No son soluciones M04.** Los 16 bloqueos aritméticos y los nueve excesos de componentes físicos demuestran la necesidad de decidir excepciones, revisar la interpretación geográfica o evaluar una modificación institucional expresamente autorizada; no justifican modificar K, eliminar partes ni alterar el grafo.

## Contraste antes de decidir

### Cáceres — origen 10, K=3

411 CUSEC, 388.190 habitantes y 1.125 aristas acreditadas por la PR #256. Con ±15 % provincial: **suelo 109.988, techo 148.806** habitantes por distrito. El único componente seccional no contradice esta condición aritmética necesaria, pero **no prueba una partición posible**. Persisten **11 municipios discontinuos** que exigen clasificación y tratamiento; no hay multipartes que crucen componentes, ni solapamientos o vacíos encerrados en el producto N08.

### Cantabria — origen 39, K=5

458 secciones, 593.623 habitantes y 1.208 aristas N08. Con ±15 % provincial: **suelo 100.916, techo 136.533**. El enclave de Valle de Villaverde tiene 249 habitantes y queda separado del cuerpo provincial; asignarlo como distrito ordinario sería incompatible con el suelo. Tres secciones abarcan componentes físicos separados con población por parte desconocida; hay 28 vacíos encerrados pendientes de tipificación. **El régimen general, por sí solo, no desbloquea Cantabria.**

## Registro nominal obligatorio de excepción

Cada caso deberá expresar:

`exception_id, CPRO, CUSEC_or_polygon_part_ids, source_edition, source_sha256, topology_unit_sha256, official_administrative_evidence, physical_geometry_evidence, exception_kind, permitted_discontinuity_scope, owner_decision_id, invalidation_conditions`.

No hay aceptación por pertenecer a una categoría («isla», «enclave», «multipartes»). Cada caso aprobado tiene alcance verificable; cualquier cambio en edición/identidad/hash obliga a revalidarlo. Nunca se infieren puentes ni habitantes de partes por área.

## Defecto de interfaz técnica detectado

`ddd_core/congreso_contract.py` valida objetos anidados mediante esquema cerrado. Actualmente **no contempla** la ubicación de una estructura bajo `decisions.population_limits.value`, mientras que el consumidor M04 necesita exactamente los campos `population_floor_ratio`, `population_cap_ratio`, `target_tolerance_ratio`.

Antes de promover la política al contrato productivo se precisa una **extensión tipada y cerrada** de esa estructura, con pruebas de rechazo a campos o razones inválidas. Este expediente no realiza esa promoción ni fija silenciosamente ratios en el motor.

## Orden de decisiones y siguientes puertas

1. El propietario aprueba o enmienda **expresamente las siete reglas generales** y determina si permite ensayos provinciales aislados sin `NATIONAL_READINESS` completo, siempre con autorización de ejecución separada.
2. Work registra la decisión institucional **sin alterar N06** y solicita implementar validador tipado, excepciones nominales y preflight actualizado; CI y revisión independiente obligatorias.
3. Las anomalías relevantes se acreditan por provincia. Cantabria requiere atención especial; Cáceres es candidato de ensayo por su topología comparativamente sencilla.
4. Se ejecuta nuevamente el diagnóstico y solo con **nueva orden concreta** podrá lanzarse M04–M06 sobre datos reales. No se publica ningún mapa sin autorización adicional.

El presente paquete **no es una orden ni una autorización de generación**.
