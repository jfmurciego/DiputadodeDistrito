# T-299 — Inventario de releases (solo lectura, 2026-11-14)

Nada se borra desde aquí: los borrados los hace el propietario con un script cuando vea esta lista. Fuente: `gh api repos/<r>/releases` y búsqueda de usos en el código, los workflows y `orchestracion/`.

| Release | Tamaño | Veredicto | Motivo |
|---|---|---|---|
| `almacen-m06-aragon-40656036271` | 428,6 MB | CONSERVAR hasta archivar en R2; después BORRAR | Draft con las copias durables del run 40656036271 (M05, M06, estado, audit, source-package). Ningún artefacto de ese run está en `archivo_r2.json` (0 entradas). Lo usa `herramientas/localizar_artefacto_durable.py` (prefijo `almacen-m06-`) y la puerta de validación (`_reutilizable-puerta-validacion.yml`) cuando el artefacto de Actions caducó; la evidencia `territorios/aut02/evidencia/` cita el run. |
| `almacen-m06-extremadura-40656175842` | 425,4 MB | CONSERVAR hasta archivar en R2; después BORRAR | Igual (aut11); además su receipt de fuentes territoriales cita el run. |
| `almacen-m06-principado_de_asturias-40241852045` | 137,7 MB | CONSERVAR | Igual (aut03); sin copia en R2. |
| `almacen-m06-castilla_la_mancha-40604483629` | 77,2 MB | CONSERVAR | Igual (aut08); sin copia en R2. |
| `almacen-m06-galicia-40604535110` | 36,2 MB | CONSERVAR | Igual (aut12); sin copia en R2. |
| `almacen-m06-cantabria-40604431189` | 6,7 MB | CONSERVAR | Igual (aut06); sin copia en R2. |
| `viewer-principado_de_asturias-35728626894-m06-769a361b76cc` | 0 (sin assets) | BORRAR | Draft vacío. Solo aparece en `documentacion_publica/evidencias/storage-metadata.json` (instantánea de evidencia) y en tests con ids sintéticos; el publicador lo recrea si hace falta (`decide_release_action` → create). |
| `viewer-extremadura-35859241320-m06-fcbd89e46ef4` | 0 (sin assets) | BORRAR | Igual. |
| `fuente-infoelectoral-02202307` | 4,6 MB | CONSERVAR | Respaldo de la 03 y de `generar_hemiciclo.py` (lee el asset por la API de releases) hasta que el Operador confirme la lectura desde R2 (T-299). |
| `mapa-congreso_huesca-v1.0.0` | 78,1 MB | CONSERVAR | Fuera del encargo; release publicado del piloto. |
| `ensemble-congreso-{sevilla,salamanca,la-rioja}-*` | 35,3 MB | CONSERVAR | Fuera del encargo; descriptores de ensembles referenciados por el registro del visor. |

Ahorro posible: ~1,1 GB (los seis `almacen-m06-*`) en dos pasos —primero archivarlos en R2 (ARC-P, con su sha256 en `archivo_r2.json`), después borrar—, y 0 B inmediatos con los dos `viewer-*` (limpieza de ruido). Aviso: son 6 `almacen-m06-*`, no 7.

Antes de borrar `almacen-m06-*`: comprobar que ninguna 00 «Reutilizar» de esos seis territorios necesita ya el artefacto caducado (la puerta lo toma de ahí).
