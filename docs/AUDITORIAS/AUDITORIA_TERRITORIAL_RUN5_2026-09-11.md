# Auditoría territorial del Run #5 — Aragón 2025

**Run:** 34584775443  
**Run ID:** `gh-34584775443-1`  
**Fecha:** 2026-09-11  
**Estado técnico:** PASS  
**Base de análisis:** `resultados/ejecuciones/gh-34584775443-1/M06/catalogo_distritos.csv` y `composicion_distritos.csv`

## 1. Propósito

Esta auditoría no valida únicamente que existan 67 distritos contiguos dentro del suelo y techo poblacional. Evalúa si la solución empieza a comportarse como una distritación territorialmente defendible y localiza qué dimensiones todavía no están incorporadas al motor M05.

## 2. Resultado poblacional

- Población total: **1.364.621**.
- Distritos: **67**.
- Target: **20.367,48 habitantes**.
- Suelo duro (0,80×): **16.293,98**.
- Techo duro (1,75×): **35.643,09**.
- Distritos bajo suelo: **0**.
- Distritos sobre techo: **0**.
- Distritos desconectados: **0**.
- Población mínima: **18.434**.
- Población máxima: **27.255**.
- Distritos dentro de ±12% del target: **65 de 67**.
- Distritos fuera de ±12%: **2 de 67**.

### Dos excepciones poblacionales

| Distrito | Población | Desviación | Secciones | Municipios | Área km² | Polsby-Popper |
|---|---:|---:|---:|---:|---:|---:|
| 16 | 27.255 | +33,82% | 42 | 30 | 1.858,40 | 0,0502 |
| 37 | 27.220 | +33,64% | 46 | 34 | 2.349,59 | 0,0821 |

Ambos están íntegramente en Teruel. El problema poblacional fino queda, por tanto, fuertemente concentrado y no justifica relajar la solución completa.

## 3. Calidad territorial

La solución cumple la contigüidad, pero todavía presenta anomalías territoriales importantes:

- **13 distritos cruzan límites provinciales**.
- **2 distritos contienen territorio de las tres provincias**.
- El distrito más extenso alcanza **4.771,16 km²**.
- El máximo número de municipios en un distrito es **78**.
- La mediana de municipios por distrito es **2**, lo que evidencia una distribución muy heterogénea entre distritos urbanos compactos y macro-distritos rurales.
- La compacidad Polsby-Popper mínima es **0,0412**; la mediana es **0,1315**.
- Hay distritos territorialmente muy extensos con compacidad muy baja, aunque su población esté próxima al target.

### Casos territoriales especialmente relevantes

| Distrito | Población | Provincias | Municipios | Área km² | Polsby-Popper |
|---|---:|---|---:|---:|---:|
| 64 | 20.374 | Teruel / Zaragoza | 78 | 4.771,16 | 0,0412 |
| 13 | 19.759 | Teruel / Zaragoza | 69 | 3.364,07 | 0,0568 |
| 30 | 21.039 | Teruel / Zaragoza | 67 | 2.640,49 | 0,0433 |
| 1 | 19.086 | Huesca / Zaragoza | 27 | 2.769,40 | 0,1003 |
| 28 | 19.331 | Huesca / Teruel / Zaragoza | 20 | 2.027,69 | 0,1778 |
| 29 | 18.904 | Huesca / Teruel / Zaragoza | 19 | 1.793,07 | 0,0756 |

El hecho de que un distrito tenga población correcta no implica que sea territorialmente aceptable.

## 4. Fragmentación municipal

A partir de `composicion_distritos.csv` se detectan **30 municipios repartidos entre más de un distrito**.

Casos principales:

- Zaragoza: **40 distritos**.
- Huesca: **5 distritos**.
- Barbastro: **3 distritos**.
- Monzón: **3 distritos**.
- Utebo: **3 distritos**.
- Otros 25 municipios aparecen divididos entre 2 distritos.

La división de Zaragoza es estructuralmente necesaria por población. Otras divisiones pueden ser necesarias o razonables, pero actualmente el algoritmo no distingue entre una división inevitable y una fragmentación evitable. Esta dimensión debe ser medida y controlada explícitamente.

## 5. Diagnóstico del motor actual

M05 v7.1.0 ha demostrado que puede resolver las restricciones duras de población sin romper la contigüidad. Sin embargo, su función objetivo todavía representa de forma incompleta la calidad territorial.

Actualmente prioriza:

1. número de violaciones de suelo/techo;
2. magnitud total de esas violaciones;
3. máximo desvío poblacional;
4. error cuadrático poblacional.

No penaliza todavía de forma explícita:

- cruces provinciales;
- fragmentación municipal evitable;
- número excesivo de municipios por distrito;
- superficie extrema;
- baja compacidad;
- coherencia comarcal;
- continuidad urbana/barrios;
- distancia interna o accesibilidad territorial;
- preservación de unidades administrativas naturales.

Por tanto, la solución actual debe considerarse **poblacionalmente válida y topológicamente contigua, pero territorialmente no promocionable como solución final**.

## 6. Requisitos derivados para la siguiente evolución

La siguiente evolución de M05 debe separar claramente tres niveles de criterio:

### Nivel A — restricciones duras
- 67 distritos exactos.
- Contigüidad de todos los distritos.
- Conservación total de población y secciones.
- Suelo 0,80×target.
- Techo 1,75×target.

### Nivel B — objetivos poblacionales prioritarios
- Llevar todos los distritos, cuando sea factible, a ±12%.
- Resolver específicamente los distritos 16 y 37 sin degradar los 65 ya dentro de tolerancia.

### Nivel C — calidad territorial
Debe incorporarse una función de coste territorial parametrizable. Como mínimo deberá medir:

- cruces provinciales;
- fragmentaciones municipales;
- número de municipios por distrito;
- compacidad;
- superficie relativa al patrón territorial;
- y, cuando la fuente esté incorporada, coherencia comarcal y urbana.

No todos estos criterios deben ser duros. Deben distinguirse restricciones, penalizaciones fuertes y preferencias blandas.

## 7. Requisito de información de distrito

El `catalogo_distritos.csv` actual es un avance, pero la ficha de distrito deberá evolucionar para incluir, cuando estén disponibles y sean verificables:

- código y nombre estable del distrito;
- provincia o provincias y porcentaje de población por provincia;
- municipio dominante y porcentaje de población del distrito;
- municipios completos y municipios fragmentados;
- número y listado de secciones;
- comarca o comarcas y peso poblacional;
- cabecera/núcleo principal;
- densidad de población;
- población urbana/rural;
- superficie y perímetro;
- compacidad;
- distritos vecinos;
- centroides y extensión;
- métricas de integridad administrativa;
- métricas electorales solo como capa posterior, nunca como criterio geométrico.

## 8. Veredicto

R011 resuelve la falta de auditabilidad de los productos intermedios. El Run #5 demuestra que los outputs M01-M08 son accesibles y que M06 permite ya una auditoría territorial real.

La siguiente prioridad técnica no es añadir iteraciones aleatorias. Es **evolucionar M05 desde un optimizador casi exclusivamente poblacional hacia un optimizador multiobjetivo territorial, manteniendo los PASS ya conseguidos y atacando de forma localizada los distritos 16 y 37**.
