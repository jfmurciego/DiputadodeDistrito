## 2026-11-07 — T-41 — Puerta humana de producción (environment produccion)

Causa: lanzar y publicar dependían del modelo; el propietario quiere un clic suyo en GitHub, sin modelo de por medio.

Cambio: los jobs de entrada de 00 (1.5.0), Activación por Elección (1.1.0), 05 (3.2.0) y 06 (2.4.0) declaran
`environment: produccion` solo en `workflow_dispatch` manual de una persona (no `github-actions[bot]` ni `ddd-registro[bot]`).
05 y 06 solo la piden como entrada directa, no al ser llamadas por la 00. Con revisor en el entorno, lanzar y publicar
exigen el clic del propietario; sin el entorno creado, GitHub lo crea sin reglas y no bloquea. Skills `operador`,
`lanzar-00` y `publicar-visor` actualizadas.

Pruebas: tests de workflows y R015 en verde, `comprobar_guardian_main.py todo` OK. PR #437.
