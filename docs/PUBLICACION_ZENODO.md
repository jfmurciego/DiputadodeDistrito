# VERSIÓN: 2.0.0
# FECHA: 2026-11-16
# CAMBIOS: T-388 (D-146): flujo por la API de Zenodo, solo mapas, CC BY 4.0; se retira la integración GitHub–Zenodo. Antes: plan A/B de D-74 (1.2.0)
# ANTERIOR: legacy/docs/PUBLICACION_ZENODO_v1.2.0.md
# Guía: publicar los mapas de Deslinde con DOI en Zenodo

## Qué es
Zenodo guarda una copia permanente de cada versión de los mapas y le da un DOI citable. Desde D-146 el depósito lo hace
el workflow **P50 Publicación académica** (job `zenodo`) por la API de Zenodo; ya no se usa la integración GitHub–Zenodo.

## Qué se sube y qué no
- **Sí:** los paquetes firmados `ddd-<territorio>-v<versión>.tar.gz`, `SHA256SUMS`, `LINAJE.json` (uno, con el linaje de todos),
  `LICENCIA_CC-BY-4.0.txt` y `NOTA_FUENTES.md` (INE e Interior; `docs/zenodo/`).
- **No:** motor, código del proyecto ni ZIP del repositorio (la herramienta rechaza cualquier otro nombre de fichero).
- Licencia de los mapas: **CC BY 4.0**. Metadatos: tipo dataset, creador «Murciego, Jesus» (ORCID 0009-0002-4434-959X,
  «Independent researcher»), enlaces a la Release de GitHub y al visor, y la nota «sin valor oficial».
- Metadatos definidos en `herramientas/zenodo_deposito.py` (la copia del antiguo `.zenodo.json` está en `legacy/`).

## El botón (P50 Publicación académica)
- `territorios`: códigos o `todos`. `destino`: **prueba** (sandbox.zenodo.org, por defecto) o **Zenodo** (el real).
- Orden: resolver versión → crear la Release `mapas-v<versión>` (firmada) → depositar. La Release se crea siempre, también con
  destino prueba: una prueba gasta esa versión (P50 se niega si los mapas no cambian), así que pruébalo antes con los mapas que
  vayan a salir de verdad o acepta subir la versión.
- Si falla el depósito, la Release ya existe: relanza solo el job `zenodo` («Re-run failed jobs»), no el botón entero.

## Series y DOI
Intenta una nueva versión del concepto `10.5281/zenodo.24093967` (la serie de Huesca). Si Zenodo no permite pasar de software a
dataset, borra ese borrador y crea un **concepto nuevo**; el informe del job lo declara (`concepto_nuevo`) y hay que actualizar
el DOI de concepto en `CITATION.cff` y el README. En el destino prueba siempre hay concepto nuevo (otro servidor).

## Garantías de la herramienta
No crea dos depósitos de la misma versión (borrador o publicado: falla cerrado con `ZENODO_YA_EXISTE`); no publica si los
ficheros del borrador no coinciden por md5 con los locales; las escrituras no se reintentan; un fallo tras crear el borrador
imprime su id y URL (sin publicar) y no deja nada a medias en silencio.

## Secretos (entorno `publicacion`)
`ZENODO_TOKEN` (zenodo.org) y `ZENODO_SANDBOX_TOKEN` (sandbox.zenodo.org) los crea el propietario en cada sitio (permisos
`deposit:write` y `deposit:actions`) y los guarda en el entorno `publicacion`. Nunca en el chat ni en ficheros. El paso de
depósito recibe solo el del destino elegido; no se imprime ni se sube como artefacto.

## Cómo se corrige un depósito
- Borrador o sandbox: bórralo en Zenodo y relanza el job `zenodo`.
- Publicado: un depósito publicado no se borra; los metadatos se editan en Zenodo y los ficheros solo cambian con una versión
  nueva (nuevo P50 con el mapa corregido).

## Una sola vez (propietario)
Desactivar la integración GitHub–Zenodo del repositorio; borrar el ZIP de código del registro 24093968 (conserva publicación y DOI);
crear los dos secretos en el entorno `publicacion`.

## Cómo citarlo
DOI de concepto (serie de mapas) o DOI de la versión concreta; `CITATION.cff` ya los lleva. Registro inicial: Mapa Congreso
Huesca 1.0.0, https://zenodo.org/records/24093968 (DOI de versión 10.5281/zenodo.24093968; DOI de concepto 10.5281/zenodo.24093967).
Versión del proyecto: 4.9.0. Los mapas no tienen valor oficial.
