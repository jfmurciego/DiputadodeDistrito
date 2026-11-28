# T-478 · Borrador «Qué cambiaría» (sin publicar; el propietario decide)

Borrador para el propietario, a partir de `INFORME.md`. Cifras de 2023 con el mapa publicado.

## Qué pasa hoy
El sistema real reparte 350 escaños en 52 circunscripciones con D'Hondt: Gallagher 5,65, el PP con el 33,3 % de los votos obtiene el 39,1 % de los
escaños, 7,8 % de los votos sin representación. El reparto de escaños por provincia se aleja de la población 10,5 puntos (Loosemore-Hanby, padrón 2022).

## Qué pasaría con 407 distritos de un escaño
- **Mayoría simple**: el PP tendría 234 de 407 (57,5 %) con el mismo 33,3 % de votos; Gallagher 21,9; 61 % de los votos sin representar.
  La desigualdad territorial baja de 10,5 a 2,0 puntos.
- **Doble vuelta por distrito**: sin coaliciones (dv_base) el cuadro apenas cambia (PP 225, PSOE 156); con bloques coaligados (dv_A) el
  Gallagher baja a 7,9, pero solo quedan dos candidaturas efectivas y el 46 % de los votos de primera vuelta sigue sin escaño en su distrito.

## Qué recibe el propietario
Una tabla comparable de seis elecciones con cinco sistemas, y la desigualdad territorial por separado: el cambio de distritos arregla el reparto
entre provincias (10,5 → 2,0) pero, con un escaño por distrito, empeora la proporcionalidad entre partidos (5,65 → 21,9 con mayoría simple).

## Qué pasa si no se hace
La auditoría seguirá citando cifras sin fuente en git («207 de 325», «padrón 2023»); con esta tabla cada cifra enlaza a un fichero con sha256.

## Criterio de aceptación
`python herramientas/indicadores_sistemas.py` regenera las tablas sin cambios (sha256 de `fuentes.csv` estable) y `tests/test_t478_indicadores.py` pasa.

## Pregunta de estudio para el propietario
Con distritos uninominales y mayoría simple, la desproporcionalidad entre partidos se multiplica por cuatro (Gallagher 5,65 → 21,9) mientras la
desigualdad entre provincias cae de 10,5 a 2,0: ¿qué se quiere comunicar como criterio principal del mapa, la igualdad del voto entre territorios
o la proporcionalidad entre partidos, y se acepta publicar los dos números a la vez sin elegir uno?
