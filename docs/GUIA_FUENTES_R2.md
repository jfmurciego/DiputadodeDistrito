# Comprobar en R2 las entradas de la batería (ARC-E)

La batería usa las mismas entradas que producción: M01 (secciones con población) y M03 (grafo) del paquete territorial de P10, archivados
una vez en R2 y verificados por sha256. La batería nunca va a ine.es; OGC e INE solo existen dentro de P10.

- Clave: `arc-e/entradas-minimas/<id16>.zip`, con `id16` = huella de la identidad del contrato (`package_sha256` y
  `compatibility_identity_sha256`), no el id del territorio: un renombrado no la invalida. El zip lleva `ENTRADAS.json` con el sha256 de cada fichero.
- Índice versionado: `orchestracion/fuentes_r2.json` (huellas medidas de las fuentes INE de P10 y, en `entradas`, clave/sha256/bytes/origen/fecha
  de cada paquete archivado; se completa con el `ARCHIVO_ENTRADAS.json` que deja el job).
- La poda (`podar_r2.py`) solo borra claves `ddd-state-*` de su lista aprobada: nada bajo `arc-e/`.

Comprobar un objeto: (1) panel de Cloudflare R2 → bucket → `arc-e/entradas-minimas/`: debe existir y su tamaño coincidir con `bytes`.
(2) Descárgalo y, en PowerShell, `Get-FileHash -Algorithm SHA256 .\<fichero>.zip`: en minúsculas, igual que el `sha256` del índice.

Archivar un territorio (una vez, lo lanza el Operador con frase del propietario): «VER Verificación del motor» con `territorios=<id>` y
`archivar_p10=<id de su 00>`. Si falta el paquete, la batería falla con `BATERIA_FALTA_PAQUETE_P10 <id>` y dice qué archivar.
