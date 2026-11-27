<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.1
NOMBRE DE VERSIÓN: Auditoría integral — veredicto, evolución, benchmark, web y dirección
FECHA: 2026-11-25
ESTADO: informe de opinión independiente (solo lectura; no cambia código, plan ni decisiones)
CAMBIOS: 1.0.1 (25-11) — corrección de un dato: la serie de mapas sí tiene un depósito posterior al de Huesca
  (DOI 10.5281/zenodo.24448721, según `docs/PLAN.md` 1.0.77, T-434); lo pendiente es citarlo. Sin más cambios.
  1.0.0 — fichero nuevo.
MOTIVO: encargo del propietario del 24-11-2026: veredicto en un fichero, evolución del proyecto, comparación con
  proyectos existentes, valoración de la web y auditoría de la dirección
ANTERIOR: 1.0.0 en el commit 99aa2877 de esta misma rama (documento sin fusionar; sin copia en `legacy/`)
-->

# Auditoría integral y veredicto — Diputado de Distrito

**Fecha de corte:** 24-11-2026 · **Rama y HEAD auditados:** `main` en `f52c298d` · **Naturaleza:** auditoría
documental y de datos, en solo lectura. No se ha ejecutado el motor, no se ha lanzado ni publicado nada.

**Escala de notas (0-10):** 5 = correcto, del montón; 7 = notable; 9 = referencia que otros copiarían. Las notas son
juicio razonado con la evidencia que se cita, no una medida.

**Límites de esta auditoría** (detalle en §13): la web en vivo no se puede abrir desde esta sesión (la red la bloquea),
así que la web se juzga por su código y por las capturas de `docs/ESTUDIOS/T423_V4/preview/` (19 y 20-11); las cifras
de calidad de los mapas son cálculo propio sobre `datos/composicion/runs/`; el contraste con proyectos de fuera sale de
búsquedas hechas hoy (enlaces en §14) y de conocimiento general, que se marca como tal.

---

## 1. Veredicto en una página

> **Diputado de Distrito es una fábrica de mapas de primera, con un algoritmo correcto pero estándar dentro, un producto
> público a medio comunicar fuera y ninguna validación externa todavía. No es del montón. Tampoco juega aún entre los
> mejores algoritmos del mundo. En España, en lo suyo, juega solo.**

| Área | Nota | En una línea |
|---|:---:|---|
| Reproducibilidad, procedencia y control | **9** | Lo mejor del proyecto. Semilla pública, huellas de todo, contratos con excepciones fechadas, fallo cerrado. Pocas veces se ve tan completo, ni en la academia |
| Cobertura y ejecución | **8,5** | 71 territorios con cadena completa: 407 distritos nacionales y 1.262 autonómicos, sección a sección, con histórico desde 2011 |
| Datos electorales (casado, cuadre, histórico) | **8,5** | Mesa → sección → distrito, cuadre con el BOE, nada «de memoria», pérdidas declaradas |
| Algoritmo Deslinde (método) | **6,5** | Composición sólida de técnicas conocidas, medida con honestidad. Sin método nuevo, sin cotas fuera de lo pequeño, sin comparación externa hecha |
| Mapas del Congreso (calidad) | **7** | Corrige de raíz la desigualdad entre provincias; dentro de la provincia está al nivel de Alemania o Italia, no del Reino Unido; unos pocos atípicos muy visibles |
| Mapas autonómicos (calidad) | **5** | Válidos según el contrato, pero con 1 de cada 4 distritos a más del 10 % de la media y casos indefendibles en público |
| Análisis político | **4,5** | Simulación mecánica, sin incertidumbre ni sensibilidad, con etiquetas propias y sin bibliografía que la respalde |
| Web y mapa | **6,5** | Bien por dentro (accesible, honesta, sin cookies, procedencia), regular por fuera (portada militante, mapa denso, móvil pesado, dos frases de método que hoy no se cumplen) |
| Validación externa y credibilidad científica | **3** | Nadie de fuera ha revisado, reproducido ni citado nada. Es la mayor carencia |
| Proceso y eficiencia | **6** | Muy controlado y muy caro en vueltas: renombrados en serie, casi una de cada cuatro decisiones corrige o matiza otra, 27 % de los minutos en ejecuciones fallidas |
| Dirección del proyecto | **7** | Visión, rigor y velocidad de decisión notables; foco, comunicación y validación externa, por debajo |
| **Conjunto (media simple)** | **6,5** | Bien alto: sobresaliente en ingeniería, aprobado en ciencia y en comunicación |

### Las tres preguntas, respondidas en corto

1. **¿Entre los mejores algoritmos del mundo o del montón?** Ni lo uno ni lo otro. Como **algoritmo**, Deslinde es
   segunda división alta: aplica bien lo que otros inventaron (cadenas ReCom, programación con restricciones, elección
   lexicográfica) y lo mide con seriedad, pero no aporta método nuevo ni ha demostrado ganar a nadie en un caso
   compartido. Como **sistema reproducible y auditable de mapas a escala de país**, sí es de primera división. Lo que
   separa al proyecto de la élite no es código: son cotas de optimalidad, mapas alternativos por miles y revisión de
   terceros (§5).
2. **¿Nuestro análisis es de los mejores de España?** En su nicho (España en distritos uninominales, sección a sección,
   con procedencia) no hay nadie más: es el mejor porque es el único. En **datos**, está entre lo más cuidado que se
   hace en España. En **análisis político**, está por debajo de lo que publican la academia y el buen periodismo de
   datos: enseña un mapa, no un resultado discutido (§7).
3. **¿La web está bien o regular?** Bien por dentro, regular por fuera. «Comprender» y «Metodología» son buenas; el
   mapa es potente pero denso; la portada resta más de lo que suma para quien llega buscando investigación (§8).
   Nota: 6,5.

### Lo que más valor añadiría ahora (por orden)

1. **Validación externa antes que más superficie.** Ejecutar la comparación ya diseñada con GerryChain puro y `redist`,
   y conseguir dos o tres revisores con nombre (politólogo, estadístico u optimizador, cartógrafo).
2. **Recuperar los mapas alternativos, ahora desde Deslinde.** Miles por provincia. Sirven para dos cosas que hoy no se
   pueden afirmar: que el mapa elegido es «normal» y que el resultado electoral no depende del trazado concreto. Además,
   la página pública de método ya dice que se hace (§8.3).
3. **Publicar la factura de cada regla y cerrar los atípicos visibles**: un distrito autonómico de 733 habitantes, un
   distrito del Congreso de 36.684 junto a otros de 137.000 (§6).
4. **Separar la voz de la investigación de la voz de la causa.** Hoy conviven en la misma portada y se restan (§8, §11).
5. **Congelar el alcance.** Primero la noche del 29-11; después, consolidar, no abrir frentes (§9, §12).

---

## 2. Dónde estamos: estado por pieza

Distingue, como pide la propia norma del proyecto, entre decidido, construido, probado, publicado y validado por terceros.

