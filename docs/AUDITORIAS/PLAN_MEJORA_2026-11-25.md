<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 2.0.0
NOMBRE DE VERSIÓN: Plan de mejora — qué falta, por qué importa y qué se propone (informe para decidir)
FECHA: 2026-11-25
ESTADO: PROPUESTA. Nada está autorizado. No es el plan (`docs/PLAN.md` no se toca); no implementa ni lanza nada
CAMBIOS: 2.0.0 (25-11, tarde) — reescrito a petición del propietario: cada tarea explica qué problema resuelve, por qué
  importa, qué se haría, qué se recibe y qué pasa si no se hace; el coste se expresa dentro del plan semanal, sin gasto
  adicional; desaparecen las olas hasta marzo; la decisión se pide por bloques. 1.0.0 — primera propuesta (tabla de tareas).
MOTIVO: el propietario no puede juzgar una tarea sin su porqué; sin informe detallado no autoriza nada
ANTERIOR: 1.0.0 en el commit 3640edab de esta misma rama (documento sin fusionar; sin copia en `legacy/`)
-->

# Plan de mejora: qué falta, por qué importa y qué propongo

**Informe para decidir · 25-11-2026 · Estado: propuesta. Nada de lo que aparece aquí está autorizado.**

## Cómo leer este informe

Está organizado en **13 bloques**, de la A a la M. Cada bloque responde a una carencia concreta del proyecto y sigue
siempre el mismo orden:

1. **Lo que pasa hoy**, con un dato o un ejemplo del propio proyecto.
2. **Por qué importa**: qué pierdes o qué riesgo corres.
3. **Qué hacen los mejores**, para que se vea la distancia.
4. **Qué propongo**, tarea a tarea: qué se hace, qué recibes, qué necesito de ti, qué tamaño tiene y qué pasa si no se hace.
5. **Mi opinión sobre la necesidad**: imprescindible, importante, conveniente o aplazable. Es mi opinión; la decisión es tuya.

Al final hay una **hoja de decisión** de una página: basta con contestar bloque a bloque «sí», «no» o «más adelante».

Los identificadores (T-463 a T-498) son provisionales: el Planificador vivo ha dado hasta T-462. La T-464 queda
reservada para la actualización del plan y no aparece en los bloques.

---

## 1. Tus dos objeciones, contestadas

### 1.1 El coste: tienes razón, lo planteé mal

Puse una cifra en dólares como si fuera dinero que hubiera que pagar. No lo es.

- La cifra salía del **libro de costes** del proyecto, donde cada chat anota su consumo equivalente al cerrarse. No es
  una factura: es una medida del tamaño de cada trabajo.
- Tú pagas un plan semanal fijo y dices que no lo has agotado en las dos últimas semanas. Esta misma sesión lo confirma
  por su lado: no está usando consumo extra.
- La ejecución en GitHub tampoco se paga: el repositorio es público. Lo único que hay es el tope que tú fijaste de
  15.000 minutos por semana.

**Regla que propongo, en vez del tope en dólares:** todo se hace dentro del plan semanal, sin gasto adicional. Se
trabaja por orden de prioridad; si una semana el plan se acaba, se para y se sigue la siguiente. Lo que quepa se hace
y lo que no, espera. Es exactamente lo que has dicho.

**Para que puedas juzgar el tamaño de cada tarea** sin dólares, uso tres tallas, comparadas con tareas tuyas ya cerradas:

| Talla | Se parece a | En el libro de costes |
|---|---|---|
| Pequeña | La clave fija del informe de la doble vuelta (T-453), el reintento de la publicación (T-454) | De 1,6 a 2,6 |
| Mediana | El árbol nuevo del archivo (T-443), el histórico de 2011 con Ceuta y Barcelona (T-448) | De 10 a 20 |
| Grande | Las autonómicas de Castilla-La Mancha (T-449), la web servida desde el archivo (T-430) | Unos 40 |

**Y el conjunto, comparado con lo que ya haces:** entre el 15 y el 24-11 el libro de costes anota unos 350 en chats
cerrados (y es parcial). Las 35 tareas de este informe suman, según mi estimación, entre 280 y 660. Es decir: **todo el
plan pesa entre una y dos veces lo que el proyecto ya consume en diez días, sin que hayas agotado tu plan**. No sé cómo
mide tu plan el límite semanal, así que no puedo traducirlo a «tantas semanas» con exactitud; lo que sí se ve es que
cabe sin pagar más.

### 1.2 El calendario: marzo no era una necesidad

Marzo salía de tres supuestos míos, no de un límite real:

1. Puse el trabajo **en fila**, una ola detrás de otra, con tres temas abiertos como máximo, para no abrir demasiados
   frentes a la vez (era la crítica principal de la auditoría a la dirección).
2. Supuse que cada diseño **espera tu aprobación**, y hay más de veinte.
3. Hay cosas que **no dependen de nosotros**: que un experto de fuera lea y conteste, que una revista responda.

Con tu plan semanal como único límite, lo que depende de nosotros son **semanas, no meses**: este proyecto ha cerrado
más de cien tareas en diez días. Lo que marca el ritmo de verdad son tres cosas: el tiempo que tú quieras dedicar a
leer y aprobar, el orden obligado entre algunas tareas (§16) y la gente de fuera.

**Lo que cambia en esta versión:** desaparecen las olas con fecha. Hay un orden por dependencias y tú eliges el ritmo:
más chats a la vez es más rápido, con más cosas a medio hacer; menos, es más ordenado y más lento.

---

## 2. La idea en una página: qué falta

Pediste llevar todos los ámbitos al nivel de los mejores, salvo la desigualdad de los distritos, que aceptas. Esto es
lo que le falta hoy al proyecto para estar ahí, dicho sin tecnicismos:

