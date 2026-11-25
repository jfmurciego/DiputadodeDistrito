<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Propuesta de plan de mejora derivada de la auditoría integral del 24-11
FECHA: 2026-11-25
ESTADO: PROPUESTA para aprobar. No es el plan (`docs/PLAN.md` no se toca), no implementa ni lanza nada
CAMBIOS: fichero nuevo
MOTIVO: encargo del propietario (25-11): convertir cada hallazgo de la auditoría en tareas con prioridad y propuesta de
  decisión, y llevar todos los ámbitos a nivel de referencia mundial salvo la desigualdad de los distritos, que se acepta
ANTERIOR: ninguna (fichero nuevo)
-->

# Propuesta de plan de mejora — de la auditoría a la cola de tareas

**Base:** `CLAUDE.md`, `docs/PLAN.md` 1.0.77, las decisiones D-205 a D-210 del 25-11 (tomadas en el chat del Planificador,
aún sin escribir en el plan), el diseño aprobado del mapa (T-458, PR 1013) y
`docs/AUDITORIAS/AUDITORIA_INTEGRAL_2026-11-24.md`.

**Qué es esto:** una propuesta. Nada se abre hasta que el propietario lo apruebe; cada tarea de estudio lleva su pregunta
para aprobar antes (D-18); cada tarea de producto empieza por un diseño al detalle (regla del 16-11).

**Identificadores:** el Planificador vivo ha dado hasta T-462 (a las 08:41 UTC del 25-11). Esta propuesta usa T-463 a
T-498 de forma **provisional**: los confirma quien escriba el plan.

---

## 1. Revisión de la auditoría

### 1.1 Una corrección

La auditoría decía que el depósito con DOI contenía solo el mapa de Huesca. El plan 1.0.77 recoge un depósito real
posterior de la serie de mapas (DOI 10.5281/zenodo.24448721, T-434). Lo que sigue pendiente es que `README.md`,
`CITATION.cff` y la web lo citen. La auditoría queda corregida en su versión 1.0.1 y el arreglo va en T-463.

### 1.2 Lo que ya han resuelto las decisiones del 25-11

| Hallazgo de la auditoría | Decisión o tarea ya en marcha | Qué queda |
|---|---|---|
| Etiqueta «Patriotas» | D-210, T-460: pasa a «Derecha nacional», en origen | La regla por defecto de la doble vuelta (T-479, pregunta dentro de la tarea) |
| Panel con jerga, leyenda y datos abajo | D-206, D-209, T-459: cifras arriba, colores fijos, ventana del distrito | Glosario y prueba con personas (T-486) |
| Nivel de sección confuso en el mapa | D-205, T-459: se retira | — |
| Distritos sin nombre | D-208, T-461 | Página propia por distrito (T-483) |
| Imagen y atribución | D-207, T-462 | — |

### 1.3 Lo que el propietario acepta y no genera tarea

**Desigualdad de población de los distritos** (incluidos Águilas, La Graciosa y las islas): se acepta tal como está
(decisión del 25-11 en este chat). No se abre ninguna tarea para corregirla. Solo se propone declararla en público
con sus cifras, dentro de la página de confianza (T-488, pregunta 8).

---

## 2. Qué significa «nivel de referencia mundial», ámbito por ámbito

Sin una meta medible, «top mundial» no se puede aprobar ni comprobar. Esta es la que se propone.

