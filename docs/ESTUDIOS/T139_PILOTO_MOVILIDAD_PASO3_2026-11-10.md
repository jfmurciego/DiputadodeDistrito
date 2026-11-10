# T-139 · Piloto de movilidad, paso 3: tabla por provincia y recomendación (2026-11-10)

Solo indicador, sin peso. No toca motor ni función de calidad; nada se publica. Sigue a los pasos 1 y 2 (mismos datos EM-1 y definición).

## Compacidad: la del motor (no se mezcla con otra)
Polsby-Popper `polsby_popper` de las propiedades del GeoJSON M06 vigente de cada provincia (misma definición que el motor, CRS EPSG:3035). Fuente: ZIP M06 del registro `orchestracion/publicaciones_visor.json`, bajado del blob git y verificado contra su sha256 (`herramientas/movilidad_em_union.py compacidad`). La población por distrito del M06 coincide con `datos/composicion` en los 37 distritos.
| Provincia | run M06 | blob | sha256 del ZIP M06 |
|---|---|---|---|
| Cádiz | 41500124775 | eafe4c84 | b394db0e089c1360… |
| Granada | 41296546816 | 611bf934 | 6eeb3324efed451f… |
| León | 41629735636 | d3f23897 | 64e44b77dcd81fee… |
| Gerona | 41298839274 | 4f8354e9 | cd4875419859e9ab… |
| Tarragona | 42514991952 | 0999b5db | 7f6674484deb6b85… |
Sha completos en `datos/movilidad/piloto_compacidad_m06.csv` (sha256 10a266c8a4d32aa93f3efd16abff191ee127e7b95e4d43caef2a294754eb93ac).

## Tabla (`datos/movilidad/piloto_tabla_provincias.csv`, sha256 628d0f79cbd9ef6d8a725e29061f63e9642a108f67b4adcb6bd06d53cbccf099)
Cohesión del plan = fracción de flujos entre áreas distintas que queda en el distrito (paso 2). ρ = Spearman entre distritos de la provincia.
| Provincia | K | Población | PP medio | PP mín. | Cohesión con capital | Sin capital | ρ cohesión–PP (con / sin) | ρ cohesión–población del distrito |
|---|---|---|---|---|---|---|---|---|
| Cádiz | 11 | 1.254.866 | 0,278 | 0,060 | 0,643 | 0,657 | 0,16 / 0,27 | 0,11 |
| Granada | 8 | 934.072 | 0,143 | 0,044 | 0,410 | 0,603 | 0,81 / 0,71 | -0,12 |
| León | 4 | 448.573 | 0,265 | 0,154 | 0,660 | 0,834 | 0,20 / 0,50 | 0,60 |
| Gerona | 7 | 808.672 | 0,148 | 0,063 | 0,615 | 0,704 | -0,32 / -0,54 | -0,75 |
| Tarragona | 7 | 848.592 | 0,105 | 0,035 | 0,556 | 0,588 | 0,46 / 0,60 | 0,82 |
| Todos los distritos | 37 | | | | | | 0,38 / 0,41 (n 37 / 32) | 0,04 |
Con 4 a 11 distritos por provincia, cada ρ provincial es muy ruidoso (León, n 4, no es interpretable); solo el conjunto de 37 da una pista.

## Lectura
- La cohesión funcional **no es la compacidad**: ρ ≈ 0,4 en conjunto (comparte poco más del 15 % del orden), con signo distinto según provincia (Granada alta, Gerona negativa). Y no sigue a la población del distrito (ρ 0,04).
- La capital pesa: quitarla sube el plan entre 0,02 (Cádiz) y 0,23 (Granada, León). Un indicador con capital premia o castiga según cómo reparte el plan la capital.
- Con un solo plan vigente por provincia **no se puede saber si discrimina** entre planes buenos y malos: falta variación dentro del territorio. Ese es el dato que decide un peso.

## Recomendación (la decide el propietario con el Planificador)
- **A. Sin peso, solo informativo** (recomendada ahora): publicar/consultar el indicador junto a población y compacidad; coste ya hecho.
- **B. Medir su discriminación en el universo de planes del motor nuevo** (mismas 5 provincias, varios planes por territorio): si la variación entre planes supera con holgura la incertidumbre (hipótesis de reparto de áreas partidas, flujos truncados, datos 2019), valorar un peso pequeño y reversible. Coste: una ejecución de ensemble por provincia, ya prevista, más una herramienta que lea los planes.
- **C. Peso ya**: no recomendable: un solo plan, datos de 2019-mar-2020, ρ ≈ 0,4 con compacidad (parcialmente redundante), y 15 capitales fuera.
Antes de cualquier peso nacional: cubrir las 15 capitales (cuatro vías en la nota del paso 2) y refrescar los datos (sin serie vigente del INE).
