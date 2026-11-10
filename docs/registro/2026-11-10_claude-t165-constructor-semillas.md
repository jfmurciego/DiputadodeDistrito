## 2026-11-10 — T-165 — Diseño del constructor de semillas sobre el núcleo único de reglas

- Causa: D-48 (línea de fondo): poder retirar algún día el constructor artesanal de la semilla canónica (M04 7.6.7 + M05 7.4.4).
- Cambio: solo documentación, `docs/ESTUDIOS/T165_CONSTRUCTOR_SEMILLAS/DISENO.md` (inventario de reglas fuera del núcleo,
  algoritmo por árboles con reparación guiada por `ddd_motor2/reglas`, invariantes, determinismo y semilla pública, medición con
  la batería T-132, riesgos y esfuerzo por fases). Sin código, sin huellas, sin lanzamientos.
- Pruebas: no aplica (documento). Cifras tomadas de `docs/ESTUDIOS/T132_BATERIA_MOTOR/BANCO.csv` y `RESUMEN_GENERADORES.md`.
- Riesgos: ninguno para producción; la fase de sustitución en el canónico (F5) invalidaría huellas y checkpoints y exige permiso.