| Bloque | Qué falta | Tareas |
|---|---|---|
| A | La web afirma dos cosas que hoy no son verdad | T-463 |
| B | Nadie ha medido el motor contra los programas que usa el resto del mundo | T-465, T-466 |
| C | En 47 de los 71 territorios no sabemos si existe un mapa mejor que el publicado | T-468, T-467 |
| D | Publicamos un mapa por territorio y no hay con qué compararlo | T-469, T-470, T-480 |
| E | La regla que elige el mapa ganador se fijó después de ver mapas | T-471 |
| F | Nadie de fuera ha comprobado ni firmado nada, y hoy no podría | T-473, T-472, T-474, T-475 |
| G | Los datos publicados solo dicen quién gana cada distrito, no los votos | T-476 |
| H | Enseñamos un mapa de colores, no un análisis | T-477, T-478, T-479, T-481 |
| I | Un ciudadano no puede encontrar su distrito escribiendo su calle | T-482, T-483 |
| J | La portada no cuenta lo mejor del proyecto y el mapa pesa en el móvil | T-484 a T-489 |
| K | Una parte del plan semanal se va en repetir y en copiar | T-490, T-491 |
| L | Todo depende de una sola persona y de la memoria de los agentes | T-492 a T-496 |
| M | Dos ideas buenas que pueden esperar | T-497, T-498 |

**Si solo hicieras cinco cosas**, serían estas, porque son las que más cambian el veredicto:

1. Corregir las dos frases de la web (bloque A). Es lo más barato y lo que más daño evita.
2. Medir el motor contra los de referencia (bloque B). Convierte mi opinión en un dato.
3. Los mapas alternativos (bloque D). Contestan a la pregunta que más te harán: «¿el resultado depende de cómo lo habéis dibujado?».
4. Licencia, kit y revisores (bloque F). Sin alguien de fuera que lo confirme, «nivel mundial» es una afirmación nuestra.
5. Buscar por calle y página propia por distrito (bloque I). Es lo que convierte el mapa en algo que la gente usa y comparte.

**Lo que este plan no toca:** la desigualdad de población de los distritos (aceptada) y la noche electoral del 29-11
(la llevan el Planificador, el Coordinador y el Operador con lo que ya está en el plan).

---

## 3. Bloque A — Decir solo lo que es verdad

### Lo que pasa hoy

La página pública «Metodología» dice dos cosas que hoy no se cumplen:

- *«se generan por ordenador miles de mapas alternativos que cumplen las mismas reglas. Comparar con todos ellos permite
  ver si el mapa elegido es normal o si favorece a alguien de forma sospechosa.»* Esos mapas alternativos se retiraron
  el 16-11: eran del motor antiguo, 10 o 25 por territorio, nunca miles. El registro de lo publicado tiene hoy cero.
- *«El programa que dibuja los distritos es público, para que cualquiera pueda revisarlo o repetirlo.»* Se puede leer,
  pero la licencia vigente dice: «El acceso al repositorio no concede ningún derecho de uso». Repetirlo exige tu permiso
  por escrito.

Además, el depósito de la serie de mapas con su DOI ya existe (lo recoge el plan), pero el README, la ficha de cita y la
web siguen citando solo el mapa de Huesca.

### Por qué importa

La portada lleva el rótulo «Investigación verificable». Quien quiera desacreditar el proyecto no necesita entender el
algoritmo: le basta con citar una frase pública que no se cumple. Es el fallo más barato de arreglar y el más caro de dejar.

### Qué propongo

**T-463 · Textos públicos veraces** (talla pequeña)

- **Qué se hace:** la primera frase se cambia por lo que sí hace hoy el motor («cada mapa compite con una docena de
  candidatos generados con las mismas reglas y se publica el mejor según un criterio fijo y público»). La segunda se
  ajusta a la licencia. Se añade el DOI vigente. Se repasan todas las afirmaciones públicas (web, documentación,
  README) y se deja una tabla «frase – prueba». Se añade una comprobación automática para que esas frases no vuelvan
  mientras no sean verdad.
- **Qué recibes:** los textos corregidos para tu visto bueno y la tabla frase – prueba.
- **Qué necesito de ti:** aprobar el texto y dar la frase al Operador para publicar «solo el sitio».
- **Si no se hace:** la contradicción sigue a la vista. Es lo primero que encontrará cualquier revisor.

### Mi opinión sobre la necesidad

Imprescindible, y la primera. Las dos frases podrán volver cuando sean verdad: la de los mapas alternativos con el
bloque D y la de repetirlo con el bloque F.

---

## 4. Bloque B — Saber de verdad cuánto vale el motor

### Lo que pasa hoy

Me preguntaste si jugamos entre los mejores algoritmos del mundo o somos del montón. Te contesté «segunda división
alta». Eso es una opinión razonada, no una medida: **nadie ha puesto nunca a Deslinde a competir con los programas que
usa el resto del mundo.** El plan lo tiene previsto desde el 10-11 (comparación con `redist` y GerryChain), pero lo
dejó «para el final».

### Qué es un banco de comparación

Es una prueba en igualdad de condiciones. Se elige un grupo de territorios. A todos los programas se les dan
exactamente las mismas piezas (las mismas secciones y los mismos municipios indivisibles), las mismas reglas (suelo,
techo, contigüidad, municipios) y el mismo tiempo. Se apunta en una tabla qué mapa encuentra cada uno.

Los programas serían cuatro: Deslinde; GerryChain usado como lo usan sus autores, con cadenas de mil a cien mil pasos
(Deslinde se apoya en él, pero con diez cadenas de 300 pasos); `redist`, el otro gran programa, de Harvard; y, donde se
pueda, el mejor mapa posible demostrado.

### Por qué importa

1. **Responde a tu pregunta con un dato**, no con mi opinión.
2. **Es lo primero que pedirá cualquier experto.** Sin esa tabla no se puede escribir un informe técnico ni pedir una revisión.
3. **Dice dónde hay que mejorar el motor y dónde no.** Evita trabajar a ciegas: por eso la tarea de mejorar la búsqueda
   (T-467) queda condicionada a lo que salga aquí.

