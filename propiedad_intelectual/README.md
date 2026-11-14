# Paquete de propiedad intelectual de Deslinde

Instantánea del motor Deslinde (versión 1.0.1) tomada del commit `439af6a523b6fc52b7c28e87ad690510aff450fa` (2026-11-12T13:55:06Z UTC), generada por
`herramientas/preparar_paquete_pi.py` 1.0.0. Contiene 1143 ficheros (50485158 bytes): `ddd_motor2/`, los módulos que
ejecuta, el `ddd_core` que importan, `docs/ARQUITECTURA/DESLINDE_1_0.md` y `docs/ESTUDIOS/`.

Esta carpeta es privada: no entra en el repositorio público (`configuracion/exclusion_publicacion.txt`).
El envío al registro lo hace el propietario con su asesor.

## Verificar

1. `sha256sum -c SHA256SUMS` comprueba el ZIP y el manifiesto (si el ZIP está presente).
2. Cada fichero del ZIP tiene su tamaño y sha256 en `MANIFEST.json` (`ficheros`).
3. Reproducir: `python herramientas/preparar_paquete_pi.py --commit 439af6a523b6fc52b7c28e87ad690510aff450fa` da los mismos bytes
   (ZIP sin compresión, orden por ruta, fecha fija 1980-01-01, permisos 0644).
