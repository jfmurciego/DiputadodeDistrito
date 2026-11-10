# T-132 (A) · Comparación de generadores: validez y calidad

Fecha: 2026-11-10. Mismas entradas (batería T-132), mismo contrato y la misma validación de producción
(`herramientas/validar_ejecucion.py`). Semillas 1-5. Detalle: `BANCO.csv` (validez) y `CALIDAD.csv` (calidad).

## Validez

| Generador | Ejecuciones | PASS | Territorios siempre válidos |
|---|---|---|---|
| Canónico (M04 7.6.7 + M05 7.4.4, semilla fija 12345) | 71 | 71 | 71/71 |
| GerryChain de producción (ReCom desde M04; semilla canónica si M04 no es admisible) | 355 | 355 | 71/71 |
| Árbol: `recursive_tree_part` por provincia + ReCom | 355 | 188 | 30/71 |
| Exacto: semilla de factibilidad CP-SAT (certificador T-136 1.1.0, perfil producción) + ReCom | 5 | 3 | 3/5 |

- GerryChain: la Formación M04 no es admisible como estado inicial en el 45 % de las ejecuciones; producción usa entonces
  la semilla M05 canónica.
- Árbol: si la semilla es admisible, ReCom da PASS siempre (188/188). Los fallos son de la semilla: sin corte equilibrado
  con unidades indivisibles, núcleos cerrados y tolerancia, o incumple techo, suelo o mixtos R012.
- Exacto, en 5 territorios donde la semilla por árboles nunca es válida: Congreso Valladolid (226 átomos, 4.577 variables, 170 s),
  Congreso Cádiz (46 átomos, 1,3 s) y Canarias (117 átomos, 3 s) dan PASS con ReCom. La Rioja (193 átomos, 20.380 variables) y
  Madrid (269 átomos, 102.719 variables) quedan DESCONOCIDO en 900 s con 2 hilos.
  Escala observada: hasta unos 5.000 variables en minutos; desde 20.000 sin respuesta en 15 min.

## Calidad frente al canónico (por territorio; orden lexicográfico vigente: fuera de tolerancia, luego desvío máximo)

| Generador | Territorios | Mejora | Empata | Empeora | Δ fuera tol. | Δ desvío máx. | Δ ECM | Δ distritos mixtos | Δ Polsby-Popper |
|---|---|---|---|---|---|---|---|---|---|
| GerryChain, mejor de 5 | 70 | 19 | 45 | 6 | −0,90 | −0,002 | +0,0003 | −0,10 | +0,033 |
| GerryChain, mediana de 5 | 70 | 14 | 45 | 11 | −0,83 | 0,000 | +0,0004 | −0,06 | +0,034 |
| Árbol, mejor de 5 | 43 | 11 | 24 | 8 | 0,00 | −0,005 | +0,0002 | −0,07 | +0,052 |
| Árbol, mediana de 5 | 43 | 7 | 21 | 15 | 0,00 | −0,003 | +0,0003 | −0,05 | +0,057 |
| Exacto (1 semilla) | 3 | 0 | 1 | 2 | +0,67 | +0,002 | +0,0069 | +1,0 | +0,017 |

Δ = media de (generador − canónico) en los territorios donde ambos son válidos. Municipios partidos: Δ 0 en todos.

Lectura técnica: GerryChain desde la semilla canónica mejora o iguala al canónico en el 91 % de los territorios (mejor de 5)
y gana compacidad (+0,03 PP). La semilla genérica por árboles no basta en 41 territorios. La factibilidad por CP-SAT resuelve
algunos de ellos, pero sin optimizar es peor que el canónico y no escala a Madrid ni a La Rioja en 15 min.