| Pieza | Decidido | Construido | Probado | Publicado | Validado por terceros |
|---|:---:|:---:|:---:|:---:|:---:|
| Cadena de datos y contratos (71 territorios) | Sí | Sí | Sí | Sí | No |
| Deslinde 1.1 (competición, D8, exacto con K ≤ 4) | Sí | Sí | Sí (71/71, bit a bit) | Sí (mapas) | No |
| Óptimo demostrado en medianos y grandes | Sí (línea de investigación) | No | No | No | No |
| Comparación con `redist` y GerryChain puro | Sí | Solo el plan | No | No | No |
| Mapas alternativos (ensembles) | Retirados | Solo los del motor viejo | — | 0 en el registro | No |
| Resultados por distrito y doble vuelta | Sí | Sí | Sí | 52 nacionales y 16 autonómicas | No |
| Histórico 2011-2023 por época | Sí | En curso | Parcial | Parcial | No |
| Web V4 | Sí | Sí | Parcial (sin lector de pantalla ni móvil real) | Sí, oficial desde el 20-11 | Consta una «auditoría externa» de textos (20-11), sin autor identificado en el repositorio |
| Noche electoral del 29-11 | Sí | Sí | **No consta ensayo en seco tras la migración de workflows** | — | — |
| Depósito con DOI | Sí | Sí | Sí | Serie de mapas depositada (DOI 10.5281/zenodo.24448721, según el plan); `README.md` y `CITATION.cff` siguen citando solo Huesca | No |
| Artículo o informe técnico | Descartado (sin JOSS ni OSF) | Borrador con pendientes | — | No | No |

Evidencia: `README.md` (bloque de estado), `docs/ESTADO.md`, `docs/PLAN.md` (D-73, D-86, D-94, D-138, D-141, D-146,
D-149), `orchestracion/publicaciones_visor.json` (`ensembles: 0`), `docs/ARTICULO_JOSS/`.

---

## 3. Evolución: de dónde venimos

| Cuándo | Hito | Qué cambió de verdad |
|---|---|---|
| Enero-marzo de 2022 | Mapa de 380 distritos de unos 100.000 habitantes de la plataforma DEMOS, con presentación anunciada en el Ateneo de Madrid. La prensa de entonces atribuye el diseño a Jesús Murciego y José Papí | La idea se convierte en mapa por primera vez. Trazado no reproducible: en el repositorio consta como «mapa histórico de 2022», con 391 geometrías, una inválida y ediciones sin acreditar |
| Septiembre de 2026 | Se recupera el procedimiento de Aragón y se parte en ocho módulos con contrato; primeras ejecuciones validadas (67 distritos, desvío máximo 9,93 %) | De mapa a procedimiento repetible |
| Septiembre-octubre | Arquitectura multiterritorio; contrato por territorio; acreditación de fuentes | De un caso a un motor |
| 8-13 de octubre | Modelo nacional: mónada de 120.000 habitantes, K por provincia, 407 como resultado y no como objetivo | La teoría se convierte en fórmula |
| 26 de octubre-9 de noviembre | Las 52 provincias y las 19 autonómicas; gestor de campañas; agentes con rol, revisor y forense; visor v2 | Escala |
| 10-14 de noviembre | Núcleo único de reglas, competición de generadores, elección D8, semilla pública, certificador exacto: Deslinde 1.0 y 1.1 | Del «sale un mapa» al «sale el mejor candidato y se sabe por qué» |
| 14-16 de noviembre | Regeneración de los 71 con Deslinde 1.1; archivo durable; licencia propietaria | Producción estable |
| 16-18 de noviembre | Migración de los flujos a la familia P00-P90; histórico por época; doble vuelta | Producto operable |
| 19-24 de noviembre | Web V4 oficial; doble vuelta nacional y de 16 autonomías; registro de la propiedad intelectual; 68 territorios publicados | Producto público |
| 29 de noviembre | Elecciones generales | Primera prueba en vivo |

**Progresión.** Es real, rápida y medible. En diez semanas: de 1 territorio a 71; de 67 distritos a 1.669; de un
optimizador sin garantía a una competición con candidato exacto; de artefactos que caducaban a un archivo con huellas;
de 36 flujos a 15; unas 4.600 pruebas automáticas; más de 1.000 PR y 625 entradas de registro (520 desde el 7 de
noviembre, con un pico de 99 en un día). Cuatro años después del mapa de 2022, el salto no es de grado: es de naturaleza.
Aquel era un dibujo; esto es un procedimiento que cualquiera puede seguir paso a paso.

**El patrón que se repite.** La superficie crece más deprisa que la consolidación. Cada fase añade un frente (350,
autonómicas, histórico, doble vuelta, tres versiones nuevas del visor, archivo, propiedad intelectual) antes de cerrar la
pregunta de fondo de la anterior: ¿es bueno el mapa, comparado con qué, y quién de fuera lo confirma? El propio plan
deja la respuesta para «la investigación del final» (punto 8 del orden vigente).

---

## 4. Fortalezas y debilidades

### 4.1 Fortalezas (con evidencia)

1. **Reproducibilidad de nivel profesional.** Semilla derivada del sha256 del padrón, del seccionado y del código
   oficial del territorio; sin semilla fija; fallo cerrado sin `PYTHONHASHSEED=0`; huella del resultado que incluye
   reglas, candidatos y entorno; misma entrada, mismo mapa bit a bit (`docs/ARQUITECTURA/DESLINDE_1_0.md` §4).
2. **La geometría no depende de los votos.** Los resultados se incorporan después, sobre el mapa ya certificado. Es
   la defensa estructural más fuerte frente a la sospecha de manipulación, y está en la arquitectura, no en una promesa.
3. **Contrato por territorio con excepciones declaradas.** Suelo, techo, K, exenciones: todo escrito antes de calcular,
   con motivo, fecha y quién decide. Ejemplo: la exención de Águilas (`territorios/nac30/config/nac30_2025.yaml`).
4. **Honestidad interna poco frecuente.** Los documentos separan «hoy» de «objetivo», listan lo que el motor no
   garantiza y publican hallazgos en contra: el estudio del óptimo exacto reconoce que en Burgos y Valladolid había
   planes mejores que el ganador y que un término de la función valía cero en todos los planes
   (`docs/ESTUDIOS/T296_OPTIMO_D8/README.md`).
5. **Certificación exacta donde cabe.** Con K ≤ 4 y hasta 372 unidades, el óptimo lexicográfico completo se demuestra
   en 1-9 segundos. Para Madrid, el certificador demostró que el desvío máximo del mapa entonces publicado era el
   mínimo posible, con un hueco de 3 habitantes (`docs/ESTADO.md`, tema 1b).
6. **El reparto de 407 arregla la desigualdad entre provincias** (§6.1): es el resultado sustantivo más defendible del
   proyecto y hoy no se cuenta en ninguna parte de la web.
7. **Datos electorales cuidados.** Nunca se reparten votos entre secciones, las pérdidas se declaran (0,2-0,54 % en
   2011), las fuentes desaparecidas se sustituyen por copia archivada marcada como no oficial.
8. **Control de lo irreversible.** Autorización por campaña con ficha y caducidad, revisor independiente, guardián de
   `main`, tope de gasto, lecciones tras cada incidente.
9. **Infraestructura barata.** Archivo de unos 12 GB por céntimos al mes; ejecución sin coste por repositorio público.

