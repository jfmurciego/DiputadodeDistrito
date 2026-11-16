## 2026-11-16 — T-378 — Diseño al detalle de P00 Campaña y de la nueva forma de trabajar (paso 9a, sin código)

- Causa: D-140 (paso 9 de D-129): P00 se presenta al detalle al propietario antes de implementarse (T-379).
- Cambio: `docs/ESTUDIOS/T378_P00_CAMPANA/DISENO_P00_CAMPANA.md` 1.0.0 (botón, una campaña = una ejecución, semáforo, reintentos/apartado/parada sistémica, versión fija, estado en R2 + issue + un commit de cierre en `main`, IA solo al cierre, absorción de Gestor/Legislatura/Elección/00, puerta como acción compuesta, validación y respaldo del 24-11, riesgos, 4 PR, coste medido de la r3/r4 y 10 decisiones) y `ANEXO_A_LIMITES_GITHUB.md` 1.0.0 (17 límites con cita y fuente oficial, consultados el 16-11).
- Pruebas: solo documento; `GovernanceHeaders`.
- Riesgos: ninguno en producción (no toca código ni workflows). No lanza ni publica.