**Riesgo, dicho claro:** puede salir que Deslinde gana, que empata o que pierde en algunos territorios. Si pierde, es
mejor saberlo nosotros antes de que lo publique otro.

### Qué hacen los mejores

Todos los métodos serios se presentan con una comparación así. Es el idioma común del campo.

### Qué propongo

**T-465 · Diseño del banco** (talla mediana; solo documento)

- **Qué se hace:** se decide por escrito qué territorios entran (propongo 14 españoles: las 8 provincias pequeñas donde
  ya conocemos el mejor mapa posible; Madrid, Barcelona y Valencia; y La Rioja, Madrid y Cataluña autonómicas; más 3
  casos clásicos de fuera, para que otros puedan compararse con nosotros), qué se mide y cuánto cómputo hace falta.
- **Qué recibes:** un documento de cuatro a seis páginas para aprobar.
- **Qué necesito de ti:** aprobar la pregunta de estudio («¿Qué calidad tiene Deslinde frente a GerryChain puro,
  `redist` y el óptimo demostrado, con las mismas reglas?») y el protocolo.
- **Si no se hace:** no hay banco.

**T-466 · Ejecución del banco** (talla grande)

- **Qué se hace:** se ejecuta lo aprobado, en GitHub o en un equipo propio. Sale una tabla. Cada caso en que Deslinde
  pierda abre su propia tarea.
- **Qué recibes:** la tabla y una página de conclusiones: dónde ganamos, dónde empatamos, dónde perdemos y por cuánto.
- **Qué necesito de ti:** la frase al Operador para ejecutarlo.
- **Si no se hace:** seguimos sin saber en qué liga jugamos, y no hay ni informe técnico ni revisores.

### Mi opinión sobre la necesidad

Imprescindible. Es la pieza de la que cuelgan más cosas: los bloques C, D, E y F la necesitan.

---

## 5. Bloque C — Demostrar que no hay un mapa mejor escondido

### Lo que pasa hoy

En cada territorio el programa prueba una docena de mapas candidatos y se queda con el mejor. ¿Es el mejor posible?

- En las 8 provincias de un solo distrito, sí: no hay nada que elegir.
- En las provincias de 2 a 4 distritos (hasta 16), sí: un segundo programa, exacto, lo demuestra en segundos.
- **En las otras 28 provincias y en las 19 autonomías, no lo sabemos.**

Y hay un precedente. El 14-11 se probó ese programa exacto en 8 provincias pequeñas. En 3, el mapa elegido ya era el
mejor posible. En 3, perdía solo en el último desempate. Y **en 2, Burgos y Valladolid, existía un mapa claramente
mejor que las diez cadenas no habían encontrado**: en Valladolid partía 2 demarcaciones en vez de 4. Se arregló porque
eran pequeñas. En Sevilla (16 distritos) o en Madrid (59) puede estar pasando lo mismo y hoy no hay forma de saberlo.

Hay un segundo indicio en las autonómicas: el laboratorio propio conseguía en Madrid 6 distritos fuera de tolerancia y
el mapa publicado tiene más (unos 13 con mi recuento, que no es exactamente el del contrato).

### Dos palabras que hacen falta

- **Cota.** Aunque no sepamos cuál es el mejor mapa, a veces se puede demostrar que ninguno puede bajar de cierto
  valor. Por ejemplo: «en Sevilla, ningún mapa válido puede partir menos de 5 demarcaciones».
- **Hueco.** Si el nuestro parte 7 y la cota es 5, estamos como mucho a 2 del mejor posible. Ese «como mucho a 2» es el
  hueco. Hoy no tenemos ese número en ningún territorio grande.

### Por qué importa

El lema del motor nuevo fue tuyo: «el motor que demuestra». Hoy demuestra en 24 de 71 territorios. Y es justo aquí
donde se distinguen los mejores grupos del mundo.

### Qué hacen los mejores

El grupo de Aquisgrán entrega a la autoridad electoral alemana mapas con su distancia máxima al mejor posible. El de
Oklahoma ha calculado el mínimo exacto de condados partidos para los mapas de Estados Unidos.

### Qué propongo

**T-468 · Cotas y mejor mapa demostrado** (talla grande; primero diseño y prototipo)

- **Qué se hace:** se amplía el programa exacto para que llegue más lejos. Objetivo: mejor mapa demostrado en las 44
  provincias con hasta 10 distritos; y en las 8 grandes y en las autonómicas, al menos un «como mucho a tanto del mejor».
- **Qué recibes:** primero un diseño; después, por cada territorio, una línea: «óptimo demostrado» o «a tanto como mucho».
- **Qué necesito de ti:** aprobar el diseño.
- **Honestidad:** es la tarea más difícil del plan y la de resultado menos seguro. En Madrid o Barcelona puede que solo
  salga un hueco amplio. Aun así, un hueco amplio es más de lo que hay hoy, que es nada.
- **Si no se hace:** el motor sigue eligiendo, pero sin demostrar en lo grande.

**T-467 · Mejorar la búsqueda** (talla grande; **solo si hace falta**)

- **Qué se hace:** cadenas más largas, más intentos, más arranques. Solo si el banco (bloque B) o las cotas enseñan
  que nos estamos dejando mapas mejores. Si el banco dice que estamos bien, **esta tarea no se hace**.
- **Importante:** cualquier mejora cambia mapas. Entraría en producción solo cuando toque regenerar por la legislatura
  nueva, para regenerar una sola vez.

### Mi opinión sobre la necesidad

T-468, imprescindible para la meta en el algoritmo. T-467, solo si los datos lo piden.

---

## 6. Bloque D — Mapas alternativos: que el mapa es normal y que el resultado no depende del dibujo

### Lo que pasa hoy

