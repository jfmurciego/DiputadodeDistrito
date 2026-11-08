---
paths:
  - "modulos/04*"
  - "modulos/05*"
  - "ddd_core/m04*"
  - "docs/ESTUDIOS/N08_*"
  - "herramientas/verificar_evidencia_n08_readonly.py"
  - "tests/test_preflight_caceres_n08.py"
---

# Huellas M05 y evidencias N08

- La huella M05 (`huella_checkpoint_m05.engine_files`) es el cierre de imports `ddd_core` desde
  `modulos/05_optimizar_distritos.py` (más `BASE_ENGINE` por ruta; T-108): tocar cualquiera, `ddd_core/config.py`
  incluido, invalida los M05/M06 previos (para la 04, #346 con `--consume-certified-product`). Un import nuevo del
  motor por otra vía (subprocess, ruta no literal) lo detecta `tests/test_huella_m05_motor_activo.py`.
- `modulos/04_generar_semillas.py` entra en la evidencia pre-M04 de los contratos `physical_components` (Canarias,
  Baleares, Las Palmas, Santa Cruz de Tenerife): cambiarlo los obliga a «Generar desde fuente territorial acreditada».
- Cambiar M04 o M05 invalida los checkpoints: la 00 siguiente va con «Ejecutar desde el principio».
- Las evidencias N08 (`docs/ESTUDIOS/N08_*`) fijan hashes de ficheros activos; si cambias uno, monta la copia
  archivada en `herramientas/verificar_evidencia_n08_readonly.py` y en `tests/test_preflight_caceres_n08.py`.
- El bucle de selección de checkpoints (`produccion-distritos.yml`) baja de etapa (M06→M05→M04→M03) cuando el validador
  rechaza: para rehacer desde Mxx basta con rechazar. Los checkpoints caducan a los 14 días.

## Lecciones 08-11 (Coordinador)
- La huella M05 es ahora el cierre de imports desde `modulos/05` (calculado, #547); antes era una lista a mano que apuntaba al v740 inactivo y no al v741. Tocar `ddd_core/config.py` invalida M05/M06. La capa M04 solo mira `m04_*.py`: posible hueco igual.
