## 2026-11-08 — T-73 — Portal Zensical público en /docs y vista Nacional en el sitio

**Causa.** El portal documental incluía contenido interno (plan, ejecuciones, auditoría) y no estaba integrado en el publicador único; la vista Nacional (T-84, #513) no se copiaba al sitio.

**Cambio.** `documentacion_publica/docs` queda con inicio, método, fuentes, datos abiertos y licencia, cómo citar (hueco para el DOI de Zenodo, sin inventarlo) y archivo R2; se retiran plan, ejecuciones, auditoría, empezar y publicación. `zensical.toml` 1.1.0 (copia en `legacy/documentacion_publica/`). `_reutilizable-publicar-sitio.yml` 3.6.0 (copia 3.5.0 en `legacy/workflows/`): construye con `zensical build --strict` en `/docs/` y copia `visor/nacional/` a `/nacional/`, con validaciones; el visor publicado no cambia.

**Pruebas.** `zensical build --strict` en verde; 19 enlaces de /docs comprobados con Playwright en local; gobernanza de workflows y cabeceras.

**Riesgos.** No publica nada; la publicación exige permiso del propietario. Sin efecto en checkpoints ni huellas.
