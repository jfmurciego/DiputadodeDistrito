## 2026-11-10 — T-149 — Los dos reutilizables restantes pierden el «_» del nombre

Causa: «_Interno — Incorporación Electoral» y «_Interno — Puerta de Validación de Fase» seguían con «_» en la lista de Actions.
Cambio: solo `name:` → «Interno · Incorporación electoral» e «Interno · Puerta de validación de fase» (VERSIÓN +1, copia en
`legacy/workflows/`). No se inlinan: la incorporación (439 líneas, un llamador) y la puerta (158 líneas, dos llamadores) las leen
unos 16 ficheros de test y la 00 las usa en cadena; inlinarlas amplía el riesgo sin ahorro de CI. Quedan como excepción temporal
`workflow_call`, igual que la generación territorial y el publicador del sitio.
Pruebas: nombres fijados en tests de diseño y gobernanza en verde. Riesgos: ninguno de ejecución.