Se publica un mapa por territorio y no hay con qué compararlo. Los alternativos que hubo se retiraron el 16-11 porque
salían del motor antiguo. Entonces dejaste dicho: «Si vuelve, será con una tarea nueva que arranque del mapa de
Deslinde». Esta es esa tarea.

### Qué son

Miles de mapas distintos del mismo territorio, todos válidos con las mismas reglas. No son para elegir otro: son para
tener con qué comparar el nuestro.

### Por qué importa: tres preguntas que hoy no se pueden contestar

1. **¿Es raro nuestro mapa?** Si parte menos municipios que el 90 % de los alternativos, es bueno y se puede decir. Hoy
   no se puede decir nada.
2. **¿El resultado electoral depende de cómo se ha dibujado?** Es la pregunta que más te harán. Con mayoría simple, el
   tablero interno da al PP 207 de 325 distritos. ¿Y en otros 10.000 mapas igual de válidos? Si ahí gana entre 200 y
   212, el resultado es cosa del sistema, no del dibujo. Si oscila entre 170 y 230, el titular depende del mapa.
   (Los números del ejemplo son inventados: hoy nadie los conoce.)
3. **La frase de Metodología** volvería a ser verdad.

### Qué hacen los mejores

Es la práctica normal. Hay simulaciones publicadas de los 50 estados de Estados Unidos, y los tribunales las usan para
detectar mapas amañados. Aquí servirían al revés: para demostrar que el nuestro no lo está. Como tu geometría no usa
votos, tienes todo a favor para que salga bien.

### Qué propongo

**T-469 · Mapas alternativos desde Deslinde** (talla grande; primero diseño)

- **Qué se hace:** 10.000 mapas válidos por provincia del Congreso, con comprobaciones de que la muestra es fiable. Se
  guardan los números de cada mapa y una muestra de 100, no las 10.000 geometrías. Un gráfico por provincia en la web.
- **Qué recibes:** por provincia, dónde cae nuestro mapa («parte menos municipios que el 87 % de los alternativos») y,
  con el bloque H, el margen del resultado electoral.
- **Qué necesito de ti:** aprobar el diseño y la frase para ejecutarlo.
- **Si no se hace:** no hay respuesta a «¿depende del dibujo?» y la frase de la web no puede volver.

**T-470 · Ficha de calidad de cada mapa** (talla pequeña)

- **Qué se hace:** con cada mapa se publica una ficha: cuán compacto es, cuántos municipios, partidos judiciales y
  comarcas parte, los desvíos de población y cuántas excepciones tiene. Esos números existen en estudios internos, pero
  no se publican con el mapa.
- **Qué recibes:** 71 fichas, en los datos abiertos y en la web.
- **Si no se hace:** quien quiera juzgar un mapa tiene que calcularlo todo por su cuenta.

**T-480 · ¿Favorece el mapa a alguien?** (talla pequeña; necesita T-469)

- **Qué se hace:** con los alternativos, se mide si nuestro mapa da a algún bloque más distritos de lo normal.
- **Qué recibes:** una página por elección: «el mapa está en la zona central» o «se desvía en tal sentido».
- **Si no se hace:** la independencia de la geometría, que es tu mejor baza, queda afirmada pero no demostrada.

### Mi opinión sobre la necesidad

T-469, imprescindible. T-470, importante y barata. T-480, pequeña, cuando haya alternativos.

---

## 7. Bloque E — Que la regla de elección no parezca hecha a medida

### Lo que pasa hoy

El mapa ganador se elige con una regla llamada D8. Esa regla tiene números que alguien decidió: el tope del 8 % de
desvío, cuatro pesos (0,5, 0,3, 0,2 y 0,3) y el orden de los criterios. Se decidieron el 10 y el 11-11, después de un
piloto en seis territorios y, como consta en el plan, «con los mapas delante».

No hay nada turbio: los votos no intervienen. Pero un detalle muestra el riesgo: cuando se aprobó, uno de sus criterios
(la frontera cortada) valía cero en todos los mapas y nadie lo sabía. Se descubrió el 14-11 y se arregló.

### Por qué importa

Elegir la regla después de ver los resultados es la objeción clásica en ciencia: «la ajustaste hasta que te gustaron
los mapas». No hace falta que sea verdad para que te la hagan.

### Qué hacen los mejores

Tres cosas, y las tres caben aquí: contar cómo se eligió; enseñar qué pasa si los números cambian (si casi ningún mapa
cambia, la regla es sólida); y fijar la regla con fecha antes de generar los mapas siguientes.

### Qué propongo

**T-471 · D8 declarada y congelada** (talla mediana)

- **Qué se hace:** un documento público «Cómo se eligió D8». Una prueba de sensibilidad: tope del 5, del 8 y del 10 %,
  pesos a la mitad y al doble; cuántos territorios cambian de mapa ganador en cada caso. Y la regla queda fijada, con
  fecha y huella, antes de generar los mapas de la legislatura nueva.
- **Qué recibes:** el documento y una tabla «con esta variante cambian tantos mapas».
- **Qué necesito de ti:** aprobar el documento.
- **Si no se hace:** cuando un revisor lo pregunte, no habrá respuesta preparada.

### Mi opinión sobre la necesidad

Importante. Es barata para lo que protege.

---

## 8. Bloque F — Que otros puedan comprobarlo y lo firmen

### Lo que pasa hoy

Nadie de fuera ha revisado el método, nadie ha reproducido un mapa, no hay publicación. En la auditoría es la nota más
baja: un 3. Y «nivel mundial» no es algo que uno se pueda conceder: lo conceden otros.

Además, hoy un tercero **no podría** comprobarlo aunque quisiera: la licencia no le deja ejecutar el programa, y las
fuentes con las que se regenera están en el archivo privado.

Son cuatro piezas, en este orden.

### Qué propongo

**T-473 · Licencia, marca e identidad: una página de opciones** (talla pequeña; decides tú)