| Ámbito | Nota hoy | Meta | Cómo se comprueba | Tareas |
|---|:---:|---|---|---|
| Reproducibilidad y procedencia | 9 | Una persona ajena reproduce un mapa bit a bit sin ayuda, en menos de 15 minutos | Prueba real con alguien elegido por el propietario | T-472 |
| Algoritmo | 6,5 | Hueco certificado en los 71 territorios; óptimo demostrado en las 44 provincias con K ≤ 10; nunca peor que GerryChain puro ni que `redist` en un banco público; 10.000 mapas alternativos por provincia con diagnóstico | Banco publicado, con los casos perdidos a la vista | T-465 a T-471 |
| Validación externa | 3 | Dos revisiones con nombre publicadas, una reproducción independiente, un informe técnico con DOI enviado a revista | Página pública de revisiones | T-472 a T-475 |
| Datos electorales | 8,5 | Conjunto completo por partido, distrito y elección, con DOI, validador y contraste cruzado | Cuadre al 100 % con el BOE y validador público | T-476 |
| Análisis político | 4,5 | Indicadores estándar, sensibilidad con intervalos, sesgo del mapa medido, marco con bibliografía verificada, informe citable | Informe aprobado por el propietario y revisado por el consejo | T-477 a T-481 |
| Web y mapa | 6,5 | Encontrar tu distrito por calle en 10 segundos; página propia por distrito; primera vista en móvil en 2,5 s; accesibilidad verificada; cero afirmaciones sin evidencia; resumen en inglés | Medición continua y prueba con cinco personas ajenas | T-463, T-482 a T-489 (sobre T-459 a T-462) |
| Proceso | 6 | 90 % de campañas a la primera; menos del 10 % de minutos en fallos; suite de PR en 8 minutos; sin copias manuales de versiones; operable por una persona sin agentes | Tablero semanal | T-490 a T-494 |
| Dirección | 7 | Identidad y licencia cerradas; consejo asesor; continuidad asegurada; nunca más de tres temas abiertos | Decisiones registradas y cumplidas tres meses | T-473, T-494 a T-496 |
| Calidad de los mapas | 7 y 5 | Desigualdad aceptada. El resto: ficha de calidad publicada y percentil frente a las alternativas | — | T-469, T-470 |

---

## 3. Reglas del plan

1. **Por olas, con puerta.** Una ola se abre cuando la anterior no tiene ninguna tarea de prioridad 0 abierta y al
   menos el 80 % está hecha.
2. **Nunca más de tres temas abiertos a la vez** y de dos a cinco chats (regla del 14-11). Es la respuesta directa al
   hallazgo de foco de la auditoría: 36 tareas nuevas abiertas a la vez repetirían el problema.
3. **Nada toca producción antes del 29-11.** La ola 0 es solo texto y decisiones.
4. **Diseño antes que implementación.** Cada tarea de producto entrega primero un diseño al detalle para aprobar; la
   implementación se reparte después en tareas del Planificador, como se hizo con el mapa.
5. **Estudios con pregunta aprobada** (D-18) y resultados que no salen del repositorio sin aprobación.
6. **Lanzar y publicar**, solo el Operador con frase del propietario y campaña con ficha.
7. **Nivel:** económico por defecto; nivel de motor solo en las tareas que tocan Deslinde, el exacto o las cadenas.
8. **Un escritor por fichero compartido** (§7).
9. **El motor cambia una sola vez:** lo que mejore Deslinde entra en producción con el corte de la legislatura nueva,
   no antes, para regenerar una vez.

---

## 4. Tabla de tareas para aprobar

Prioridad: P0 = imprescindible; P1 = alta; P2 = media; P3 = baja. El calendario lo marca la ola, no la prioridad.

### Ola 0 — antes del 29-11 (solo texto y decisiones)

| Id | Ámbito | Tarea | Prio. | Depende de | Nivel | Propuesta de decisión |
|---|---|---|:---:|---|---|---|
| T-463 | Web, credibilidad | Textos públicos veraces: retirar de Metodología «miles de mapas alternativos» y «repetirlo»; DOI vigente en `README.md`, `CITATION.cff` y «Cómo citar»; barrido de afirmaciones públicas contra evidencia | P0 | — | Económico | Sí: se quitan hasta que sean verdad; se publica con «Solo el sitio» |
| T-464 | Plan | Actualización del plan: D-205 a D-210, las decisiones de esta ronda y la cola aprobada | P0 | Respuestas del propietario | Planificador | La escribe el Planificador vivo; este chat no toca `docs/PLAN.md` |

La noche electoral del 29-11 no genera tarea nueva: ya está en el plan (D-99, D-118, D-149; PR 800 y 801). Va como
pregunta 3.

### Ola 1 — diciembre: que el motor demuestre lo que vale y que otros puedan comprobarlo

