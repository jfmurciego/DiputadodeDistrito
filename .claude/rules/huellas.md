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

- `modulos/05_optimizar_distritos.py` está en la huella M05 (`huella_checkpoint_m05.ENGINE_FILES`): tocarlo
  invalida los M06 previos para la 04 (lo resolvió #346 con `--consume-certified-product`).
- `modulos/04_generar_semillas.py` entra en la evidencia pre-M04 de los contratos `physical_components` (Canarias,
  Baleares, Las Palmas, Santa Cruz de Tenerife): cambiarlo los obliga a «Generar desde fuente territorial acreditada».
- Cambiar M04 o M05 invalida los checkpoints: la 00 siguiente va con «Ejecutar desde el principio».
- Las evidencias N08 (`docs/ESTUDIOS/N08_*`) fijan hashes de ficheros activos; si cambias uno, monta la copia
  archivada en `herramientas/verificar_evidencia_n08_readonly.py` y en `tests/test_preflight_caceres_n08.py`.