- **Por qué va primero:** sin permiso para ejecutar, nadie puede reproducir. Bloquea las dos tareas siguientes.
- **Qué se hace:** una página con tres opciones y sus consecuencias. A: cerrada, como hoy. B: el código se puede leer y
  ejecutar para comprobar o investigar, sin uso comercial ni copia. C: se abren las reglas y el validador y el motor
  sigue cerrado. Más dos cosas: separar las dos voces (Deslinde es el motor y el estudio; Diputado de Distrito, la
  propuesta) y registrar las marcas. El nombre se puede proteger de verdad; las técnicas, que son públicas, no.
- **Qué recibes:** la página de opciones.
- **Qué necesito de ti:** elegir. Mi recomendación es B.
- **Si no se hace:** la licencia sigue chocando con «verificable» y los bloques siguientes no llegan a su meta.

**T-472 · Kit de reproducción** (talla mediana)

- **Qué se hace:** una «caja cerrada» con todo fijado dentro. Con una sola orden regenera Huesca y una provincia grande
  y comprueba que la huella coincide con la publicada. Una guía de dos páginas.
- **Qué recibes:** el kit y una prueba real: una persona de fuera, elegida por ti, lo consigue en menos de 15 minutos
  solo con la guía.
- **Qué necesito de ti:** elegir a esa persona.
- **Si no se hace:** la reproducibilidad, que es lo mejor del proyecto (un 9), sigue siendo algo que solo nosotros hemos visto.

**T-474 · Revisión externa** (talla pequeña para los agentes; el trabajo de verdad es tuyo)

- **Qué se hace:** un dossier para revisores (definición del método, banco, kit, datos), una plantilla de informe y una
  página pública «Revisiones» donde se cuelgan los informes íntegros, con la respuesta del proyecto.
- **Qué necesito de ti:** elegir e invitar a dos o tres personas: alguien de sistemas electorales, alguien de
  optimización o estadística, alguien de cartografía o derecho electoral.
- **Si no contestan:** convocatoria abierta con el kit.
- **Si no se hace:** la nota de validación externa no se mueve del 3.

**T-475 · Informe técnico de Deslinde** (talla mediana o grande)

- **Qué se hace:** un documento citable, en español y en inglés, con su DOI: el problema, las reglas, D8, la semilla
  pública, el contrato, el banco, las cotas y los límites. No abre el código.
- **Qué necesito de ti:** el 14-11 decidiste «sin JOSS ni OSF». Esto cambia esa decisión solo en un punto: se publica un
  informe. Y elegir la revista, si quieres enviarlo.
- **Si no se hace:** para el mundo académico el proyecto no existe, porque no hay nada que citar.

### Mi opinión sobre la necesidad

Las cuatro son imprescindibles para la validación externa. Lo lento aquí no es nuestro trabajo: es que alguien de fuera
lea y conteste.

---

## 9. Bloque G — Datos completos

### Lo que pasa hoy

Los datos que se publican por distrito dicen quién gana, pero no los votos de cada partido. La tabla completa existe
por dentro y está archivada, pero no se publica.

### Por qué importa

Un investigador o un periodista no puede rehacer ninguna cuenta con lo publicado. Y en datos estás muy cerca de lo
mejor de España: falta el último paso.

### Qué propongo

**T-476 · Datos abiertos 2** (talla mediana)

- **Qué se hace:** una tabla por partido, distrito y elección; la doble vuelta con cada regla; la composición de cada
  distrito y su ficha de calidad. Con diccionario de campos, un validador, contraste con el BOE y con el archivo
  electoral de la Universidad de Valencia, y DOI.
- **Aclaración:** has decidido que el visor no muestre votos por sección (D-205). Esto es por distrito: no lo contradice.
- **Qué recibes:** el conjunto de datos y el borrador de un artículo de datos.
- **Si no se hace:** los bloques H y D siguen pudiéndose hacer por dentro, pero nadie de fuera puede comprobarlos.

### Mi opinión sobre la necesidad

Importante.

---

## 10. Bloque H — Que el análisis sea análisis

### Lo que pasa hoy

La web enseña un mapa de colores y una ficha por distrito. No hay ninguna cifra que resuma qué cambiaría con el sistema.
La doble vuelta supone que todos los votos de los partidos eliminados pasan al finalista de su bloque y que nadie se
abstiene. Y no hay ni una referencia de ciencia política en todo el repositorio.

Dijiste que esto es «estadística respaldada por ciencia política». Hoy la estadística está; el respaldo aún no está escrito.

### Qué propongo

**T-478 · Los indicadores** (talla pequeña o mediana)

- **Qué se hace:** cuatro o cinco números por elección y por sistema (el real, mayoría simple, doble vuelta con cada
  regla), de 2011 a 2023:
  - **desproporcionalidad:** cuánto se separa el reparto de escaños del reparto de votos;
  - **número efectivo de partidos:** cuántos partidos cuentan de verdad;
  - **prima al ganador;**
  - **votos que se quedan sin representación;**
  - **desigualdad territorial**, que es tu mejor resultado: baja del 10,7 % al 1,9 %.
- **Por qué:** es lo primero que preguntará cualquier politólogo o periodista. En 2023 el PP tuvo el 33 % del voto en
  toda España; con mayoría simple, el tablero interno le da 207 de los 325 distritos de 49 provincias, el 64 %. Un análisis serio pone ese
  dato delante y lo discute. Uno que lo esconde pierde la confianza del lector.
- **Qué recibes:** las tablas y un bloque «Qué cambiaría» para la web.
- **Qué necesito de ti:** aprobar la pregunta de estudio.

**T-479 · Sensibilidad de la doble vuelta** (talla mediana)

- **Qué se hace:** se repite la cuenta suponiendo que el trasvase es del 100, del 80 y del 60 %, y que parte de los
  eliminados se abstiene. En las dobles vueltas reales el trasvase nunca es total.
