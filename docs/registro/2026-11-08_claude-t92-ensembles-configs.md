## 2026-11-08 — T-92 — Configs de ensemble para 10 provincias más y generador

`herramientas/generar_config_ensemble.py` 1.0.0 (nuevo): copia el molde de La Rioja y rellena id, provincia, K y rutas desde el contrato; los umbrales se leen del contrato y se rechaza el territorio si difieren del molde. Reproduce exactamente las configs de Jaén, Córdoba y Sevilla (test). Nuevas `configuracion/ensemble/`: madrid (K59), alava (K3), albacete (3), almeria (6), castellon (5), cuenca (2), huesca (2), lugo (3), orense (3), tarragona (7).

Lanzables (`stage=ensemble_10`) = 14 previas + 10 = 24. Fuera: Cádiz (techo 1,16 aprobado para el ensemble, pero su contrato exime del suelo a San Fernando, 11031, y el ensemble no modela exenciones); K=1 sin ensemble (Ávila, Ceuta, Melilla, Segovia, Soria, Teruel, Zamora); con `topology_bridges` (Alicante 1, Badajoz 2, Baleares 1, Burgos 3, Cantabria 1, Ciudad Real 1, Gerona 1, Guipúzcoa 1, Huelva 1, Las Palmas 1, Lérida 1, Málaga 1, Murcia 2, Navarra 2, Palencia 2, Pontevedra 2, Santa Cruz de Tenerife 2, Valencia 1, Valladolid 1, Vizcaya 1); con exención de suelo municipal (Barcelona). Autonómicas no tratadas (comarca/otro esquema).

Pruebas: `tests/test_generar_config_ensemble.py`, `test_ensemble_configs_territorios`, `test_ensemble_toolkit` en verde. No toca motor, contratos ni workflows; sin efecto en huellas.
