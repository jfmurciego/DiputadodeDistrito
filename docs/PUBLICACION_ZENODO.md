# VERSIÓN: 1.0.0
# FECHA: 2026-11-09
# ANTERIOR: ninguna (fichero nuevo)
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

## Pendiente
- El DOI real, tras la primera publicación, para la insignia y el campo `identifiers`.