| Id | Ámbito | Tarea | Prio. | Depende de | Nivel | Propuesta de decisión |
|---|---|---|:---:|---|---|---|
| T-465 | Algoritmo | Banco público de comparación: diseño del protocolo (instancias, métodos, métricas, cómputo). Solo documento | P0 | — | Motor | Aprobar la pregunta de estudio y el protocolo; sin lanzar |
| T-466 | Algoritmo | Banco: ejecución y tabla de resultados | P0 | T-465 | Motor | Campaña con ficha y tope de minutos; se publica aunque Deslinde pierda en algún caso |
| T-467 | Algoritmo | Deslinde 2, búsqueda: curva de longitud, ráfagas cortas, arranques múltiples, lo que el laboratorio hace y el generador no | P1 | T-466 | Motor | Entra en producción solo con el corte de la legislatura nueva |
| T-468 | Algoritmo | Cotas y óptimo: hueco certificado en los 71 y óptimo demostrado con K ≤ 10. Diseño y prototipo | P1 | T-465 | Motor | Resolutor abierto y determinista; objetivo de 44 provincias con óptimo y 8 con cota |
| T-469 | Algoritmo, web | Mapas alternativos generados desde Deslinde: 10.000 por provincia, con diagnóstico y percentil del mapa elegido | P1 | T-466 | Motor (diseño) | Vuelven los alternativos; cumple la condición que puso D-138 |
| T-470 | Algoritmo, datos | Ficha de calidad de cada mapa: forma, cortes, demarcaciones partidas, desvíos, exenciones | P1 | — | Económico | Se publica siempre, también cuando no favorece |
| T-471 | Algoritmo | D8 declarada y congelada: cómo se eligió, sensibilidad al tope y a los pesos, huella y fecha antes de regenerar | P1 | T-466 | Motor | Congelar D8 antes de ver los mapas de la legislatura nueva |
| T-472 | Reproducibilidad | Kit de reproducción para terceros: contenedor fijado, un comando, guía de dos páginas, prueba con una persona ajena | P0 | T-473 | Económico | Aprobar el kit y elegir a la persona de la prueba |
| T-473 | Dirección | Licencia, marca e identidad: documento de opciones de una página | P0 | — | Económico | Opción B: código visible con licencia de reproducción para investigación, más registro de marcas; sin más cambios en 12 meses |
| T-474 | Validación | Revisión externa: dossier, plantilla de informe, tres perfiles, página pública «Revisiones» | P1 | T-466, T-472 | Económico | El propietario elige e invita; los informes se publican íntegros |
| T-475 | Validación | Informe técnico de Deslinde (preprint), en español y en inglés, con DOI | P1 | T-466, T-468 | Motor | Publicar sin abrir el código: cambia D-94 solo en eso |

### Ola 2 — enero y febrero: el análisis y el producto público

| Id | Ámbito | Tarea | Prio. | Depende de | Nivel | Propuesta de decisión |
|---|---|---|:---:|---|---|---|
| T-476 | Datos | Datos abiertos 2: por partido, distrito y elección, con diccionario, validador, contraste cruzado y DOI; borrador de artículo de datos | P2 | T-470 | Económico | Publicar por distrito (D-205 lo permite) |
| T-477 | Análisis | Marco teórico y bibliografía verificada, de seis a ocho páginas | P1 | — | Económico | Aprobar la pregunta; el texto final lo aprueba el propietario |
| T-478 | Análisis | Indicadores por elección y sistema: desproporcionalidad, número efectivo de partidos, prima, votos sin representación, desigualdad de reparto | P1 | T-476 | Económico | Aprobar la pregunta; se publican para todos los sistemas |
| T-479 | Análisis | Sensibilidad de la doble vuelta: escenarios de trasvase y abstención, intervalo de escaños, distritos decididos y en el aire | P1 | T-476 | Motor | Aprobar la pregunta; regla por defecto de la web, dentro del diseño |
| T-480 | Análisis | Sesgo y robustez del mapa: curva de votos y escaños, media y mediana, percentil frente a las alternativas | P2 | T-469, T-478 | Económico | Aprobar la pregunta |
| T-481 | Análisis | Informe «España en distritos uninominales, 2011-2026» | P2 | T-477 a T-480 | Económico | Lo aprueba el propietario antes de salir |
| T-482 | Web | «Busca tu distrito» por municipio, código postal y calle, con el callejero del INE y sin terceros | P1 | T-459, T-461 | Económico | La dirección no sale del navegador |
| T-483 | Web | Página propia por distrito, con dirección estable e imagen para compartir | P1 | T-461, T-462 | Económico | Las 407 del Congreso primero |
| T-484 | Web | Portada de estudio: cifras verificadas y «Busca tu distrito»; la causa, en página propia | P1 | T-482 | Económico | Opción B de la auditoría; textos e imágenes, del propietario |
| T-485 | Web | Móvil primero: vista rápida aprobada (D-192), teselas vectoriales, presupuesto de rendimiento como puerta | P1 | T-459, T-430 | Económico | 100 KB en la primera vista y 2,5 s en móvil, o no se publica |
| T-486 | Web | Lenguaje llano y prueba con cinco personas ajenas | P2 | T-459 | Económico | Glosario único; se corrige lo que no entiendan tres de cinco |
| T-487 | Web | Accesibilidad verificada con lector de pantalla y móviles reales; declaración pública | P2 | T-485 | Económico | Declaración de accesibilidad firmada |
| T-488 | Web, credibilidad | Página «Confianza»: revisores, cómo citar, contacto, licencias, límites y decisiones aceptadas; resumen y método en inglés | P2 | T-474 | Económico | Incluye la desigualdad aceptada, con sus cifras |
| T-489 | Web | Un solo sitio: retirar del público V2, V3, visor nacional y tablero; cabeceras de seguridad; cero llamadas a terceros (con T-316) | P2 | T-430 | Económico | Redirigir todo a la V4 |

