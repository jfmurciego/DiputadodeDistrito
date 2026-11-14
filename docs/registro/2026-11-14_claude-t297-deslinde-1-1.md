## 2026-11-14 — T-297 — Deslinde 1.1: frontera medida en D8 y candidato exacto (CP-SAT)

- Causa: T-296 demostró que (H2) la frontera cortada de D8 valía 0 en todos los planes, porque M02 calculaba
  la longitud compartida solo como filtro y no la escribía, y que (H1) en Burgos y Valladolid hay planes válidos con
  menos demarcaciones partidas que el ganador y que las cadenas no encuentran.
- Cambio:
  - `modulos/02` 7.4.0: cada arista geométrica lleva `shared_border_m` (m, 3 decimales, CRS de trabajo; las aristas no
    cambian).
  - `modulos/03` 7.6.0: conserva `shared_border_m`.
  - Paquete Deslinde 1.1.0:
    - `exacto.py` 1.0.0, nuevo: CP-SAT determinista (1 hilo, semilla 0, tiempo determinista) sobre la clave D8 por
      etapas. Aplica con 2 ≤ K ≤ 4, una circunscripción y sin exenciones.
    - `competicion.py` 1.5.0: candidato «exacto» con D8; si no prueba el óptimo, su mejor plan válido; si no hay
      ninguno, no compite. Entra en `huella_resultado`.
    - lock con ortools 9.14.6206 y sus dependencias.
  - `bateria_motor.py` 1.2.7: el recuento de candidatos cuenta el exacto.
  - `bateria-motor.yml` 1.1.6 y `_reutilizable-generacion-territorial.yml` 1.5.2: instalan ortools con `--no-deps`.
  - `DESLINDE_1_0.md` 1.1.0, con la copia anterior en `legacy/`.
- Efectos:
  - Cambian los mapas, la huella motor2 y el binding pre-M04 (blob de M02 y M03) de todos los territorios. Toda 00
    debe ir con «Generar desde fuente».
  - Con A, C y D5 el exacto no actúa.
  - La aceptación no cambia, salvo el recuento de candidatos (+1 exacto).
- Pruebas:
  - `tests/test_t297_deslinde_1_1.py`: exacto óptimo y determinista, «no aplica», frontera M02/M03 y recuento.
  - Suites de motor 2, paquete, M02, workflows y gobernanza, en local.
  - Competición real en Burgos, Valladolid, Huesca y La Rioja, dos veces (misma huella).
