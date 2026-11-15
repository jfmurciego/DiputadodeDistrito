## 2026-11-15 — T-339 — Smoke de carga de todos los entrypoints y refuerzo del test de T-338

Causa: T-338 (#808) no se vio en CI porque los tests corren en un proceso con módulos ya cargados; un fallo de carga por ruta solo aparecía en el workflow.

Cambio: solo un test, `tests/test_t339_smoke_entrypoints.py`. (1) Deriva del repo los `python X.py` / `python -m X` de `procedimiento.sh` y `.github/workflows/*.yml` (≈94; exclusiones explícitas: `pip`, `py_compile`, `unittest`) y ejecuta cada uno con `--help` por ruta en subproceso limpio, con el PYTHONPATH que fija su workflow; falla por errores de carga (import, atributo, nombre, sintaxis, sys.modules). (2) Refuerza el test 3 de T-338: `validar_fuentes_reanudacion.py` con params reales de aut11 y paquete vacío debe llegar al cargador y fallar por «Fuentes BLOQUEADAS».

Pruebas: ~10 s. Con el cargador anterior a #808 falla el punto (2) con el `AttributeError` real; el punto (1) por sí solo no lo detecta (el cargador se invoca de forma perezosa, no al arrancar), pero cubre fallos de carga en el arranque de todos los entrypoints. No toca workflows ni motor.
