# Puerta geométrica posterior a #214 — verificación y política corregida

Fecha: 2026-10-04  
Base de trabajo revisada: `main@68dde5b2f73e7bd587fac123133eac8405c8e5df`  
Commit que introdujo la puerta investigada: `d4f8b84769290aa252498399b66ba90c37b44612` (#214)

## Causa demostrada

#214 mezcló dos preguntas distintas:

1. si una normalización modifica identidad, cobertura o topología;
2. si un defecto ya presente en la fuente es admisible para el consumidor territorial.

La implementación exigía `candidate_overlap_count == 0` para declarar `topology_ready`. Por ello un solape original e inalterado convertía la normalización completa en `BLOCKED`, incluso cuando no se había modificado ninguna sección.

La política corregida no considera un solape preexistente como éxito ni como fallo de normalización por el mero hecho de existir. Primero exige conservación exacta antes/después por pareja; después evalúa el defecto original contra el uso declarado.

## Política

### Control A — seguridad de la normalización

Se conserva como condición dura:

- identidad y orden de secciones;
- atributos no geométricos;
- cobertura declarada;
- validez poligonal del derivado;
- evidencia de cobertura por sección sin usar el área de un raw inválido como equivalencia;
- relaciones de solape y contacto antes/después por **pareja de secciones**.

Cada relación conserva geometría y huella. Los solapes se clasifican como `NEW`, `INCREASED`, `DECREASED`, `DISPLACED_OR_RESHAPED`, `REMOVED` o `PRESERVED`. Los cambios de contacto se detectan también por geometría, por lo que un desplazamiento con la misma suma de áreas no queda oculto.

Si una geometría raw inválida hace fallar una operación de baseline, se registra `PAIR_BASELINE_NOT_EVALUABLE`. Nunca se sustituye el error por área cero. Sólo se permite cerrar esa limitación mediante evidencia alternativa ya exigida por la política de reparación: igualdad exacta de conjunto/frontera para deduplicaciones o consenso independiente de reparación con conservación exacta de frontera para auto-intersecciones. Sin esa prueba, la normalización bloquea.

La tolerancia semántica de normalización sigue siendo `null`.

### Control B — admisibilidad del defecto original

Un defecto original no se acepta por provenir del INE ni por permanecer inalterado.

Para `target_sectioning`, los solapes originales se evalúan **pareja por pareja** contra el contrato vigente de `modulo_02_construir_adyacencias`. Cuando el territorio declara `predicate: contact`, la admisibilidad de precisión exige que el solape no supere el `max_precision_overlap_area_m2` ya declarado y se mide en el CRS efectivo del consumidor. Separadamente se reproduce el predicado completo de M02 para registrar si esa pareja generaría o no una arista. Así, un defecto submétrico puede ser admisible sin crear una adyacencia inexistente. El CRS se resuelve con el mismo fallback que M02; esas reglas son preexistentes del consumidor, no tolerancias nuevas de normalización.

Para `population_sectioning_origin`, la fuente no se certifica aisladamente. La adquisición sólo puede dejarla `DEFERRED_TO_CONSUMER_GATE`; el informe temporal debe emitir además `geometry_admissibility=READY`. Cada pareja con defecto original debe quedar ligada a destinos geométricamente idénticos uno-a-uno, conservar exactamente su relación espacial y corresponder a una pareja del seccionado objetivo ya admisible para su consumidor territorial. Un `READY` de conservación de población por sí solo no acredita el defecto.

La ausencia de `declared_use` es fail-closed: `normalization_safety` puede ser `READY`, pero la decisión global no lo es mientras `source_admissibility` permanezca `NOT_EVALUATED`.

## Verificación sobre los artefactos existentes

No se lanzó ningún territorio ni workflow. Se usaron exclusivamente los artefactos diagnósticos de los runs indicados, todos producidos sobre `d4f8b84769290aa252498399b66ba90c37b44612`.

| Territorio | Run | Fuente que bloqueó #214 | Evidencia #214 | Comparación antes/después | Normalización segura | Admisibilidad de fuente con política corregida | Bloqueo restante |
|---|---:|---|---|---|---|---|---|
| Andalucía | 37214999583 | origen población 2025 | 65 candidatos reportados por #214 (55 con área positiva, 10 contactos de área 0); 0 secciones normalizadas; hash geométrico antes=después; target 2026 sin solapes | transformación nula en el origen | **Sí** | **Diferida en adquisición / no acreditable con estos artefactos en el gate temporal** | los 55 solapes de área positiva del origen no tienen pareja solapada admisible correspondiente en el target 2026; los 10 candidatos de área 0 no se tratan como solape; `geometry_admissibility` debe bloquear hasta nueva evidencia |
| Islas Baleares | 37215005673 | target 2023 | 12 candidatos reportados (8 con área positiva, 4 de área 0); máx. 0,015704 m²; 1 sección normalizada | 0 cambios de solape; 0 cambios de contacto | **Sí** | **Sí** | replay read-only: 12/12 quedan dentro del contrato; las 12 producirían arista M02 |
| Castilla y León | 37215013261 | origen población 2025 | 28 candidatos reportados por #214 (27 con área positiva, 1 de área 0); 0 secciones normalizadas; hash geométrico antes=después; target 2026 sin solapes | transformación nula en el origen | **Sí** | **Diferida en adquisición / no acreditable con estos artefactos en el gate temporal** | los 27 solapes de área positiva del origen carecen de relación destino solapada ya admisible; el candidato de área 0 no se trata como solape y nada se acepta por invariancia |
| Castilla-La Mancha | 37215019634 | target 2023 | 41 candidatos reportados (39 con área positiva, 2 de área 0); máx. 0,123284 m²; 1 sección normalizada | 0 cambios de solape; 0 cambios de contacto | **Sí** | **Sí** | 41/41 permanecen dentro del máximo de precisión de 1 m²; 37 producirían arista M02 y 4 quedan registradas como `NO_EDGE_UNDER_DECLARED_CONSUMER` |
| Comunidad Valenciana | 37215032201 | target 2023 | 159 candidatos reportados (118 con área positiva, 41 de área 0); 4 secciones normalizadas; dos pares >11 m² en la evidencia de #214 | 0 cambios de solape; 0 cambios de contacto | **Sí** | **No** | 157/159 candidatos quedan dentro del máximo; exactamente dos parejas lo exceden: `4617201001–4619401013` = 12,111238 m² y `4617201001–4619401008` = 11,827709 m². Entre los 157 admisibles, 140 producirían arista M02 y 17 no |
| País Vasco | 37215041294 | target 2024 | 4 candidatos, todos con área positiva; máx. 0,005446 m²; 1 sección normalizada | 0 cambios de solape; 0 cambios de contacto | **Sí** | **Sí** | replay read-only: 4/4 quedan dentro del contrato y las 4 producirían arista M02 |
| Aragón | 37215049347 | origen población 2025 | 11 candidatos reportados por #214 (9 con área positiva, 2 de área 0); 0 secciones normalizadas; hash geométrico antes=después; target 2026 sin solapes | transformación nula en el origen | **Sí** | **Diferida en adquisición / no acreditable con estos artefactos en el gate temporal** | los 9 solapes de área positiva del origen no pueden heredar admisibilidad del target; los 2 candidatos de área 0 no se tratan como solape; `geometry_admissibility` debe bloquear sin evidencia adicional |

En los cuatro datasets donde la normalización sí modificó geometrías —Islas Baleares, Castilla-La Mancha, Comunidad Valenciana y País Vasco— se reconstruyeron localmente las relaciones pairwise a partir de los raw preservados del propio artefacto. Resultado: **0 cambios de solape, 0 cambios de contacto y 0 operaciones raw no evaluables** en esos casos.

En Andalucía, Castilla y León y Aragón, la fuente que #214 bloqueó no fue modificada: su `geometry_set_sha256_before` coincide exactamente con `geometry_set_sha256_after`. Esto acredita que #214 estaba clasificando un defecto de fuente como fallo de normalización, pero no acredita por sí solo la admisibilidad temporal de esa fuente.

## Regresiones exigidas

La suite incorpora casos para:

- dataset sin modificación con solape original: seguridad de normalización independiente del defecto;
- solape original admisible por una regla explícita del consumidor;
- defecto original inadmisible;
- solape nuevo y solape aumentado;
- cambio espacial con igual área total;
- baseline raw no evaluable con evidencia alternativa **de pareja** verificable y sin sustitución por cero;
- baseline raw no evaluable **sin** evidencia alternativa, que permanece bloqueado;
- cambio de contacto detectado end-to-end;
- solape aumentado y desplazamiento espacial con igual área detectados end-to-end;
- ausencia de consumidor declarado, que no puede producir `READY`;
- CRS efectivo del consumidor, incluido el fallback vigente de Castilla y León;
- defecto original del seccionado de población que sólo pasa si queda ligado a un destino 1:1 y a una pareja target ya admisible.

## Alcance

La corrección conserva raw, hashes, issues, `derivation`, validación post-materialización y receipts existentes. No elimina la puerta de compatibilidad población–seccionado ni transforma una fuente histórica en certificada por el mero hecho de poder materializarla.

Este trabajo corrige la semántica de la puerta geométrica. La admisibilidad de precisión y el efecto de adyacencia quedan separados: Castilla-La Mancha conserva sus solapes submétricos como defectos tolerados sin convertir automáticamente esas parejas en aristas M02. **No demuestra ni promete activación completa de los siete territorios.**

## Cierre de revisión de #219

La revisión independiente posterior detectó y cerró cuatro riesgos antes de considerar la PR lista para nueva revisión:

- la rama se reconstruyó sobre el `main` vigente; los avances de `main` comprobados durante la revisión no solapan los ficheros funcionales de esta PR;
- la ausencia de consumidor declarado es fail-closed: `normalization_safety=READY` no equivale a `READY` global;
- el seccionado origen cross-year sólo puede acreditar un defecto si queda ligado a correspondencias geométricas 1:1 y a una pareja target ya admisible; los paquetes históricos cross-year sin esa evidencia no se reutilizan;
- la ligadura cross-year es material: ambos roles geométricos deben incluir dentro del bundle el JSON indicado por `derivation.path`; su SHA y su payload derivado se verifican, el audit durable es la fuente de decisión y la copia inline debe coincidir exactamente;
- la regla M02 se reproduce en el CRS efectivo del consumidor, incluido el fallback contractual, y existen regresiones end-to-end para baseline no evaluable, cambios de contacto, solape aumentado y desplazamiento con igual área.
