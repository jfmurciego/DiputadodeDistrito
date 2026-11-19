## 2026-11-19 — T-409 — Ajustes de la doble vuelta en P30 tras la revisión de #911

Causa: dos puntos de la revisión de #911. (1) Si `doble_vuelta.py` fallaba tras escribir `cobertura.json`, `doble_vuelta/` seguía existiendo y el
paso de archivo lo subía a R2 incompleto. (2) `sin_t409_run` quitaba `"${extra[@]}"` en cualquier paso de registro.
Cambio: `p30-resultados-electorales.yml` 1.0.3 (copia 1.0.2 en `legacy/`): el paso de la doble vuelta borra `doble_vuelta/` al empezar y
con un `trap` en la salida si no llegó a `ok=1` (tras ambas herramientas): el directorio solo existe si ambas terminan bien y el paso de
archivo no pasa `--extra` sin él. Tests: `sin_t409_run` se aplica solo al paso «Archivo en origen» (en `tests/_t379_2b.py` y
`test_t376_p30_equivalencia.py`); nuevo test del orden `rm`→`trap`→`mkdir`→herramientas→`ok=1`. Comprobado a mano el trap (con fallo, sin directorio).
`--alias` en P30 queda para cuando #914 esté en main. Toca un workflow compartido. `no-automerge`.
