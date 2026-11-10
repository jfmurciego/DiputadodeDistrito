## 2026-11-10 — T-164 — Certificador exacto con modelo ligero (D-48)

- Causa: Madrid (K=59) no resolvía en el modelo monolítico del certificador T-136 y faltaba una cota de calidad donde
  el exacto no escala.
- Cambio: `herramientas/certificador_exacto.py` 1.2.0. Nuevo `--modelo ligero`: cota inferior por relajación fluida
  sin contigüidad (por clave R012), cota superior por superátomos contiguos dentro de los distritos de la pista
  (`--grano`) y modelo completo si hay ≤ `--umbral-exacto` átomos. Da `OPTIMO_CERTIFICADO` si las cotas coinciden; si
  no, `COTA` con el hueco. La cota de CP-SAT se informa también cuando el solver no termina. Sin cambios en producción
  ni en huellas.
- Resultados (`docs/ESTUDIOS/T136_CERTIFICADOR_EXACTO.md`): Álava, Huesca y Cádiz, óptimo certificado en ≤ 2 s.
  Madrid: minimax óptimo certificado (17.236 = publicado), techo con hueco de 3 hab., 0,6 GB.
- Pruebas: `python -m unittest tests.test_certificador_ligero tests.test_certificador_exacto` (7 + 7).
