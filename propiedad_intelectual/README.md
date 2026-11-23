# Paquete para el Registro de la Propiedad Intelectual de Deslinde

Carpeta de salida de `herramientas/preparar_paquete_pi.py` (2.0.0, T-281, D-196). Solo se versiona este README: el
ZIP, los PDF y los manifiestos se generan en local y **no se suben** (`.gitignore`), porque llevan el nombre del autor y
duplican el código.

## Generar (lo hace el autor, sobre `main`)

```bash
git fetch origin main && git checkout --detach origin/main
python herramientas/preparar_paquete_pi.py --commit HEAD --autor "Nombre y apellidos" --fecha AAAA-MM-DD
# si el registro limita las páginas de código: --extremos 25 (25 primeras y 25 últimas páginas)
```

Sale aquí:

- `paquete_deslinde.zip`: `paquetes/deslinde/`, `docs/ARQUITECTURA/DESLINDE_1_0.md` y los estudios que cita.
- `COPIA_IDENTIFICATIVA.pdf`: portada, descripción (`docs/registro_pi/DESCRIPCION.md`), índice con sha256 y código.
- `NOTA_AUTORIA.pdf`: lo que definió y decidió el autor (`docs/registro_pi/NOTA_AUTORIA.md`), para la pregunta sobre IA.
- `MANIFIESTO.txt`, `SHA256SUMS` y `MANIFEST.json`: huellas. Verificar con `sha256sum -c SHA256SUMS`.

Mismo commit, autor, fecha y `--extremos` dan los mismos bytes.
