## 2026-11-09 — T-127 — Preparación de Zenodo: metadatos y guía (sin publicar)

Autorización: orden del propietario (09-11) vía planificador: «prepara lo de Zenodo». No se lanza ni se publica nada; no se toca ningún workflow.
Causa: aún no hay DOI; los metadatos tenían marcas «rellenar» y diferencias con Zenodo.
Cambio: `.zenodo.json` (licencia `apache-2.0`, nombre «Jesús» como en `docs/ARTICULO_JOSS/paper.md`, palabra clave «secciones censales», relación `isDocumentedBy` con el visor); `CITATION.cff` (quitadas las marcas «rellenar», «Jesús»); nuevo `docs/PUBLICACION_ZENODO.md` para el propietario.
Prueba en seco (lectura de `publicar-version-mapa.yml` 1.1.0 y `cadena-publicacion.yml`, sin ejecutar): produce `ddd-<territorio>-v<versión>.tar.gz` (M06 + contexto + LINAJE.json + CITATION + SHA256SUMS), atestación SLSA y Release `mapa-<t>-v<v>`. Huesca: el M06 publicado pesa ~108 KB (blob 81c4e7b3), el paquete ≪ 1 MB. Hallazgo: Zenodo–GitHub archiva el zipball del repositorio en ese commit (~850 MB, ≪ 50 GB), no los adjuntos de la Release; el paquete firmado no iría al depósito. Arreglo posible (decisión del propietario, tocaría el workflow): subir el paquete por la API de Zenodo o describirlo como complemento.
Pendiente del propietario: afiliación (no consta), versión 4.7.0 (CITATION) frente a 4.9.0 (README) — corrección lista: `version` y `date-released` en `CITATION.cff` y cabecera de `README.md`, a aplicar cuando responda —, y el DOI real para insignia e `identifiers` (paso 5, tras la primera publicación).
Riesgos: ninguno; los metadatos no afectan al motor ni a huellas.
