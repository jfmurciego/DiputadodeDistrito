## 2026-11-14 — T-281 — Paquete de propiedad intelectual de Deslinde (instantánea reproducible)

- **Causa:** D-91 (revisada), D-92 y D-95: el código de Deslinde, su definición formal y los estudios son privados y
  se registran como propiedad intelectual; hace falta una instantánea verificable por hashes, no una copia del repo.
- **Cambio:** `herramientas/preparar_paquete_pi.py` 1.0.0 (stdlib, determinista): desde un commit (por defecto HEAD,
  leyendo solo objetos git) toma la lista blanca `ddd_motor2/`, los módulos que ejecuta (05 y 06), el cierre AST de
  imports `ddd_core` (10 ficheros), `docs/ARQUITECTURA/DESLINDE_1_0.md` y `docs/ESTUDIOS/`; excluye CLAUDE.md, `.claude/`
  y ficheros de secretos; falla si encuentra tokens, claves, rutas `/home/` o `/Users/` o correos (estos, solo en
  texto). Escribe en `propiedad_intelectual/` MANIFEST.json, ZIP sin compresión con orden y fecha fijos, SHA256SUMS y
  README. `configuracion/exclusion_publicacion.txt` 1.0.0: lista de exclusión del repo público para T-273.
  Ejemplo versionado sobre `439af6a`: 1128 ficheros, 50,4 MB; ZIP sha256 `adb87221…43bc` (no se versiona: > 5 MB).
  En `main` hay 15 ficheros de `docs/ESTUDIOS/` con rutas `/home/…` o `/Users/…`: el script para; el ejemplo los deja
  fuera con `--excluir` (constan en `excluidos_explicitos`) a la espera de que el propietario decida sanearlos o excluirlos.
- **Pruebas:** `tests.test_preparar_paquete_pi` (5: lista blanca y exclusiones, determinismo de ZIP y sha256, lectura del
  commit y no del árbol, fallo ante secreto y ruta personal, exclusión explícita); dos ejecuciones reales idénticas
  (`cmp`) y `sha256sum -c`; GovernanceHeaders y guardián.
- **PR/run:** sin run. El envío al registro lo hace el propietario con su asesor.
