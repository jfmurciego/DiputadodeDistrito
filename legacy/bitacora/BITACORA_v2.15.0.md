# Bitácora de progreso

**Versión:** 2.15.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.14.0.md`

## R001–R013
Se recuperó y profesionalizó el procedimiento; se formalizaron M01–M08, fuentes congeladas, caché territorial, validación, outputs completos, manifiestos, versionado y continuidad documental. Run #5 reveló defectos de validación territorial; Run #6 aisló una desconexión originada en M04; M04 v7.3.0 corrigió la construcción conexa. Run #7 consiguió por primera vez todos los PASS estructurales R012, pero dejó un distrito fuera de ±12 %.

## R014 — Escape de mínimo local en M05
La auditoría de Run #7 demostró que M05 v7.2.0 no carecía de candidatos: estaba atrapado en un mínimo local porque cualquier primer movimiento útil empeoraba temporalmente el contador de distritos fuera de ±12 %.

Se preservó M05 v7.2.0 y se publicó M05 v7.3.0, con greedy determinista y recocido reproducible dentro del espacio de restricciones duras. Configuración Aragón v7.5.0 parametriza la búsqueda.

## Run #8 — 34592470470 — R014 VALIDADO
SUCCESS sobre commit `d57dc9cd77af4fa09780794401381d9727d1c71b`.

M05 v7.3.0:
- objetivo inicial: 1 distrito fuera de ±12 %, max_rel_dev 0,549676;
- objetivo final: **0 distritos fuera de ±12 %**, max_rel_dev **0,119431695687**;
- `hard=0`;
- greedy aceptados=0;
- movimientos de recocido aceptados=1.030;
- unidades finalmente cambiadas=75;
- iteraciones ejecutadas=9.038.

Validación final: 67 distritos; 1.463 secciones; 1.364.621 habitantes; Huesca 11 / Teruel 7 / Zaragoza 49; 0 bajo suelo; 0 sobre techo; 0 desconectados; 0 cruces provinciales; 0 violaciones municipales.

Run #8 reutilizó M01–M03 desde caché y publicó M01–M08. También verificó workflow v2.7.1: no reaparece el error de heredoc de `PRODUCTOS.json`.

Expediente: `docs/EJECUCIONES/GITHUB_RUN_0008_2026-09-11.md`.

## Reconciliación de gobernanza posterior a auditoría
Se actualizan README, Estado Maestro, Continuidad, Bitácora, Registro y contrato M05 con el estado real. `POLITICA_DE_VERSIONES.md` pasa a v1.1.0 y deja de exigir el retirado `MEMORIA_DEL_PROYECTO.md`. Se define `main` como rama canónica y las `infra/fuentes-reproducibles*` como históricas/no activas. Se prohíben referencias falsas a rutas `legacy` inexistentes y se cataloga la deuda histórica recuperada incompletamente.

La ausencia de suite unitaria completa queda explícita como deuda de ingeniería; no invalida la evidencia de integración de Run #8, pero es el siguiente frente de robustez.

## Reglas permanentes
Un informe nunca sustituye al producto. Una ejecución local/IA no sustituye a GitHub reproducible. Corregir el primer módulo que rompe contrato. Toda versión nueva preserva legacy y documenta el cambio. No relajar R012 ni ±12 % para obtener un PASS.