- **Qué recibes:** por distrito, si está «decidido» o «en el aire»; y los escaños con un intervalo («entre tantos y tantos»).
- **Dentro de esta tarea** va una pregunta para ti: qué regla aparece por defecto en la web. Hoy es «Tres bloques»,
  que supone coaliciones que no existieron. El supuesto mínimo es «Sin coaliciones». Es criterio tuyo.
- **Si no se hace:** cualquier crítico dirá, con razón, que el resultado depende de un supuesto no contrastado.

**T-477 · Marco teórico** (talla mediana)

- **Qué se hace:** de seis a ocho páginas: qué dice la ciencia política sobre el distrito uninominal y la doble
  vuelta, y qué hipótesis del proyecto se pueden medir. Con 25 a 40 referencias, cada una comprobada, nunca de memoria.
- **Por qué:** «Contra el sistema de partidos» supone que el distrito debilita a los partidos. Lo que se conoce es
  más matizado: aumenta el voto personal y la atención al distrito, pero el Reino Unido y Francia conservan partidos
  fuertes. Decirlo tú antes de que te lo digan da credibilidad.
- **Qué necesito de ti:** aprobar la pregunta y, después, el texto.

**T-481 · Informe «España en distritos uninominales, 2011-2026»** (talla mediana)

- **Qué se hace:** la pieza que junta todo lo anterior y se puede citar y enviar a prensa y a universidades.
- **Qué necesito de ti:** aprobarlo antes de que salga.

### Mi opinión sobre la necesidad

T-478 y T-479, imprescindibles. T-477 y T-481, importantes: son el respaldo y el producto.

---

## 11. Bloque I — Que cualquiera encuentre su distrito

### Lo que pasa hoy

El buscador del mapa admite «Provincia, comunidad o CUSEC». Casi nadie sabe qué es un CUSEC. Para encontrar tu distrito
hay que buscar la provincia y moverse por el mapa. Y con tu decisión de hoy de quitar el nivel de sección, acercarse
hasta ver la propia calle será menos útil. Buscar por dirección pasa a importar más.

### Qué hacen los mejores

Los mapas «calle a calle» de la prensa suelen dejarte escribir tu calle. Es lo primero que hace la gente: buscarse.

### Qué propongo

**T-482 · «Busca tu distrito»** (talla mediana)

- **Qué se hace:** el INE publica el callejero del censo electoral, la lista oficial que dice a qué sección pertenece
  cada tramo de calle. Nosotros ya sabemos qué sección va a cada distrito. Juntándolos: municipio, calle, número, y sale
  tu distrito. También por código postal. Sin servicios de terceros.
- **Privacidad:** la dirección no sale del navegador de quien busca.
- **Qué recibes:** un buscador en la portada y en el mapa, con el 99 % de acierto comprobado en una muestra de 1.000 tramos.
- **Si no se hace:** el mapa es para quien ya sabe moverse por él.

**T-483 · Una página propia por distrito** (talla mediana)

- **Qué se hace:** cada uno de los 407 distritos tiene su dirección web estable, con su nombre, sus datos y su mapa. Al
  compartirla por WhatsApp o en redes sale una imagen con el distrito.
- **Por qué:** así es como se difunde un proyecto de este tipo: «mira cuál sería tu distrito y quién habría ganado».
  La ventana del distrito que se está construyendo se abre dentro del mapa: no es una página con dirección propia
  que se pueda enviar a alguien.
- **Qué recibes:** 407 páginas generadas en cada publicación.

### Mi opinión sobre la necesidad

Las dos, imprescindibles para el producto. Van detrás de lo que ya está en marcha (ventana, nombres e imágenes del distrito).

---

## 12. Bloque J — Que la web convenza y cargue rápido

**T-484 · Portada con datos** (talla pequeña o mediana; el contenido es tuyo)

- **Lo que pasa hoy:** la portada no tiene ni un dato. El mejor argumento del proyecto, que la desigualdad entre
  provincias baja del 10,7 % al 1,9 %, no aparece en ninguna parte. Y conviven la consigna y el rótulo de investigación.
- **Qué se hace:** una o dos maquetas con un titular numérico y «Busca tu distrito», con la causa en su propia página.
- **Qué necesito de ti:** elegir. La comunicación es criterio tuyo, no mío.

**T-485 · Móvil primero** (talla mediana)

- **Lo que pasa hoy:** abrir el mapa descarga unos 470 KB, más los distritos de la provincia (Madrid, 891 KB). El 22-11
  aprobaste la carga ligera: la parte de la portada está hecha; la del mapa, no.
- **Qué se hace:** lo que falta de lo aprobado, y pasar a «teselas»: el mapa se envía en trozos pequeños según te
  acercas, en vez de provincias enteras.
- **Qué recibes:** primera vista en el móvil en 2,5 segundos, medida en cada publicación.

**T-486 · Lenguaje llano y prueba con cinco personas** (talla pequeña)

- **Lo que pasa hoy:** el mapa usa palabras de casa: «Mayoritario DDD», «Navegador electoral».
- **Qué se hace:** un glosario único, y sentar a cinco personas ajenas ante el mapa con un guion. Se corrige lo que no
  entiendan tres de las cinco. Con cinco personas se encuentra la mayoría de los problemas.
- **Qué necesito de ti:** las cinco personas.

**T-487 · Accesibilidad comprobada** (talla pequeña)

- **Lo que pasa hoy:** la revisión de accesibilidad se hizo leyendo el código. El propio informe dice que no se probó
  con un lector de pantalla ni con un móvil real.
- **Qué se hace:** un guion de prueba para una persona con lector de pantalla y tres móviles, y una declaración pública.

**T-488 · Página «Confianza» e inglés** (talla pequeña o mediana)

- **Qué se hace:** una página con quién ha revisado, cómo citar, contacto, licencias, y los límites y decisiones
  aceptadas, incluida la desigualdad de los distritos con sus cifras. Y un resumen y el método en inglés.
