# T-365 · Histórico de las generales por época (D-125): diseño mínimo y piloto nac22 2019-11

VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
MOTIVO: D-125 (distritos con los datos de cada época, sin traslado al mapa 2023), D-126/D-128 (población), T-199 (elección en el registro).
Sin tocar el motor: `modulos/01-08`, `ddd_core/`, `ddd_motor2/` se ejecutan tal cual; las huellas M04/M05 no cambian.

## 1. Qué fichero hace qué

| Fichero | Papel |
|---|---|
| `configuracion/historico_epoca/contrato_<AAAA_MM>.json` (5, versionados) | **Contrato por elección**: seccionado del año (fichero, sha256, URL INE, clave R2), tabla de población (sha256, herramienta, año de referencia D-126, huellas de 30832 y Censo 2011), escaños BOE (CSV de T-330 con su sha256 y BOE), votos del Observatorio (manifiesto y sha256 por provincia, clave R2), y por provincia: `nacNN`, K del BOE, contrato base (ruta+sha256), población (`secciones_sin_dato`, `secciones_sin_seccionado` con su población) y `estado` (LISTA / BLOQUEADA_RELLENO / BLOQUEADA_SIN_DATO). |
| `herramientas/contrato_historico_epoca.py` | `contrato` los genera (determinista, sin reloj ni red). `materializar` verifica cada fuente local contra el contrato, casa seccionado y población (fallo cerrado) y escribe `territorios/<t>/config/<t>_h<AAAA_MM>.yaml` (no versionado, `.gitignore`). `electoral` monta el paquete M07, ejecuta M07/M08 y escribe `PUERTA_<t>_<AAAA_MM>.json` y `MANIFEST.json`. `cadena` = materializar + admisión + M01..M06 + electoral. |
| `tests/test_t365_historico_epoca.py` | Contratos coherentes con los ficheros acreditados (K = BOE, total 350, huellas), transformación del contrato, fallo cerrado de `materializar`, puerta, y flujo M07/M08 real sobre un M06 sintético (control positivo y negativo). |
| `bajar_fuentes.sh` | Baja las fuentes de una elección y provincia (INE y Observatorio) y comprueba el sha256 contra el contrato; reconstruye la tabla de población con la herramienta declarada. |
| `casado.py`, `casado_2019_11.csv` | Casado por provincia seccionado / población / votos (medido, ver §5). |
| `piloto_nac22_2019_11/` | Evidencia del piloto (puerta, manifiesto, resultados, composición M06, contrato de provincia). |

## 2. Contrato de provincia (derivado, no versionado)

Desde `territorios/nacNN/config/nacNN_2025.yaml` (sha256 en el contrato), cambia solo:
fuentes (`io.input`: seccionado del año y población en CSV `Periodo,Secciones,Total,origen`), años (`meta.year` = año de la elección,
`source_population_year` = año de referencia D-126, `source_section_year` = seccionado), `run_name` `nacNN_hAAAA_MM` y rutas de salida,
`POP_<año>`, K (`k_districts`, M04, M06, `validation.expected_districts`, `province_districts`; `k_source: norma`),
`source_baseline` y `generation_state.source_inputs` (sha256). Suelo, techo, atomicidad, reparto, exenciones y parámetros de M02-M06:
los del contrato base (no se cambian sin decisión del propietario). Falla cerrado si: una fuente no coincide en sha256, el contrato base
cambió, seccionado y población no casan, un puente topológico apunta a una sección inexistente en el año, o hay `topology_accreditation`.

Admisión: `ddd_core.territory_contract` 1.5.0 añade la dimensión de elección al catálogo (decisión del Planificador, 16-11): un
contrato con `meta.historico_epoca` compara K, origen y justificación con la provincia del contrato de SU elección (cuyo sha256 debe
coincidir); nivel y autorización siguen saliendo del catálogo maestro. Sin `historico_epoca`, idéntico a 1.4.1: comprobado sobre los
172 contratos `territorios/*/config/*_20*.yaml` (0 diferencias) y fijado por test. No está en el cierre de imports de M05: huellas intactas.

## 3. Reutilización

