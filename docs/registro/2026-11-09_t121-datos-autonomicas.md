## 2026-11-09 — T-121 — Reagregación del histórico autonómico a los distritos vigentes (paso 3, 3 comunidades de prueba)

**Causa:** orden del propietario (09-11): reproducir para las comunidades el paso B de las generales (D-13: peso por población).

**Cambio:** `herramientas/reagregacion_autonomicas.py` 1.0.0 (nuevo; reutiliza T-83/T-85 sin modificarlos). Por comunidad y elección del calendario (#568): secciones del Observatorio → secciones vigentes (equivalencia T-85) → distrito (`datos/composicion/`) → mayor resto. Resultado en `datos/resultados/historico/autonomicas/<comunidad>/<aaaamm>/` (CSV por distrito y partido, MANIFEST con sha256 de cada fuente y cuadre) y `<comunidad>/rotacion.csv` (ganador de la fuente; se homologa cuando exista la tabla de siglas, PR siguiente). Probadas Galicia (4 elecciones, legislaturas de 43-47 meses), Madrid (5, con 2021 anticipada) y Castilla y León (5, con 2022 anticipada): 14/14 cuadran. Σ distritos + perdido = Σ fuente exacta; fuente frente al total autonómico del Observatorio (sin CERA) 0,00 %; pérdida por geometría ≤ 0,32 % (tope D-17 0,5 %).
**Dos respaldos declarados:** (1) la composición M06 de Madrid se hizo con otro seccionado (46 secciones vigentes ausentes, 79 569 hab.): se asignan al distrito más próximo por geometría y el MANIFEST lo cuenta; (2) las secciones de 2026 posteriores al seccionado 2024 se toman del vigente 2025. Quedan sin geometría Castilla y León 2011 (678 votos, 0,05 %) y 2026 (3 874, 0,32 %).
**Límite:** la fuente no publica huellas previas; el sha256 es el de la primera descarga (en el MANIFEST). Comunidades sin dato por sección (solo municipio) no están en esta entrega.

**Pruebas:** `tests/test_reagregacion_autonomicas.py` (sintéticos a mano y literales de la fuente: Galicia 2024 = 1 466 201 votos a candidaturas).

**Efectos:** ninguno en huellas, checkpoints ni workflows. Nada lanzado ni publicado.

**Madrid, aproximado en distrito (decisión del Planificador 09-11: sin regenerar la composición):** el MANIFEST de cada elección declara `asignacion_por_geometria` (46 secciones, 79 569 hab., método) y el de la comunidad marca `aproximado_en_distrito: true` y `nivel: seccion` para que el visor lo muestre.

**Desviación de la composición M06 frente al seccionado INE 2025 (secciones vigentes ausentes / habitantes / % de la comunidad):** Canarias 12 / 18 712 / 0,83 · Cantabria 0 · Castilla-La Mancha 11 / 16 863 / 0,79 · Castilla y León 0 · Cataluña 30 / 50 334 / 0,62 · Navarra 6 / 8 091 / 1,18 · Comunidad Valenciana 35 / 54 487 / 1,00 · Extremadura 0 · Galicia 0 · La Rioja 1 / 1 542 / 0,47 · Madrid 46 / 79 569 / 1,12 · País Vasco 1 / 1 694 / 0,08 · Asturias 2 / 2 423 / 0,24 · Murcia 3 / 3 963 / 0,25. Sin composición en el repositorio: Andalucía, Aragón e Illes Balears (hueco: no hay distritos vigentes que reagregar).