### Ola 3 — febrero y marzo: proceso y dirección

| Id | Ámbito | Tarea | Prio. | Depende de | Nivel | Propuesta de decisión |
|---|---|---|:---:|---|---|---|
| T-490 | Proceso | Gobernanza ligera: git como archivo de versiones; `ANTERIOR` apunta a un commit comprobado por test; sin copias nuevas en `legacy/` | P1 | — | Motor (diseño) | Las cabeceras de versión se conservan; las copias físicas, no |
| T-491 | Proceso | A la primera: preflight único en contenedor, pruebas por impacto, métricas del proceso arregladas, tablero semanal | P1 | — | Económico | Metas: 90 % a la primera, menos del 10 % de minutos en fallos, suite en 8 minutos |
| T-492 | Proceso | Operable por una persona: índice único, archivo de lo histórico, manual sin agentes probado por un tercero | P2 | T-490 | Económico | Un tercero ejecuta una campaña de prueba solo con el manual |
| T-493 | Proceso | Segundo control proporcional al publicar: resumen previo de lo que cambia y revisor obligatorio solo en P40 y P50 | P2 | — | Económico | Matiza D-127 |
| T-494 | Dirección | Decisiones y foco: ficha de decisión de cinco líneas, límite de tres temas, libro de costes único | P2 | — | Económico | Regla nueva en `CLAUDE.md` |
| T-495 | Dirección | Consejo asesor y continuidad: encargo de tres perfiles, segundo mantenedor, custodia de cuentas | P1 | T-473 | Económico | Consejo con veto sobre lo que se afirma en público |
| T-496 | Dirección | Plan de difusión 2026-2027: calendario, piezas y kit, solo con datos técnicos verificados | P2 | T-481 | Económico | Temas y textos, del propietario (D-18) |
| T-497 | Participación | Observaciones públicas por distrito, con respuesta publicada. Solo diseño | P3 | T-483 | Económico | Solo diseño por ahora |
| T-498 | Algoritmo | Un caso de referencia de otro país, de los que usa la literatura | P3 | T-475 | Motor | Solo después del informe técnico |

---

## 5. Ficha de cada tarea

Formato: alcance · criterio de hecho · ficheros o turno · efecto externo. Las de estudio llevan su pregunta (D-18).

### Ola 0

**T-463 · Textos públicos veraces.** Alcance: en `documentacion_publica/docs/metodo.md`, la frase de los «miles de
mapas alternativos» pasa a decir lo que hoy se hace («cada mapa compite con otros candidatos generados con las mismas
reglas y se publica el mejor según un criterio fijo y público») y la de «revisarlo o repetirlo» se ajusta a la licencia
vigente; DOI vigente en `README.md`, `CITATION.cff` y `citar.md`; tabla frase ↔ evidencia ↔ estado de toda afirmación
pública (web, documentación pública, README). Hecho: cero afirmaciones sin evidencia y un test que impide volver a
publicar las frases retiradas mientras no exista el producto. Turno: `metodo.md` (después, T-488). Efecto externo: una
publicación «Solo el sitio».

**T-464 · Actualización del plan.** La hace el Planificador vivo con lo aprobado aquí.

### Ola 1

**T-465 · Banco de comparación, diseño.** Pregunta: «¿Qué calidad tiene Deslinde frente a GerryChain puro, `redist` y
el óptimo demostrado, en los mismos territorios, con las mismas reglas y las mismas unidades?». Alcance: instancias
neutras con el formato del estudio del óptimo exacto para 14 territorios (los 8 pequeños con óptimo conocido; Madrid,
Barcelona y Valencia; La Rioja, Madrid y Cataluña autonómicas) y 3 instancias públicas de las que usa la literatura,
para que otros puedan compararse; métodos: Deslinde 1.1, cadenas ReCom puras con 10³, 10⁴ y 10⁵ pasos, ráfagas cortas,
SMC de `redist` con 5.000 y 50.000 planes, y el exacto; métricas: la clave D8 término a término, hueco al óptimo o a la
mejor cota, tiempo, memoria y fracción de planes válidos; diez semillas públicas; entorno fijado. Hecho: protocolo
aprobado, con tabla vacía, presupuesto de cómputo y revisión independiente. No lanza nada.

