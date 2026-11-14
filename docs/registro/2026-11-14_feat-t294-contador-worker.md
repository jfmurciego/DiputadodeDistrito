## 2026-11-14 — T-294 — Contador de visitas sin datos personales: Worker, pruebas y guía (fase 2, parte 1)

- **Causa:** el propietario elige la opción A de la propuesta (contador propio sin cookies) y la librería autoalojada.
- **Cambio:** `herramientas/contador_worker/` (Worker de Cloudflare con D1: solo día UTC, ruta de lista blanca y contador; sin logs; tope diario), `tests/test_contador_worker.py` y `docs/ESTUDIOS/T294_ANALITICA_SIN_COOKIES/DESPLIEGUE_CLOUDFLARE.md`. No toca los visores (pendiente de T-310), ni workflows, ni producción.
- **Pruebas:** `python -m unittest tests.test_contador_worker` y `node --test` del Worker; `pruebas-plataforma.yml` 1.10.3 ejecuta `node --test` en el guardián (la prueba se saltaba en el Docker sin Node). Tope total diario, captura de errores de D1 y solo el dominio propio como origen (revisión de #780).
- **PR:** pendiente (con `no-automerge`).
