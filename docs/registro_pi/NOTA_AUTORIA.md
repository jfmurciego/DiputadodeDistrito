<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Nota de autoría de Deslinde 1.0
FECHA: 2026-11-23
ESTADO: candidato (el autor la revisa con su asesor antes de presentarla)
CAMBIOS: 1.0.0 — fichero nuevo (T-281).
MOTIVO: D-196: el formulario del registro pide declarar si hubo IA y la protección cubre la autoría humana; esta nota
  resume lo que el autor definió y decidió, con su referencia en `docs/PLAN.md`. `[AUTOR]` y `[FECHA]` los rellena el
  autor al generar el paquete (`--autor`, `--fecha`): ningún dato personal se versiona.
ANTERIOR: ninguna (fichero nuevo)
-->
# Deslinde 1.0 · Nota de autoría

Autor: [AUTOR]. Fecha: [FECHA].

## Uso de inteligencia artificial

Sí. El código fuente, los documentos y los estudios se redactaron con asistentes de inteligencia artificial
(Claude Code) por encargo del autor, que dirigió el trabajo, revisó los resultados y tomó cada decisión de diseño.
Las decisiones están registradas con fecha en el plan del proyecto (`docs/PLAN.md`, referencias D-nn).

## Lo que definió y decidió el autor

1. Concepción y nombre. Delimitar distritos uninominales de forma reproducible a partir de las secciones censales; el
   nombre «Deslinde» y su composición: trazado canónico + 10 cadenas ReCom + elección D8 + mapa vigente como
   candidato (D-84). El método: competición de candidatos bajo un núcleo único de reglas, quedándose con el mejor plan
   por territorio y nunca peor que el canónico (D-32, D-48).
2. Reglas del núcleo (qué es un plan válido). Población entre suelo y techo como únicos límites duros y la tolerancia
   como objetivo; ningún distrito cruza provincias; exención del suelo solo si todas las particiones están exentas
   (D-44). Máximo un distrito mixto por municipio partido, sin admitir las infracciones del mapa vigente, con
   excepciones explícitas y motivadas que aprueba el autor (D-66).
3. Criterios de naturalidad. Elección del criterio C tras el piloto en seis territorios: población dentro de
   tolerancia y, a igualdad, menos partidos judiciales y comarcas partidos y mejor forma, cortando por donde hay menos
   vínculo (D-57, D-62).
4. Regla de elección (función D8). D8 = criterio C con el desvío máximo limitado al 8 % solo para elegir entre
   candidatos válidos, no como regla del núcleo (D-68). Deslinde 1.1: frontera compartida medida, candidato exacto
   para K <= 4 y desempate por desvío máximo (D-98). El mapa vigente entra como candidato y punto de partida (D-79).
5. Semillas públicas. La semilla sale de los sha256 del padrón y del seccionado oficiales de la edición más el
   territorio (D-50), y el territorio se identifica por su código oficial en la tabla maestra, no por el nombre de la
   carpeta (D-90). El número de cadenas es parte de la regla pública, fijado por edición antes de generar (D-63).
6. Publicación y protección. Hoja de ruta de Deslinde y definición formal publicada (D-86); licencias (D-97); el
   repositorio sigue público y Deslinde se protege con licencia propietaria y este registro (D-196).

## Lo que aportaron los asistentes

La redacción del código y de los documentos según esas decisiones, las pruebas y las mediciones que el autor pidió
para decidir (estudios citados en la definición formal). Ninguna regla, criterio ni umbral se adoptó sin su
aprobación.
