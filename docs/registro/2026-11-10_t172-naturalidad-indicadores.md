## 2026-11-10 — T-172 — Indicadores de naturalidad (paso 1 del piloto)

**Causa:** la función de calidad de la competición solo mira población; la forma y las demarcaciones no se medían de forma comparable (decisión del propietario, 10-11: más pruebas y distritos más naturales).
**Cambio:** `ddd_motor2/naturalidad.py` (métricas, no reglas: Polsby-Popper, convexidad perímetro envolvente/perímetro, aristas y frontera cortadas, demarcaciones partidas y % de población en su demarcación mayoritaria, cohesión de movilidad EM-1) y `ddd_motor2/naturalidad_mapas.py` (geometría del seccionado INE, EPSG:3035). `datos/naturalidad/vigentes.csv` + MANIFEST con sha256: los 67 mapas de `datos/composicion/` (partidos judiciales, comarcas agrarias RD 1076/2014, comarcas de Aragón y Cataluña). Producción no lo importa; sin cambios en huellas ni workflows.
**Pruebas:** `tests.test_motor2_naturalidad` (8; la de forma necesita shapely), `GovernanceHeaders`; regeneración bit a bit comprobada en dos territorios.
**Riesgos:** ninguno en producción. Comarcas administrativas solo de Aragón y Cataluña (no hay más en el repo); movilidad 2019.