**T-466 · Banco, ejecución.** Alcance: ejecutar el protocolo en el flujo de verificación del motor o en un equipo
propio; resultados versionados; cada caso en que Deslinde pierda abre su tarea. Hecho: tabla completa, reproducible con
un comando. Turno: `p80-verificacion-motor.yml`. Efecto externo: campaña con ficha.

**T-467 · Deslinde 2, búsqueda.** Alcance: medir la curva de longitud (300, 3.000 y 30.000 pasos), ráfagas cortas
sobre la clave D8, arranques múltiples y paralelismo; incorporar lo que el laboratorio hacía y el generador no (objetivo
por circunscripción y corte por la mitad de la población). Hecho: en los 8 casos con óptimo conocido lo alcanza sin el
exacto en al menos 7; en el banco, nunca peor que el mejor competidor heurístico con el mismo presupuesto; tiempo por
territorio no mayor del doble; reproducible bit a bit. Turno: `paquetes/deslinde/` y `ddd_motor2/`, uno a la vez con
T-468 y T-469. Cambia mapas: producción solo con el corte.

**T-468 · Cotas y óptimo.** Alcance: diseño y prototipo de cotas inferiores por cada término de D8 y de óptimo más allá
de K = 4; técnicas a evaluar: cortes de contigüidad perezosos, descomposición por subterritorios, generación de columnas
con precio exacto para la cota. Hecho: «hueco certificado» publicado para los 71, aunque sea holgado, y óptimo demostrado
en las 44 provincias del Congreso con K ≤ 10 (hoy: 8 triviales y hasta 16 con K de 2 a 4).

**T-469 · Mapas alternativos.** Alcance: generación desde el mapa de Deslinde; 10.000 planes válidos por provincia del
Congreso con el método que mejor salga del banco; varias cadenas y diagnóstico de convergencia sobre métricas resumen;
producto «Alternativas» en el archivo (métricas de todos los planes y una muestra de 100, no 10.000 geometrías);
percentil del mapa elegido; gráfico por provincia en la web. Hecho: diagnóstico en verde en al menos el 90 % de los
territorios y la frase de Metodología vuelve, con enlace a los datos. Autonómicas, después.

**T-470 · Ficha de calidad.** Alcance: Polsby-Popper, Reock, aristas y kilómetros cortados, municipios, partidos
judiciales y comarcas partidos, desvío medio, máximo y percentiles, número de exenciones; en el producto certificado,
en datos abiertos y en la ficha del territorio. Hecho: 71 fichas con test de cuadre contra la composición.

**T-471 · D8 declarada y congelada.** Alcance: documento público «Cómo se eligió D8» con la cronología de decisiones y
lo que se miró en cada una; sensibilidad con tope del 5, 8 y 10 %, recargos a la mitad y al doble, y el orden de los
términos de demarcaciones y frontera cambiado; cuántos territorios cambian de ganador en cada variante. Hecho: D8 con
huella y fecha anteriores a la primera regeneración de la legislatura nueva.

**T-472 · Kit de reproducción.** Alcance: imagen de contenedor fijada por su resumen, un comando que regenera Huesca y
una provincia grande y compara la huella con la publicada, guía de dos páginas, comprobación en una máquina limpia.
Hecho: una persona sin acceso previo lo consigue en menos de 15 minutos solo con la guía.

**T-473 · Licencia, marca e identidad.** Alcance: una página con tres opciones (A, cerrada como hoy; B, código visible
con licencia de reproducción para investigación; C, reglas y validador abiertos y motor cerrado), la separación de voces
entre Deslinde (motor y estudio) y Diputado de Distrito (la propuesta), y el registro de marcas, que tramita el
propietario. Hecho: decisión registrada, `LICENSE` y textos públicos alineados.

**T-474 · Revisión externa.** Alcance: dossier (definición formal, banco, kit, datos), plantilla de informe, perfiles
(sistemas electorales; optimización o estadística de distritación; cartografía o derecho electoral), página «Revisiones».
Hecho: al menos dos informes publicados íntegros, con respuesta.

