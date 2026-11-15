## 2026-11-15 — T-338 — Cargador de territorio_ids registra el módulo en sys.modules

Causa: `_territorio_ids_t220()` (T-220, #747) cargaba `ddd_core/territorio_ids.py` con `spec_from_file_location` + `exec_module` sin registrarlo en `sys.modules`; el `@dataclass(frozen=True)` falla con `AttributeError: 'NoneType' object has no attribute '__dict__'`. #806 (T-336) lo invocó desde la reanudación (P00 aut11 run 43694989383, job «Adyacencias territoriales») y lo destapó. Los tests no lo veían porque `ddd_core.territorio_ids` ya estaba en `sys.modules`.

Cambio: `herramientas/validar_fuentes_reanudacion.py` y `herramientas/promover_catalogo_operacional.py` (1.1.4, copia legacy 1.1.3) registran el módulo antes de `exec_module` y lo retiran si falla.

Pruebas: `tests/test_t338_cargador_territorio_ids.py` (subproceso limpio, sin precargar; falla sin el arreglo y pasa con él). Sin cambios en M04/M05 ni huellas.
