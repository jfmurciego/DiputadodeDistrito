# Comprobar las fuentes nacionales en R2 (ARC-E)

El índice versionado es `orchestracion/fuentes_r2.json`: por fichero, clave en R2, sha256, bytes, URL oficial y fecha de descarga.
Las claves llevan la huella: `arc-e/fuentes/ine/<nombre>_<sha256[:12]>.zip`. Las entradas mínimas por territorio van en
`arc-e/entradas-minimas/<id16>.zip` (id16 = huella de la identidad del contrato, no el id del territorio). La poda no toca `arc-e/`.

1. En el panel de Cloudflare: R2 → bucket → carpeta `arc-e/fuentes/ine/`; el objeto debe existir y su tamaño coincidir con `bytes`.
2. Descarga el objeto y en PowerShell: `Get-FileHash -Algorithm SHA256 .\seccionado_2023_7a15e700a459.zip`
   El valor (en minúsculas) debe ser el `sha256` del índice.
3. Origen: `origen_url` es la fuente oficial del INE; `seccionado_2025` y `65034` también están en `inputs/partes` con la misma huella.

Subida (una vez, la lanza el Operador con frase del propietario): «VER Verificación del motor» con `subir_fuentes=true`. Los jobs de la
batería bajan de R2, verifican el sha256 y nunca van a ine.es; si no cuadra, fallan.
