# VERSIÓN: 1.2.0
# FECHA: 2026-11-10
# CAMBIOS: T-210 (D-74): plan B para el corte 5.0.0 y aclaración de qué guarda el depósito. Antes: DOI de concepto y de versión confirmados por el propietario (T-159)
# ANTERIOR: legacy/docs/PUBLICACION_ZENODO_v1.1.0.md
# Guía para el propietario: publicar un mapa con DOI en Zenodo (sin pasos de comandos)

## Qué es
Zenodo es un archivo científico gratuito. Cada vez que el proyecto publica una «versión de mapa», Zenodo guarda una
copia permanente y le da un DOI: un enlace que no caduca y que tu compañero puede citar.

## Lo que haces tú (una sola vez)
1. Entra en zenodo.org con tu cuenta de GitHub → tu nombre → **GitHub** → activa el interruptor del repositorio
   `DiputadodeDistrito`.
2. En GitHub: repositorio → **Settings → Environments → New environment**, nómbralo `publicacion` y marca
   **Required reviewers** con tu usuario. Así ninguna versión sale sin que tú la apruebes.

## Lo que haces cada vez
1. Dices al Operador, en su chat, qué territorio publicar y con qué número de versión (p. ej. «Huesca, 1.0.0»).
2. GitHub te pide aprobación (revisor del entorno `publicacion`). Apruebas.
3. En unos minutos aparece la página del depósito en Zenodo con su DOI.

## Qué obtienes
- Una página en Zenodo con título, autor, licencia (Apache-2.0), descripción, enlace al visor y al repositorio.
- Un DOI **de esa versión** y otro DOI «de concepto» que apunta siempre a la última.
- Aviso visible de que los mapas son un ejercicio de investigación sin valor oficial.

## Cómo citarlo
Usa el DOI de la versión concreta; el botón «Cite this repository» de GitHub ya ofrece la cita (sale de `CITATION.cff`).
Cuando exista el primer DOI real se añadirá la insignia al README y a `CITATION.cff`.

## Qué verá tu compañero (limitación conocida)
La integración automática de Zenodo guarda el **código del repositorio en esa versión** (unos 850 MB, muy por debajo del
límite de 50 GB), pero **no los ficheros adjuntos a la Release** (el paquete del mapa y su manifiesto SHA-256). Lo
adjunto sigue en la Release de GitHub, con su firma verificable. Decisión del propietario (09-11): no se cambia el flujo.

## Datos de autor que constan
Nombre «Jesus Murciego», ORCID 0009-0002-4434-959X, afiliación «Independent researcher» (decisión del propietario, 09-11).
Versión del proyecto: 4.9.0.

## Primer depósito
Mapa Congreso Huesca 1.0.0 (versión «mapa-congreso_huesca-v1.0.0», 9-11-2026): https://zenodo.org/records/24093968

- **DOI de versión:** 10.5281/zenodo.24093968 (solo ese mapa).
- **DOI de concepto** (todas las versiones; resuelve a la última): 10.5281/zenodo.24093967.

Ambos DOI los copió el propietario de la página del depósito. El fichero del depósito es el ZIP de código fuente de GitHub, **no** el paquete firmado `.tar.gz` (su sha256 está en la Release). El depósito es un mapa (Huesca), no el proyecto entero: el README cita el DOI de concepto como archivo de las versiones de mapa publicadas, no como cita de todo el motor.

## Verificado
- El propietario comprobó el 10-11-2026 que ambos DOI (24093967 y 24093968) resuelven a la página de Huesca en Zenodo, con el fichero `jfmurciego/DiputadodeDistrito-mapa-congreso_huesca-v1.0.0.zip` (el ZIP de código, no el paquete firmado).

## Plan A (ahora) y plan B (corte 5.0.0) — D-74
- **Plan A, hasta el corte:** se mantiene la integración GitHub–Zenodo descrita arriba. Cada depósito de mapa guarda el ZIP de
  código del repositorio; el paquete firmado y su manifiesto SHA-256 están solo en la Release de GitHub. El DOI de concepto
  24093967 es la serie de versiones de mapa (hoy solo Huesca 1.0.0), no la cita del proyecto.
- **Plan B, desde el corte 5.0.0:**
  1. DOI de **software** por edición del motor (una versión del motor = un DOI, desde la 5.0.0).
  2. Depósito de **datos** por mapa, con el paquete firmado y su manifiesto, subido por la API de Zenodo con un token de
     Zenodo que crea el propietario y guarda como secreto del repositorio (nunca en el chat ni en ficheros).
  3. Hasta que el propietario cree ese secreto y apruebe el cambio de flujo, no se modifica la publicación.
