## 2026-11-07 — T-61 — Configuraciones de ensemble para 10 provincias

Nuevas `configuracion/ensemble/congreso_<p>.json` (esquema idéntico al de La Rioja/Sevilla; solo cambian id, provincia, K y rutas): guadalajara (K2), caceres (3), leon (4), jaen (5), cordoba (6), toledo (6), granada (8), zaragoza (8), asturias (8), la_coruna (9). Elegidas por contrato: sin `topology_bridges`, sin exenciones de suelo ni de partición, CRS 3035, `POP_2023`, una sola provincia. Descartadas de la lista propuesta por tener puentes gobernados: Burgos, Badajoz, Pontevedra (además exención municipal) y Navarra.

Pruebas: `tests/test_ensemble_configs_territorios.py` y `tests/test_ensemble_toolkit.py` (cubren las nuevas por glob) en verde. No se probó el runner en local: no hay M03/M05 ni volcados en el entorno cloud (los artefactos dan 403). No toca motor ni workflows.

### Lanzamientos propuestos (los lanza el Operador con permiso del propietario)
Workflow `06 Escenarios y Ensembles` (`generar-alternativas-territoriales.yml`), siempre `stage=ensemble_10`, `execution_confirmed=true`, `deploy_pages=false`. Orden:
1. `territory_id=congreso_guadalajara` (la más pequeña; prueba). Si falla, parar e informar.
2. congreso_caceres · 3. congreso_leon · 4. congreso_jaen · 5. congreso_cordoba · 6. congreso_toledo
7. congreso_granada · 8. congreso_zaragoza · 9. congreso_asturias · 10. congreso_la_coruna (de menor a mayor K; 7–10 tras validar 1–6).
Requieren M05 vigente de cada territorio (si el paquete caducó, la 06 rehace M01–M05).
