## 2026-11-14 — T-308 — Revertir los commits de robots de la tanda 1 fallida (deslinde11-r2)

Revert (`git revert --no-commit d7f6a78b^..05d3fc21`) de los 25 commits de github-actions y ddd-registro[bot]
que dejaron los runs fallidos 43624849879, 43624860974, 43624871718, 43624882353 y 43624893510 (aut01-aut05).
Sin commits humanos ni de PR en el rango. Quita los ids viejos (p. ej. `territory_id: aragon` en
`aut02_2025.yaml`, que dejaba la CI en rojo) y devuelve el catálogo de procedencia a su estado previo.
Sin ediciones manuales; sin lanzar ni publicar.
