# Comprobar en R2 las entradas de la batería (ARC-E)

La batería parte de la MISMA fuente que producción y recalcula: baja de R2 el paquete P10 de la fuente del territorio (el
`ddd-source-package` que lleva el contrato), lo restaura como hace la 00 y ejecuta M01, M02 y M03 con el código de `main`. No hay grafo M03
archivado: cambiar M02/M03 cambia lo que se calcula. La batería nunca va a ine.es; OGC e INE solo existen dentro de P10.

- Clave: `arc-e/paquetes-p10/<package_sha256>.zip`, con `package_sha256` = sha256 del bundle del paquete = el del contrato del territorio
  (`generation_state.package_sha256`). Sin id de territorio: un renombrado no la invalida. El zip contiene `manifest.json` y el bundle.
- Al archivar y al leer se comprueba que el sha256 del bundle es el `package_sha256` del contrato y que lo acepta la misma validación
  de la 00 (`seleccionar_paquete_fuentes`). Paquete alterado o de otro contrato: `BATERIA_PAQUETE_P10_CORRUPTO`; ausente:
  `BATERIA_FALTA_PAQUETE_P10 <t>` (dice qué archivar).
- Transición al árbol nuevo (T-443, D-188): el paquete se busca primero en `fuentes/por-territorio/<ámbito>/<territorio>/paquete.zip` y, si falta,
  en la clave vieja. Toda entrada de índice (`fuentes_r2.json`, `archivo_r2.json`, `almacen_m06_r2.json`, el fijado de la doble vuelta) puede llevar
  `clave_anterior` (en la doble vuelta, `informe_clave_anterior` y `clave_r2_anterior`) junto a la clave nueva: se prueba solo si falta el objeto
  nuevo; un sha256 distinto falla cerrado. Se quita al borrar lo viejo (D-178).
- Índice versionado: `orchestracion/fuentes_r2.json` (huellas medidas de las fuentes INE que consume P10 y la de Interior). El job de
  archivado deja `ARCHIVO_PAQUETES_P10.json` (clave, sha256 del zip, bytes, `package_sha256`, run de origen, fecha) como artefacto.
- La poda (`podar_r2.py`) solo borra claves `ddd-state-*` de su lista aprobada: nada bajo `arc-e/`.

Comprobar un objeto: (1) panel de Cloudflare R2 → bucket → `arc-e/paquetes-p10/`: debe existir `<package_sha256>.zip` del territorio
(su `package_sha256` está en `territorios/<id>/config/<id>_2025.yaml`). (2) Descárgalo y, en PowerShell,
`Get-FileHash -Algorithm SHA256 .\<fichero>.zip` y compáralo con el `sha256_zip` de `ARCHIVO_PAQUETES_P10.json`; dentro, el bundle
(`prepared_sources.zip`) debe dar el `package_sha256` del contrato.

Archivar un territorio (una vez, urgente: los `ddd-source-package` caducan a los 30 días; lo lanza el Operador con frase del propietario):
«VER Verificación del motor» con `territorios=<id>` y `archivar_p10=<id del run de P10 o de la 00 cuyo paquete es el del contrato>`.
