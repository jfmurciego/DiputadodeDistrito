# Corte 5.0.0 · paso 0 · MANIFEST (T-213, 2026-11-10)

Congelación reversible, solo copias. Origen: `main` en verde `4f5870e72e5051217f331517b1c58958e1304552` (`pruebas-plataforma` completada en success;
los commits posteriores `606ec07` y `3c02ac5` solo añaden docs/registro y no tocan estos ficheros). Etiqueta `pre-5.0.0`: NO creada desde la nube (el proxy deniega escritura en git/tags y git/refs, HTTP 403); la crea el Operador (abajo).

| Fichero | Origen en `main` | sha256 |
|---|---|---|
| publicaciones_visor.json | orchestracion/publicaciones_visor.json | b1704e9ac8466f48f01b8385eede47d6afcb15e46ec0e25ddbdf4aea3f187436 |
| INDEX.json | datos_abiertos/INDEX.json | 8fd0d9357d6b34986b59b32370ab8e1d78dbd21579560fc9da50cafdbec386d6 |
| catalogo_procedencia.json | orchestracion/catalogo_procedencia.json | 5563603664c919a6a96511d748375e2be737dc72fe30ccee3e5cbfcf461fc5dc |
| archivo_r2.json | orchestracion/archivo_r2.json | 57be640663e5e677c5337cf018c18e4dee61eb3d751b05a69223e5660f379a6b |
| inventario_r2_registro.csv | derivado de archivo_r2.json (clave, tamaño, sha256, fecha) | a491f75eab7f3acae7881618043be5ffaa5b38687336e0132a82a262544e4c05 |

## Inventario de R2: del REGISTRO, no del cubo
El entorno cloud no tiene credenciales de R2 (`R2_BUCKET`, `R2_ACCOUNT_ID`, `AWS_*` ausentes), así que **no se ha listado el cubo**.
`inventario_r2_registro.csv` es lo que el archivista anotó: 390 objetos, 1.976.209.280 bytes (104 `ddd-audit`,
102 `ddd-audit-electoral`, 184 `ddd-minimo`/`ddd-state`). **Discrepancia**: CORTE_5_0_0.md cita 624 objetos; el registro
en `main` tiene 390. Hay que contrastar con el cubo real (orden abajo) antes de fiarse de cualquiera de las dos cifras.

Orden para el Operador (solo lectura, con las credenciales del entorno `produccion`/archivo):
```
aws s3api list-objects-v2 --bucket "$R2_BUCKET" --endpoint-url "https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com" \
  --query 'Contents[].[Key,Size,ETag]' --output text > inventario_r2_cubo.tsv
```
(el ETag de objetos multiparte no es sha256; para sha256 cruzar con `archivo_r2.json`). Comparar claves con el CSV.

## Vuelta atrás
`git checkout pre-5.0.0` y estos ficheros: los 3 originales deben coincidir byte a byte con las copias.

## Orden de etiqueta (Operador; reversible)
```
S=4f5870e72e5051217f331517b1c58958e1304552
T=$(gh api -X POST repos/jfmurciego/DiputadodeDistrito/git/tags -f tag=pre-5.0.0 -f message="Congelación previa al corte 5.0.0" -f object=$S -f type=commit --jq .sha)
gh api -X POST repos/jfmurciego/DiputadodeDistrito/git/refs -f ref=refs/tags/pre-5.0.0 -f sha=$T
```
