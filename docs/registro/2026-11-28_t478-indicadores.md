## 2026-11-28 — T-478 — Indicadores por elección y sistema, 2011-2023

Causa: la auditoría cita cifras (PP 33 %, «207 de 325», 10,7 % → 1,9 %) sin fuente reproducible en git (D-214, paquete H).
Cambio: `herramientas/indicadores_sistemas.py` 1.0.0 (Gallagher, Loosemore-Hanby, número efectivo, prima, votos sin representación, escaños BOE→partido homologado; doble vuelta con `doble_vuelta.resolver`) y, en `docs/ESTUDIOS/T478/`, tablas CSV, `fuentes.csv` con sha256, `INFORME.md` y borrador `QUE_CAMBIARIA.md`. 2023 con los mapas publicados y con el histórico; 2011-2019 solo con el histórico (etiquetado).
Comprobaciones: PP 33 % = % de votos; «207 de 325» no reproducible (hemiciclo.json vetado), no se inventa; 10,7 → 1,9 con padrón 2022 y 2025 da 10,5 → 2,0 y 11,0 → 1,7.
Pruebas: `tests/test_t478_indicadores.py` (casos a mano, escaños BOE literales); `test_t220_renombrado`, `GovernanceHeaders`, guardián.
Riesgos: sin efecto en el motor, el contrato ni la publicación; no invalida checkpoints ni huellas; no hace falta ninguna 00. Provincias del mapa publicado sobre el tope de desajuste: 06, 46, 02, 04 (señalado en el informe).
