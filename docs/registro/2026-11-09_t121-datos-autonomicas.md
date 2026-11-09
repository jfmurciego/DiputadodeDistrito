## 2026-11-09 — T-121 — Reagregación del histórico autonómico a los distritos vigentes (paso 3, 3 comunidades de prueba)

**Causa:** orden del propietario (09-11): reproducir para las comunidades el paso B de las generales (D-13: peso por población).

**Cambio:** `herramientas/reagregacion_autonomicas.py` 1.0.0 (nuevo; reutiliza T-83/T-85 sin modificarlos). Por comunidad y elección del calendario (#568): secciones del Observatorio → secciones vigentes (equivalencia T-85) → distrito (`datos/composicion/`) → mayor resto. Resultado en `datos/resultados/historico/autonomicas/<comunidad>/<aaaamm>/` (CSV por distrito y partido, MANIFEST con sha256 de cada fuente y cuadre) y `<comunidad>/rotacion.csv` (ganador de la fuente; se homologa cuando exista la tabla de siglas, PR siguiente). Probadas Galicia (4 elecciones, legislaturas de 43-47 meses), Madrid (5, con 2021 anticipada) y Castilla y León (5, con 2022 anticipada): 14/14 cuadran. Σ distritos + perdido = Σ fuente exacta; fuente frente al total autonómico del Observatorio (sin CERA) 0,00 %; pérdida por geometría ≤ 0,32 % (tope D-17 0,5 %).
**Dos respaldos declarados:** (1) la composición M06 de Madrid se hizo con otro seccionado (46 secciones vigentes ausentes, 79 569 hab.): se asignan al distrito más próximo por geometría y el MANIFEST lo cuenta; (2) las secciones de 2026 posteriores al seccionado 2024 se toman del vigente 2025. Quedan sin geometría Castilla y León 2011 (678 votos, 0,05 %) y 2026 (3 874, 0,32 %).
**Límite:** la fuente no publica huellas previas; el sha256 es el de la primera descarga (en el MANIFEST). Comunidades sin dato por sección (solo municipio) no están en esta entrega.

**Pruebas:** `tests/test_reagregacion_autonomicas.py` (sintéticos a mano y literales de la fuente: Galicia 2024 = 1 466 201 votos a candidaturas).

**Efectos:** ninguno en huellas, checkpoints ni workflows. Nada lanzado ni publicado.
