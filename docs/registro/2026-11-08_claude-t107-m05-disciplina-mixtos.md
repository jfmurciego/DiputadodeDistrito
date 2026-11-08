## 2026-11-08 — T-107 — M05 canónico respeta la disciplina municipal (Ávila, Castilla y León)

Causa: la 00 de Castilla y León del 08-11 (run 42497104110) se lanzó con «Canónico» y la del 30-10 (run 40979527162)
con «GerryChain 50». No es regresión de M04, política ni contrato: la política de Castilla y León y el contrato no
cambian entre 627514a y 526a029, y M04 (7.5.9 el 28-10 y 7.6.7 hoy) expone la misma unidad `05:05019:F1` (sección
0501906003). GerryChain impone como máximo un distrito mixto por municipio partido; el M05 canónico (7.4.2) no, y
llevó esa sección del residual de Ávila (distrito 2, mixto) al distrito 1 (rural): Ávila en 0, 1 y 2 con dos mixtos y la
04 falló en `validar_ejecucion` (R012). El volcado del 28-10 (canónico) ya tenía el mismo defecto.
Cambio: `ddd_core/m05_opt_engine_v741.py` 7.4.3: con `require_municipality_discipline`, voraz y recocido rechazan el
movimiento que aumenta los municipios partidos con más de `max_mixed_districts_per_split_municipality` distritos
mixtos (campo municipal como el validador); el informe M05 añade `municipal_discipline`. Sin cambios de suelo, techo,
K ni atomicidad.
Pruebas: reproducción local con el motor real (grafo M03 de `diagnostico/poblacion-20261028`): antes, 05019 en 0/1/2
con 2 mixtos; después, M06 y `validar_ejecucion` PASS (Ávila con un solo mixto, 48 movimientos rechazados, max_rel_dev
0,1537 → 0,1364). Test nuevo `test_m05_disciplina_municipal_canonico`; M05, exenciones, R015/R016 en verde.
Siguiente 00 de Castilla y León: «Ejecutar desde el principio» (cambia el motor M05; el fichero no está en la huella).
