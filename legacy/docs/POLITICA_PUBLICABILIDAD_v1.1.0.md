# Política de publicabilidad de mapas distritales DDD

**Versión:** 1.1.0
**Nombre de versión:** Alcance medible de comunidades de interés
**Fecha:** 2026-09-13
**Estado:** vigente — C-13
**Anterior:** `legacy/docs/POLITICA_PUBLICABILIDAD_v1.0.0.md`

## 1. Decisión

`PASS` territorial significa que una ejecución satisface su contrato técnico. No significa que el mapa sea publicable como propuesta política, electoral o institucional. El visor y sus GeoJSON son, mientras no se superen estas puertas, **vistas técnicas de resultados**, no mapas defendibles ni recomendados.

Un mapa solo puede recibir `PUBLICABLE` cuando los nueve criterios sustantivos y las garantías transversales de esta política estén en `PASS`. Un `NOT_EVALUATED` o `NOT_EVALUABLE` bloquea igual que un `FAIL`: ausencia de prueba no es prueba favorable.

## 2. Nueve criterios sustantivos

| ID | Criterio | Puerta mínima de publicación |
|---|---|---|
| P01 | Equilibrio poblacional | Todos los distritos dentro de la tolerancia declarada; excepciones prohibidas en publicación. |
| P02 | Contigüidad | Todos los distritos contiguos conforme al contrato topológico aplicable. |
| P03 | Confinamiento provincial | Ningún distrito cruza provincia cuando esa es la unidad de reparto de K. |
| P04 | Disciplina municipal | Cumplimiento completo de atomicidad y reglas de partición declaradas. |
| P05 | Forma | Polsby–Popper presente para todos; mínimo ≥0,05 y no más del 30 % de distritos por debajo de 0,15. |
| P06 | Neutralidad partidista | Métricas predefinidas y publicadas; no se admite decidir el umbral después de observar el mapa. |
| P07 | Comunidades de interés | Fuente, regla y medición explícitas; una mención inerte a comarcas no cuenta. |
| P08 | Inteligibilidad | Todos los distritos tienen nombre estable, explicable y no partidista. |
| P09 | Base jurídica | Norma o naturaleza propositiva citada, tolerancia justificada y límites de validez expresos. |

P05 es una puerta interna provisional, no una afirmación de que Polsby–Popper sea una norma legal ni una medida completa de calidad. El umbral 0,15 procede de la referencia histórica del propio proyecto. El suelo 0,05 evita formas extremas y el límite sistémico del 30 % impide aprobar un territorio cuya mala forma sea general, sin penalizar automáticamente fronteras naturales o administrativas concretas.

P07 se aplica a una comunidad supra-municipal: comarca o equivalente funcional
declarado. P04 ya cubre municipios y no puede duplicarse como P07. La fuente debe
ser pública, versionada, no partidista y cubrir todos los municipios. Deben
publicarse comunidades partidas, comunidades por distrito, peso de la comunidad
dominante y retención poblacional. Los umbrales se fijan antes de ejecutar; sin
fuente o sin umbral, P07 es `NOT_EVALUABLE` y bloquea la publicación.

## 3. Garantías transversales

- **G01 — Robustez frente a semilla:** distribución multi-semilla y posición del mapa elegido.
- **G02 — Validación independiente:** recomputación contra la especificación, separada del motor.
- **G03 — Integridad de datos:** conciliación de universos, recuentos y excepciones explícitas.
- **G04 — Trazabilidad:** configuración, fuentes, código, checksums y decisión de promoción identificables.

Las garantías no sustituyen los nueve criterios; determinan si sus resultados pueden creerse y reproducirse.

## 4. Resolución de C-02: Castilla y León

La crítica queda **confirmada**. Castilla y León tiene 40 de 82 distritos por debajo de 0,15 (48,78 %) y un mínimo de 0,02809. Incumple las dos condiciones de P05. Su estado correcto es:

- `TECHNICAL_PASS` para M01–M06;
- `PUBLICATION_BLOCKED_SHAPE` para publicación;
- disponible únicamente como vista técnica etiquetada.

Aragón supera provisionalmente P05: 17 de 67 por debajo de 0,15 (25,37 %) y mínimo 0,05273. Extremadura también lo supera, pero continúa bloqueada por población y no se promociona.

## 5. Resolución de C-03: qué demuestra realmente la correlación

El valor numérico de Claude es correcto: en Castilla y León, la correlación de Pearson entre desviación poblacional **absoluta** y Polsby–Popper es −0,3293; Spearman es −0,3323.

La interpretación causal incluida en la auditoría no se sostiene con ese signo. Si la primera variable es desviación absoluta, una correlación negativa significa que los distritos con **peor** balance poblacional tienden a tener **peor** forma. No demuestra que apretar la población haya degradado la forma. Los cuartiles lo confirman: el cuartil con mejor balance tiene Polsby–Popper medio 0,1980; el de peor balance, 0,1165.

Por tanto:

- se confirma que el optimizador no contabiliza explícitamente el coste de forma;
- se rechaza como no demostrada la afirmación de que la mejora poblacional observada causó la degradación geométrica;
- no se modifican pesos ni motor sin una comparación controlada entre soluciones, prohibida en este paquete.

## 6. Resolución de C-14: estado actual

| Territorio | Contrato técnico | P05 forma | Publicabilidad global | Motivo rector |
|---|---|---|---|---|
| Aragón | PASS | PASS provisional | BLOCKED | faltan neutralidad, comunidades, nombres, base jurídica y robustez multi-semilla |
| Castilla y León | PASS | FAIL | BLOCKED | fallo sistémico de forma, además de los criterios no evaluados |
| Extremadura | BLOCKED | PASS provisional | BLOCKED | incumple su tolerancia poblacional y no está promocionada |

La conclusión es inequívoca: **hoy no hay ningún mapa DDD publicable como propuesta política**. Sí existen dos resultados territoriales técnicamente certificados que pueden mostrarse como evidencia de ingeniería, siempre que esa naturaleza quede visible.

## 7. Regla de promoción

La promoción requiere una matriz completa P01–P09, G01–G04 y una decisión firmada en el expediente del run. No se permite compensar un `FAIL` con un resultado sobresaliente en otro criterio, ni rebajar umbrales después de ver el resultado.
