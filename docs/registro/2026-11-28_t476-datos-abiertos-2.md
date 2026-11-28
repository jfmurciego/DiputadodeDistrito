## 2026-11-28 — T-476 — Datos abiertos 2: votos por partido y distrito, doble vuelta y composición (sin publicar)

**Causa:** las fichas de datos abiertos solo traen el ganador por distrito; faltaban los votos por partido, la doble vuelta y la composición.

**Cambio:** `herramientas/datos_abiertos_votos.py` 1.0.0 (`generar` y `--comprobar`) y su salida en `docs/ESTUDIOS/T476/votos/`
(fuera de `datos_abiertos/`: la P40 actual no la borra ni la publica). 2023-07 en los 52 nac; 2011-11 a 2019-11 solo en
los 11 nac con el mismo mapa que el vigente; los 41 × 5 restantes, en `no_construible.csv` (votos por sección fuera de git).
Doble vuelta con `doble_vuelta.py` y bloques 2026-11-25. Informe y diccionario: `docs/ESTUDIOS/T476/INFORME.md`.

**Pruebas:** `tests/test_t476_datos_abiertos_votos.py` (7), `GovernanceHeaders`, `test_t220_renombrado` y guardián en verde.
`--comprobar`: 0 errores; defecto máx. frente al BOE 7,4 % en 2023 (voto CERA); ganador 2023 = `datos/resultados/<nac>.csv` en los 52.

**Riesgos y pendientes:** no toca `generar_datos_abiertos.py`, la P40 ni CI. Para publicar hace falta la P40 1.3.2 (conservar y excluir
`votos/`), con permiso del propietario. Contraste con la Universidad de Valencia no alcanzable (proxy 403). Aviso: nac46 distrito 23,
votos del ganador de la tabla un 16 % distintos del run (desajustes T-103/T-104); el ganador coincide. Sin efecto en 00 ni huellas.
