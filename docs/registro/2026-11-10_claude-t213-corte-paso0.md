## 2026-11-10 — T-213 — Corte 5.0.0 paso 0: copias y manifiesto de congelación

Causa: D-75, hoy solo lo reversible del corte (CORTE_5_0_0.md, paso 0). Cambio: copias de `publicaciones_visor.json`,
`INDEX.json`, `catalogo_procedencia.json` y `archivo_r2.json` con sha256, inventario de R2 derivado del registro
(el cubo no es accesible desde la nube; orden para el Operador en el MANIFEST) en `docs/ARQUITECTURA/corte_5_0_0/`.
Etiqueta `pre-5.0.0` PENDIENTE (proxy cloud 403; orden en MANIFEST) sobre `4f5870e72e5051217f331517b1c58958e1304552` (último `main` con `pruebas-plataforma` en success). Sin código, workflows ni producción.
Pruebas: sha256 de las copias iguales a los de `main`. Riesgos: ninguno. 390 objetos (los 624 del documento eran previos a la poda de 234 claves de hoy). Orden del paso 7: listar el cubo y comprobar objeto a objeto contra archivo_r2.json antes de copiar.
