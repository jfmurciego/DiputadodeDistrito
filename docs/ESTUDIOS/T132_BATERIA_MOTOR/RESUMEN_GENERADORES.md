# T-132 (A) · Comparación de generadores

Fecha: 2026-11-10. Mismas entradas (batería T-132), mismo contrato y la misma validación de producción
(`herramientas/validar_ejecucion.py`). Semillas 1-5. Detalle por ejecución: `BANCO.csv`.

| Generador | Ejecuciones | PASS | Territorios siempre válidos | Mediana s |
|---|---|---|---|---|
| Canónico (M04 7.6.7 + M05 7.4.4, semilla fija 12345) | 71 | 71 | 71/71 | — (matriz base) |
| GerryChain de producción (ReCom desde M04; semilla canónica si M04 no es admisible) | 335 | 335 | 67/67 | 22 |
| Árbol: `recursive_tree_part` por provincia + ReCom | 332 | 188 | 30/67 | 18 |

- Sin terminar por el tope de 2 h de la sesión: Andalucía, Castilla y León, Cataluña y C. Valenciana (los dos generadores)
  y Madrid (árbol, parcial). Se completan con `banco_generadores.py ejecutar … --saltar-hechos`.
- GerryChain: la Formación M04 no es admisible como estado inicial en 150/335 ejecuciones (45 %); producción usa entonces
  la semilla M05 canónica. Con 5 semillas da 5 particiones distintas en 38 territorios y la misma en 18; siempre válidas.
- Árbol: cuando la semilla es admisible, ReCom y la validación dan PASS siempre (188/188). Los 144 fallos son todos de la
  semilla: `recursive_tree_part` no halla corte equilibrado (ReselectException, 122) con las unidades indivisibles,
  los núcleos cerrados fijados y la tolerancia del contrato (y con la banda suelo/techo); o la semilla incumple techo (15),
  suelo (4) o mixtos R012 (3), que el árbol no conoce.
- Nunca válido con árbol (23): Canarias, Cantabria, Castilla-La Mancha, Navarra, Extremadura, Galicia, Illes Balears,
  La Rioja, Madrid, País Vasco, Murcia y, del Congreso, Baleares, Barcelona, Cádiz, Las Palmas, Madrid, Málaga, Murcia,
  Pontevedra, Sevilla, Valencia, Valladolid y Zaragoza. A veces (14): Aragón, Asturias (comunidad), y del Congreso Álava,
  Alicante, Asturias, Badajoz, Granada, Huelva, León, Navarra, Orense, Santa Cruz de Tenerife, Tarragona y Vizcaya.

Lectura técnica: la validez depende hoy del constructor M04/M05 canónico; una semilla genérica por árboles no basta en
un tercio de los territorios porque no incorpora R012, los núcleos cerrados ni la granularidad de las unidades.
