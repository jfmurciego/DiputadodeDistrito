# T-102 · Congreso 350 · diseño (fase 1)

VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: propuesta al Coordinador · ANTERIOR: ninguna (fichero nuevo)
Decisión: D-19 (propietario). Producto paralelo; no toca los 407 (contratos `congreso_*`, K de N06, M08 ni publicaciones).

## 1. Declaración del K alternativo
- **Contratos paralelos** `territorios/congreso350_<prov>/config/congreso350_<prov>_2025.yaml` (52), no una variante
  del perfil de política: así el `territory_id` distinto separa checkpoints, huellas, catálogo, manifiestos y visor
  sin tocar ninguna lógica de los 407.
- Los genera una herramienta **nueva** `herramientas/generar_provincias_congreso_350.py` (idempotente): copia el
  contrato `congreso_<prov>` vigente (fuentes, CRS, puentes heredados, exenciones municipales) y cambia solo
  identidad, rutas y K. No modifica `generar_provincias_congreso.py`.
- K por provincia = columna `escanos_circunscripcion` de `configuracion/resultados_oficiales_congreso_2023.csv`
  (BOE-A-2023-18907), con su sha256 en el contrato. Campos ya previstos en el esquema:
  `k_source: legal_apportionment`, `apportionment_source: boe_congreso_2023`, `legal_apportionment_reused: true`,
  `k_reference_source: BOE-A-2023-18907#<sha256 csv>`. Test: suma 350 y 52 contratos.
- K se escribe en `territory_contract.k_districts`, `modulo_04.k_districts`, `modulo_06.expected_districts`,
  `validation.expected_districts` y `validation.province_districts`.

## 2. Suelo, techo y atomicidad (sin cambios)
- Se mantienen los del 407 por provincia: suelo 0,85, techo 1,15 (o el techo propio de la política, p. ej. 1,40 en
  Las Palmas), atomicidad 1,15, disciplina municipal, contigüidad, una provincia por distrito.
- La política necesita una entrada `congreso350_<prov>` por provincia con los mismos `population_limits` que su
  `congreso_<prov>` (el materializador los sobrescribe desde ahí). Se añaden solo filas nuevas (fichero compartido:
  aviso previo al Coordinador).

## 3. Huellas y checkpoints
- M01-M03 no dependen de K: mismas fuentes y parámetros → mismos productos. Con `territory_id` nuevo no hay
  checkpoint previo, así que la primera 00 los **recalcula** (determinista). No propongo copiar checkpoints entre
  territorios: exigiría tocar `seleccionar_checkpoint_productivo` y los workflows. Coste: minutos de M01-M03 por
  provincia. Control: el test de la prueba local compara el sha256 del grafo M03 con el del `congreso_<prov>`.
- La huella del motor (`huella_checkpoint_motor`) ya incluye `territory_id` y `territory_contract` (K): M04-M06 se
  regeneran solos; no se invalida nada de los 407. No se toca M04/M05 (sin cambios de huella M05 ni N08).

## 4. Gestor, catálogo y nombres
- Gestor: ámbito nuevo `congreso 350` en `herramientas/legislatura_vigente.py` (y en la lista del workflow
  `gestor-campanas.yml`), que selecciona las 52 filas `congreso350_*` y admite `--territorios` como «provincias».
  `legislatura_vigente.yaml` gana 52 filas con `ambito: congreso_350`; «nacional» y «legislatura completa» no las
  incluyen (siguen siendo 52 / 71).
- Registro electoral: unidades `congreso350_<prov>` con la misma elección (clave `ES-NAC-<CPRO>-20230723`) y el mismo
  paquete Infoelectoral (espejo del release); `election_id` `congreso350_<prov>_2023-07-23`.
- Catálogo de procedencia (T-74): filas nuevas con `variant: congreso_350` y `parent_territory: congreso_<prov>`.
- Nombres: selector 00 «Congreso 350 Madrid»; productos `congreso350_madrid_2025_m06_*`; distritos `C350-28-01…`.
  Sin choque con `congreso_madrid_*` ni con los CUDIS de los 407.
- `publicaciones_visor.json` no cambia: el eslabón electoral no publica y la 05 no se lanza (D-18).

## 5. Provincias especiales
- **K=1** (Ceuta, Melilla): sin partición; M04-M06 dan un distrito igual a la provincia (ya funciona hoy en los 407).
- **K=2-3** (Soria 2; Ávila, Cuenca, Guadalajara, Huesca, Palencia, Segovia, Teruel, Zamora 3): pocos distritos muy
  grandes; la atomicidad 1,15 casi nunca obliga a dividir municipios. Riesgo: la capital supera el techo en las de
  K=2-3 (p. ej. si un municipio > 1,15 × media, se divide; ya está previsto). Soria (K 1 → 2) es la prueba.
- **Islas** (Baleares 8, Las Palmas 8, Santa Cruz de Tenerife 7): `component_districts` del 407 (7/1/2 y 8/1/1) no
  suma el nuevo K. **Decisión del propietario**: reparto por islas (propongo Hamilton por población de cada
  componente, con exención de suelo explícita donde la isla quede bajo 0,85, como Menorca hoy). Fuera de la prueba
  de 3 y de la ola de 52 hasta que se decida.
- **Madrid**: 37 (2023), no 38 (2026).

## 6. Prueba local (fase 2) y fuera de alcance
- Motor real en local: Soria (2), Valladolid (5) y Madrid (37); informe M05 sin no-PASS y M06 con K exacto.
- Fuera: lanzar, publicar, tocar los 407, votos a los 350 distritos (T-83 B / T-85, después) y selector del visor (T-84).

## Preguntas al Coordinador / propietario
1. ¿Vale `congreso350_<prov>` (contratos paralelos) frente a una variante de política?
2. ¿Vale recalcular M01-M03 en vez de copiar checkpoints?
3. Islas: ¿Hamilton por componente con exenciones, o se dejan fuera de la primera ola?

## Aprobación y resultados (fase 2)
- Aprobado por el Coordinador el 08-11: (1) contratos paralelos sí; (2) recalcular M01-M03 sí; (3) islas fuera de la
  primera ola (decisión del propietario pendiente). Quedan 49 gemelos (327 escaños; las islas suman los 23 restantes).
- Prueba local con el motor real (M01-M06, fuentes INE 2023: seccionado de ine.es y 65034 del repositorio):

| Provincia | K | Secciones | Población | Desviación mín / máx | Estado |
|---|---|---|---|---|---|
| Soria | 2 | 216 | 89.528 | −0,002 % / +0,002 % | 2 PASS; grafo M03 = el de `congreso_soria` |
| Valladolid | 5 | 565 | 521.333 | −5,4 % / +3,4 % | 5 PASS |
| Madrid | 37 | 4.479 | 6.871.903 | −14,3 % / +14,5 % | 37 PASS (M04 236 s, M05 87 s) |

- Nota de entorno: en local la sección 2808002027 (Majadahonda) quedó sin contacto medible con el shapefile INE; se probó
  con un puente solo en el contrato temporal. En producción la fuente es la OGC acreditada (la de los 407, que no lo
  necesitó); si la 00 de Madrid 350 diera `isolated=1`, ocurriría igual en el 407.
