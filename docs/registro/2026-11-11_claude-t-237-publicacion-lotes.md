## 2026-11-11 — T-237 — P50 publica un lote de runs 00 con una sola aprobación

- Causa: `production_run_id` admitía un solo run 00; publicar N territorios exigía N despliegues y N aprobaciones de `produccion`.
- Cambio: `production_run_id` acepta una lista (espacios o comas). `registro_publicaciones_visor.py` 1.7.0 añade
  `parse-run-ids` (ids numéricos; un repetido se RECHAZA, no se deduplica; `scenario_id` solo con un id) y
  `merge-descriptors` (rechaza dos runs del mismo territorio y el mapa 350). El publicador (3.13.0) descarga, acredita
  y describe TODOS los runs antes de crear ningún blob: si uno falla no se registra ninguno y el error dice cuál.
  Después, un candidato, un despliegue y un commit. P50 3.6.0: solo cabecera y texto del campo; la puerta
  `produccion` no cambia. Con un id, mismas rutas y pasos que antes.
- Pruebas: `tests/test_t237_publicacion_lotes.py` (23, con `gh` y `python` falsos en Acreditar y Validar: lista válida, separadores, id único idéntico, vacía, inválido,
  duplicado, territorio repetido, 350, pasos reales del workflow con `gh` falso, orden validar→blob, puerta intacta).
- Límites: en lote la evidencia es `publicacion_visor_<run>.json` por run (el informe de la 00 sigue leyendo la de un id).
- Límite: la comprobación de identidad ya registrada (`candidate`) sigue tras crear los blobs, como antes; si falla quedan
  blobs huérfanos, pero no se escribe el registro ni hay commit.