### 4.2 Debilidades (con evidencia)

1. **Cero validación externa.** Ningún experto ajeno ha revisado el método, nadie ha reproducido un mapa, no hay
   publicación ni cita. La comparación con `redist` y GerryChain puro está diseñada y sin ejecutar; el artículo quedó
   descartado. Para un proyecto cuyo lema público es «investigación verificable», es la carencia número uno.
2. **Licencia y relato se contradicen.** La página de método dice que «el programa que dibuja los distritos es público,
   para que cualquiera pueda revisarlo o repetirlo»; la licencia dice que «el acceso al repositorio no concede ningún
   derecho de uso». Se puede leer; no se puede repetir sin permiso escrito. Verificable, en ciencia, significa lo segundo.
3. **Una afirmación pública que hoy no se cumple.** La misma página dice que «se generan por ordenador miles de mapas
   alternativos» para comprobar si el mapa elegido es normal. Los alternativos se retiraron (eran 10 o 25 por
   territorio, del motor viejo) y el registro del visor tiene cero.
4. **Igualdad de población por debajo de los estándares exigentes**, con atípicos que cualquier crítico encontrará en
   cinco minutos (§6.3).
5. **Búsqueda corta y sin cota en lo grande.** Diez cadenas de 300 pasos es un presupuesto muy pequeño para Madrid (59
   distritos) o Barcelona (50); fuera de K ≤ 4 no se sabe a qué distancia queda el mapa del mejor posible.
6. **La función de elección se eligió mirando mapas.** El tope del 8 %, los recargos 0,5/0,3/0,2/0,3 y el orden de los
   términos salen de un piloto y de la preferencia del propietario «con los mapas delante». El preregistro quedó en
   borrador y se descartó. No es manipulación partidista (los votos no intervienen), pero sí margen de
   discrecionalidad que hay que declarar.
7. **Análisis político delgado** (§7): simulación mecánica, bloques con etiquetas propias, ningún índice estándar,
   ninguna medida de incertidumbre.
8. **Sobrecarga de proceso.** 14.254 ficheros; 2.611 copias en `legacy/` de versiones que git ya guarda; 928
   documentos en `docs/`; unas 163.000 líneas de herramientas y pruebas frente a unas 29.000 de motor. Notación de
   módulos, de territorios y de flujos cambiada sobre la marcha; del visor v2 a la V4 en once días.
9. **Dependencia de una persona y de agentes de IA.** Un solo humano decide, aprueba y conoce el conjunto; el
   conocimiento operativo vive en instrucciones para agentes. No hay equipo, ni consejo asesor, ni relevo.
10. **Identidad sin resolver**: ¿campaña cívica, investigación o producto? Se nota en la licencia (de abierta a
    «repositorio privado» y de ahí a «público con licencia propietaria», en ocho días) y en la portada (§11).

---

## 5. El algoritmo frente al mundo: en qué liga jugamos

### 5.1 Qué es Deslinde, sin adornos

Deslinde 1.1 hace competir, bajo un único núcleo de reglas duras, a estos candidatos: (a) el trazado propio del
proyecto (constructor más mejora local); (b) el mapa publicado; (c) diez cadenas de 300 pasos de ReCom ponderado sobre
GerryChain, usadas como **buscador** de un buen plan, no como muestreador; (d) un resolutor exacto (OR-Tools CP-SAT) si
K ≤ 4 y hay una sola circunscripción; (e) una enumeración completa si el espacio es mínimo. Gana el primero por una
clave lexicográfica pública (D8): validez, distritos fuera de tolerancia, exceso sobre el 8 % de desvío, partidos
judiciales y comarcas agrarias partidos, frontera cortada, desvío máximo.

**Prestado:** las cadenas ReCom y GerryChain, CP-SAT, la contigüidad por árbol, la idea de objetivo lexicográfico.
**Propio:** el contrato con excepciones declaradas, la semilla derivada de las huellas de las fuentes, la regla «nunca
peor que el trazado propio ni que el publicado», la naturalidad medida con partidos judiciales y comarcas agrarias, la
reparación determinista del mapa vigente y la aceptación automática. La originalidad está en el sistema, no en la
matemática.

### 5.2 Los referentes

| Familia | Referentes | Qué tienen que Deslinde no tiene |
|---|---|---|
| Muestreo de planes | ReCom y GerryChain (DeFord, Duchin, Solomon); SMC y el paquete `redist` (McCartan, Imai), con simulaciones publicadas para los 50 estados de EE. UU.; Forest ReCom y Cycle Walk (grupo de Duke y colaboradores); Marked Edge Walk y Balanced Up-Down Walk (2025-2026) | Distribución objetivo conocida, diagnósticos de convergencia, decenas de miles de planes por mapa, uso como prueba en tribunales |
| Optimización exacta | Shahmizad y Buchanan (2025): mínimo exacto de condados partidos para los mapas del Congreso y de las cámaras estatales de EE. UU., según su resumen; RWTH de Aquisgrán (Goderbauer, Lübbecke): distritos alemanes con cotas de optimalidad y escenarios de 125, 200 y 250 distritos para la autoridad electoral federal | Óptimo o cota a escala real, no solo con K ≤ 4 |
| Optimización a gran escala | Short bursts; generación de columnas (Gurnee y Shmoys); programación entera escalable (Brous y Shmoys, 2025) | Mejores resultados que la búsqueda por cadenas en objetivos concretos, demostrados en comparación |
| Uso institucional | Instituto Nacional Electoral de México: recocido simulado y colonia de abejas artificiales, con función de coste pública (desvío de ±15 %, integridad municipal, tiempos de traslado, compacidad) y observaciones de los partidos | El algoritmo decide distritos legales de verdad |
| Comisiones independientes | Reino Unido, Australia, Canadá, Nueva Zelanda | Tolerancias estrictas y audiencias públicas |
| Herramientas ciudadanas | Dave's Redistricting, Districtr, DistrictBuilder | Miles de usuarios dibujando y midiendo |

### 5.3 Criterio a criterio

| Criterio | Deslinde hoy | Lo mejor que hay | Distancia |
|---|---|---|---|
| Garantía de óptimo | Demostrado solo con K ≤ 4 y una circunscripción. Sin cota en el resto | Óptimos y cotas a escala de estado o de país | Grande |
| Presupuesto de búsqueda | 10 cadenas × 300 pasos | 10⁴ a 10⁶ pasos o planes | Grande, y barata de cerrar |
| Calidad heurística medida | En 8 provincias con óptimo conocido, antes de añadir el exacto: óptimo en 3, a un desempate en 3, peor en 2. En lo grande, sin medir | — | Media, y desconocida donde más importa |
| Mapas alternativos para contexto | Retirados | Práctica estándar | Grande |
| Función objetivo | Lexicográfica, pública, con reglas duras aparte | Comparable (lexicográfica en la optimización exacta reciente; suma ponderada en México) | Pequeña |
| Reproducibilidad | Bit a bit, semilla derivada de las fuentes, fallo cerrado | Código, semillas y datos abiertos | A favor en trazabilidad; en contra en apertura |
| Procedencia y auditoría | Huellas de todo, contrato, certificación, catálogo público | Rara vez tan completo | **A favor** |
| Compacidad y forma | Medida en estudios (Polsby-Popper medio 0,16 → 0,24); en la elección solo cuenta la frontera cortada | Métricas estándar publicadas plan a plan | Media |
| Validación independiente | Ninguna | Revisión por pares, tribunales, autoridades electorales | Muy grande |
| Participación pública | Decide una persona | Audiencias y alegaciones | Estructural |
| Escala | Unas 36.500 secciones | Millones de bloques censales | No limita para España |