- **Por qué:** lo que declaras tú se defiende mejor que lo que descubre otro. Y sin inglés, nadie de fuera puede leerlo.

**T-489 · Un solo sitio** (talla pequeña)

- **Lo que pasa hoy:** junto a la web oficial siguen publicadas las versiones anteriores del visor y el tablero.
- **Qué se hace:** se retiran y se redirigen. Se quitan las llamadas a terceros que queden.
- **Por qué:** un buscador puede enseñar la versión vieja antes que la buena.

### Mi opinión sobre la necesidad

T-485, imprescindible (ya estaba aprobada). T-484 y T-488, importantes. T-486, T-487 y T-489, convenientes y baratas.

---

## 13. Bloque K — Gastar menos plan en hacer lo mismo

Este bloque es el que más tiene que ver con tu primera objeción: no añade nada visible, pero libera plan semanal para el resto.

**T-491 · A la primera** (talla mediana)

- **Lo que pasa hoy:** el estudio de costes de primeros de noviembre midió que el 27 % de los minutos de ejecución se
  iba en ejecuciones fallidas, y que solo el 45 % de los territorios salía a la primera (el 16 % en las autonómicas).
  Cada fallo es diagnosticar, arreglar y relanzar: plan semanal gastado en repetir.
- **Qué se hace:** primero se mide cómo está hoy. Después: una comprobación previa única que caza el fallo en minutos
  y no a la hora; pruebas que solo ejecutan lo que un cambio toca; arreglar la herramienta de métricas, que hoy pierde
  datos; y un tablero semanal.
- **Meta:** 90 % a la primera y menos del 10 % de minutos en fallos.
- **Si no se hace:** se sigue pagando en plan semanal lo que se podría evitar.

**T-490 · Gobernanza ligera** (talla mediana; primero diseño, porque toca una regla tuya)

- **Lo que pasa hoy:** cada vez que cambia un fichero versionado, se guarda a mano una copia de la versión anterior en
  `legacy/`. Hay 2.611 copias. Pero git ya guarda todas las versiones de todos los ficheros.
- **Por qué importa:** cada cambio abulta más, cada revisión lee más y cada agente gasta más.
- **Qué se hace:** las cabeceras de versión se conservan (son tu disciplina y están en las huellas). Lo que cambia es
  que «anterior» apunta a la versión guardada en git, comprobada por un test, en vez de a una copia. Ya se ha hecho así
  una vez, en el diseño del mapa aprobado hoy.
- **Qué necesito de ti:** aprobar el diseño. Sin tu sí, esta regla no se toca.

### Mi opinión sobre la necesidad

T-491, imprescindible: se paga sola. T-490, importante.

---

## 14. Bloque L — Que el proyecto no dependa de una sola persona ni de la memoria

**T-495 · Consejo asesor y continuidad** (talla pequeña; el trabajo es tuyo)

- **Lo que pasa hoy:** una sola persona decide, aprueba y conoce el conjunto. Los agentes ejecutan y revisan la forma,
  pero no discuten los supuestos. Y el dominio, las cuentas y las claves están en una sola mano.
- **Qué se hace:** un encargo de una página para tres asesores (qué perfil, qué se les pide) y un plan de continuidad.
- **Qué necesito de ti:** elegir a las personas.

**T-494 · Decisiones y foco** (talla pequeña)

- **Lo que pasa hoy:** de unas 216 decisiones registradas, unas 50 corrigen o matizan a otra (recuento aproximado).
- **Qué se hace:** una ficha de cinco líneas por decisión (qué, por qué, alternativa, qué la cambiaría, cuándo caduca)
  y un libro de costes único. Es una regla de trabajo: solo vale si te convence.

**T-493 · Segundo control al publicar** (talla pequeña)

- **Lo que pasa hoy:** el 15-11 quitaste el revisor obligatorio porque aprobar a mano cientos de pasos era inviable.
  Desde entonces el único control para lanzar y publicar es una frase en un chat.
- **Qué se hace:** revisor obligatorio solo en el paso de publicar, con un resumen previo de lo que va a cambiar.

**T-492 · Manual para operar sin agentes** (talla mediana; aplazable)

- **Lo que pasa hoy:** el conocimiento de cómo se lanza y se publica vive en las instrucciones de los agentes.
- **Qué se hace:** un manual, probado por un tercero que ejecuta una campaña de prueba solo con él.

**T-496 · Plan de difusión** (talla pequeña; aplazable)

- **Lo que pasa hoy:** el mapa de 2022, muy inferior, tuvo prensa. No he encontrado eco del trabajo de 2026.
- **Qué se hace:** calendario y piezas, solo con datos técnicos verificados. Temas y textos, tuyos.

### Mi opinión sobre la necesidad

T-495, importante. T-494 y T-493, convenientes. T-492 y T-496, aplazables hasta que haya informe.

---

## 15. Bloque M — Para más adelante

**T-497 · Observaciones públicas por distrito** (solo diseño). Las mejores comisiones electorales dejan que los vecinos
aleguen sobre su distrito y contestan en público. Aquí sería un formulario por distrito con respuesta publicada.

**T-498 · Un caso de otro país** (talla mediana). Demuestra que el motor no vale solo para España. Ya estaba en tu
hoja de ruta. Solo después del informe técnico.

Las dos son aplazables.

---

## 16. El orden, y por qué ese orden

No hay fechas: hay dependencias. Una tarea va detrás de otra solo cuando la necesita.

