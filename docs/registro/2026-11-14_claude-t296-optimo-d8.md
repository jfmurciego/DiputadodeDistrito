## 2026-11-14 — T-296 — óptimo exacto de D8 (CP-SAT) y hueco del ganador de Deslinde

- Causa: D-73 (1) y D-86.3: certificar con un resolutor exacto abierto la función D8 (D-68) bajo las reglas del núcleo
  y medir cuánto le falta al ganador de Deslinde. Estudio privado (D-92): sin publicar código.
- Cambio: `docs/ESTUDIOS/T296_OPTIMO_D8/` (nuevo): `optimo_d8.py` 1.0.0 (CP-SAT lexicográfico por etapas sobre el mismo
  Problema, reglas y clave D8 que la competición; solo lee `ddd_motor2` y `herramientas/certificador_exacto.py`), informe y
  `resultados/` de 9 territorios. No toca motor, núcleo, producción, locks ni workflows.
- Resultado: óptimo D8 demostrado en 8 provincias del Congreso con K 2-4 (1-9 s). El ganador lo iguala en Álava, Huesca y
  La Rioja; pierde solo en desvío en Cuenca, Guadalajara y Lugo; en Burgos (2 frente a 3) y Valladolid (2 frente a 4) hay
  planes válidos con menos demarcaciones partidas. El término de frontera vale 0 siempre (el M03 no trae
  `shared_border_m`). La Rioja autonómica (K=33): solo cota en 120 s.
- Pruebas: en local, el canónico y el ganador fijados son factibles en el modelo y dan su clave oficial (20/20); cada
  óptimo pasa `reglas.evaluar`. Sin ejecuciones en Actions.
