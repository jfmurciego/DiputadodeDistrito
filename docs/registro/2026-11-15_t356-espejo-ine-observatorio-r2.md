## 2026-11-15 — T-356 — Script de espejo en R2 de los seccionados INE 2010-2026 y el Observatorio

**Causa.** Para el histórico desde 2011 (D-105) faltan en R2 (ARC-E) 14 de los 17 seccionados del INE y las 625 piezas del Observatorio (T-306 §3); el propietario las sube desde Windows.

**Cambio.** `herramientas/espejo_ine_observatorio_r2.ps1` 1.0.0 (patrón del de Galicia, T-354): baja las 17 URL del INE y las 625 piezas, valida (no HTML; ZIP con firma y legible; JSON), verifica el sha256 del índice o lo mide y registra, sube con metadato sha256 a `arc-e/fuentes/ine/` y `arc-e/fuentes/nazioenbehatokia/` (sha12 en el nombre), reanuda (sidecar `.ok` y `head-object`), reintenta ante 429/5xx/reset (Retry-After), pide confirmación antes de sobrescribir el JSON de resultado, sale con 1 si falla alguna, usa `C:\ddd` y no toca credenciales. Se baja por raw sin checkout (lee el índice de main). `orchestracion/fuentes_r2.json`: 14 entradas `seccionado_<año>.zip` nuevas (5 con sha256 de T-85; 9 con sha256 null = fail-closed) y 625 `nazioenbehatokia/<ruta>` con las huellas de `fuente_nazioenbehatokia.json`, todas «pendiente de subir».

**Revisión (misma 1.0.0, aún no en main).** Corregido: rutas absolutas en `Escribir-Sin-Bom` (`Ruta-Completa`: absolutas intactas, relativas contra `Get-Location`; 1.0.0 las concatenaba y cada pieza fallaba tras bajarla); la reanudación recalcula el sha256 del fichero; cancelar la sobrescritura sale con 2; .ps1 solo ASCII (PS 5.1 lo lee como ANSI sin BOM); mientras la PR no se fusione hay que pasar `-Indice` con la raw de la rama (error claro si el índice trae menos de 642 piezas).

**Pruebas.** `tests.test_t356_espejo_ine_observatorio` (positivas y negativas), t298, t299, t220_renombrado. El script no se ha ejecutado (la nube no ejecuta PowerShell ni llega al INE con credenciales).

**Riesgos.** Solapes en `fuentes_r2.json` con #827 y #797: rebasar la que se fusione después. Tras subir, el propietario pega el JSON de resultado y se actualiza el índice (sha256 y bytes de los 9 sin medir). No cambia huellas M05.
