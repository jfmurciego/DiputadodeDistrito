## 2026-11-10 — T-163 — Motor 2: semilla pública aprobada (D-50)

- Causa: decisión del propietario D-50: la semilla pública es el sha256 del fichero oficial de padrón y seccionado de la
  edición más el identificador del territorio, como ya estaba en el código.
- Cambio: `ddd_motor2/semilla.py` 1.0.1: quita la marca de «propuesta» de la cabecera; misma fórmula
  (`ddd-semilla-publica/1`) y mismas semillas. Copia 1.0.0 en `legacy/ddd_motor2/`.
- Pruebas: `python -m unittest tests.test_motor2_semilla`.
