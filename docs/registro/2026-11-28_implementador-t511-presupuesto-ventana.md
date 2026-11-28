## 2026-11-28 — T-511 — Presupuesto de la ventana de 5 horas (D-217)

**Causa.** Ninguna skill, regla ni decisión nombraba la ventana de 5 horas, el modelo ni el esfuerzo por rol, y el bloque «Relevo» de tres skills mandaba crear la sucesora con el mismo modelo que la predecesora (el caro se heredaba). Dos flotas agotaron la ventana el 27 y el 28-11 (investigación T-509, hallazgo C-1).

**Cambio.**
- `configuracion/presupuesto_ventana.json` (nuevo): ventana de 90 USD de equivalencia, reparto 30 % reserva del propietario / 15 % coordinación / 55 % trabajo, modelo y esfuerzo por rol y coste estimado por sesión (ancladas al libro: mediana 2,95 USD; a calibrar con T-512). Las cifras se cambian aquí, sin tocar código.
- `herramientas/presupuesto_ventana.py` 1.0.0 (nuevo): `--plan <flota.json>` sale 0 si el plan cabe, 1 con líneas `::error` si no (rol desconocido, modelo o esfuerzo por encima de la tabla sin `autorizado_propietario`, coordinación o trabajo fuera de su parte, total que invade la reserva), 2 si el plan o la configuración no se leen.
- Skills `planificador`, `coordinador`, `operador` (Relevo, paso 3): citan la tabla en vez de «mismo modelo», con `model` y `effort` explícitos. `presupuesto`: línea de modelo y esfuerzo corregida y sección «Ventana de 5 horas».

**Pruebas.** `tests/test_t511_presupuesto_ventana.py` (14): fixtures `flota_26_fable_max.json` (26 sesiones Fable a máximo → ≠ 0) y `ola_dentro_del_reparto.json` (→ 0), límites exactos de trabajo y coordinación, autorización, cifras desde la configuración, entradas inválidas y `grep` de «mismo modelo» = 0 en las skills.

**Riesgos.** Sin efecto sobre el motor, huellas ni workflows: no exige ninguna 00. Los costes por sesión son estimaciones; un modelo más barato en coordinación puede errar más (C-8). Fuera de alcance: la regla del 70 % de D-160 y quién releva.