- Paso A / cadena: `reagregacion_historico.escribir_paquete` (paquete M07), `historico_m07m08` (`ejecutar`, `leer_resumen`,
  `escribir_participacion`), `historico_campana.contraste_boe`, `MAX_PERDIDOS` y `D70` (misma puerta que la ficha #819),
  `fuente_nazioenbehatokia.leer_provincia`, `poblacion_seccion_historica` (T-358). M07 sin tabla de equivalencia: votos y mapa son del mismo seccionado.
- No se reutiliza el traslado año→2023 (T-328/T-329): D-125 lo sustituye para las generales.

## 4. Piloto local nac22 2019-11 (cadena real hasta M08, 16-11)

Fuentes bajadas desde la sesión cloud con HTTP 200 y sha256 igual al contrato: `seccionado_2020.zip` (www.ine.es), `30832.csv` y
`indicadores_seccion_censal_csv.zip` (www.ine.es), `data/201911/sekzioa/22.json` (nazioenbehatokia.eus). Tabla de población de T-364
(#840@f3e7d9a, sin `--estricto`; con 29005 y los seccionados 2015-2020 de sha256 acreditado): 2019-11 sha256 `c6eb6f8a…` (= T-364). La de T-358 daba la misma composición en Huesca. R2 no probado desde la nube (sin credenciales; en Actions sí).

`python herramientas/contrato_historico_epoca.py cadena --eleccion 2019-11 --territorio nac22 --fuentes DIR` (~15 s):
casado 286/286/286; K = 3 (BOE-A-2019-18147); M06: 73.615 / 73.609 / 73.610 hab. (desviación máx. 0,005 %, todos PASS);
M07 PASS, 111.396 votos, 0 sin asignar; M08 3 distritos = 3 escaños; contraste BOE por partido: 5/5 comparados, defecto máx.
1,15 % (tolerancia 10 %). **PUERTA PASS.** Ganador PSOE en los 3. Repetida: composición M06 idéntica (sha256 `adf786fc…`); los zip
M06/M08 cambian de hash por la fecha interna (conocido).

## 5. Riesgos y bloqueos

1. **Casado población ↔ seccionado.** Con la tabla de T-364 (`no_listada`, decisión del Planificador 16-11) ya no queda ninguna sección
   del seccionado sin población en 2019-11. Quedan las **secciones con población sin geometría** en el seccionado del año
   (`secciones_sin_seccionado` del contrato): 2011-11 44 (13 prov.), 2015-12 31 (15), 2016-06 36 (11), 2019-04 30 (9), 2019-11 52 (14 prov.,
   75.795 hab.; `casado_2019_11.csv`). Hoy `materializar` falla cerrado en esas provincias (**decisión pendiente del propietario**:
   p. ej. asignarlas a la sección del seccionado que las contiene, o excluirlas declarando su población).
2. **Población.** Contratos con la tabla de T-364 sin `--estricto` (46 municipios con aviso, decisión pendiente del propietario); si cambia,
   se regeneran (versión 1.1.0, copia en `legacy/`). Estados: 2015-12 27 LISTA / 11 BLOQUEADA_RELLENO / 14 BLOQUEADA_SIN_DATO; 2016-06
   38/13/1; 2019-04 40/12/0; 2019-11 y 2011-11 52 LISTA. Generables hoy (LISTA y sin `secciones_sin_seccionado`) en 2011-11, 2015-12, 2016-06, 2019-04 y 2019-11: 39, 23, 29, 31 y 38
   (las secciones del seccionado sin población solo están medidas en 2019-11: 0; en las otras, `materializar` lo comprueba y falla cerrado).
3. **Contrato base cambiante.** Si un robot reescribe `nacNN_2025.yaml`, `materializar` falla (huella): se regenera el contrato (barato).
4. **Votos sin geometría.** 6 provincias de 2019-11 tienen 1-3 secciones de votos fuera del seccionado: van a «sin asignar» y la puerta
   las limita (≤ 0,1 %).
5. **Motor de producción.** El piloto usa M04/M05 canónicos; la 00 de producción compite con motor2 (P30). Integrarlo en Actions es de
   T-360 (workflows): un job «histórico por época» que llame a `cadena` por provincia, o la 00 con el contrato `_hAAAA_MM`.
6. **Puentes.** 20 contratos base tienen `topology_bridges` (de 2023): se verifican contra el seccionado de cada año; si un extremo no existe, falla.

## 6. Registro, visor y T-355

- El `MANIFEST.json` lleva `kind: historico_epoca`, `election_date` y `election_id = nacNN_<fecha>` (dimensión de T-199/T-201: la
  unicidad `canonical` es por territorio, familia y elección). No se escribe el registro ni se publica.
- Para T-355 (#830 se rehace sobre esto): kind nuevo en `registro_publicaciones_visor.py` y en la lista blanca del catálogo de
  procedencia (T-361: el conjunto de productos es cerrado), publicación por fecha separada del vigente, numeración pública 1..K
  (T-135), provincias no LISTA excluidas, y los consumidores que aún eligen por `run_id` (`resultados_ligeros`,
  `generar_datos_abiertos`, `generar_hemiciclo`, `legislatura_vigente`; T-199) deben filtrar por elección.
