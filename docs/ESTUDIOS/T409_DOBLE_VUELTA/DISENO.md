# T-409 · Doble vuelta con coaliciones — diseño (solo documento)

Estado: PROPUESTA para aprobación del propietario. Base: D-167 (17-11). No toca código ni datos. Implementación tras
la migración P (D-165/D-166, T-313).

## 1. Escenarios

Bloques (cada partido homologado en uno solo; tabla propuesta en `configuracion/bloques_partidos_PROPUESTA.csv`):
1 Izquierdas, 2 Nacionalistas, 3 Patriotas. Partido sin bloque = «independiente».

| Escenario | Quién se coaliga en primera vuelta | Va por partido |
|---|---|---|
| `primero` (actual, se conserva) | — | todos; gana el más votado, sin segunda vuelta |
| `dv_base` (propuesta, referencia) | nadie | todos |
| `dv_1_izquierdas` | bloque 1 = una sola candidatura | 2, 3 y sin bloque |
| `dv_2_nacionalistas` | bloque 2 = una sola candidatura | 1, 3 y sin bloque |
| `dv_3_patriotas` | bloque 3 = una sola candidatura | 1, 2 y sin bloque |
| `dv_4` | 1 y 3 (cada uno una candidatura) | 2 (por partido) y sin bloque |

«Coaligado» = se suman los votos reales de sus partidos en el distrito (sin tasas inventadas) y compite como
candidatura única. Interpretación del enunciado (ver pregunta 1).

## 2. Reglas por distrito (operativas)

1. Candidaturas = partidos, salvo los bloques coaligados del escenario (suma de votos).
2. **Primera vuelta**: si una candidatura tiene >50 % de la base (§4), gana. Sin segunda vuelta.
3. **Segunda vuelta**: finalistas = las dos más votadas. Cada candidatura eliminada transfiere **todos** sus votos al
   finalista de su mismo bloque (si el finalista es una candidatura-bloque, o un partido del mismo bloque). Si su bloque
   no tiene finalista, o no tiene bloque → **abstención** (no suma a nadie). Un finalista conserva sus votos.
4. Gana el finalista con más votos de la segunda vuelta; su cuota = votos / suma de votos de ambos finalistas
   (los abstenidos no cuentan).
5. Dos finalistas del mismo bloque (bloque no coaligado): los eliminados de ese bloque van al más votado de los dos
   en la primera vuelta (pregunta 4).
6. Sin ≥2 candidaturas con votos no hay segunda vuelta: gana la única.

## 3. Empates y casos límite

- Empate por el segundo puesto (2.º = 3.º): se desempata por orden alfabético del id canónico y
  `empate=true` en la salida (determinista, repetible). Recomendación; ver pregunta 3.
- Empate en la segunda vuelta: igual criterio, `empate=true`.
- Distrito sin votos (total 0): sin ganador, `ganador` vacío.
- Votos en blanco/nulos: fuera (los datos agregados son por candidatura).

## 4. Base del cálculo — recomendación

**Votos a candidaturas** (suma de `votes` por partido, que es lo que ya existe como `total_votes` en
`electoral_outputs`). Razón: los blancos no llegan a P31 (no hay fuente por sección fiable para todos los años) y
cambiaría la cuota respecto de `winner_share` actual. Con votos válidos (con blancos) la mayoría del 50 % es más
exigente; requeriría una fuente nueva. Pregunta 2.

## 5. Dónde va

- Hoy: `modulos/07_agregar_resultados_electorales.py`, `electoral_outputs()` (≈ línea 1476): `by_party` por
  `[district_id, party]`, `bloc` ya existe como `parties.classification` (clasificación del diccionario de partidos,
  distinta del bloque de D-167), ganador por `groupby().idxmax()` (≈ línea 1484). Se llama en ≈ línea 1642.
- Tras D-166: P31 = `modulos/p31_agregacion.py`, P32 = `modulos/p32_resultados_distrito.py`. Nomenclatura
  nueva del campo: **`bloque_ddd`** (para no chocar con `bloc`), `escenario`, `vuelta_decisiva`.
- Nuevo módulo puro `ddd_core/p31_doble_vuelta.py`: `resolver(by_party, bloques, escenario) -> DataFrame` sin I/O;
  P31 lo llama tras `electoral_outputs` y escribe el CSV; `primero` sigue siendo el `winners` de hoy sin cambios.
  P32 lo empaqueta en el M08/P32 junto al ganador actual (campo adicional, no sustituye).
- La tabla aprobada pasa a `configuracion/bloques_partidos.csv` (editable por el propietario), cargada y validada por
  `ddd_core/bloques.py`: un partido, un bloque; toda candidatura homologada de la elección debe estar (vacío = sin bloque
  explícito); sha256 en el manifiesto.
- Huellas: si afecta a P31/P32, invalida su huella (`.claude/rules/huellas.md`); decir en la PR qué 00 hace falta.

## 6. Formato de salida

`resultados_doble_vuelta.csv` (largo, una fila por distrito y escenario):
`district_id, escenario, vuelta_decisiva (1|2), candidatura_ganadora, bloque_ganador, votos_1v, cuota_1v,
finalista_a, finalista_b, votos_a_2v, votos_b_2v, cuota_ganador_2v, votos_abstencion, empate`.
Detalle opcional `resultados_doble_vuelta_detalle.csv` (distrito, escenario, candidatura, votos_1v, destino,
votos_transferidos). Total de votos conservado: 1v = 2v + abstención (test).