Tres matices para leer bien la tabla:

- La curva que se midió es la del **número de cadenas** (se aplana entre 5 y 10: 172 distritos fuera de tolerancia
  sin cadenas, 126 con 5, 125 con 10, 124 con 20). No consta que se haya medido la de la **longitud** ni la de otro
  generador. Que más cadenas iguales no mejoren no demuestra que no haya planes mejores: Burgos y Valladolid lo probaron.
- El candidato exacto cerró esos dos casos. La misma medición sugiere que en provincias medianas y grandes, donde no
  hay exacto, el hueco existe y nadie lo ha medido. Es una inferencia, no un dato.
- En las autonómicas, la batería de aceptación dejaba 236 distritos fuera de tolerancia y el laboratorio propio
  conseguía bastantes menos (Madrid 21 frente a 6): hay margen conocido sin recoger
  (`docs/ESTUDIOS/T196_BATERIA_D8/README.md`).

### 5.4 Veredicto de liga

- **Investigación de métodos (élite mundial): no.** No hay método nuevo, ni propiedad demostrada, ni victoria en un
  caso compartido con otros.
- **Aplicación del estado del arte: segunda división alta.** Integrador competente que mide lo que hace. Por encima
  del proyecto unipersonal típico; por debajo de los grupos que publican.
- **Ingeniería de reproducibilidad y procedencia de un mapa nacional: primera división.** Aquí el proyecto no tiene
  que envidiar a nadie, y en trazabilidad supera a la mayoría del código académico.
- **Impacto institucional: sin debutar.** México lleva décadas decidiendo distritos legales con un algoritmo.
- **España: liga propia.** No he encontrado ningún otro trabajo que trace distritos uninominales para toda España a
  partir de secciones censales; el único precedente es el mapa de 2022 del mismo autor. Ser el único es mérito, pero
  no es comparación: en una liga de un equipo no hay clasificación.

### 5.5 Qué hace falta para subir de división

Las cuatro cosas están ya en el plan (líneas de investigación y hoja de ruta de Deslinde). Falta ejecutarlas y falta
orden: hoy van al final.

1. **Comparación en casos compartidos**: los 8 pequeños con óptimo demostrado más Madrid, Barcelona y Valencia, con
   GerryChain puro y con `redist`, mismas reglas y unidades. Burgos y Valladolid como casos de prueba.
2. **Cotas donde no hay óptimo**: al menos cota inferior del número de distritos fuera de tolerancia y de demarcaciones
   partidas, por descomposición o por relajación.
3. **Miles de mapas alternativos por provincia** generados desde Deslinde, con el percentil del mapa elegido en cada
   métrica.
4. **Un informe técnico con revisores**. Sin él, todo lo anterior solo lo sabe el proyecto.

---

## 6. Los mapas frente a los estándares internacionales

### 6.1 Lo mejor: el reparto entre provincias

Población por representante, provincia a provincia (padrón de 2023; cálculo propio):

| | Sistema actual (350 escaños) | Propuesta (407 distritos) |
|---|:---:|:---:|
| Desvío medio respecto a la media nacional | 21,3 % | **3,8 %** |
| Representantes en provincias a más del 15 % de la media | 58,0 % | **2,7 %** |
| Índice de desigualdad de reparto (Loosemore-Hanby de escaños frente a población) | 10,7 % | **1,9 %** |
| Extremos | Soria 44.764 – Madrid 185.727 (4,15 a 1) | Ceuta 83.052 – Zamora 166.927 (2,01 a 1) |

La regla de la mónada (un distrito por cada 120.000 habitantes, mínimo uno por provincia) reduce a menos de la quinta
parte la desigualdad territorial del voto. Es un resultado limpio, de ciencia política clásica, y la web no lo dice.

### 6.2 Dentro de cada territorio: cifras propias

Desvío de cada distrito respecto a la media de su territorio, con el último mapa publicado de cada uno:

| | Congreso, mapa anterior | Congreso, Deslinde 1.1 | Autonómicas, Deslinde 1.1 |
|---|:---:|:---:|:---:|
| Distritos | 407 | 407 | 1.262 |
| Desvío medio / mediana | 4,8 % / 2,2 % | 6,2 % / 4,4 % | 9,2 % / 5,5 % |
| Dentro de ±5 % | 68,1 % | 53,3 % | 46,8 % |
| Dentro de ±10 % | 83,5 % | 78,6 % | 73,1 % |
| Dentro de ±15 % | 96,3 % | 96,3 % | 85,2 % |
| A más del 25 % | 10 (2,5 %) | 10 (2,5 %) | 91 (7,2 %) |
| Máximo | 69 % | 69 % | 98 % |

Frente a la media **nacional** (118.146 habitantes), los 407 distritos del Congreso quedan: 70,5 % dentro de ±10 %,
87,0 % dentro de ±15 %, 18 a más del 25 %, y una razón entre el mayor y el menor de 4,55 a 1 (2,7 a 1 sin Águilas).
Municipios repartidos entre distritos del Congreso: 47 de 8.131.

### 6.3 Con qué se compara

| Referencia | Desvío admitido |
|---|---|
| EE. UU., Congreso | Prácticamente cero |
| Reino Unido, Nueva Zelanda | ±5 % |
| Australia | ±10 % al trazar (y ±3,5 % proyectado) |
| Comisión de Venecia | No más del 10 %; nunca más del 15 % salvo circunstancias especiales |
| Alemania | ±15 % como objetivo; ±25 % obliga a redibujar |
| México | ±15 % |
| Italia (2017), Francia | ±20 % dentro de la circunscripción o del departamento |
| Canadá | ±25 % |
| **Contrato del Congreso en el proyecto** | Suelo 0,85 y techo 1,15 de la media provincial, con exenciones declaradas |
| **Contrato autonómico general** | Suelo 0,80, techo 1,75, tolerancia del 12 % como objetivo, no como regla |

Verificado hoy por búsqueda: Comisión de Venecia, México e Italia. El resto es conocimiento general: conviene citar la
norma exacta antes de usarlo en público.

**Lectura.**

- **Congreso: nivel Alemania-Italia, no nivel Reino Unido.** El 96 % dentro de ±15 % es defendible en Europa
  continental. El 21 % a más del 10 % incumple la recomendación general de la Comisión de Venecia.
- **Deslinde 1.1 cambió igualdad por naturalidad, y eso hay que decirlo.** Con el motor nuevo, los distritos del
  Congreso dentro de ±5 % bajan del 68 % al 53 %. A cambio, los partidos judiciales partidos bajan de 298 a 167 y las
  comarcas agrarias de 218 a 123 (estudio de naturalidad). El intercambio está medido y decidido; lo que falta es
  hacerlo público con sus números, porque el principio fundacional invocado es la igualdad de representación y los
  estándares internacionales ponen la igualdad por delante de las demarcaciones.
