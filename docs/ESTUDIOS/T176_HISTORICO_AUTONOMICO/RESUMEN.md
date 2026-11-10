# Histórico autonómico desde 2011: cobertura (10-11)

Tabla completa: `COBERTURA.csv` (generada con `herramientas/medir_historico_autonomico.py`; 75 elecciones en alcance, 17 comunidades; Ceuta y Melilla no tienen autonómicas).

**Resultado: 9 de 17 comunidades completas y cuadradas** (Canarias, Castilla y León, Cataluña, Navarra, Comunidad Valenciana, Galicia, La Rioja, Madrid, País Vasco). **42 de 75 elecciones cuadran** (≤0,5 % de voto, D-17; pérdida máxima 0,14 %). Ninguna en el repositorio deja de cuadrar. Quedan 33 huecos. Siglas: la sigla de la fuente tal cual, «sin homologar» (`siglas_sin_homologar.json`).

| Hueco | Elecciones | Causa | Acceso |
|---|---|---|---|
| Andalucía | 5 | dato por sección existe, falta composición de distritos vigentes | nube; requiere generar el territorio (ejecución 00) |
| Illes Balears | 4 | ídem | nube; ídem |
| Aragón 2019, 2023, 2026 | 3 | ídem | nube; ídem |
| Aragón 2011, 2015 | 2 | fuente solo por municipio | descarga manual |
| Asturias | 5 | fuente solo por municipio (SADEI) | descarga manual |
| Cantabria 2011, 2015, 2019 | 3 | 2011 sin datos publicados; 2015 y 2019 solo municipio, incompletos | descarga manual |
| Castilla-La Mancha 2011, 2015, 2023 | 3 | solo municipio (2011 y 2015 incompletos) | descarga manual |
| Murcia 2011, 2015, 2023 | 3 | solo municipio (CREM) | descarga manual |
| Extremadura | 5 | solo provincia, incompleto | descarga manual |

Hecho hoy: reagregadas Cantabria 2023, Castilla-La Mancha 2019 y Murcia 2019 (las únicas con dato por sección y composición): 3/3 cuadran, pérdida 0 %.
Los datos municipales (Asturias, Murcia, Castilla-La Mancha, Aragón antiguo) solo permitirían un reparto aproximado por población dentro del municipio; no se hace sin decisión del propietario (peso D-13 ya aplicado a las demás).

**T-207 (10-11):** composición canónica de Andalucía (6029 secciones) y Aragón (1463) por punto interior del seccionado INE 2025 en el M06 publicado, exacta en distritos, secciones y población. Medido: 8 elecciones pasan de HUECO a PENDIENTE_DE_REAGREGAR (Andalucía 5, Aragón 2019, 2023, 2026); aún falta el paso B (reagregación con seccionados históricos, solo en el runner). T-207b: Illes Balears (670 secciones) cuadra exacta con el seccionado INE 2023 (sha256 7a15e700…) y pasa también a PENDIENTE_DE_REAGREGAR (4 elecciones).