**T-475 · Informe técnico.** Alcance: problema, reglas, D8, semilla pública, contrato, banco, cotas y límites; en
español y en inglés; depósito con DOI. Hecho: depositado y enviado a la revista que elija el propietario.

### Ola 2

**T-476 · Datos abiertos 2.** Alcance: tabla por partido, distrito y elección (2011 a 2023, 2026 cuando exista el
escrutinio por mesa, y las autonómicas con datos por sección), doble vuelta por regla, composición y ficha de calidad;
diccionario, esquema y validador; contraste por provincia con el BOE y con el archivo SEA. Hecho: cuadre al 100 % con
el BOE, validador público y DOI.

**T-477 · Marco teórico.** Pregunta: «¿Qué dice la evidencia comparada sobre el distrito uninominal y la doble vuelta
(voto personal, disciplina de partido, desproporcionalidad, participación) y qué hipótesis del proyecto se pueden
medir?». Hecho: de 25 a 40 referencias, cada una comprobada con su DOI o ISBN, nunca de memoria.

**T-478 · Indicadores.** Pregunta: «¿Cómo cambian la proporcionalidad, la fragmentación y la representación territorial
con cada sistema, de 2011 a 2023?». Alcance: sistema real, mayoría simple y doble vuelta con cada regla. Hecho: fórmulas
con test contra valores publicados y bloque «Qué cambiaría» en la web.

**T-479 · Sensibilidad de la doble vuelta.** Pregunta: «¿Cuántos distritos cambian de ganador si el trasvase no es
total o si parte de los eliminados se abstiene?». Alcance: escenarios con trasvase del 100, 80 y 60 % y abstención
diferencial; estimación con microdatos postelectorales públicos si la nube llega a ellos (si no, descarga manual del
propietario). Hecho: por distrito, ganador y margen por escenario; escaños con intervalo. Dentro del diseño, la pregunta
de la regla por defecto en la web (hoy «Tres bloques»; recomendación técnica: «Sin coaliciones», que es el supuesto
mínimo).

**T-480 · Sesgo y robustez del mapa.** Pregunta: «¿Favorece el mapa elegido a algún bloque frente a los mapas
alternativos válidos?». Hecho: curva de votos y escaños, diferencia entre media y mediana y percentil del resultado.

**T-481 · Informe de síntesis.** Hecho: informe aprobado por el propietario y revisado por el consejo.

**T-482 · Busca tu distrito.** Alcance: callejero del censo electoral del INE (tramo de vía → sección → distrito) y
códigos postales, servidos por municipio desde el propio sitio; la búsqueda se resuelve en el navegador. Hecho: 99 % de
acierto en una muestra de 1.000 tramos; menos de 50 KB por municipio.

**T-483 · Página por distrito.** Alcance: una página estática por distrito generada en la publicación, con nombre,
datos (D-209), mapa, imagen para compartir, datos estructurados y descarga. Hecho: 407 páginas en el mapa del sitio.

**T-484 · Portada de estudio.** Alcance: maqueta con titular numérico («407 distritos», «la desigualdad entre
provincias baja del 10,7 % al 1,9 %»), buscador y acceso a la causa en página propia; las imágenes de cabecera y el pie
los decide el propietario. Hecho: maqueta aprobada.

**T-485 · Móvil y rendimiento.** Alcance: lo que falta de D-192 (vista rápida del mapa), teselas vectoriales desde el
archivo, medición en cada publicación. Hecho: primera vista de 100 KB comprimidos y 2,5 s en móvil.

**T-486 · Lenguaje llano.** Hecho: glosario único y guion de prueba con cinco personas ajenas; se corrige lo que no
entiendan tres.

**T-487 · Accesibilidad verificada.** Hecho: informe con lector de pantalla y tres móviles reales; declaración pública.

**T-488 · Página «Confianza».** Alcance: revisores e informes, cómo citar con DOI, contacto, licencias, límites y
decisiones aceptadas con sus cifras, material de prensa; resumen y método en inglés. Turno: `metodo.md` tras T-463.

**T-489 · Un solo sitio.** Alcance: retirar del sitio público las versiones anteriores, con redirecciones; cabeceras
de seguridad; junto con el fondo de mapa propio (T-316). Turno: `p40-publicacion.yml`, después de que T-430 retire Pages.

### Ola 3

