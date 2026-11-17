## 2026-11-17 — T-393 — Diseño del alta de los territorios-elección `<t>_hAAAA_MM` (solo documento)

- Causa: D-150 pide dar de alta el histórico por época en la resolución; con la opción A el `validate` del catálogo no pasa (4 hallazgos medidos sobre e2702b25) y el Planificador (D-149) cambia T-393 a diseño.
- Cambio: `docs/ESTUDIOS/T393_HISTORICO_IDS/DISENO_HISTORICO_IDS.md` 1.0.0: id propio frente a variante de `nacNN`, filas del catálogo y clave de edición, `contract_path` materializado al vuelo, qué es producto disponible, consumo por P00, ficheros y tests de la implementación y contraste con T-378 §2/§8. Sin cambios en código, workflows ni datos.
- Pruebas: ninguna (documento). Recuentos de provincias generables medidos sobre `configuracion/historico_epoca/contrato_*.json`.
- Riesgos: ninguno en ejecución; la implementación queda detrás de T-377 con turno exclusivo.
