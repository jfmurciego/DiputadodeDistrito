## 2026-11-14 — T-257 — paquete independiente Deslinde 1.0.0 (fuente única)

- Causa: D-86 y D-88 (con D-94: Zenodo solo mapas; el paquete es privado): Deslinde vivía dentro de `ddd_motor2/`,
  atado a rutas del repo (tabla maestra, `publicaciones_visor.json`, tablas de naturalidad, `ddd_core`).
- Cambio: nuevo paquete `paquetes/deslinde/` (`deslinde` 1.0.0, privado: pyproject, README, `requirements-deslinde.lock`,
  `MAPAS.json` vacío; la licencia la fija #744). El núcleo se MUEVE (no se copia): `reglas/*`, `adaptadores`,
  `calidad`, `exhaustivo`, `excepcion_d66`, `competicion`, `naturalidad_clave`, `informe`, la fórmula de la semilla, la
  cadena ReCom ponderado (`ponderado`) y los candidatos (`candidatos`: piezas finas, reparación, Vigente, Ponderado,
  CanonicoDelRun). Nuevos: `territorio` (resolutor del código oficial), `tablas` (las aporta quien llama), `contrato`,
  `exenciones` (copia literal vigilada de `ddd_core/population_cap_exemptions.py`: unificarla toca la huella M05),
  `api` y CLI. `ddd_motor2/__init__.py` aliasa los módulos movidos (mismo objeto) y registra el resolutor de la tabla
  maestra (`semilla.py` 1.2.0) y las tablas del repo (`tablas_repo.py`). `generadores` 1.3.0, `produccion` 1.2.0 (la
  huella motor2 incluye el paquete), `naturalidad_competicion` 1.7.0, `preparar_paquete_pi` 1.0.1 (incluye el paquete),
  `DESLINDE_1_0.md` 1.0.2 (§8). `.zenodo.json` y `CITATION.cff` no cambian
  (D-94: los metadatos del depósito de mapas van en T-276).
- Pruebas: mapas bit a bit con la batería real (10 cadenas, D8), `main` b5bd69e frente a la rama: misma
  `huella_resultado` en nac22 `3ffb7d5b…`, nac26 `831dd23d…`, aut17 `d50a21d0…` y nac35 `a241b52c…` (contrato 2025 con la
  exención 35-G01 del de 2026; la batería no admite contratos 2026). Paquete aislado en nac26: los mismos 12 candidatos.
  `tests/test_t257_paquete_deslinde.py` (fuente única, aislamiento, copia vigilada, equivalencia en 3 territorios) y
  las suites del motor 2, P30, batería, certificador, huellas, T-220/T-258 y T-127.
- Efectos: cambia la huella motor2 (D-89): la primera 00 con `motor: motor2` rehace el P30. Ni M04 ni M05 cambian.
