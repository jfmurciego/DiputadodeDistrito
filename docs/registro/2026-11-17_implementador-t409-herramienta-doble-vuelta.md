## 2026-11-17 — T-409 — Herramienta de doble vuelta con coaliciones (D-167)

Causa: D-167 pide el escenario de doble vuelta con coaliciones como paso aparte, sin tocar el ganador actual. Cambio: nuevo
`herramientas/doble_vuelta.py` (núcleo puro `resolver` + CLI con manifiesto sha256) y `tests/test_t409_doble_vuelta.py`
(casos sintéticos con valores a mano: mayoría en primera, transferencia por bloque, abstención, empate, dos finalistas del
mismo bloque, dv_A/dv_B, CLI determinista). Lee `district_id, party, votes` (salida de P31) y la tabla de bloques de #901
(el test de la tabla real se salta hasta que #901 esté en `main`). Sin tocar `modulos/`, workflows ni visor; no entra en el
flujo (enganche tras #899). Riesgos: el id de partido de P31 debe coincidir con las siglas homologadas de la tabla (los
no encontrados quedan sin bloque); a confirmar con el CSV real al enganchar. PR con `no-automerge`.