**T-490 · Gobernanza ligera.** Alcance: diseño para que `ANTERIOR` apunte a un commit comprobado por test en vez de a
una copia; herramienta que recupera cualquier versión; adaptación del test de gobernanza. Hecho: ninguna copia nueva en
`legacy/` y las 2.611 existentes archivadas fuera del árbol de trabajo o conservadas como historia, según decida el
propietario. Turno exclusivo: test de gobernanza, `CLAUDE.md` y reglas.

**T-491 · A la primera.** Alcance: un único preflight en contenedor antes de cualquier campaña, pruebas de PR por
impacto, `metricas_proceso.py` por ventanas (hoy pierde datos) y tablero semanal. Hecho: tres semanas seguidas en meta.

**T-492 · Operable por una persona.** Hecho: un tercero ejecuta una campaña de prueba de un territorio solo con el manual.

**T-493 · Segundo control.** Alcance: antes de publicar, resumen de territorios, huellas y diferencias con lo publicado;
revisor obligatorio solo en los entornos de publicación.

**T-494 · Decisiones y foco.** Alcance: ficha de cinco líneas (qué, por qué, alternativa, qué la cambiaría, cuándo
caduca), límite de tres temas, medida mensual de decisiones corregidas, libro de costes único de agentes y ejecución.

**T-495 · Consejo asesor y continuidad.** Alcance: encargo para tres perfiles, segundo mantenedor con permisos,
custodia de dominio, cuentas y secretos. Las personas las elige el propietario.

**T-496 · Plan de difusión.** Alcance: calendario y piezas, con el kit de comunicación que quedó en borrador; solo
datos técnicos verificados.

**T-497 · Observaciones públicas.** Solo diseño. **T-498 · Otro país.** Solo tras el informe técnico.

---

## 6. De cada hallazgo a su tarea

| Hallazgo de la auditoría | Destino |
|---|---|
| Cero validación externa | T-472, T-474, T-475 |
| La licencia contradice «repetirlo» | T-463 ahora; T-473 de fondo |
| «Miles de mapas alternativos» no se cumple | T-463 ahora; T-469 de fondo |
| Desigualdad de población y atípicos | Aceptado; se declara en T-488 |
| Búsqueda corta | T-467 |
| Sin cota fuera de lo pequeño | T-468 |
| Sin comparación con otros métodos | T-465, T-466 |
| Sin mapas alternativos | T-469 |
| Función de elección decidida viendo mapas | T-471 |
| Compacidad sin publicar por plan | T-470 |
| Margen del laboratorio sin recoger en autonómicas | T-467 |
| Sin participación pública | T-497 |
| Resultado principal sin contar; sin índices | T-478, T-481 |
| Doble vuelta sin sensibilidad | T-479 |
| Etiquetas de bloques | D-210 y T-460, en curso |
| Supuesto por defecto de la doble vuelta | T-479 |
| Resultado dependiente del trazado | T-469, T-480 |
| Sesgo del mapa sin medir | T-480 |
| Sin bibliografía ni hipótesis a prueba | T-477 |
| Portada que mezcla consigna e investigación; sin datos | T-484 |
| El mejor resultado (10,7 % → 1,9 %) no se cuenta | T-484, T-478 |
| Jerga, leyenda, datos abajo | T-459 en curso; T-486 |
| Sin búsqueda por calle ni página por distrito | T-482, T-483 |
| Móvil pesado | D-192; T-485 |
| Accesibilidad sin verificar en real | T-487 |
| Restos de versiones anteriores | T-489 |
| Pie hostil; imágenes generadas | Pregunta dentro de T-484 |
| Faltan piezas de confianza e inglés | T-488 |
| DOI de la serie sin citar | T-463 |
| Informe técnico descartado | T-475 |
| Copias `legacy/`, documentación desbordada | T-490, T-492 |
| Minutos en fallos; éxito a la primera | T-491 |
| Decisiones corregidas; frentes abiertos | T-494; regla 2 de §3 |
| Sin revisor al lanzar y publicar | T-493 |
| Una sola persona; sin contrapeso | T-495, T-492 |
| Dependencia de agentes para operar | T-492 |
| Identidad y licencia sin cerrar | T-473 |
| Comunicación y prensa | T-496 |
| Noche del 29-11 sin ensayo | Ya en el plan; pregunta 3 |
| Notaciones y versiones del visor en serie | Regla 2 de §3; T-494 |

---

## 7. Ficheros compartidos y turnos

