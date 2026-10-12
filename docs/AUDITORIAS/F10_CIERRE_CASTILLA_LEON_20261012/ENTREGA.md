# Cierre F10 — Castilla y León (2026-10-12)

Estado anterior: BLOCKED, pareja población/seccionado 2025/2026. Estado tras aplicar el conciliador compartido v1.2.0: **BLOCKED**.

La corrección compartida asigna la suma sólo cuando la geometría de varios CUSEC origen es exactamente igual a una única geometría destino y todos los códigos comparten provincia y municipio. La regresión real encuentra 2 fusión/fusiones admisibles, por un total de 2,693 habitantes. El saldo no asignado de los componentes auditados disminuye de 84,197 a 81,504; no hay reparto por área ni entre varios destinos.

La reproducción, ids origen/destino, poblaciones, componente restante, identidades de los tres archivos fuente, hash de fixture y hash del informe previo están en [resultado_reconciliacion.json](resultado_reconciliacion.json). La evidencia de origen permanece en `F10-20261011-adquisiciones/castilla_y_leon/evidence` bajo el almacén protegido.

Se revisó la alternativa oficial INE de resultados por secciones censales del Censo anual 2021–2025 ([INE](https://www.ine.es/dynt3/inebase/index.htm?capsel=10614&padre=10607)). INE suprime secciones con menos de 50 habitantes; la fuente tampoco acredita que las observaciones correspondan a la identidad de las secciones destino 2026. Por ello no se usa para cubrir el saldo pendiente.

Quedan bloqueados 23 componentes, clasificados en el replay reducido por causa geométrica; la asignación completa aún no conserva el total y el consumidor no pasa. La salida reducida se limita a las unidades pendientes del fixture real, por lo que la puerta territorial completa debe reejecutarse con las adquisiciones protegidas y la versión v1.2.0 antes de cualquier acreditación. No se promovió ni modificó producto territorial certificado.

Rama `codex/f10-cierre-castilla-leon`, dependiente de `codex/f10-fusion-exacta` (PR #246).