- **Los atípicos son pocos pero muy visibles.** En el Congreso hay 10 distritos a más del 25 % de la media de su
  provincia: cinco en Baleares (cuatro de Mallorca al +28 %, pegados a los tres de Palma, que están al −11 %, y uno de
  Ibiza al −36 %), dos en Las Palmas (Lanzarote al +39 % y el oeste de Gran Canaria al −46 %), Águilas (−69 %),
  Fuengirola (−27 %) y el Morrazo (−25 %). Solo una parte se explica por la insularidad; el resto sale de reglas
  propias: municipio indivisible, núcleos urbanos cerrados, un solo distrito mixto por municipio.
- **El caso que resume el problema.** Águilas forma sola un distrito de **36.684 habitantes** en una provincia con
  media de 119.000, porque Lorca se declara indivisible. La excepción está impecablemente documentada; el resultado es
  difícil de defender ante un tercero. La práctica internacional partiría Lorca.
- **Las provincias de un solo distrito** cargan con todo el redondeo: Zamora, 166.927 habitantes y un diputado.
- **Autonómicas: el problema es de planteamiento, no de motor.** Usar como K el número actual de escaños produce
  distritos diminutos (La Rioja, 9.800 habitantes de media; Ceuta y Melilla, 3.400) hechos con piezas que no se
  parten. Resultado: 1 de cada 4 distritos a más del 10 %, 91 a más del 25 %, y en Canarias **un distrito de 733
  habitantes** (la sección de La Graciosa, sola) frente a una media de 31.600. Ese mapa está en el registro de
  publicaciones del visor; un dato así desacredita al resto.

---

## 7. El análisis electoral frente a lo que se hace en España

### 7.1 Con quién se compara

| Quién | Qué hace | Mejor que el proyecto en | Peor que el proyecto en |
|---|---|---|---|
| Periodismo de datos (mapas «calle a calle» de los grandes diarios y televisiones) | Resultado real por sección censal, la misma noche | Alcance, diseño, móvil, búsqueda por dirección, rapidez | No construyen distritos ni contrafactuales; procedencia poco visible |
| Academia (archivo SEA de la Universidad de Valencia; grupos de sistemas electorales; estudios de reforma) | Datos homogéneos y simulaciones de reformas, revisadas por pares | Marco teórico, índices, revisión, cita | Trabajan con las circunscripciones existentes; no trazan distritos |
| Agregadores y casas de encuestas | Predicción | Audiencia | Otro objeto |
| Propuestas de reforma (Consejo de Estado, sistema mixto, 43 distritos de la Comunidad de Madrid) | Diseño institucional | Legitimidad | Ningún mapa reproducible sección a sección que yo haya encontrado |
| Mapa DEMOS de 2022 | 380 distritos, mapa interactivo | Tuvo prensa | No reproducible; el proyecto actual lo supera en todo lo técnico |

### 7.2 Veredicto

- **En datos: entre lo mejor de España.** Casado mesa-sección-distrito, cuadre con el BOE, equivalencias entre
  seccionados, histórico con distritos de cada época, huellas. El archivo SEA es más amplio; este es más trazable.
- **En el objeto: único.** Nadie más enseña «quién habría ganado en tu distrito».
- **En análisis: del montón, tirando a bajo.** Lo que hay es una agregación mecánica bien hecha. Falta casi todo lo
  que convierte un mapa en un análisis.

### 7.3 Lo que falta para que sea análisis

1. **Contar el resultado principal.** Con mayoría simple y los votos de 2023, el tablero interno da, en 49 provincias,
   PP 207 de 325 distritos (64 %), PSOE 106, PNV 7 y Bildu 5; VOX, Sumar, Junts, ERC y el resto, cero
   (`dashboard/hemiciclo.json`, con ejecuciones anteriores a Deslinde 1.1). Es la primera pregunta de cualquier
   politólogo: mayoría fabricada y desaparición de terceros partidos. Un análisis serio la pone delante y la discute
   (índice de Gallagher, prima al ganador, número efectivo de partidos, votos sin representación).
2. **Sensibilidad de la doble vuelta.** Hoy el voto de los eliminados pasa entero al finalista de su bloque y nadie se
   abstiene. Hacen falta escenarios (trasvase del 100, 80 y 60 %, abstención diferencial) y decir cuántos distritos
   cambian de ganador en cada uno.
3. **Etiquetas neutrales y supuesto mínimo por defecto.** «Patriotas» para PP y VOX es una etiqueta propia, no una
   categoría de la disciplina, y la vista por defecto («Tres bloques») presupone coaliciones previas que no existieron.
   El supuesto mínimo es «sin coaliciones».
4. **Robustez frente al trazado.** ¿Cuántos escaños cambian si se cambia de mapa entre los válidos? Solo los mapas
   alternativos lo contestan (§5.5).
5. **Sesgo del propio mapa.** Como la geometría no usa votos, el proyecto puede permitirse demostrar que su mapa no
   favorece a nadie: curva de votos y escaños, diferencia entre media y mediana, percentil frente a los alternativos.
6. **Bibliografía.** El repositorio cita a GerryChain y ReCom, y a García-Trevijano una vez. No hay una sola referencia
   de ciencia política. La frase «estadística respaldada por ciencia política» hoy describe una intención, no un
   documento. Mínimo que debería estar: Duverger; Cox (*Making Votes Count*); Carey y Shugart sobre el voto personal;
   Cain, Ferejohn y Fiorina (*The Personal Vote*); Taagepera y Shugart (*Seats and Votes*); Gallagher sobre
   desproporcionalidad; Samuels y Snyder sobre desigualdad de reparto; Handley y Grofman sobre delimitación comparada;
   el código de buenas prácticas de la Comisión de Venecia; el informe del Consejo de Estado de 2009.
7. **La hipótesis central, sometida a prueba.** «Contra el sistema de partidos» supone que el distrito uninominal
   debilita a los partidos. La evidencia comparada dice algo más matizado: aumenta el voto personal y el servicio al
   distrito, pero el Reino Unido y Francia conservan partidos fuertes y disciplina alta. Un proyecto que se presenta
   como investigación tiene que decirlo y medir lo que sí cambia.

---

## 8. La web y el mapa

Juzgada por el código de `visor/v4/`, la documentación pública y las capturas del 19 y 20-11. No he podido abrirla.

### 8.1 Notas

| Página | Nota | Por qué |
|---|:---:|---|
| Comprender | 8 | Lo mejor de la web: «Hoy votas una lista. Con un diputado de distrito, votas a una persona», tabla hoy/propuesta, ejemplo de Huesca, sección «Qué no es» |
| Metodología | 8 | Lenguaje llano, nueve pasos, capítulo de límites. Dos frases que hoy no se sostienen (§8.3) |
| Explorar (mapa) | 6,5 | Potente y honesto; denso, con jerga y pesado en el móvil |
| Portada | 5 | Identidad visual cuidada; mensaje de militancia, ningún dato, ninguna llamada a «busca tu distrito» |
| **Conjunto** (pesan más el mapa y la portada) | **6,5** | Bien por dentro, regular por fuera |

