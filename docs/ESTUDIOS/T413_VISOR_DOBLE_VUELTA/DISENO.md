# T-413 · Visor: doble vuelta por distrito — diseño (solo documento)

VERSIÓN: 1.2.0 · FECHA: 2026-11-19 · ESTADO: aprobado (D-172, punto 3 cambiado: V4) · ANTERIOR: 1.1.0 (#905)

**Cambio (19-11, propietario vía Planificador)**: el mapa NO va en `visor/v3/` sino en `visor/v4/mapa/` (diseño de la V4: T-415, `docs/ESTUDIOS/T415_V4_PORTADA/`); donde este documento dice «V3» léase «V4/mapa» (V3 no se toca). Primera entrega: página independiente con datos de ejemplo, sin enlazar.

D-172 (18-11, propietario, relayado por el Planificador): «sí a todo», las 10 recomendaciones del §9 quedan **decididas**. Según el plan 1.0.68 en curso (D-172 aún no consta en `docs/PLAN.md` de `main`; D-171 no se cita).

Base: D-167, D-168, D-170, T-409 (`docs/ESTUDIOS/T409_DOBLE_VUELTA/DISENO.md`, #904, `herramientas/doble_vuelta.py`).
Maquetas: [`maquetas.html`](maquetas.html) (HTML estático, tema claro/oscuro del sistema; ejemplo de T-409 §7).
No toca `visor/`, workflows ni datos. Nota de nombres: el prompt dice `web/`; hoy `web/` solo tiene `textos.md` y el visor público
es `visor/v3/` (la raíz redirige a `/v3/`; V3 ya tiene el eje «sistema proporcional/mayoritario DDD»). Este diseño asume V3.

## 1. Cómo elige el usuario el escenario

En V3, con ámbito Congreso y sistema «mayoritario DDD» (407 distritos), una fila de botones «Regla de elección» (control
segmentado; en móvil, desplazable en horizontal):

| Botón (texto visible) | Id interno | Texto de una línea |
|---|---|---|
| **Tres bloques** (por defecto) | `dv_A` | Izquierdas, Nacionalistas y Patriotas se presentan cada uno como una sola candidatura. |
| **Dos bloques** | `dv_B` | Solo Izquierdas y Patriotas se presentan juntos; los nacionalistas, partido a partido. |
| **Sin coaliciones** | `dv_base` | Cada partido se presenta por separado. |
| **Más votado** (secundaria) | `primero` | Gana el partido con más votos, sin segunda vuelta (regla de hoy). |

Sin parámetros técnicos visibles (D-129/D-130): ni ids `dv_*`, ni umbrales. El enlace profundo guarda `?regla=tres|dos|base|primero`.
Recordar la última elección en `localStorage` (con `try/catch`, la página funciona sin él). Al cambiar de regla se conservan
territorio, distrito abierto y capa de color. La regla se muestra siempre en la ficha y en el título del mapa (nada se ve «sin regla»).

## 2. Colores (bloque y partido), contraste y modo oscuro

Dos capas, conmutador «Colorear por: bloque | partido» (por defecto, bloque):

- **Por bloque** (el color del ganador de cada distrito). Fichas de color con **texto del bloque siempre escrito** (leyenda y ficha): el color
  nunca es el único portador de información.
- **Por partido**: paleta ya existente de V2/V3 (`--pp`, `--psoe`, … `--otros`). Con `dv_A` el ganador es un bloque, no un partido:
  se pinta con el color del bloque y rayado fino («candidatura de bloque»); la leyenda lo dice.
- Intensidad: color pleno si la cuota del ganador en la decisiva supera al otro finalista por ≥ 5 puntos; color claro (opacidad .55)
  si no. Empate (`empate=true`): rayado diagonal del color del ganador. Sin dato: gris con puntos.
- Sin bloque (partido independiente que gana, solo con `dv_B`/`dv_base`): gris rayado + etiqueta «Sin bloque».

Tokens propuestos (calculados; razón de contraste frente al fondo, WCAG 2.1: texto ≥ 4,5, objetos gráficos ≥ 3):

| Bloque | Claro (fondo `#fffdf8`) | Contraste | Oscuro (fondo `#14181a`) | Contraste |
|---|---|---|---|---|
| Izquierdas | `#b3261e` | 6,43 | `#ff8a80` | 7,83 |
| Nacionalistas | `#0b6e69` | 5,99 | `#4fd1c5` | 9,58 |
| Patriotas | `#1f5fa8` | 6,34 | `#7fb2ff` | 8,27 |
| Sin bloque | `#5b6470` + rayado | 5,90 | `#a8b0bb` + rayado | 8,16 |

Definidos como variables en `:root`, redefinidos en `@media (prefers-color-scheme: dark)` y en `[data-theme="dark"]` (V3 hoy no
tiene modo oscuro: es cambio nuevo y acotado a estos tokens y al panel; el resto del visor sigue claro hasta otra tarea; pregunta 6).
Daltonismo: rojo/verde-azulado/azul se distinguen por luminancia y por el rayado de los casos especiales; la ficha repite el nombre.

## 3. Qué se ve al tocar un distrito

Ficha (panel lateral en escritorio; hoja inferior en móvil). De arriba abajo:

1. **Titular**: «Distrito N · <provincia>» y una frase: «Decide la segunda vuelta · gana Izquierdas con el 52,9 %» o «Gana Patriotas en
   primera vuelta con el 54,3 %».
2. **Primera vuelta**: barra apilada por bloque y tabla de candidaturas (votos, % sobre votos a candidaturas; D-168). Con `dv_A` cada
   bloque suma sus partidos (desplegable «Ver por partido»); con `dv_B`/`dv_base` las filas son partidos, con chip de bloque.
   Marca «Nadie pasa del 50 %» o «Supera el 50 %: no hay segunda vuelta».
3. **Finalistas** (si hubo segunda vuelta): las dos más votadas.
4. **Transferencias por bloque**: una fila por candidatura eliminada: «Nacionalistas (15) → Izquierdas», o «→ abstención (su bloque no tiene finalista)»;
   «Sin bloque» → abstención. Total de abstención.
5. **Segunda vuelta**: barra de dos finalistas, votos y cuota del ganador (sobre la suma de los dos finalistas; los abstenidos no cuentan).
6. **Empate**: aviso «Empate por el segundo puesto / en la segunda vuelta: se resuelve por orden alfabético y se marca; regla fija, no sorteo».
7. **Comparación**: línea «Con otra regla: Tres bloques → Izquierdas · Dos bloques → Izquierdas · Sin coaliciones → Patriotas · Más votado → PP»
   (cuatro chips; tocar uno cambia la regla). Es la información más útil del producto: dónde cambia el ganador.
8. **Procedencia**: elección, run, sha256 corto del fichero (ver §5).

## 4. Leyenda y texto de la regla (español llano)

Leyenda (bajo el mapa, plegable en móvil): cuatro muestras (Izquierdas, Nacionalistas, Patriotas, Empate / sin dato) y dos líneas: «Color
pleno: ventaja de 5 puntos o más. Color claro: ventaja menor.» + «Rayado: candidatura de bloque o empate».

Texto «Cómo funciona» (enlace junto al selector; el mismo en la ficha; claves nuevas en `web/textos.md`, que escribe el propietario):

> En cada distrito se cuentan los votos a las candidaturas (sin blancos ni nulos). Si una candidatura saca más de la mitad, gana en primera vuelta.
> Si no, pasan a segunda vuelta las dos más votadas. Los votos de cada candidatura eliminada se suman a la finalista de su mismo bloque
> (Izquierdas, Nacionalistas o Patriotas). Si su bloque no tiene finalista, o el partido no pertenece a ningún bloque, esos votos se abstienen
> y no cuentan. Gana la finalista con más votos. «Tres bloques» agrupa los tres bloques desde la primera vuelta; «Dos bloques» solo Izquierdas
> y Patriotas; «Sin coaliciones» no agrupa a nadie. No se inventan porcentajes de trasvase: solo se suman votos reales. Es una simulación; no tiene valor oficial.

## 5. Datos que necesita el visor

Hoy el visor lee los M08 desde `orchestracion/publicaciones_visor.json` (`kind=canonical_m08`, blob + sha256) y versiones ligeras en
`datos/resultados/` (solo ganador por distrito, sin votos por partido: `MANIFEST.json` → `partidos` vacío). Con T-409 PR 2 y el
enganche, el CSV por partido y distrito se archiva en origen (R2). Para el visor:

- **Registro**: `kind` propio `doble_vuelta` en `publicaciones_visor.json` (aislamiento como el histórico, D-154): campos de siempre
  (`id`, `territory_id`, `run_id`, `blob_sha`, `sha256`, `source_type`) más `eleccion`, `m06_run_id` (linaje: el M06 con el que se calculó)
  y `bloques_sha256` (tabla de bloques usada). Solo se añade; ningún `doble_vuelta` sustituye al vigente.
- **Datos abiertos** (`datos_abiertos/<id>/doble_vuelta.csv` y `doble_vuelta_detalle.csv`, CC BY 4.0, y entrada en `INDEX.json` con
  sha256): el visor los lee con el mismo cargador que ya verifica sha256 de GeoJSON; si no coincide, no se muestra la regla y se avisa.
- **Formatos** (los de T-409 §6, sin cambios): `resultados_doble_vuelta.csv` (14 columnas, una fila por distrito y escenario) para el
  mapa y la cabecera de la ficha; `..._detalle.csv` (distrito, escenario, candidatura, bloque, votos_1v, destino, votos_transferidos)
  para primera vuelta, transferencias y desplegable por partido. **Petición a T-409**: añadir `bloque` al detalle y `votos_1v` de cada
  partido también en `dv_A` (una fila por partido con su candidatura de bloque), para que la ficha no recalcule nada en el navegador. **Estado**: el detalle no está en `main` (la PR #907 de T-409 lo añade con `--detalle`, aún sin fusionar) (T-409 §6 lo marca «opcional» y `herramientas/doble_vuelta.py` en `main` solo escribe el CSV de 14 columnas); la ficha de transferencias (§3.4) y el desplegable por partido dependen de él, así que la PR 6 de §8 espera a la PR de T-409 con la pregunta 9.
- Tamaño estimado: 407 distritos × 4 reglas, ~12 000 filas de detalle ≈ 0,5 MB sin comprimir; se carga bajo demanda por territorio.
  `primero` sale del M08 actual (misma fuente, sin duplicar).
- El visor **no** aplica la regla en JavaScript: solo muestra lo generado por `doble_vuelta.py` (un solo algoritmo; el test de contrato lo comprueba).

## 6. Territorios ya publicados sin votos por partido

- La regla «Más votado» sigue funcionando con el M08 actual para todos los territorios.
- Sin `doble_vuelta` en el registro del territorio: los tres botones nuevos salen **deshabilitados con motivo** («Aún no calculada en este
  territorio; llegará al regenerarlo») y el visor se queda en «Más votado» con aviso visible (maqueta 3). Nunca se rellenan con votos
  reconstruidos ni con datos de otro territorio (CLAUDE.md: datos oficiales no de memoria).
- Aviso global (una línea en la leyenda): «Reglas de doble vuelta disponibles en N de 71 territorios».
- Mezcla en el mapa nacional: se pinta la regla elegida donde existe y gris «Sin dato» donde no, con contador; nunca se mezclan reglas
  distintas en un mismo mapa sin decirlo.
- Se llena al regenerar con P30/T-409 (relanza y regenera, objetivo 08-11): no hay migración de lo antiguo.

## 7. Móvil

- Selector: control segmentado desplazable, objetivos ≥ 44 px, texto ≥ 14 px; no depende de hover.
- Mapa a pantalla completa; leyenda plegable («Leyenda ▾»); «Colorear por» en el mismo menú.
- Ficha: hoja inferior arrastrable (50 % → 90 %), cierre con botón y gesto; tablas pasan a tarjetas de una columna; el desplegable por partido empieza cerrado.
- Sin desbordamiento horizontal de página; gutter 16 px; foco y `aria-label` en barras (texto equivalente de cada barra) y `aria-pressed` en botones.
- Probar a 360 × 640 y 390 × 844 con Playwright; tema oscuro con `prefers-color-scheme`.

## 8. Tests y orden de PR

Tests (por rebanadas; esperados literales o del §7 de T-409, nunca recalculados con el mismo código):
1. Contrato: el cargador acepta el CSV de `doble_vuelta.py` sobre un fixture y rechaza sha256 distinto, columnas que faltan y escenario desconocido (Python, `tests/test_visor_doble_vuelta.py`).
2. Selección de regla y enlace profundo `?regla=` (Node, como `test_visor_galeria.js`): orden, defecto «Tres bloques», deshabilitado sin datos.
3. Ficha del ejemplo §7: texto «gana Izquierdas 52,9 %», transferencia «Nacionalistas → abstención», total 1v = 2v + abstención.
4. Tokens de color: contraste ≥ 4,5 (texto) y ≥ 3 (relleno) en claro y oscuro, leyendo el CSS; los cuatro bloques con tokens en ambos temas.
5. Territorio sin `doble_vuelta`: botones deshabilitados, aviso presente, ninguna cifra inventada.
6. Mismo ganador que `resultados_doble_vuelta.csv` en cada distrito (el visor no recalcula).
7. Móvil (Playwright, 2 tamaños): sin scroll horizontal, objetivos ≥ 44 px, hoja inferior abre y cierra.
8. Regresión: «Más votado» idéntico al visor actual.

Orden de PR (una por capa; ninguna lanza ni publica):
1. Esta (diseño + maquetas). 2. Datos: T-409 PR 2 (`doble_vuelta.py`) y su enganche + archivo en R2 (tras #899). 3. Publicador P40:
escribe `doble_vuelta` en registro y `datos_abiertos/` con sha256 (toca workflows: aviso al Planificador). 4. Capa de lectura del visor sin UI
(cargador, verificación, tests 1, 5, 6). 5. Selector, mapa, leyenda y tokens (tests 2, 4, 7). 6. Ficha de distrito (test 3). 7. Texto del
propietario en `web/textos.md`. 8. Publicar (Operador, frase D-52 del propietario). 9. Decidir si «Más votado» se retira (pregunta 1).

## 9. Preguntas — DECIDIDAS (D-172, 18-11): se adopta la recomendación en las 10

1. **¿Qué pasa con la mayoría simple?** Recomiendo: la doble vuelta es lo principal («Tres bloques» por defecto) y «Más votado» queda como cuarta
   opción secundaria, visible, porque es la regla de hoy y sirve de comparación. No retirarla hasta que la doble vuelta cubra los 71 territorios.
2. **¿Escenario por defecto?** Recomiendo `dv_A` («Tres bloques»), el de coalición completa de D-168.
3. **¿V3 es el visor donde va?** Recomiendo sí (es el público y ya tiene «sistema mayoritario DDD»); V2/V1 no cambian.
4. **¿Nombres de los botones?** Recomiendo «Tres bloques / Dos bloques / Sin coaliciones / Más votado»; los ids `dv_*` no se muestran.
5. **¿Colorear por bloque por defecto?** Recomiendo sí; «por partido» como alternativa (con `dv_A` el ganador es el bloque).
6. **¿Modo oscuro?** Recomiendo implementarlo solo en tokens nuevos y ficha ahora, y el resto de V3 como tarea aparte (V3 hoy no lo tiene).
7. **¿Línea de comparación entre reglas en la ficha (§3.7)?** Recomiendo sí; es lo que más aporta y no cuesta datos extra.
8. **¿Umbral visual de «ventaja pequeña» (5 puntos)?** Recomiendo 5 puntos; es solo estilo, no regla electoral.
9. **¿Añadir `bloque` y votos por partido en `dv_A` al detalle de T-409?** Recomiendo sí (PR 2 de T-409, antes de fusionarla).
10. **¿Avisar de «simulación sin valor oficial» en la propia ficha?** Recomiendo sí, una línea fija.
