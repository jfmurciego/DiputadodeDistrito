# Ficha: autonómicas vigentes sin votos por partido (T-421)

Faltan los votos por partido de la elección vigente de aut03, aut08, aut11 y aut14: el Observatorio (`fuentes/observatorio_autonomicas/index.json`)
no tiene dato por sección de 03-202305, 08-202305, 11-202512 ni 14-202305 (sí de las otras 13). Fuente: `configuracion/calendario_autonomicas.csv`.
Sin ellos la tabla `bloques_partidos_autonomicas_2026-11-19.csv` no los cubre. aut18 y aut19 (Ceuta, Melilla) no tienen autonómicas.

| Territorio | Elección | Fuente oficial (calendario) | Granularidad | Adaptador | Huella |
|---|---|---|---|---|---|
| aut03 Asturias | 2023-05-28 | SADEI, `https://www.sadei.es/sadei/pxweb/es/01/19__04/190426.px` | municipio, completos | nuevo (PxWeb → votos por sección) | por definir |
| aut08 Castilla-La Mancha | 2023-05-28 | Junta de CLM, `Resultados_CLM_2023.xlsx` (datosabiertos.castillalamancha.es); contraste: PDF de elecciones.castillalamancha.es | municipio, completos | nuevo (xlsx) | por definir |
| aut11 Extremadura | 2025-12-21 | Junta Electoral de Extremadura / DOE, `https://www.asambleaex.es/juntaelectoral/?page_id=23404` | provincia, INCOMPLETOS | nuevo; antes hay que localizar dato por municipio o sección | por definir |
| aut14 Murcia | 2023-05-28 | CREM, `http://econet.carm.es/web/crem/inicio/-/crem/sicrem/PU2077/sec9_c1.html`; XML `.../xml/xml14.xml` | municipio, completos | nuevo (XML CREM) | por definir |

## Qué hace falta (por territorio)
1. **Fuente**: bajar el fichero oficial y fijar su sha256 en `territorios/<aut>/config/fuentes_oficiales.yaml` (recibo en `evidencia/fuentes_electorales/`); espejo en R2 si el origen rechaza runners (P10 tipo P12).
2. **Adaptador**: de la fuente a `distrito/partido/votos` por sección con el modelo de `adaptador_siel_andalucia_2026.py`; con granularidad municipal hay que repartir a sección con la regla vigente de M07 (sin inventar votos; marca `aproximado_en_distrito`).
3. **Huella**: sha256 de la fuente + del adaptador + del paquete electoral; cuadre de votos totales contra la cifra oficial de la Junta/Parlamento (suma exacta o pérdida declarada).
4. **Bloques**: al tener los partidos, añadirlos a `herramientas/bloques_autonomicas.py` (misma regla: mismo partido, mismo bloque; resto sin bloque) y regenerar.

## Orden y riesgo
aut08 y aut14 (municipal, completos) primero; aut03 después (PxWeb); aut11 el último: su fuente es provincial e incompleta, puede no dar dato por sección. Cambiar la fuente electoral invalida el par electoral (modo de 00: `p10-fuentes.yml` tipo P12 «regenerar» → `preparacion-legislatura-vigente.yml` → 00 «Reutilizar»).
