# T-220 · Renombrado de carpetas de territorios (APARCADA)

Estado: aparcada por el propietario (2026-11-11). Solo lectura sobre `origin/main@ef8fa62`; no se ha editado código.
Tabla: `equivalencias_t220.csv` (71 filas, desde `configuracion/notacion_territorial.csv`, sha256 13299081…e621ee).

## Decisiones ya tomadas (Planificador/propietario)
1. Una sola PR. 2. También `config/<viejo>_2025|2026.yaml` → `<nuevo>_…yaml`. 3. La detección por prefijo `congreso_`
pasa a `ambito` del resolutor, con test que falle si reaparece en código o workflows. 4. Tabla versionada con sha256.
5. `congreso350_*` y `congreso` fuera. 6. `datos_abiertos/<viejo>/` y URLs conviven un ciclo; borrado con frase del
propietario. 7. Bloques nuevos de shell en workflows con test bajo `bash -eo pipefail`. Va tras T-265 (semilla por
código oficial) y antes de regenerar las 71.

## Inventario (ficheros fuera de legacy/ con algún id viejo; cota alta: ids cortos sobrecuentan texto)
| Categoría | Recuento |
|---|---|
| `territorios/` | 71 carpetas a `git mv` (~1.800 ficheros), incluidos `config/<id>_AAAA.yaml` y `meta.territory_id` |
| `configuracion/` | 61 (catálogo `territory_id`/`parent_territory_id`, registro electoral, políticas, `ensemble/<id>.json`) |
| `herramientas/` · `ddd_core/` · `ddd_motor2/` | 36 · 3 (congreso_contract, territory_contract, territorio_ids) · 2 |
| `.github/workflows` | 5 (generar-alternativas: 18 rutas literales; pruebas-plataforma 3) |
| `orchestracion/` | publicaciones_visor 475 refs, archivo_r2 1.890, catalogo_procedencia 978, estado_operativo 644, +8 menores |
| `datos_abiertos/` | INDEX.json 156, index.html 52, 52 carpetas públicas |
| `datos/` · `resultados/` · `visor/` · `publicado/` | 218 · 28 · 2 (nacional) · 4 |
| `tests/` · `evals/` | 765 (rutas literales `territorios/<id>` en 30) · 23 |
| `docs/` | 575 (AUDITORIAS, ESTUDIOS, registro: histórico, no se toca) |
| Detección por prefijo `congreso_` | 26 ficheros (p. ej. `_reutilizable-generacion-territorial.yml:472` `case territorios/congreso_*`) |

Tamaño estimado: ~1.800 renombres + 150-200 ficheros editados (sin contar orquestación regenerable).

## Alias y rutas que no deben quedar vivas
- Alias único: `ddd_core.territorio_ids.resolver_id` (acepta viejo/nuevo; contador `LECTURAS_LEGACY`).
- Histórico: registro del visor de solo adición (viejas intactas; nuevas con `alias_de`); evidencias y receipts se
  mueven con la carpeta y se leen vía resolutor; claves R2 y artefactos no se renombran.
- No vivas: `territorios/<viejo>/`, `configuracion/ensemble/<viejo>.json`, opciones `choice` viejas, literales viejos
  en herramientas, ddd_core y workflows.

## Riesgos
- Huellas M05/N08 y checkpoints M04: cambian (`meta.territory_id`, rutas de config) → 00 «Generar desde fuente».
- Catálogo y `territory_contract` (una entrada por id); workflows `choice` + test opciones = catálogo.
- Gestor: claves `ES-<ámbito>-<unidad>-<fecha>` y seguimiento por id. Visor/dashboard: buscar por id con respaldo.
- Detección por prefijo: con `nacNN` falla en silencio. Madrid AUT13/NAC28 y Ceuta/Melilla AUT18-19/NAC51-52: alias por id exacto.

## Tests necesarios
- T-265: la semilla no cambia con id viejo o nuevo (`tests/test_motor2_semilla.py`, rama `claude/t265-semilla-codigo-oficial`).
- Ninguna ruta antigua viva: sin ids viejos fuera de legacy/, histórico de docs, registro del visor, evidencias y la tabla.
- Carpetas `territorios/` = códigos de la tabla ∪ `congreso350_*` ∪ `congreso`.
- Sin detección por prefijo `congreso_` en código ni workflows. Bloques de shell nuevos bajo `bash -eo pipefail`.
