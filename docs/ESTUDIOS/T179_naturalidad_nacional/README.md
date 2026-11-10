# Naturalidad en las 52 provincias del Congreso: C y D8 frente a A

Misma entrada, mismas reglas del núcleo y mismas semillas públicas que el piloto (`docs/ESTUDIOS/T172_naturalidad`).
Se comparan tres mapas por provincia:

- **A**: el mapa vigente del motor actual (`datos/composicion/`).
- **C**: el más natural (menos partidos judiciales y comarcas agrarias partidos y menos frontera cortada) entre el mapa
  vigente y lo que recorren 20 cadenas de 300 pasos sobre el grafo ponderado; la población solo cuenta hasta cumplir la
  tolerancia.
- **D8**: como C, pero sin pasar del 8 % de desvío máximo (solo para elegir; no es regla).

Nada cambia en suelo, techo, K ni tolerancia: todos los mapas cumplen el núcleo. 8 provincias tienen un solo distrito
(Ávila, Ceuta, Melilla, Palencia, Segovia, Soria, Teruel y Zamora): no hay nada que elegir y no entran en los totales.

## Resumen (44 provincias con más de un distrito)

| | A (vigente) | D8 | C |
|---|---|---|---|
| Partidos judiciales partidos | 298 de 398 | 167 | 146 |
| Comarcas agrarias partidas | 218 de 281 | 123 | 97 |
| Polsby-Popper medio | 0,160 | 0,242 | 0,259 |
| Convexidad media | 0,545 | 0,633 | 0,650 |
| Desvío máximo medio | 10,0 % | 11,4 % | 16,4 % |
| Suma de desvíos (personas) | 2.295.238 | 2.854.026 | 4.162.676 |
| Distritos fuera de tolerancia | 7 | 6 | 6 |

- **C mejora en 42 provincias y empata en 2 (Álava y Baleares); no empeora en ninguna.**
- **D8 mejora en 40, empata en 3 (Álava, Baleares y Valencia) y empeora en 1 (Alicante, por un partido judicial).**
- D8 consigue el 86 % de la mejora de C en partidos judiciales (131 de 152 partidos judiciales menos) con un desvío medio
  de 11,4 % frente a 16,4 %. El desvío medio de D8 pasa del 8 % porque cuenta los distritos fuera de tolerancia y las
  provincias donde ningún candidato bajaba del 8 % (gana el de menor exceso).
- Los distritos fuera de tolerancia son excepciones ya aceptadas (municipios o islas exentos); C no añade ninguno y
  quita uno.

## Dónde C o D8 empeoran algo frente a A

| Territorio | Función | Qué empeora frente a A |
|---|---|---|
| Alicante | D8 | partidos judiciales partidos 10 → 11 |
| León | D8 | Polsby-Popper medio 0.264 → 0.25 |

Ninguna provincia se queda sin candidato válido (salvo las de un solo distrito, que no lo necesitan).

## Ficheros

- `mapas/TABLA.csv` y `mapas/TABLA.md`: las 52 provincias, con A, D8 y C.
- `mapas/EMPEORA.csv`: lo anterior en datos.
- Láminas (A, D8, C) de 12 provincias variadas: León, Badajoz, Burgos (enclave de Treviño), Baleares y Las Palmas
  (islas), Lugo, Zaragoza, Sevilla, Valencia, Madrid, Barcelona y Asturias; `mapas/DISTRITOS.csv` las detalla por distrito.
- `resultados/<provincia>/`: RESULTADO.json (huella, semillas, versiones del entorno) y los CSV de cada mapa.

## Cómo se ha hecho

`ddd_motor2/naturalidad_competicion.py` 1.2.0 con `--funciones C,D8 --reanudar`, en sesión (sin workflow), con el
seccionado INE de cada contrato (sha256 en `datos/naturalidad/MANIFEST.json`). Islas: partición y puentes marítimos de
`configuracion/particiones_insulares_2025.json`; enclaves y exclaves: `topology_bridges` del contrato. De 1 s a 4 min
por provincia. Las autonómicas van en una segunda parte.
