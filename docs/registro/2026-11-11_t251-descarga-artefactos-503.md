## 2026-11-11 — T-251 — La puerta distingue cuota de egress (503) de artefacto caducado

- `herramientas/descargar_artefacto.py` 1.0.0 (nuevo): envuelve `gh run download` y clasifica el fallo. HTTP 503
  «Egress is over the account limit» = transitorio: reintenta con espera 30/60/120/240/480 s (≤ 15,5 min) y, si se agota,
  `ARTIFACT_EGRESS_QUOTA` (código 75): cuota de Actions (Settings → Billing), no artefacto perdido, no regenerar.
  404/410/«no valid artifacts»/«expired» = definitivo: `ARTIFACT_MISSING` (código 44) sin reintento y con la remediación
  por tipo (M06 → 00 «Generar desde fuente territorial acreditada»; electoral → 00 «Reutilizar» o 03 con reutilizar=false).
- `_reutilizable-puerta-validacion.yml` 1.3.0 (legacy 1.2.3): sus dos descargas usan el helper; el motivo va a `puerta.json`.
  Un 503 en la certificación ya no cae a la copia durable ni se informa como «Falta certificación».
- Pruebas: `tests/test_descargar_artefacto.py` (respuestas simuladas, sin red ni esperas). El resto de `gh run download`
  de otros workflows queda igual (fuera de alcance).