### 8.2 Lo que está bien

- Arquitectura clara de cuatro páginas y una identidad visual coherente.
- Mapa con cinco niveles (comunidad, provincia, distrito, municipio y sección), cuatro reglas de elección, navegador
  de elecciones desde 2011 y panel «De dónde sale este mapa» con su procedencia.
- Accesibilidad trabajada: salto al contenido, etiquetas, tabla alternativa al mapa, foco visible, movimiento reducido.
- Sin cookies, contador propio, datos abiertos con licencia y huellas.
- Portada ligera (unos 234 KB).
- Avisos de simulación claros y repetidos.

### 8.3 Lo que está regular o mal

1. **La portada mezcla consigna e investigación.** «Contra el sistema de partidos», «Abstención consciente» y, debajo,
   «Investigación verificable». Quien llega buscando un estudio ve un cartel de campaña; quien llega por la causa no necesita la
   metodología. No juzgo la posición política: juzgo su efecto sobre la credibilidad ante investigadores, periodistas e
   instituciones, que son el público que el propio proyecto dice buscar.
2. **Dos afirmaciones de la página de método que hoy no se cumplen**: los «miles de mapas alternativos» y que el
   programa se puede «repetir» (§4.2, puntos 2 y 3). Son las dos frases que un crítico citaría primero.
3. **Ningún dato en la portada.** Ni 407, ni la reducción de la desigualdad, ni un titular. El mejor argumento del
   proyecto no aparece.
4. **El mapa habla en jerga interna**: «Mayoritario DDD», «Navegador electoral», «Productos del registro durable de
   DDD», buscador por «CUSEC». Faltan dos cosas que el público espera: buscar por municipio, código postal o dirección,
   y una ficha de distrito con dirección propia para compartir.
5. **Disposición.** En las capturas, en escritorio el mapa ocupa la mitad del ancho, la leyenda tapa el suroeste y los
   botones de encuadre pisan el control de zoom; en móvil, el panel de herramientas va antes que el mapa y hay que
   pasar varias pantallas para verlo. Conviene comprobarlo en vivo: desde entonces se han retirado carteles.
6. **Peso.** Abrir el mapa son unos 470 KB comprimidos más los distritos de la provincia (Madrid, 891 KB). La carga
   ligera para móvil está aprobada y pendiente. Los mapas de referencia usan teselas vectoriales y no ficheros
   completos por provincia.
7. **Restos de versiones anteriores.** El sitio sigue montando la V2, la V3, el visor nacional y el tablero junto a la
   V4 oficial, y `web/textos.md` (los textos de la V2 que debía escribir el propietario) sigue casi vacío. No afecta a
   la V4, pero es superficie que mantener y que un buscador puede enseñar antes que la buena.
8. **Pie hostil.** La primera frase legal que lee el visitante es una advertencia de acciones contra el plagio. En un
   proyecto que pide confianza, lo primero debería ser cómo citar y reutilizar los datos.
9. **Imágenes generadas por IA** del Congreso y del mapa de España en la cabecera de un sitio que promete datos
   verificables. Están declaradas, pero restan.
10. **Faltan piezas de confianza**: quién ha revisado, cómo contactar, resumen en inglés, material de prensa, el DOI.

### 8.4 Opciones (decide el propietario)

- A. Dos puertas claras desde la portada: «La propuesta» (la causa, con su voz) y «El estudio» (neutro, con datos).
- B. Portada de estudio con un titular numérico y «Busca tu distrito»; la causa, en una página propia.
- C. Dejarla como está y asumir que el público será el ya convencido.

---

## 9. Auditoría de la dirección del proyecto

Se audita el trabajo de dirección por sus huellas en el repositorio: reglas, decisiones registradas, plan y resultados.

| # | Aspecto | Nota | Evidencia | Qué le falta |
|---|---|:---:|---|---|
| 1 | **Visión y constancia** | 9 | Del mapa de 2022 al motor de 2026 sin perder la idea; objetivo escrito: «un motor repetible», no un mapa | Decidir qué quiere ser de mayor (§11) |
| 2 | **Rigor e integridad** | 8,5 | «Hay que ser fiel a la realidad», datos oficiales «nunca de memoria», geometría sin votos, pérdidas y excepciones declaradas, nunca se publica un plan inválido | Aplicarse el mismo rigor a los textos públicos (§8.3) y a la elección de la función de calidad |
| 3 | **Creatividad y originalidad** | 7,5 | Detalle en §10 | Publicar lo propio para que cuente como aportación |
| 4 | **Velocidad y calidad de decisión** | 7 | 216 decisiones registradas, con motivo; excepciones fechadas | Unas 50 corrigen, matizan o sustituyen a otra (medida aproximada, por palabras clave); varios «sí a todo» en un día; alguna fusión antes de la medida que la condicionaba |
| 5 | **Foco y gestión del alcance** | 5 | Su primera regla es «camino crítico, sin desvíos» | El alcance lo abre él: mapa de 350, 19 autonómicas, histórico por época, doble vuelta, tres visores nuevos, archivo, propiedad intelectual, tres renombrados, todo antes de unas elecciones |
| 6 | **Control del riesgo** | 8 | Autorización por campaña, revisor independiente, guardián, topes, lecciones tras cada incidente | Quitó el revisor obligatorio del entorno de producción: el único control de lanzar y publicar es una frase en un chat. Y la dependencia de una sola persona |
| 7 | **Gestión de recursos** | 6,5 | Coste medido y con tope; infraestructura de céntimos | 27 % de los minutos en ejecuciones fallidas y 45 % de éxito a la primera (del 27-10 al 10-11); el gasto en agentes solo se anota desde mediados de noviembre (unos 280 USD en chats cerrados del 15 al 24-11, parcial) |
| 8 | **Calidad de ingeniería exigida** | 7,5 | Pruebas, contratos, determinismo, diseño antes de implementar | Complejidad autoinfligida: copias `legacy/`, cabeceras manuales de versión, documentación desbordada |
| 9 | **Organización y delegación** | 7 | Estructura de roles con agentes (planificador, coordinador, operador, implementadores), relevos y traspasos: es innovadora y funciona | No hay ningún par humano que le lleve la contraria en estadística, ciencia política o cartografía |
| 10 | **Comunicación y posicionamiento** | 4,5 | La página «Comprender» demuestra que sabe explicarlo | Portada, sin inglés, tono legal defensivo, afirmaciones públicas sin revisar contra el estado real. No he encontrado eco en prensa del trabajo de 2026; el mapa de 2022, muy inferior, sí lo tuvo |
| 11 | **Apertura a la crítica** | 8 | Encarga auditorías, guarda lecciones, escribe «solo la excelencia es aceptable» y publica hallazgos en contra | Que la crítica venga también de fuera |
| 12 | **Estrategia de propiedad intelectual** | 5 | Registro de autoría hecho; licencias por tipo de contenido | Tres giros en ocho días; la licencia actual protege poco (las técnicas son públicas y lo anterior al 14-11 sigue bajo Apache-2.0) y cuesta credibilidad |
| | **Conjunto** | **7** | | |

### Perfil