| Paso | Tareas | Por qué ahí |
|---|---|---|
| 1. Ya, sin tocar producción | T-463 (textos), T-473 (licencia), T-465 (diseño del banco) | Son tres documentos. T-463 corta un riesgo abierto. Las otras dos desbloquean casi todo lo demás |
| 2. Tras el 29-11 | T-466 (banco), T-472 (kit), T-470 (ficha), T-476 (datos), T-478 (indicadores), T-477 (marco), T-491 (a la primera), T-482 (buscar distrito) | No dependen entre sí. T-491 va pronto porque ahorra plan a todo lo que viene |
| 3. Con el banco hecho | T-468 (cotas), T-469 (alternativos), T-471 (D8), T-467 si hace falta, T-479 (sensibilidad), T-483 (página por distrito), T-485 (móvil), T-484 (portada), T-490 (gobernanza) | El banco dice qué método usar para los alternativos y si hay que mejorar la búsqueda |
| 4. Con resultados | T-475 (informe técnico), T-474 (revisores), T-480 (sesgo), T-481 (informe), T-488 (confianza), T-486, T-487, T-489 | Necesitan lo anterior para tener algo que enseñar |
| 5. Cuando quieras | T-495, T-494, T-493, T-492, T-496, T-497, T-498 | No bloquean nada |

**Cuánto dura, con honestidad:** el trabajo de los agentes cabe en semanas, dentro de tu plan. Lo que alarga el
calendario es otra cosa: tu tiempo para leer y aprobar los diseños (hay más de veinte), el paso 3, que es
investigación de verdad y puede torcerse, y los revisores de fuera, que tardan lo que tarden.

---

## 17. Hoja de decisión

Basta con contestar por bloque: **sí**, **no** o **más adelante**. Nada empieza sin tu sí.

| Bloque | Qué resuelve | Tareas | Tallas | Mi opinión |
|---|---|---|---|---|
| A | Dos frases de la web que no son verdad | T-463 | 1 pequeña | Imprescindible |
| B | Medir el motor contra los de referencia | T-465, T-466 | 1 mediana, 1 grande | Imprescindible |
| C | Demostrar que no hay mapa mejor | T-468; T-467 solo si hace falta | 1 grande (más 1 condicional) | Imprescindible |
| D | Mapas alternativos y ficha de calidad | T-469, T-470, T-480 | 1 grande, 2 pequeñas | Imprescindible |
| E | Regla de elección declarada y fijada | T-471 | 1 mediana | Importante |
| F | Licencia, kit, revisores, informe técnico | T-473, T-472, T-474, T-475 | 2 pequeñas, 2 medianas | Imprescindible |
| G | Datos completos por partido y distrito | T-476 | 1 mediana | Importante |
| H | Indicadores, sensibilidad, marco, informe | T-478, T-479, T-477, T-481 | 4 medianas | Imprescindible en parte |
| I | Buscar por calle y página por distrito | T-482, T-483 | 2 medianas | Imprescindible |
| J | Portada, móvil, lenguaje, accesibilidad, confianza, un solo sitio | T-484 a T-489 | 2 medianas, 4 pequeñas | Mixta |
| K | Gastar menos plan en repetir y copiar | T-491, T-490 | 2 medianas | Imprescindible en parte |
| L | Consejo, foco, segundo control, manual, difusión | T-492 a T-496 | 1 mediana, 4 pequeñas | Conveniente |
| M | Observaciones públicas; otro país | T-497, T-498 | 1 pequeña, 1 mediana | Aplazable |

**Cuatro decisiones aparte de los bloques:**

1. **Licencia** (dentro del bloque F): A, B o C. Recomiendo B.
2. **Informe técnico:** ¿se publica, cambiando «sin JOSS ni OSF» solo en eso? Recomiendo sí.
3. **Ritmo:** ¿hasta cinco chats a la vez (más rápido) o tres temas como máximo (más ordenado)? Es criterio tuyo.
4. **Quién escribe el plan:** recomiendo que lo aprobado lo integre el Planificador vivo, con D-205 a D-210, para que
   no haya dos escribiendo el mismo fichero.

---

## 18. Glosario

- **Banco de comparación:** prueba de varios programas con los mismos territorios, las mismas reglas y el mismo tiempo.
- **Cadena:** forma de buscar mapas: se parte de uno y se va cambiando poco a poco, miles de veces.
- **Cota:** valor que ningún mapa puede mejorar, demostrado.
- **Hueco:** distancia máxima entre nuestro mapa y el mejor posible.
- **D8:** la regla con la que se elige el mapa ganador entre los candidatos.
- **Mapas alternativos:** miles de mapas válidos del mismo territorio, para comparar el nuestro con ellos.
- **DOI:** identificador permanente de una publicación o de unos datos; es lo que se cita.
- **Informe técnico:** documento citable que explica el método; se puede publicar sin pasar aún por una revista.
- **Callejero del censo electoral:** lista oficial del INE que dice a qué sección pertenece cada tramo de calle.
- **Teselas:** forma de enviar un mapa en trozos pequeños, según el nivel de acercamiento.

## 19. De dónde sale cada dato

- Frases de Metodología: `documentacion_publica/docs/metodo.md`. Licencia: `LICENSE`.
- Mapas alternativos retirados y registro a cero: decisiones D-138 y D-141; `orchestracion/publicaciones_visor.json`.
- Burgos y Valladolid: `docs/ESTUDIOS/T296_OPTIMO_D8/README.md`.
- Cómo se eligió D8: decisiones D-57, D-62 y D-68 del plan.
- PP 207 de 325: `dashboard/hemiciclo.json` (49 provincias, ejecuciones anteriores a Deslinde 1.1).
- Desigualdad del 10,7 % al 1,9 %: cálculo de la auditoría (§6.1).
- Peso de la web y carga ligera: `docs/ESTUDIOS/T441_CARGA_LIGERA/DISENO.md`; D-192.
- Accesibilidad: `docs/ESTUDIOS/T295_ACCESIBILIDAD/INFORME.md`.
- Minutos en fallos y éxito a la primera: `docs/ESTUDIOS/T155_COSTE/`.
- Copias en `legacy/`: recuento del repositorio.
- Libro de costes: `docs/ESTADO.md` y las entradas del Coordinador en `docs/registro/`.
- Referentes de fuera: enlaces en el §14 de `docs/AUDITORIAS/AUDITORIA_INTEGRAL_2026-11-24.md`.
