---
title: Cómo se hace este mapa
hide:
  - navigation
---
<!-- VERSIÓN: 2.0.1 · FECHA: 2026-11-26 · T-463: solo afirmaciones ciertas hoy (sin «miles de mapas alternativos», sin «repetirlo»). 2.0.0 · 2026-11-19 · T-423: reescrita para el público general (decisión del propietario): capítulos en español llano,
     sin jerga ni códigos internos. Ejemplo de Huesca: cifras de datos_abiertos/INDEX.json (nac22) y visor/v2/datos/provincias.json.
     ANTERIOR: legacy/documentacion_publica/docs/metodo_pre_t463_20261126.md -->

# Cómo se hace este mapa

Esta página cuenta, paso a paso y sin tecnicismos, cómo se dibujan los distritos de Diputado de Distrito y cómo se cuentan los votos en ellos. Usamos como ejemplo la provincia de Huesca.

## 1. Qué es un diputado de distrito

Hoy, en las elecciones al Congreso, cada provincia elige varios diputados a la vez y los escaños se reparten entre las listas de los partidos. Votas a una lista, no a una persona.

Con un **diputado de distrito**, cada provincia se divide en trozos más pequeños, los distritos. Cada distrito elige **a una sola persona**. Así sabes quién es tu representante y a quién pedir cuentas.

Este proyecto dibuja esos distritos para toda España, con datos oficiales, y muestra qué habría pasado con los votos reales de unas elecciones ya celebradas. Es un estudio: **no tiene valor oficial**.

## 2. De dónde salen los datos

Solo usamos datos oficiales y públicos:

- **Cuánta gente vive en cada sitio**: el padrón del Instituto Nacional de Estadística (INE).
- **El mapa en trozos pequeños**: las secciones censales del INE. Una sección censal es una zona pequeña, normalmente de entre unos cientos y unos pocos miles de habitantes. Es la misma unidad que se usa para organizar las mesas electorales.
- **Los votos**: los resultados oficiales del Ministerio del Interior, mesa a mesa.
- **Los escaños de hoy**: los publicados en el Boletín Oficial del Estado (BOE).

¿Por qué solo datos oficiales? Porque así cualquiera puede comprobar de dónde sale cada cifra. Nada se estima a ojo ni se copia de memoria.

## 3. Cuánta gente vive en cada trozo del mapa

Lo primero es saber cuántas personas viven en cada sección censal. Con el padrón del INE, cada trozo del mapa queda con su población.

En Huesca hay 286 secciones censales repartidas en 202 municipios. Algunas están en la ciudad de Huesca y son pequeñas en superficie; otras abarcan varios pueblos del Pirineo.

## 4. Qué trozos se tocan entre sí

Un distrito tiene que ser una pieza continua: no puede tener un trozo aquí y otro a 50 kilómetros sin nada que los una.

Por eso, antes de dibujar, se apunta qué secciones son vecinas, es decir, cuáles comparten frontera. Con esa lista de vecinos se garantiza después que cada distrito sea de una pieza.

## 5. Cómo se dibujan los distritos

Cada provincia recibe un número de distritos según su población: en toda España salen **407 distritos**. Huesca, que hoy elige 3 diputados, tendría 2 distritos.

Para dibujarlos se siguen tres reglas:

1. **Población parecida.** Todos los distritos deben tener una población similar, para que cada voto pese más o menos lo mismo.
2. **Municipios enteros siempre que se pueda.** Un pueblo no se parte entre dos distritos. Un municipio solo se reparte cuando es demasiado grande para caber en un distrito o cuando no hay otra forma de que las poblaciones salgan parecidas.
3. **Piezas unidas.** Cada distrito es un territorio continuo.

En Huesca el resultado son dos distritos: uno de 106.342 habitantes con 74 municipios y otro de 120.536 habitantes con 128 municipios. Ningún municipio queda partido.

## 6. Cómo se mejoran y se comprueban

El primer dibujo casi nunca es el mejor. El ordenador lo va retocando, pasando secciones de un distrito a su vecino, para que las poblaciones se parezcan más sin romper ninguna de las reglas.

Cada mapa compite con una docena de candidatos generados con las mismas reglas, y se publica el mejor según un criterio fijo y público.

Al final, cada distrito se comprueba uno por uno: que tenga una sola pieza, que su población esté dentro de lo permitido y que respete los municipios. Si algo falla, el mapa no se publica.

## 7. Cómo se cuentan los votos en cada distrito

Con el mapa ya dibujado, se suman los votos reales de cada mesa electoral al distrito al que pertenece. Así se sabe cuántos votos tuvo cada partido en cada distrito.

El mapa muestra dos formas de elegir al diputado:

- **Mayoría simple en el distrito.** Gana el candidato con más votos, aunque no llegue a la mitad. No es el sistema actual: hoy los escaños se reparten de forma proporcional por listas provinciales.
- **Doble vuelta.** Si nadie supera la mitad de los votos, los dos más votados pasan a una segunda vuelta. Los votos de los demás se suman al finalista de su mismo bloque (Izquierdas, Nacionalistas o Patriotas). Si su bloque no tiene finalista, esos votos no cuentan en la segunda vuelta.

La doble vuelta se ve con tres reglas: «Tres bloques» (cada bloque va unido desde el principio), «Dos bloques» (solo Izquierdas y Patriotas van unidos) y «Sin coaliciones» (cada partido por su cuenta). No se inventan porcentajes de trasvase: solo se suman votos reales.

## 8. Cómo puedes comprobarlo tú

Todo está publicado:

- Los distritos de cada provincia y sus resultados se pueden descargar.
- Cada fichero lleva una **huella digital**: un código que demuestra que el fichero no ha cambiado desde que se publicó. Si alguien lo modifica, aunque sea una coma, la huella deja de coincidir.
- El código del programa que dibuja los distritos se puede leer en GitHub, para que cualquiera pueda revisarlo. Su uso, copia o modificación requiere permiso escrito del autor, según su licencia.

## 9. Límites: lo que este mapa no dice

- **Es una simulación.** Usa los votos de unas elecciones celebradas con el sistema actual. Con distritos de un solo diputado, la gente quizá habría votado de otra manera.
- **La doble vuelta es una hipótesis.** Supone que quien vota a un partido apoyaría al finalista de su bloque. En la realidad, cada persona decide.
- **Las secciones no tienen resultado propio en el mapa.** Cuando el mapa colorea una sección, usa el color de su distrito; no es el resultado de esa sección.
- **La población cambia.** Los distritos se dibujan con el padrón de un año concreto y habría que actualizarlos.
- **No es una propuesta oficial** ni sustituye a los resultados oficiales de ninguna elección.
