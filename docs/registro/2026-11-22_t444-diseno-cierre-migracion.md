## 2026-11-22 — T-444 — Diseño del cierre de la migración de workflows

- **Causa:** quedan 7 workflows fuera del esquema P (D-129, D-130) y ni #913, #938 ni #956 los borran.
- **Cambio:** `docs/ESTUDIOS/T444_CIERRE_MIGRACION/DISENO.md` 1.0.0, solo diseño. Para cada fichero: destino, qué lo llama, prueba de equivalencia, fecha y riesgo. Plan R1 (retirada de la 00, el Gestor, Legislatura y Elección), R2 (puerta como acción compuesta), R3 (nombres `p90-*` de la fusión automática y del revisor, con `veredicto`/`pruebas` intactos y fusión solo con frase del propietario) y R4 (paso 10). Ruleset `proteger-main` leído el 22-11: solo `veredicto`, ninguna aprobación obligatoria. Al final, 7 preguntas al propietario.
- **Pruebas:** solo documentación; `GovernanceHeaders` y guardián.
- **Riesgos:** ninguno; no toca código ni workflows. `no-automerge`.
