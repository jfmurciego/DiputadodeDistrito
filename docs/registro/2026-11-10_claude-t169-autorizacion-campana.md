## 2026-11-10 — T-169 — Autorización por campaña (D-52)

Causa: cada lanzamiento exigía una frase del propietario; las campañas de muchos territorios la repetían sin valor añadido.
Cambio: regla en `CLAUDE.md` (compactado a 100 líneas) y parches en las skills `operador`, `lanzar-00`, `lanzar-campana` y
`publicar-visor`; `docs/autorizaciones/` con README y plantilla. Parte de `docs/ESTUDIOS/T157_AUTORIZACION_CAMPANA/`.
No sustituye la aprobación de `produccion` ni fusiona PR `no-automerge`. Tope semanal 15.000 min, aviso al 70 %.
Pruebas: `git apply --check` previo; gobernanza R015 y guardián de main. Riesgo: amplía la autoridad del Operador,
por lo que la PR lleva `no-automerge` y la fusiona el Coordinador tras revisión independiente, con orden del propietario.
