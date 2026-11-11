## 2026-11-11 — T-265 — Deslinde: la semilla sale del código oficial de la tabla maestra (D-90)

- Decisión: D-90 (y D-61/6). El territorio de la semilla pública deja de ser el nombre de la carpeta. Ahora es el código
  oficial de la tabla maestra (`configuracion/notacion_territorial.csv`, sha256 `13299081…e621ee`): AUTnn = CODAUTO y
  NACnn = CPRO del INE. Lo resuelve el resolutor único (`ddd_core.territorio_ids.codigo_semilla`), que acepta el id viejo
  y el nuevo. Es un cambio único y deliberado de los mapas.
- Cambios (las versiones anteriores están en `legacy/`):
  - `ddd_motor2/semilla.py` 1.0.1 → 1.1.0: esquema `ddd-semilla-publica/2`. El hash usa el código y no la carpeta. Si el
    territorio no está en la tabla (incluidos `congreso350_*` y `-350`), da `ErrorContrato` y no cae al nombre.
    `descripcion` registra `codigo`, `derivacion` y `tabla_maestra` (ruta y sha256).
  - `ddd_motor2/competicion.py` 1.4.1 → 1.4.2: `huella_resultado` incluye el esquema, el código y el sha256 de la tabla.
    `VERSION` pasa a 1.4.2, así que `--reanudar` no reutiliza los COMPETICION.json de la semilla vieja.
  - `ddd_motor2/produccion.py` 1.1.0 → 1.1.1: la huella `motor2` incluye la tabla maestra y `ddd_core/territorio_ids.py`.
  - `ddd_motor2/informe.py` 1.1.0 → 1.1.1: COMPETICION.md dice el código y el sha256 de la tabla.
  - `docs/ARQUITECTURA/DESLINDE_1_0.md` 1.0.0 → 1.0.1: la semilla por código entra en la definición 1.0.1 (§4) y se cierra
    el punto abierto 2. Se elige 1.0.1 y no 1.1.0 porque reglas, elección D8 y candidatos no cambian y «1.1» queda para
    D-87/D-88.
- Tests: `tests/test_motor2_semilla.py` incluye la fórmula del esquema 2 y la clase `CodigoOficial`:
  - renombrar la carpeta (`congreso_alava`→`nac01`, `la_rioja`→`aut17`, `congreso_la_rioja`→`nac26`, `melilla`→`aut19`)
    no cambia ni la semilla ni la descripción (salvo el campo `territorio`);
  - un territorio fuera de la tabla falla;
  - la huella del resultado y la huella `motor2` registran la semilla.
  Se regeneran `HUELLAS_FIJAS` y `HUELLAS_FIJAS_A` en `tests/test_motor2_aceptacion.py`, que ahora usa ids de la tabla.
  Los tests con ids sintéticos (`prueba`, `sintetico`) usan ids reales (`ceuta`, `la_rioja`).
- Tests pasados (unittest, local, Python 3.13, `requirements.lock` + gerrychain `--no-deps`):
  - `test_motor2_*` (semilla, aceptacion, competir, competicion, competicion_d8, competidor, informe, reglas, adaptadores,
    exhaustivo, cota_nodos, poda_constantes, naturalidad);
  - `test_p30_motor2_produccion`, `test_huella_checkpoint_motor`, `test_certificador_*`, `test_estado_produccion_motor2`,
    `test_resolver_territorio`, `test_notacion_territorial` y R015 `GovernanceHeaders`.
  - Fallan igual en `main` 9710814, por el entorno: `test_bateria_motor.test_t212_forma_con_la_m01_de_las_entradas`,
    `test_estado_produccion_y_visor` (1 error) y `test_huella_m05_motor_activo` (2 errores).
- Prueba local con el motor real (los 3 territorios de T-254): entradas con `bateria_motor.py entradas … --seccionado
  shapefile` y `PYTHONHASHSEED=0 python3 -m ddd_motor2.competir` (D8, 10 cadenas). Se hicieron dos ejecuciones con esta
  rama y una con `main` 9710814 (semilla vieja).

  | Territorio | Código | Ganador nuevo | Frente al canónico | Fuera tol. | Desvío máx. | Partidas | Ganador viejo |
  |---|---|---|---|---|---|---|---|
  | congreso_huesca | NAC22 | ponderado-s2002714695 | mejora | 0 | 0,02111 | 1 (canónico 8) | el mismo plan (misma `huella_plan`), otra semilla |
  | congreso_la_rioja | NAC26 | ponderado-s1753368524 | mejora | 0 | 0,00154 | 2 (canónico 8) | otro plan: 2 partidas, desvío 0,00338 |
  | la_rioja | AUT17 | ponderado-s479522733 | mejora | 1 | 0,41776 | 7 (canónico 9) | otro plan: 8 partidas |

  - Aceptación: la clave del ganador nunca es peor que la del canónico, mejora en los 3. Frente al vigente también mejora
    en los 3, con los mismos fuera de tolerancia que el vigente publicado.
  - Reproducibilidad: en las dos ejecuciones salen la misma `huella_resultado` y los mismos sha256 de las 12
    composiciones de cada territorio.
  - Nueva referencia «bit a bit» desde la fusión (D-90, e):
    - congreso_huesca `7085a317fbe1ef6be34c4a7c6141e4cc7df838be8915a2817637395dcbcd33f4`;
    - congreso_la_rioja `3deb5f2883830b08bedba4f276f5aae5abddc4a60975d698ae453fcfc151fa2b`;
    - la_rioja `1e75f2649519c4122a51dda4904b626c53d52657c1250405ffeb6f117d22efdb`.
- Huellas: cambian la huella `motor2` (código, tabla maestra y resolutor) y todas las `huella_resultado`. No toca M04,
  M05, `modulos/` ni N08. Modo de 00: un M06 con P30 de la semilla vieja no se reutiliza (la capa `motor2` cambia). Las
  71 se regeneran tras esta fusión y antes de T-220. No se lanza nada.
