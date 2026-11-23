# T-448 · Barcelona (08) en 2011-11: la sección 0804703001 de Cardona (solo diagnóstico; nada implementado)

Barcelona es la única provincia en BLOQUEADA_SIN_DATO del contrato 2011-11 (1.5.0, PR #982). El bloqueo se debe a una sola sección, 0804703001 (Cardona, 08047). Este documento mide las opciones y deja preguntas al propietario. No se implementa nada hasta que el propietario decida.

## Fuentes (bajadas el 23-11 desde la nube; sha256 iguales a los acreditados)
| Fichero | sha256 | Acreditación |
|---|---|---|
| `seccionado_2012.zip` | 772ad76b84e1… | `orchestracion/fuentes_r2.json`, T-357 |
| `seccionado_2015.zip` | 50dda58ed4af… | T-357 `SHA256SUMS.txt` |
| `cartografia_censo2011_nacional.zip` | d0151e0cc126… | T-357 |
| `indicadores_seccion_censal_csv.zip` (Censo 2011 por sección) | 305a19f11b87… | T-357 |
| `30832.csv` (Atlas 2015-2024) | 37716cba8cda… | T-357 |
| `1mun00.csv` (total municipal del Censo 2011) | ad95479c07ce… | `total_municipal_censo_2011.json` (D-185) |
| Observatorio 2011, `data/201111/sekzioa/08.json` | 4b92e1265db7… | contrato 2011-11 |

## Qué pasa (medido)
1. **Censo 2011 (1-nov-2011):** Cardona tiene 5 secciones: 01001 = 1.180, 01002 = 845, 01003 = 1.780, 02001 = 915 y 02003 = 270. Suman 4.990 hab. El total municipal de `1mun00` es 5.057 (67 más que la suma por secciones).
2. **Seccionado 2012:** 01001, 01002, 01003, 02001 y **03001**. 02003 desaparece y aparece la 03001 (1,93 km²). La 03001 está formada así:
   - el 25,4 % de su área es la antigua 02003 entera (0,49 km²; el 100 % de 02003 cae dentro de 03001 y su centroide también);
   - el 74,6 % es un trozo rural de 02001 (65,7 km²; le quita el 2,2 % del área).
3. **Por qué queda sin dato:**
   - La regla B' (D-158) toma como madre la sección con mayor solape de área, la 02001 (0,746). Tendría que repartir sus 915 hab. entre madre e hija según el Atlas, pero el Atlas (2015-2024) **no tiene la 03001 en ningún año**, así que no hay reparto (`repartir_madres` → `sin_dato`).
   - A la vez, D-153 **excluye** los 270 hab. de 02003 porque su sucesora (03001) no tiene fila («la sucesora 0804703001 no tiene fila en la tabla de población»).
   - Resultado: la provincia pierde 270 hab. y la 03001 queda sin dato.
4. **Seccionado 2015:** la 03001 vuelve a integrarse entera en la 02001 (el 100 % de su área). El Atlas 2015 da a esa 02001 ampliada 1.189 hab. (en 2012: 02001 + 03001).
5. **Observatorio 2011:** los votos de Cardona ya vienen con los códigos de 2012. La 03001 tiene **472 electores** de 4.141 en el municipio (11,4 %), así que está habitada; un 0 sería falso.
6. **Mapa:** Cardona (5.057 hab.) está muy por debajo del límite de atomicidad (`municipality_atomicity_limit_ratio` 1,15 de la media, unos 203.565 hab.). Va entera a un distrito, así que **para el mapa solo cuenta su total municipal**, no el reparto entre sus secciones.
7. **Aviso aparte, sin efecto en el mapa por el punto 6:** en Cardona los códigos 01001-01003 de 2012 no corresponden a los mismos polígonos que en el Censo (la 01002 de 2012 es en un 59 % la 02001 del Censo). Por eso la población por sección de Cardona no casa con sus electores (01002: 845 hab. y 1.410 electores). Hoy el contrato toma la población por código como «dato».

## Opciones medidas
Base del contrato actual: Barcelona = 5.487.390 hab. (sin la 03001 ni los 270 de 02003), K = 31, media = 177.012,58, suelo 0,85 = 150.460,7, techo 1,15 = 203.564,5, estimada = 21.487 (0,3916 %).

| Opción | 03001 | Cardona | Barcelona | Media (Δ) | Efecto en el distrito de Cardona | Estimada | Estado |
|---|---|---|---|---|---|---|---|
| **1. Asignar la contenida:** 02003 (Censo, 270 hab., 100 % dentro y con el centroide en 03001) pasa a 03001 en lugar de excluirse; la madre 02001 conserva 915 | 270 | 4.990 (= Censo por secciones) | 5.487.660 | 177.021,29 (+8,71) | +270 hab. = +0,153 % de la media | 21.757 (0,3965 %) | LISTA |
| **2. Residuo municipal del Censo** (como 36059, D-185, ampliado a hijas sin dato): 03001 = 5.057 − 4.720 | 337 | 5.057 (= `1mun00`) | 5.487.727 | 177.023,45 (+10,87) | +337 hab. = +0,190 % de la media | 21.824 (0,3977 %) | LISTA |
| 3. Sección vacía declarada (03001 = 0; 02003 sigue excluida) | 0 | 4.720 | 5.487.390 | 177.012,58 (0) | ninguno; se pierden 270 hab. (0,005 % de la provincia) | 21.487 (0,3916 %) | LISTA |
| 4. Proporcional a electores 2011 (472/4.141 sobre el resto) | ≈ 607 | 5.327 | 5.487.997 | 177.032,16 | +607 hab. (+0,343 %) | – | LISTA; mezcla censo electoral y población (fuente no acreditada como población) |
| 5. Sin cambios | – | – | – | – | Barcelona (31 escaños) fuera del histórico 2011 | – | BLOQUEADA_SIN_DATO |

Ninguna de las opciones 1-3 acerca la provincia al tope del 1 % ni mueve el suelo o el techo más de 10 hab. La diferencia entre la 1 y la 2 (67 hab.) es la misma que hay entre el Censo por secciones y el total municipal de `1mun00`.

## Preguntas al propietario
1. **¿Qué valor recibe la 0804703001?** Recomendación: **opción 1**. Usa solo el Censo por secciones (la misma fuente que el resto de la provincia), no inventa población, recupera los 270 hab. excluidos y aplica la regla de D-153 (sucesora por centroide) a un caso que hoy cae en su excepción. Se declararía como `reasignada` (cuenta como estimada) y se limitaría a una sucesora sin fila que contiene la sección del Censo al 100 % y en el mismo municipio. La opción 2 es la alternativa si se prefiere cuadrar con `1mun00` como en 36059, pero mezcla las dos fuentes dentro de la provincia.
2. **¿Se aplica la regla solo a Barcelona/Cardona o a toda sucesora sin fila en 2011-11?** Recomendación: regla general con las condiciones de la pregunta 1 (100 % contenida, centroide dentro, mismo municipio). Hoy solo la cumple Cardona; un test lo fijaría.
3. **¿Se abre una tarea aparte para el aviso del punto 7** (códigos de Cardona reutilizados con otros polígonos entre el Censo y 2012)? Recomendación: no por ahora. No cambia el mapa porque Cardona es atómica; solo afectaría a un análisis por sección.

## Si se aprueba la opción 1 (para el implementador)
- `herramientas/contrato_historico_epoca.py`: en `asignar_sin_seccionado`, la exclusión por «sucesora sin fila» pasa a asignación cuando la sucesora es hija sin dato de B' y contiene la sección del Censo; la hija sale de `sin_dato`.
- Se regenera el contrato 2011-11 (1.6.0). Necesita `1mun00` del espejo de la PR #982.
- Test con el literal 270 del Censo.
- Para nac08_h2011_11: «Generar desde fuente territorial acreditada».
