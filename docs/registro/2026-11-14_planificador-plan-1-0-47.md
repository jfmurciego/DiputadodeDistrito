## 2026-11-14 — T-322 — Plan 1.0.47: galería fotográfica del visor V3 en la cola

- Causa: el propietario pide añadir la PR #792 (galería del visor V3, hecha con ChatGPT) a la cola, con revisión y prioridad del Planificador.
- Cambio: `docs/PLAN.md` 1.0.47 añade T-322 con los defectos encontrados (CI en rojo, XSS por `innerHTML`, llamadas a
  Wikimedia en cada visita frente al texto de transparencia, licencia sin comprobar, sin versión ni legacy, tests por regex) y el criterio de hecho;
  prioridad P3, después del 29-11. T-321 hecha (#789). Siguiente id T-323. Copia en `legacy/docs/PLAN_v1.0.46_20261114.md`.
- Efectos: solo documentación.