Un fundador-arquitecto con criterio propio, obsesión sana por la trazabilidad y una capacidad de decisión muy por
encima de la media. Ha hecho solo, con agentes, en diez semanas, lo que normalmente pide un equipo y un año. Sus
puntos fuertes son los del ingeniero y el jurista: reglas claras, excepciones escritas, nada sin fuente.

Sus puntos débiles son los del fundador que lo quiere todo a la vez:

- **Abre frentes más deprisa de lo que los cierra.** El coste no está en los créditos de cada respuesta, que vigila
  mucho, sino en el número de frentes, que no vigila.
- **Pule la forma mientras la pregunta de fondo espera.** Tres notaciones y tres visores nuevos han pasado por delante
  de «¿es bueno el mapa y quién lo confirma?».
- **Decide con los mapas delante.** Es buen instinto de producto y mala práctica de método si no se declara.
- **Confunde proteger con cerrar.** En este campo, la credibilidad viene de que otros puedan repetirlo.
- **No tiene contrapeso humano.** Los agentes ejecutan y revisan forma; no discuten los supuestos.

### Tres consejos, de director a director

1. Cambiar la pregunta diaria de «¿qué más construimos?» a «¿qué afirmación nuestra ha confirmado alguien de fuera?».
2. Nombrar un consejo de tres personas (ciencia política, estadística u optimización, cartografía o derecho electoral)
   y darles derecho de veto sobre lo que se afirma en público.
3. Elegir una identidad principal y dejar que las otras dos la sirvan (§11).

---

## 10. Creatividad y originalidad

El punto de partida que plantea el propietario es correcto: la idea no es nueva (García-Trevijano, y antes el
distrito uninominal a doble vuelta, que Francia usa hace décadas) y las técnicas tampoco. La originalidad hay que
buscarla en otro sitio, y existe.

**Dónde no hay originalidad:** en la teoría política (heredada), en el algoritmo de búsqueda (GerryChain), en el
resolutor (OR-Tools), en la idea de elegir por orden lexicográfico.

**Dónde sí la hay:**

1. **La operacionalización.** Convertir «la mónada» en una fórmula sin ambigüedad (K por provincia = población entre
   120.000, redondeado, mínimo uno; el total es un resultado) y defender que 350 «invierte la causalidad». Es una
   decisión de diseño institucional con criterio, y además reduce la desigualdad territorial a la quinta parte.
2. **El contrato con excepciones declaradas antes de calcular.** Traslada al trazado de distritos una disciplina
   propia del derecho y de los ensayos clínicos. No conozco otro proyecto de trazado que la aplique así.
3. **La semilla pública derivada de las huellas de las fuentes.** Elimina la sospecha de «probar semillas hasta que
   salga el mapa que gusta». Idea sencilla, efecto grande, y publicable.
4. **«Nunca peor que el publicado».** Tratar el mapa vigente como candidato y como punto de partida da estabilidad
   entre ediciones, que es lo que una autoridad electoral pediría.
5. **La naturalidad a la española.** Partidos judiciales y comarcas agrarias como aproximación a las «comunidades de
   interés». Es una respuesta local e ingeniosa a un problema que en otros países se resuelve con audiencias.
6. **Los distritos de cada época** para el histórico, en vez de proyectar el pasado sobre el mapa de hoy.
7. **La organización del trabajo con agentes**: roles, relevos, autorización por campaña, libro de costes. Como
   experiencia de dirección es, probablemente, lo más novedoso del proyecto, aunque no sea su objeto.

**Qué clase de creatividad es.** No es invención matemática: es síntesis e ingeniería institucional. Nota: 7,5. Sube
a 8,5 el día que dos de esas ideas (la semilla y el contrato) estén escritas, publicadas y citadas por otros.

**Sobre «por primera vez».** Hay que afinar la frase para que nadie la desmonte. El primer mapa es de 2022 y es del
mismo autor. Lo que ocurre por primera vez en 2026 es otra cosa, y es más valiosa: por primera vez el mapa es un
procedimiento reproducible, sección a sección, con reglas escritas, resultados reales por distrito y huellas que
permiten comprobarlo. Esa es la afirmación exacta y defendible.

**Sobre «sacarlo de la teoría ya es un gran paso».** De acuerdo, con un matiz. Que se pueden trazar distritos
razonables con datos oficiales no estaba en duda: lo hace cualquier país con sistema mayoritario. Lo que el proyecto
demuestra no es la viabilidad sino la **concreción**: convierte un debate abstracto en un objeto que cada ciudadano
puede mirar («este sería mi distrito y este habría ganado»). Ese cambio de plano es la aportación real. El objeto
prueba que la propuesta es practicable; no prueba que sea deseable. Eso lo discutirá la ciencia política, y por eso el
proyecto necesita ponerse delante de ella.

**Sobre «estadística respaldada por ciencia política».** Hoy es, sobre todo, geografía computacional e ingeniería de
datos al servicio de una tesis política. El respaldo de la ciencia política todavía hay que escribirlo (§7.3).

---

## 11. Hacia dónde vamos

**Lo que dice el plan:** noche del 29-11; regenerar la legislatura nueva con el padrón de 2025; corte de versión;
investigación (óptimo en medianos, comparación, función de calidad); reglas generalizables a otros países; web servida
desde el archivo; repositorio de publicación.

**Mi lectura:** los objetivos técnicos son los correctos; el orden, no. La validación va la última y es lo que más
pesa en la respuesta a «en qué liga jugamos».

**La decisión de fondo que falta: qué es el proyecto.** Hoy intenta ser tres cosas con requisitos opuestos.

| Identidad | Qué exige | Qué tiene hoy | Qué le sobra hoy |
|---|---|---|---|
| **Campaña cívica** (la causa del diputado de distrito) | Relato, alcance, mapa fácil, prensa, móvil | La causa y la portada | La jerga y el peso del mapa |
| **Investigación** | Apertura, revisión por pares, neutralidad de etiquetas, bibliografía | Rigor interno, datos, honestidad | La consigna en portada y la licencia cerrada |
| **Producto** (Deslinde como motor para terceros o para otros países) | Comparativas, referencias, clientes, soporte | Reproducibilidad y procedencia de primera | Estar atado a una causa política concreta |

Los nombres ya ofrecen la salida: **Deslinde** puede ser el motor neutral (investigación o producto) y **Diputado de
Distrito**, la propuesta que lo usa. Separarlos de verdad (voz, sitio, licencia) deja que cada uno gane su público sin
restarle al otro. Como producto, la competencia real no son los algoritmos académicos sino las herramientas comerciales
de dibujo manual; un motor automático, certificado y con procedencia es un argumento diferencial, pero solo se vende
con comparativas y referencias.

### Qué falta, por plazos

**Hasta el 29-11 (camino crítico):** ensayo en seco de la noche electoral con los flujos nuevos (no consta hecho);
corregir las dos frases de la página de método; retirar de lo publicado o explicar el distrito de 733 habitantes;
ningún frente nuevo.

**Diciembre:** comparación con GerryChain puro y `redist` en los casos pequeños y en tres grandes; mapas alternativos
desde Deslinde; página pública «lo que cuesta cada regla» (igualdad, municipios, naturalidad) con las cifras de §6;
índices de desproporcionalidad y sensibilidad de la doble vuelta; portada con datos; búsqueda por municipio.

