## 2026-11-28 — T-476 — Datos abiertos 2: votos por partido y distrito, doble vuelta y composición (EN CURSO, traspaso)

Estado: sin código aún; esta entrada es el traspaso a la sesión que sigue (relevo del Coordinador, 28-11).

**Fuentes en git (verificadas en local, con sha256 en sus manifiestos):**
- 2023, los 52 nac vigentes: `datos/resultados/runs/<nacNN>_<run_m08>_partidos.csv` (distrito 0..K-1, partido, votos,
  blancos, nulos, censo). `datos/resultados/MANIFEST.json` → `partidos_runs["nacNN/<run>"]` da `sha256_csv`,
  `run_territorial`, `sha256_composicion` y `sha256_zip` (Infoelectoral). El run M08 de cada nac es el de `datos_abiertos/INDEX.json`.
- Composición vigente: `datos/composicion/runs/<nacNN>_<run_territorial>.csv` (seccion, distrito, poblacion), sha256 en
  `datos/composicion/MANIFEST_RUNS.json`.
- 2011-11 a 2019-11: `datos/resultados/historico/<AAAAMM>/<id_legacy>_partidos.csv` y `<id_legacy>.csv` (censo, votantes),
  T-83, reagregados al mapa de `datos/composicion/<id_legacy>.csv` (su `sha256_m06` = `distritos_m06` del MANIFEST del
  histórico en los 52). Solo en 11 nac ese mapa es la MISMA partición, con las mismas etiquetas, que el vigente:
  nac01, nac05, nac07, nac34, nac40, nac42, nac44, nac49, nac50, nac51, nac52. En los otros 41 el histórico está sobre
  un mapa anterior y los votos por sección (espejo T-89) no están en git → criterio (3): listar con motivo, no construir.
- BOE: `configuracion/resultados_oficiales_congreso_{2011_11,2015_12,2016_06,2019_04,2019_11,2023}.csv` (solo
  candidaturas con escaño en alguna provincia; codigo INE). Siglas BOE → fuente: `configuracion/alias_siglas_boe_espejo.csv`
  (sin separadores múltiples). Código INE por nac: `provincia` en `datos/resultados/historico/MANIFEST.json`.
  Cuadre 2023 probado: suma distritos ≤ BOE en todo partido casado, defecto máx. 7,4 % (VOX, Orense) = voto CERA, que el
  ZIP por mesa no trae; usar `fuente_nazioenbehatokia.contrastar_provincia` con `UMBRAL_DEFECTO` 0,10 (mismo criterio que T-83).
- Doble vuelta: no hay CSV nac en git (está en R2, `configuracion/doble_vuelta_publicada.json`); calcular con
  `herramientas/doble_vuelta.py` (`cargar_tabla`, `cargar_alias`, `aplicar_alias`, `resolver`, escenarios dv_base/dv_A/dv_B)
  y `configuracion/bloques_partidos_2026-11-25.csv` («Derecha nacional») + `alias_partidos_generales.csv` (eleccion AAAAMM).
- Ganador publicado 2023: `datos/resultados/<nacNN>.csv` (contraste por distrito con la tabla).

**Riesgo encontrado:** `herramientas/generar_datos_abiertos.py` (P40) hace `rmtree` de toda subcarpeta de `datos_abiertos/`
que no sea territorio y `--materializar` copia el paquete entero al sitio. Si los datos van a `datos_abiertos/votos/`, hay
que subirlo a 1.3.2 (legacy) para que no la borre y la excluya de `--materializar` (sin publicar en esta tanda). Fichero
compartido: avisar antes.

**Contraste Universidad de Valencia (criterio 4):** `www.uv.es` no se alcanza desde la nube (proxy 403, 27-11): anotarlo.

**Pendiente:** herramienta `herramientas/datos_abiertos_votos.py` (genera y `--comprobar`), diccionario, informe con lo no
construible, test, VERSIÓN/legacy donde toque, y las pruebas de siempre (test_t220_renombrado, GovernanceHeaders, guardián).
