## 2026-11-14 — T-281 — Paquete de propiedad intelectual de Deslinde (instantánea reproducible)

- **Causa:** D-91 (revisada), D-92 y D-95: el código de Deslinde, su definición formal y los estudios son privados y
  se registran como propiedad intelectual; hace falta una instantánea verificable por hashes, no una copia del repo.
- **Cambio:** `herramientas/preparar_paquete_pi.py` 1.0.0 (stdlib, determinista): desde un commit (por defecto HEAD,
  leyendo solo objetos git) toma la lista blanca `ddd_motor2/`, los módulos que ejecuta (05 y 06), el cierre AST de
  imports `ddd_core` (10 ficheros), `docs/ARQUITECTURA/DESLINDE_1_0.md` y `docs/ESTUDIOS/`; excluye CLAUDE.md, `.claude/`
  y ficheros de secretos; falla si encuentra tokens, claves privadas o correos (estos, solo en texto). Las rutas
  `/home/` o `/Users/` no paran: quedan como `avisos` en el manifiesto (decisión del Planificador: el paquete es
  privado y excluir estudios debilita el registro; sanear solo importa al público, y los estudios no van, D-92). Escribe en `propiedad_intelectual/` MANIFEST.json, ZIP sin compresión con orden y fecha fijos, SHA256SUMS y
  README. `configuracion/exclusion_publicacion.txt` 1.0.0: lista de exclusión del repo público para T-273.
  Ejemplo versionado sobre `439af6a`: 1143 ficheros, 50,5 MB, 15 avisos de ruta en `docs/ESTUDIOS/`, nada excluido;
  ZIP sha256 `5ae301e7…85ad` (no se versiona: > 5 MB).
- **Pruebas:** `tests.test_preparar_paquete_pi` (6: lista blanca y exclusiones, determinismo de ZIP y sha256, lectura del
  commit y no del árbol, fallo ante token y clave privada, ruta personal incluida con aviso, exclusión explícita); dos ejecuciones reales idénticas
  (`cmp`) y `sha256sum -c`; GovernanceHeaders y guardián.
- **PR/run:** sin run. El envío al registro lo hace el propietario con su asesor.