## 7. Ejemplo (valores a mano, independientes del código)

Distrito: A (izq) 30, B (izq) 15, C (pat) 28, D (pat) 12, E (nac) 15; total 100.
- `primero`: A.
- `dv_base`: finalistas A 30, C 28; B→A (45), D→C (40), E abstención → **A 45–40** (52,9 %).
- `dv_1_izquierdas`: A+B 45 vs C 28: ninguno >50; D→C (40); E abst. → **izq 45–40**.
- `dv_3_patriotas`: C+D 40 vs A 30; B→A (45); E abst. → **A 45–40**.
- `dv_4`: A+B 45, C+D 40 coaligados, E 15: finalistas 45 y 40; E sin finalista nacionalista → abstención → **izq 45–40**.

## 8. Tests

Por rebanadas (un test → código): (1) >50 % gana en primera; (2) ejemplo de §7 en los cinco escenarios; (3)
transferencia a finalista de su bloque; (4) abstención sin finalista de su bloque o sin bloque; (5) empate
determinista con `empate=true`; (6) conservación de votos; (7) invariante: un partido, un bloque, y toda candidatura
homologada cubierta; (8) `primero` idéntico al `idxmax` actual (regresión); (9) distrito sin votos. Esperados: literales
y, para el 2023, el BOE (`configuracion/resultados_oficiales_congreso_2023.csv`, sha256 en el manifiesto) como base de
votos, nunca recalculados con el mismo código.

## 9. Orden de PR (tras T-313)

1. Esta (diseño + tabla propuesta). 2. `ddd_core/bloques.py` + `configuracion/bloques_partidos.csv` aprobada + tests de
la tabla. 3. `ddd_core/p31_doble_vuelta.py` puro + tests (sin cableado). 4. Cableado en P31 (huella). 5. Paquete P32.
6. Visor (decisión aparte). Una PR por capa; ninguna lanza ni publica.

## 10. Preguntas abiertas (con recomendación)

1. **Escenarios 1-3**: ¿«escenario k» = solo el bloque k se coaliga y el resto por partido? Recomiendo sí, más `dv_base`
   sin coaliciones como referencia.
2. **Base**: ¿votos a candidaturas o votos válidos con blancos? Recomiendo candidaturas (§4).
3. **Empates**: ¿orden alfabético del id con `empate=true`? Recomiendo sí; alternativa: más votos en la provincia.
4. **Dos finalistas del mismo bloque**: ¿cada eliminado de ese bloque va al más votado de los dos? Recomiendo sí.
5. **Partidos sin bloque** (229 de 366 filas, 142 siglas): ¿abstención siempre? Recomiendo sí (D-167, sin tasas inventadas).
6. **Coaliciones mixtas** (CHA-IU, Podemos–Sumar con marcas territoriales): una candidatura homologada = un bloque;
   CHA-IU queda vacío hasta decisión. ¿Bloque de CHA-IU?
7. **Ámbito**: ¿solo Congreso (provincia = distrito de P32) o también autonómicas? Recomiendo solo Congreso en la primera PR.
8. **Nombre del campo** `bloque_ddd` frente a `bloc` ya existente: ¿conforme?

## 11. Tabla propuesta de bloques

Fuente (nunca de memoria): `datos/homologacion_siglas/homologacion_siglas_generales.csv`
(sha256 `58a179fa41655572fa92b88eb9985963a0685ecc97839a6f520f613fdb5b43a3`; reglas `reglas_generales.json`
sha256 `fe8a3487c2ca5f5b5f2ab24fc0c3d598b43f01cdac1630bf0733242b1fe59617`), elecciones 2011-11, 2015-12, 2016-06,
2019-04, 2019-11, 2023-07. Una fila por (elección, partido homologado): 366 filas, 185 partidos.
Fichero: `configuracion/bloques_partidos_PROPUESTA.csv` (sha256 `c7c688744b183a9ca7cd412b0258e77b2f1df9992b046255eaccbff78328f4db`).
- `siglas` = partido homologado; `denominacion` = siglas reales de la fuente agrupadas (el repositorio no trae el nombre
  largo; no se añaden de memoria). Todo es PROPUESTA hasta que el propietario la apruebe.
- Asignadas: 45 filas Izquierdas, 70 Nacionalistas, 22 Patriotas. Los de izquierda nacionalista (ERC, CUP, EH Bildu, BNG,
  NC, COMPROMÍS, MÉS, CHA, ANDECHA) van a Nacionalistas.
- **Vacías (dudosas o sin criterio)**: 142 siglas, entre ellas las de mayor peso a decidir: Cs, UPyD, UPN y coaliciones,
  PAR, PRC, FAC, CHA-IU, EN MAREA, ADELANTE ANDALUCÍA, AHORA CANARIAS, EXISTE, CpM, Caballas, MDyC, PACMA, PIRATA,
  JXC/JxG/unio.cat/CCD (sigla ambigua), VERDES/LOS VERDES/LV-GV, FE, PT, y la cola de partidos menores. La lista
  completa: filas con `bloque_propuesto` vacío del CSV.
