## 2026-11-08 — T-113 — Histórico 2019-11 en el Gestor 2.0 (paso A por provincia)

Causa: D-10, D-12 y D-22: la opción «histórico» del «0 Gestor de Campañas» fallaba siempre al planificar; el paso A
de T-83 (reagregación → M07/M08) solo se había ejecutado a mano en Álava, Badajoz y Huesca.
Cambio: `herramientas/historico_campana.py` 1.0.0 (nuevo): plan por provincia (elección soportada, M06 publicado en
`datos_abiertos/INDEX.json`, composición y fichero del espejo T-89) y `ejecutar` en el runner: seccionado 2025 y padrón
desde `inputs/partes` (sha256), M06 del blob (sha256 de INDEX), espejo de la elección y seccionados INE históricos
(sha256 de T-83/T-85), paso B + paso A; puerta: cuadre exacto, M07 PASS y mismo ganador que B (código 0).
`herramientas/gestor_campanas_2.py` 1.1.0: «histórico: generales 2019-11» da la matriz (con «todos», las 52; una provincia
sin M06 publicado o sin composición se omite con «todos» y, pedida por nombre, falla con mensaje claro); el
resto del histórico, autonómico, mapa 350, ensemble y publicar «sí» (puerta 04 del histórico sin adaptar) fallan al
planificar. `herramientas/reagregacion_historico.py` 1.2.0: `--elecciones` (por defecto todas; las geometrías de
todos los años se siguen cargando, resultado idéntico). `gestor-campanas.yml` 1.6.0: job «histórico» (matriz tras el
clic de produccion del job del plan, artefacto `ddd-historico-<clave>-<territorio>` por provincia; no publica ni
escribe en el repositorio).
Pruebas: `tests/test_t113_gestor_historico.py` (6), `test_gestor_campanas_2`, B y A de T-83, cargador YAML estricto,
`GovernanceHeaders`. Local real: Huesca 201911 por `historico_campana.py ejecutar`, igual al histórico versionado.
Riesgos: sin motor, `modulos/`, `ddd_core/`, política ni contratos; no invalida huellas ni checkpoints. El resultado
queda en artefactos (caducan a 90 días): traerlo a `datos/resultados/historico/` y publicar es tarea aparte (04).