**Primer trimestre de 2027:** informe técnico con revisores; cotas en medianos y grandes; decisión de identidad y de
licencia de una vez; consejo asesor; carga ligera y teselas; resumen en inglés.

---

## 12. Riesgos principales

| Riesgo | Probabilidad | Daño | Mitigación |
|---|:---:|:---:|---|
| Un crítico publica el distrito de 733 habitantes, el de Águilas o la frase de los «miles de mapas» | Alta | Alto | Corregir antes de buscar difusión |
| Noche del 29-11 sin ensayo completo | Media | Alto | Ensayo en seco o renunciar al directo y publicar al día siguiente |
| Persona única | Cierta | Muy alto | Documentación para un ingeniero humano; consejo asesor; un segundo con permisos |
| La portada aleja a investigadores y periodistas | Alta | Medio | Separar voces |
| Dispersión tras el 29-11 (legislatura nueva, histórico, otros países, repositorios) | Alta | Medio | Un trimestre de consolidación |
| La licencia cerrada impide la validación que el proyecto necesita | Media | Alto | Licencia de reproducción para investigación, o apertura del núcleo de reglas y del validador |
| Etiquetas de bloques leídas como sesgo | Media | Medio | Etiquetas neutrales; «sin coaliciones» por defecto |
| Dependencia de un proveedor de agentes para operar | Media | Medio | Procedimientos ejecutables sin agentes |

---

## 13. Límites de esta auditoría

- **Web:** no he podido abrir `diputadodedistrito.es` desde la sesión. Juzgo código y capturas del 19 y 20-11; desde
  entonces se han retirado cuatro carteles del mapa. No hay datos de visitas en el repositorio.
- **Motor:** no lo he ejecutado. Me apoyo en la definición formal, en los estudios versionados y en los datos publicados.
- **Cifras propias:** desvíos calculados sobre `datos/composicion/runs/<territorio>_<run>.csv`, tomando el run más
  reciente de cada territorio (los 71 coinciden con los que el `README.md` da como cadena completa validada). «Mapa
  anterior» son los ficheros `datos/composicion/congreso_*.csv`. El desvío es respecto a la media del territorio, sin
  aplicar exenciones ni cuotas por circunscripción, por eso no coincide con el recuento «fuera de tolerancia» del
  proyecto. El reparto entre provincias usa `visor/v2/datos/provincias.json` (escaños de 2023 y K de 407).
- **Decisiones corregidas:** recuento por palabras clave sobre las líneas de decisión del plan; orientativo.
- **Externo:** una búsqueda por tema, hoy. No he leído los artículos completos. La atribución del mapa de 2022 sale del
  resumen de la prensa que devuelve el buscador; la página no se pudo abrir.
- **Notas:** son opinión. Otra persona con la misma evidencia podría mover cualquiera un punto.
- **El encargo llegó cortado por el principio** («…estilo y que me des un veredicto en un fichero MD»). Si la primera
  parte pedía algo más, no está cubierto.

---

## 14. Fuentes

**Internas:** `README.md`; `docs/ESTADO.md`; `docs/PLAN.md` (decisiones D-26 a D-204);
`docs/ARQUITECTURA/DESLINDE_1_0.md`, `ADR-001-enfoque.md`, `MADUREZ.md`; `docs/ESTUDIOS/T296_OPTIMO_D8/`,
`T196_BATERIA_D8/`, `T179_naturalidad_nacional/`, `T155_COSTE/`, `T295_ACCESIBILIDAD/`, `T441_CARGA_LIGERA/`,
`N06_DECISION_K_20261012/`, `T423_V4/preview/`; `docs/ARTICULO_JOSS/paper.md`; `documentacion_publica/docs/metodo.md`;
`visor/v4/`; `web/textos.md`; `LICENSE`; `dashboard/hemiciclo.json`; `datos/composicion/`;
`orchestracion/publicaciones_visor.json`; `territorios/nac30/config/nac30_2025.yaml`.

**Externas (consultadas el 24-11-2026):**

- Mapa de 2022: [Crean un «mapa» nacional del Diputado de Distrito](https://thediplomatinspain.com/2022/01/30/crean-un-mapa-nacional-del-diputado-de-distrito/) ·
  [Cómo quedaría España si se aplicara el Diputado de Distrito](https://thediplomatinspain.com/2022/03/11/como-quedaria-espana-si-se-aplicara-el-diputado-de-distrito/) ·
  [Servimedia](https://www.servimedia.es/noticias/plataforma-demos-propone-reformar-ley-electoral-para-crear-figura-diputado-distrito%E2%80%99/2800535)
- ReCom: [Recombination: a family of Markov chains for redistricting](https://arxiv.org/pdf/1911.05725)
- SMC y `redist`: [Sequential Monte Carlo for sampling balanced and compact redistricting plans](https://arxiv.org/abs/2008.06131) ·
  [página del proyecto](https://imai.fas.harvard.edu/research/smcredist/)
- Optimización exacta: [Political districting to minimize county splits](https://par.nsf.gov/biblio/10579889-political-districting-minimize-county-splits)
- Alemania: [revisión de la literatura y caso alemán](https://or.rwth-aachen.de/files/research/repORt/LitSurvey_PoliticalDistricting__Goderbauer_Winandy_20181024.pdf) ·
  [escenario de 125 distritos](https://www.or.rwth-aachen.de/files/research/repORt/WKStudie_125_repORt51_GoderbauerEtAl_2018.pdf)
- México: [Simulated annealing and artificial bee colony for the redistricting process in Mexico](https://pubsonline.informs.org/doi/10.1287/inte.2019.0992) ·
  [modelo matemático y algoritmos del INE](https://repositoriodocumental.ine.mx/xmlui/bitstream/handle/123456789/152748/Anexo4ModeloMatematicoyAlgoritmos230815.pdf)
- Métodos de 2025-2026: [Cycle Walk](https://www.arxiv.org/pdf/2509.08629) · [Marked Edge Walk](https://arxiv.org/pdf/2510.17714v1) ·
  [Balanced Up-Down Walk](https://arxiv.org/pdf/2602.11993) · [programación entera frente a short bursts](https://arxiv.org/pdf/2508.07446v2) ·
  [Spanning trees and redistricting](https://arxiv.org/abs/2210.01401)
- Estándares: [Código de buenas prácticas de la Comisión de Venecia](https://www.venice.coe.int/images/SITE%20IMAGES/Publications/Code_conduite_PREMS%20026115%20GBR.pdf) ·
  [criterios del ISTAT para los colegios de 2017](https://www.istat.it/it/files//2017/12/A-Audizione-Collegi-2017_Camera_Senato_per-pubblicazione.pdf)
- España: [archivo electoral SEA](https://link.springer.com/10.1038/s41597-021-00975-y) ·
  [mapas «calle a calle», explicados](https://maldita.es/malditateexplica/20230727/elecciones-mapas-resultados-elecciones-representacion/) ·
  [diario de sesiones de la Asamblea de Madrid sobre las 43 circunscripciones](https://www.asambleamadrid.es/static/doc/publicaciones/IX-DS-609.pdf)