| Fichero o zona | Orden de escritores |
|---|---|
| `visor/v4/` | T-459 (en curso) → T-486 → T-485 → T-482 → T-483 → T-484 |
| `documentacion_publica/docs/metodo.md` | T-463 → T-469 (la frase vuelve) → T-488 |
| `paquetes/deslinde/`, `ddd_motor2/` | T-467 → T-468 → T-469 |
| `p80-verificacion-motor.yml` | T-466 → T-469 |
| `p40-publicacion.yml` | T-430 (en curso) → T-483 → T-489 |
| Gobernanza, `CLAUDE.md`, reglas | T-490 → T-494 |
| `README.md`, `CITATION.cff`, `LICENSE` | T-463 → T-473 |

---

## 8. Preguntas al propietario

Una sola ronda. Un «sí» acepta la recomendación.

1. **Alcance y orden.** ¿Apruebo las olas 0 y 1 y dejo las olas 2 y 3 en cola, para abrirlas al cerrar la anterior,
   con un máximo de tres temas abiertos? Recomendación: sí.
2. **Textos de método.** ¿Se retiran ya las dos frases y se añade el DOI vigente, y se publica con «Solo el sitio»
   cuando des la frase al Operador? Recomendación: sí.
3. **Noche del 29-11.** ¿Sin un ensayo en seco completo antes del 28-11 no hay directo y se publica con el escrutinio
   definitivo por mesa, como prevé D-118? Recomendación: sí.
4. **Licencia.** ¿Opción B: código visible con licencia de reproducción para investigación, más el registro de las
   marcas? Recomendación: sí. Sin ella, ni el kit ni la revisión externa pueden llegar a su meta.
5. **Publicación científica.** ¿Se publica un informe técnico sin abrir el código, cambiando D-94 solo en eso?
   Recomendación: sí.
6. **Mapas alternativos.** ¿Vuelven, generados desde Deslinde, como preveía D-138? Recomendación: sí.
7. **Motor.** ¿Deslinde 2 y la función D8 congelada entran con el corte de la legislatura nueva, para regenerar una
   sola vez? Recomendación: sí.
8. **Desigualdad aceptada.** ¿Se registra como decisión y se declara en la web con sus cifras, sin tareas de
   corrección? Recomendación: sí. Lo declarado se defiende mejor que lo descubierto.
9. **Tope.** ¿Olas 0 y 1 con un tope de 300 USD de agentes y 3.500 minutos de ejecución, con aviso al 70 %?
   Recomendación: sí.
10. **Quién escribe el plan.** ¿El Planificador vivo integra lo aprobado en el plan 1.0.78, con D-205 a D-210, y este
    chat no toca `docs/PLAN.md`? Recomendación: sí. Dos planificadores escribiendo el mismo fichero es el riesgo que
    el propio plan prohíbe.

---

## 9. Coste y calendario estimados

Estimación a partir del libro de costes de los chats cerrados del 15 al 24-11 (de 0,6 a 39 USD por tarea). Margen
amplio: puede desviarse a la mitad o al doble. No incluye a Coordinador, Planificador y Operador.

| Ola | Tareas | Agentes (USD) | Ejecución (min) | Publicaciones | Plazo |
|---|:---:|:---:|:---:|:---:|---|
| 0 | 2 | 5-10 | 0 | 1 | 25 a 28-11 |
| 1 | 11 | 130-290 | 2.000-3.500 | 0 | 30-11 a 20-12 |
| 2 | 14 | 85-210 | 300-600 | 4-6 | enero y primera semana de febrero |
| 3 | 9 | 60-150 | 100-300 | 0-1 | febrero y marzo |
| **Total** | **36** | **280-660** | **2.400-4.400** | **5-8** | **unas 16 semanas** |

---

## 10. Riesgos del propio plan

| Riesgo | Mitigación |
|---|---|
| Que el plan repita el defecto que corrige: demasiados frentes | Olas con puerta y tres temas como máximo |
| Que el banco deje mal a Deslinde en algún caso | Se publica igual: la credibilidad viene de enseñarlo; el caso abre tarea |
| Que los revisores no contesten | Convocatoria abierta con el kit y la página de revisiones; el consejo como primera revisión |
| `redist` exige un entorno aparte | Contenedor propio en un equipo o runner; no entra en las dependencias del motor |
| Diez preguntas pendientes del propietario | Una sola ronda; la ola 1 solo necesita las preguntas 1, 4, 5, 6, 7 y 9 |
| Choque con el trabajo en curso (mapa de la V4, noche electoral) | Turnos de §7; nada antes del 29-11 salvo texto |
| Identificadores repetidos entre dos planificadores | Provisionales hasta que el Planificador vivo los escriba |
