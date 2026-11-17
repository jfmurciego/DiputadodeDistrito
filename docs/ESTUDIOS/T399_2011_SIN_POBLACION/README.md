# T-399 · Las 105 secciones del seccionado 2012 sin población en 2011-11: qué son (solo lectura, sin implementar A ni B)

Medido con fuentes ya acreditadas (sin descargas nuevas): `seccionado_2012.zip` (772ad76b…), `cartografia_censo2011_nacional.zip` (d0151e0c…, www.ine.es/censos2011_datos), tabla de indicadores del Censo 2011 (T-357), Observatorio 2011 (provincia 08). Detalle por sección: `madres.csv`.

## Hallazgos
1. **Fuente de un seccionado 2011**: la cartografía del Censo 2011 (`cartografia_censo2011_nacional.zip`, 35.960 secciones) baja desde la nube y ya está acreditada (T-357). También responden 200 desde la nube `https://www.ine.es/prodyser/cartografia/seccionado_2011.zip` (65.361.765 bytes) y `seccionado_2010.zip`; no los he descargado ni verificado su contenido ni su sha256 (pendiente, si se elige A). `www.ine.es` no rechaza la nube.
2. Las 105 secciones son **dos grupos**:
   - **63 hijas** (partidas de una sección del Censo): su geometría cae ≥ 50 % (56 con ≥ 90 %) dentro de una sección del Censo con población y en el mismo municipio (63/63). Son 60 madres (57 con una hija; 3 con dos: 0820501005, 0820505001, 0827801001), con 179.435 hab. en el Censo. Las madres siguen en el seccionado 2012 con su código y la mitad de su área (mediana 52 %; una desaparece). Confirma la hipótesis: la población de la madre en el Censo ya incluye la de sus hijas, y rellenar las hijas la cuenta dos veces.
   - **42 sin madre** (27 en Pontevedra, 5 en Valencia…): existen en la cartografía del Censo con el mismo código y la misma geometría (> 90 %), pero **sin fila en la tabla de indicadores**. No son hijas: es dato que falta en el Censo. Aquí no hay doble cómputo con la tabla; falta saber si su población está en el total municipal oficial del Censo (no tenemos esa fuente).
3. **Los votos de 2011 siguen el seccionado anterior**: en Barcelona (08) solo 2 de las 16 hijas tienen votos propios en el Observatorio, y las 16 madres sí. Con el seccionado 2012 los votos de las hijas no existen (los de la madre quedan con la población de la madre): el desalineo afecta también a M07. Solo medido en 08; el resto, por comprobar.
4. Lo contrario (44 secciones del Censo que no están en 2012) es lo que resolvió T-396 (D-153).
5. Aparte (otra tarea): provincia 35, puente de La Graciosa `3502401010` no está en el seccionado 2012 ni en la cartografía del Censo ni en la tabla del Censo (su par 3502401001 sí): la causa es el puente, no el seccionado.

## Recomendación
- **A** para las 63 hijas: usar para 2011-11 el seccionado del propio Censo 2011 (o `seccionado_2011` si su sha y contenido lo confirman). Las hijas desaparecen, población = Censo sin relleno y los votos casan con la madre. B (repartir la madre con proporciones del Atlas 2015) solo tendría sentido manteniendo 2012, y no hay votos por hija.
- Para las **42 sin fila en el Censo**: ahí sí cabe el relleno de D-126 (Atlas 2015, `rellenada_año_cercano`), pero el ajuste al total municipal exige el total oficial del Censo 2011 por municipio, que no está en el repo; sin él el ajuste no actúa (ver `docs/ESTUDIOS/T399_SIN_POBLACION/`). Pontevedra (27 de 42) queda en BLOQUEADA_RELLENO (2,6 %) aunque se rellene, y 3605901003 no tiene dato en ningún año.
- #883 no debe fusionarse con la regla actual (doble cómputo en las 63).
