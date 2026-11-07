## 2026-11-07 — T-47 (b) — Archivista R2: reintentos ante fallos transitorios

Causa: la primera ejecución del archivista (run 42393003447) falló con HTTP 500 en `GET actions/artifacts` y
`archivar_artefactos_r2.py` no reintentaba.
Cambio: `archivar_artefactos_r2.py` 1.0.1 (copia 1.0.0 en `legacy/herramientas/`): reintentos con espera
exponencial (2, 4, 8, 16, 32 s; 6 intentos) ante 5xx, 429 y errores de red en el listado, la descarga y R2
(head y subida), con un aviso por intento. Los 4xx no se reintentan.
Pruebas: `tests/test_archivar_artefactos_r2.py` (11, con 500 simulado y espera sustituida).
