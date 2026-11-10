# Histórico autonómico desde 2011: cobertura (10-11)

Tabla completa: `COBERTURA.csv` (generada con `herramientas/medir_historico_autonomico.py`; 75 elecciones en alcance, 17 comunidades; Ceuta y Melilla no tienen autonómicas).

**Resultado (T-207c, 10-11): 11 de 17 comunidades completas y cuadradas** (Andalucía, Baleares, Canarias, Castilla y León, Cataluña, Navarra, Comunidad Valenciana, Galicia, La Rioja, Madrid, País Vasco). **54 de 75 elecciones cuadran** (≤0,5 % de voto, D-17; pérdida máxima 0,37 %, Andalucía 2026). Ninguna en el repositorio deja de cuadrar. Quedan 21 huecos. Siglas: la sigla de la fuente tal cual, «sin homologar» (`siglas_sin_homologar.json`).

| Hueco | Elecciones | Causa | Acceso |
|---|---|---|---|
| Aragón 2011, 2015 | 2 | fuente solo por municipio | descarga manual |
| Asturias | 5 | fuente solo por municipio (SADEI) | descarga manual |
| Cantabria 2011, 2015, 2019 | 3 | 2011 sin datos publicados; 2015 y 2019 solo municipio, incompletos | descarga manual |
| Castilla-La Mancha 2011, 2015, 2023 | 3 | solo municipio (2011 y 2015 incompletos) | descarga manual |
| Murcia 2011, 2015, 2023 | 3 | solo municipio (CREM) | descarga manual |
| Extremadura | 5 | solo provincia, incompleto | descarga manual |

Hecho hoy: reagregadas Cantabria 2023, Castilla-La Mancha 2019 y Murcia 2019 (las únicas con dato por sección y composición): 3/3 cuadran, pérdida 0 %.
Los datos municipales (Asturias, Murcia, Castilla-La Mancha, Aragón antiguo) solo permitirían un reparto aproximado por población dentro del municipio; no se hace sin decisión del propietario (peso D-13 ya aplicado a las demás).

**T-207/T-207b/T-207c (10-11):** composición canónica de Andalucía (6029 secciones), Aragón (1463) y Baleares (670; seccionado INE 2023, sha256 7a15e700…) por punto interior, exacta contra el M06 publicado. Reagregadas las 12 elecciones (Andalucía 5, Aragón 2019, 2023 y 2026, Baleares 4): 12/12 cuadran. Baleares va con `aproximado_en_distrito` (secciones de 2025 ausentes de la composición 2023, asignadas por geometría). Aragón 2011 y 2015 siguen en hueco (solo municipio).
