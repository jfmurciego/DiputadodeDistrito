# T-509 · Ámbito D · Repositorio, tests y deuda

VERSIÓN: 1.0.0 · FECHA: 2026-11-28 · ESTADO: entrega de investigación · ANTERIOR: ninguna (fichero nuevo)
Datos de máquina: `D_repositorio.json` (mismos ids). Verificado por un revisor independiente el 28-11 (secciones 9 y 10). Medido sobre el árbol de `investigacion/2026-11-28` (commit 9e630d11d).

## 1. Veredicto

1. El árbol ocupa **1.068 MB y 14.483 ficheros**; GitHub da 467 MB de repositorio.
2. **342 MB (32 %) son copias exactas** de otro fichero del mismo árbol.
3. El peso del clon no está en `legacy/`, como decían las auditorías: legacy son 15 MB comprimidos. El 80 % son
   tres carpetas de binarios: `inputs/partes`, una auditoría del 09-10 con sus ZIP y los estudios.
4. `legacy/` sí pesa en el árbol y en las búsquedas: 2.675 ficheros, y el 93 % no lo cita nada vivo.
5. La regla VERSIÓN + legacy añade **355 ficheros y 35 MB por semana**; tres cuartos son copias enteras del registro.
6. La regla cubre el 38 % de los ficheros activos y solo está probada en 22.
7. Hay **95.210 líneas de tests para 28.822 de motor**. El motor está bien cubierto por tests de comportamiento.
8. Pero entre el 17 y el 18 % de las aserciones y el 23 % de los ficheros de test comprueban texto de workflows, documentos o HTML.
9. 107 ficheros de código quedan fuera de la tubería: 20 sin ninguna cita, 9 solo en documentos y 78 sin cita de
   código ni de workflows (49 de ellos solo en su test).
10. **Liga de hoy: segunda.** Trazabilidad muy superior a la media de un proyecto de investigación, dentro de un
    árbol de «todo dentro» que un tercero no puede clonar, buscar ni entender con comodidad.

## 2. Estado objetivo de referente mundial

- **Un repositorio de código de menos de 150 MB.** Motor, herramientas de la tubería, workflows, tests y documentación
  viva. GerryChain (github.com/mggg/GerryChain) no guarda datos de entrada junto al motor.
- **Datos, evidencia y archivo fuera de git, con manifiesto de sha256 dentro.** Es la recomendación de Wilson et al.,
  «Good enough practices in scientific computing» (PLOS Comput Biol, 2017). El proyecto ya lo hace bien en tres
  sitios (`inputs/MANIFEST.sha256`, los espejos de P10 en R2, `datos_abiertos/INDEX.json`): falta hacerlo siempre.
- **El historial de git es la única memoria de versiones.** Las cabeceras siguen; las copias numeradas, no.
- **Tests clasificados por lo que protegen**, con la suite de motor separada de la de textos, y validación de
  workflows por estructura (actionlint y análisis del YAML), no por frases.
- **Tres guardias automáticas**: tamaño de fichero, código sin punto de entrada y citas a rutas inexistentes.
- GitHub recomienda repositorios de menos de 1 GB y avisa a partir de 50 MB por fichero.

## 3. Qué ocupa qué (medido)

| Carpeta | MB en el árbol | Ficheros | MB comprimidos en el clon | Qué es |
|---|---:|---:|---:|---|
| `docs/` | 398,6 | 2.677 | 165,0 | `AUDITORIAS` 303 MB (una sola carpeta, 262 MB), `ESTUDIOS` 90 MB |
| `territorios/` | 186,0 | 3.185 | 9,5 | 136 MB son la copia de `inputs/partes` en `aut02`; evidencia 32 MB |
| `legacy/` | 152,7 | 2.675 | 15,2 | 655 copias del registro (104 MB) y 79 del plan (7,5 MB) |
| `resultados/` | 138,2 | 46 | 18,7 | `lotes_autonomos` 119 MB, sin ninguna cita |
| `inputs/` | 137,7 | 15 | 132,7 | las partes de los dos ZIP de entrada del INE |
| `tests/` | 17,1 | 2.752 | 2,8 | fixtures 12,2 MB en 2.213 ficheros |
| `datos/` | 13,9 | 1.735 | 3,1 | composición y resultados publicados |
| resto | 24,1 | 1.398 | 9,1 | código, visor, configuración, workflows |

Por tipo: ZIP y partes de ZIP 532 MB (87 ficheros), GeoJSON 173 MB (71), Markdown 117 MB (2.106), JSON 60 MB,
PNG 52 MB, CSV 50 MB, Python 25 MB (1.759). En `docs/` hay 67 ZIP (252 MB), 90 PNG (50 MB) y 5 PDF.
Los 30 ficheros mayores son todos binarios o GeoJSON de entre 9,6 y 30,5 MB; ninguno es código.

## 4. Hallazgos (impacto tras la verificación)

### D-1 · El 80 % del peso del clon son tres carpetas de binarios, y 342 MB son copias exactas (impacto 3)
- **Hoy.** `inputs/partes` (132,5 MB comprimidos), `docs/AUDITORIAS/F04_F10_20261009` (86,9 MB; 262 MB en disco, con
  el mismo ZIP de 11 MB cinco veces) y `docs/ESTUDIOS` (67 MB): 287 MB entre las tres. `inputs/partes` está entero otra vez en
  `territorios/aut02/inputs/partes`. `resultados/lotes_autonomos` (119 MB) no lo cita ningún workflow, código,
  test ni configuración. `.gitattributes` declara LFS para dos ficheros que no existen (`git lfs ls-files` da 0).
- **Evidencia.** `git cat-file --batch-all-objects --batch-check` con `%(objectsize:disk)` cruzado con
  `git ls-files -s`; `gh api repos/<repo> --jq .size` da 466.702 KB; el checkout tarda 13 a 15 s en 6 jobs medidos.
- **Propuesta.** Llevar a R2 o a un release, con índice de sha256: primero lo que nadie lee (`lotes_autonomos`,
  `legacy/publication`), luego los ZIP de la auditoría (salvo los 5 de `originales/`, 28 MB, que un test abre), luego la copia de `aut02`, y al final `inputs/partes` con un
  paso de descarga verificada. Sin reescribir el historial.
- **Criterio.** El árbol baja de 1.068 a menos de 600 MB con los tres primeros pasos y a menos de 450 MB con el
  cuarto; las copias exactas bajan de 342 a menos de 50 MB; un paso de la nocturna (no la suite de las PR) baja los ficheros del índice y
  comprueba su huella; los tres tests que leen esa auditoría siguen pasando.
- **Coste y riesgo.** Talla M. Paso 1, riesgo bajo. Paso 2, medio: `tests/test_f10_receipt_contract.py:140-146`
  abre los ZIP de `originales/` y comprueba su sha256, así que esos 5 se quedan o el test se adapta en la misma PR.
  El cuarto toca cuatro workflows, 52 configuraciones de `territorios/*/config` y 12 herramientas: es cambio de CI y
  necesita el detalle del propietario. D-35 deja en R2 solo entradas mínimas, productos y auditorías: los lotes y
  las copias de entradas encajan mejor en un release. Impacto 3 y no 4: el coste medido son 13 a 15 s por checkout.

### D-2 · Gobernanza legacy: 35 MB y 355 ficheros por semana, 93 % sin cita viva (impacto 4)
- **Hoy.** Del 14 al 28-11 entraron en `legacy/` 710 ficheros y 70,2 MB. El 76 % de esos megas son 271 copias enteras
  del registro: `herramientas/numerar_registro.py:116` copia el fichero completo en cada numeración y el fichero
  crece (38 KB la primera copia, 214 KB la última), así que el coste es cuadrático.
- De 2.675 ficheros, **2.189 (141,8 MB) no los cita nada vivo**, ni siquiera una cabecera ANTERIOR.
- De 1.494 ficheros activos de texto, solo 570 llevan ANTERIOR: 307 apuntan a legacy (1 a un fichero que no existe),
  180 dicen «ninguna» y **82 ya apuntan a un commit o a una versión**. `GovernanceHeaders` comprueba 22 ficheros
  (17 de código y 5 documentos).
- **Corrección a lo anterior.** C-10 y la auditoría del 24-11 presentan legacy como el peso del repositorio. Medido,
  son 15,2 MB del clon: git comprime las copias casi iguales. Su coste real es árbol, búsquedas y lectura de agentes.
- **Propuesta en tres escalones**, aprobables por separado: (1) los ficheros que solo crecen (registro y plan) dejan
  de copiarse; (2) ANTERIOR pasa a `git:<sha>` y un test lo comprueba, solo
  en el siguiente cambio real de cada fichero; (3) se retira lo que nadie cita, con índice.
- **Criterio.** Tras una numeración real no aparece ningún fichero nuevo en `legacy/docs/`; `git ls-files legacy |
  wc -l` da menos de 550; `GovernanceHeaders` pasa y falla si se altera un sha a mano; la huella M05 es la misma
  antes y después.
- **Coste y riesgo.** Talla M. Es una regla del propietario: necesita su sí. Ya previsto como T-490 en el plan de
  mejora del 25-11, que D-214 dejó como propuesta; no está en `docs/PLAN.md`. Los escalones 1 y 3 no tocan la huella M05; el 2
  la cambiaría si se reescribe la cabecera de `modulos/05` o de su cierre de `ddd_core` (la huella es el sha256 de
  los bytes): nunca se reescriben cabeceras en bloque.

### D-3 · Tests: entre el 17 y el 18 % de las aserciones comprueba texto, no conducta (impacto 3)
- **Hoy.** 504 ficheros, 4.462 tests, 15.351 aserciones. Clasificación por importaciones:

| Qué protegen | Ficheros | Tests |
|---|---:|---:|
| Motor y núcleo (`ddd_core`, `modulos`, `ddd_motor2`, `ddd_ensemble`) | 143 | 1.553 |
| Herramientas y contratos | 160 | 1.008 |
| Una herramienta más texto de workflows | 85 | 1.180 |
| Solo texto de workflows (24) o de workflows y documentos (3) | 27 | 198 |
| Solo documentos y gobernanza | 34 | 196 |
| Solo HTML o JS del visor | 7 | 31 |
| Solo datos u otros, sin importar código | 48 | 296 |

- Entre 2.607 y 2.701 aserciones (17–18 %, según la expresión regular) son «este literal está en este texto». 116 ficheros (23 %) no importan código del proyecto.
  135 (27 %) leen `.github/workflows` y hay 43 copias de workflows antiguos en `tests/fixtures`.
- Ejemplo: `tests/test_workflows_principales_ligeros.py:34-37`, con 33 de 39 aserciones de ese tipo.
- 107 ficheros se llaman `test_tNNN_…`: dicen la tarea que los creó, no lo que protegen.
- **Por qué importa.** Ese test falla cuando se renombra un paso y no falla cuando el paso deja de funcionar. Con la
  migración de notación pendiente (T-313), cada renombrado arrastra decenas de tests sin cambio de comportamiento.
  No está medido cuántas PR han tenido que tocar tests de texto: por eso el impacto es 3.
- **Propuesta.** Un manifiesto de clasificación generado por un guion versionado (sin mover ficheros); regla para tests nuevos:
  importan código o analizan estructura; los 27 de solo workflows se sustituyen por actionlint más un test de
  estructura por familia; los de documentos, en un grupo que no bloquea las PR de motor.
- **Criterio.** Con ese mismo guion, la fracción de aserciones de texto baja a menos del 10 % sin perder ningún test de
  comportamiento; renombrar un paso de un workflow sin cambiar su comando rompe como mucho 3 tests.
- **Coste y riesgo.** Talla L. Confianza media: la clasificación es estática y un 21 % de las funciones queda sin
  determinar.

### D-4 · Del 58 % al 95 % de lo que devuelve una búsqueda cae en zonas congeladas (impacto 3)
- **Hoy.** `production_run_id` sale 1.148 veces y 1.092 están en legacy, registro, auditorías o fixtures;
  `p20-distritos`, 185 de 320; `TERRITORIAL_READY_PAIR_INCOMPATIBLE`, 84 de 112. No existe `.ignore`.
- **Propuesta.** Un fichero `.ignore` en la raíz con las zonas congeladas, que readmite con `!` los ficheros de
  legacy que producción usa (D-5). No borra nada. Para buscar en el archivo, `git grep`, que no lee `.ignore`.
- **Criterio.** `rg -c production_run_id` suma menos de 80 y `rg --no-ignore` sigue dando el total; la suite no cambia.
- **Coste y riesgo.** Talla S, riesgo bajo con esa salvedad: la búsqueda de los agentes no puede saltarse `.ignore`.
  Es la mejora más barata de este informe.

### D-5 · legacy mezcla archivo con piezas que producción usa (impacto 3)
- **Hoy.** 132 ficheros de legacy (4,75 MB) los cita código, workflows o configuración vivos; 42 más, solo tests.
  `.dockerignore` excluye `legacy/*` y readmite 16 ficheros uno a uno y una carpeta entera con otros 16
  (`legacy/workflows/retirados_20261031/`): 32 en la imagen. Las evidencias N08 fijan 7 rutas de legacy.
- **Propuesta.** Una lista generada `legacy/CON_CARGA.txt` y un test que falle si una cita apunta a una ruta ausente.
  Sin mover nada. Con esa lista, la limpieza de D-2 es mecánica.
- **Criterio.** El test falla al borrar un fichero con carga y pasa al borrar uno de los 2.189 sin cita.
- **Coste y riesgo.** Talla S. No mueve ni cambia contenido, así que no altera huellas.

### D-6 · Código fuera de la tubería, con lista (impacto 3)
- **Hoy.** De 384 ficheros de código (105.810 líneas): 20 sin ninguna cita (2.227 líneas), 9 solo en documentos
  (1.115) y 78 sin cita de código ni de workflows (16.553; 49 solo en su test y 6 con cita de configuración). Entre estos, 6 módulos de `ddd_core` de la familia `congreso_*` y
  `national_campaign_planner` (2.004 líneas). Amplía B-10, que dio el recuento sin lista. El código muerto
  del motor ya lo midió T-254 (D-85); lo nuevo aquí son las herramientas.
- Los 20 sin cita: las ocho `herramientas/auditar_*_m05.py` y `auditar_relevo_d25_2x2.py`,
  `auditar_compatibilidad_interanual_f10.py`, `aplicar_mejor_movimiento_topologico_m04.py`,
  `diagnosticar_puertas_congreso.py`, `extraer_candidaturas_boe.py`, `generar_config_bootstrap.py`,
  `reparar_propiedad_geojson_zip.py`, `validar_esquema_m06.py`, `validar_poblacion_ine_2026_aragon.py`,
  `ver_visor_v2_local.py`, `verificar_almacen_fuentes_local.py` y `receta_cierre.py` (raíz).
- **Propuesta.** Una PR por grupo, y un test de guardia: todo `.py` está citado por un workflow, por otro código o
  por una lista de herramientas de una sola vez con su motivo.
- **Criterio.** El test de guardia falla hoy con 29 nombres y pasa cuando los 20 se retiran y los 9 se retiran o
  entran en la lista; la huella M05 calculada con
  `herramientas/huella_checkpoint_m05.py` es la misma antes y después.
- **Coste y riesgo.** Talla M. Análisis por nombre: una carga con el nombre construido en ejecución se me escaparía.
  «Sin cita» no es «sin uso»: varias se lanzan a mano (por ejemplo `ver_visor_v2_local.py`).

### D-7 · No hay guardia de tamaño ni presupuesto del repositorio (impacto 3)
- **Hoy.** El protocolo de esta investigación pide «sin binarios ni ficheros de más de 1 MB»; nada lo comprueba.
  La auditoría del 09-10 metió 262 MB en una carpeta.
- **Propuesta.** Un test: ningún fichero de más de 1 MB fuera de una lista de excepciones que solo puede encoger.
- **Criterio.** Una PR de prueba con un fichero de 2 MB fuera de la lista deja el test en rojo.
- **Coste y riesgo.** Talla S. Sin esta guardia, lo que limpie D-1 vuelve a llenarse.

### D-8 · El reparto de la suite usa tiempos del 07-11 (impacto 2)
- **Hoy.** `tests/tiempos_ci.json` tiene 287 módulos (660 s). 226 de los 504 ficheros actuales no tienen tiempo y 9
  de los que lo tienen ya no existen. Cuatro módulos suman 254 s (38 %): `test_pre_m04_evidence_pipeline` (68,7 s),
  `test_codauto_preparation_contract` (67,3), `test_gestor_campana_nacional` (65,1) y
  `test_registro_electoral_comun` (52,6). Los 10 más lentos son el 63 %.
- **Propuesta.** La nocturna regenera el fichero desde su log y lo deja como artefacto (la PR la abre un
  implementador); se perfilan los cuatro de más de 50 s.
- **Criterio.** Menos del 5 % de ficheros sin tiempo; los cuatro módulos bajan de 254 s a menos de 100 s.
- **Coste y riesgo.** Talla M, riesgo bajo. Los ficheros sin tiempo pesan la mediana y nadie ha medido cuánto
  desequilibra eso los grupos: el daño es una hipótesis, de ahí el impacto 2.

### D-10 · Evidencia y datos de ejecución se guardan dentro de git (impacto 2)
- **Hoy.** `territorios/*/evidencia`: 2.686 ficheros y 32,2 MB que escriben los robots en `main`. `tests/fixtures`:
  2.213 ficheros, con árboles enteros congelados de 500 ficheros. Complementa B-5 con el recuento por carpeta.
  Desde el 16-11 solo entraron 21 ficheros nuevos de evidencia y 45 de fixtures (legacy 567, registro 204).
- **Propuesta.** Evidencia al archivo, con un índice por territorio en git (una línea por ejecución con su huella).
- **Criterio.** La siguiente campaña autorizada de un territorio cambia como mucho 3 ficheros en su carpeta de
  evidencia (no se lanza una solo para comprobarlo).
- **Coste y riesgo.** Talla L, riesgo alto si se hace de golpe: lo leen el dashboard, la publicación y la selección
  de checkpoints. Necesita diseño aprobado.

### D-9 · Raíz y carpetas (impacto 2)
- **Hoy.** 25 ficheros en la raíz; 5 sin ninguna cita (`PR_BODY.md`, `N1-CANDIDATO.md`, `SUBSANACION_N1.md`,
  `LEEME_KIT.md`, `receta_cierre.py`). 8 ficheros `.lock`. 30 carpetas de primer nivel, tres de un solo fichero.
  `docs/AUDITORIAS` y `docs/auditorias` solo se distinguen por mayúsculas: en un Mac son la misma carpeta.
- **Propuesta.** Unir las dos carpetas, retirar los 5 sueltos y hacer el resto en la ventana de T-313.
- **Criterio.** Ninguna carpeta difiere de otra solo en mayúsculas; 15 ficheros o menos en la raíz.
- **Coste y riesgo.** Talla S. Los `.lock` están citados en 9 workflows, el Dockerfile y 8 tests.

## 5. Estructura objetivo y qué rompería cada paso

Objetivo, sin renombrar el motor: `ddd_core/`, `modulos/`, `ddd_motor2/`, `ddd_ensemble/`, `paquetes/` (motor);
`herramientas/` (solo lo que cita la tubería, más una lista de una sola vez); `tests/` (con manifiesto de
clasificación); `configuracion/`, `territorios/<id>/config` (contratos); `docs/` (texto vivo, sin binarios);
`legacy/` reducido a los ficheros con carga; `.github/`, `.claude/`. Fuera de git, con índice dentro: entradas,
auditorías con binarios, lotes, evidencia de ejecución.

| Paso | Qué rompería | Cómo evitarlo |
|---|---|---|
| `.ignore` (D-4) | Los tests, nada. La búsqueda de los agentes deja de ver legacy | Readmitir con `!` los ficheros con carga; `git grep` para el archivo |
| Guardias de tamaño y de citas (D-5, D-7) | Nada: son tests nuevos | Lista de excepciones igual al estado de hoy |
| Dejar de copiar registro y plan (D-2.1) | Tests de `numerar_registro`; `gobernanza.md`; `CONTRIBUTING.md` punto 3 | Misma PR; `README` y los 5 documentos canónicos de R015 no entran en la exención |
| Retirar binarios sin lector (D-1) | 3 tests leen `F04_F10_20261009`; uno abre los 5 ZIP de `originales/` | Dejar carpeta, JSON y esos 5 ZIP, o adaptar el test |
| ANTERIOR a `git:<sha>` (D-2.2) | `GovernanceHeaders` exige ruta en legacy; el sha anterior no está en un clon sin historia | Adaptar el test; comprobación completa en la nocturna con historia, y solo formato en la PR; no reescribir cabeceras del motor (huella M05) |
| Retirar legacy sin cita (D-2.3) | 57 rutas citadas por tests, 32 de la imagen, 7 de N08, 7 de R015 | Están en la lista de carga de D-5: no se tocan |
| Retirar código sin cita (D-6) | Tests de las 78 herramientas; con la regla actual, cada borrado pide copia en legacy | Aprobar antes D-2; comprobar la huella M05 antes y después |
| Mover tests a carpetas | `repartir_tests.py` (un solo nivel), 47 nombres en workflows, 13 en reglas y skills, 49 importaciones entre tests, 4 rutas en N08 | No mover: clasificar con manifiesto |
| `inputs/partes` fuera (D-1.4) | 4 workflows, 12 herramientas, 52 configuraciones | Paso de descarga verificada; última fase, con diseño |

**Huellas.** Ningún paso de las tres primeras filas, ni D-1, ni D-2.1, ni D-2.3 toca `ddd_core`, `modulos/04` ni `modulos/05`:
la huella M05 (cierre de importaciones desde `modulos/05`) y la evidencia pre-M04 no cambian. D-2.2 sí la cambiaría
si se reescribiera la línea ANTERIOR de un fichero del motor: solo se aplica con el siguiente cambio real. Las evidencias N08
fijan huellas de 26 rutas (7 de legacy, 6 de `ddd_core`, 5 de herramientas, 4 de módulos y 4 de tests): esas 26 no
se mueven ni se editan en ningún paso.

## 6. Camino en tres pasos

1. **Esta semana (sin decisión del propietario sobre reglas).** `.ignore` (D-4), guardia de tamaño (D-7), lista de
   legacy con carga (D-5), unir `docs/auditorias` y retirar los 5 sueltos (D-9), manifiesto de tests (D-3.1).
   **Prueba:** `rg -c production_run_id` suma menos de 80; los dos tests de guardia están en la suite y fallan con
   una PR de prueba; la suite coincide por nombre con `origin/main`.
2. **Este mes (con su sí a D-1 y D-2).** Dejar de copiar registro y plan, retirar los binarios sin lector, retirar
   legacy sin cita y los 29 ficheros de código sin cita, regenerar `tiempos_ci.json`.
   **Prueba:** árbol de menos de 450 MB; `git ls-files legacy | wc -l` menor de 550; `git ls-files | wc -l` menor de
   12.500 (hoy 14.483); la numeración de una PR no añade ficheros a `legacy/`.
3. **Este trimestre (con diseño).** `inputs/partes` y evidencia de ejecución fuera de git con índice; tests de
   workflows por estructura; decidir una a una las 78 herramientas sin cita de código ni de workflows.
   **Prueba:** árbol de menos de 320 MB; aserciones de texto por debajo del 10 %; la siguiente campaña autorizada
   cambia como mucho 3 ficheros de evidencia.

## 7. Lo que no pude comprobar

- **Coste por semana con el historial.** El clon local no tiene historia anterior al 16-11 (`git rev-parse
  --is-shallow-repository` da `true`), así que el ritmo de legacy lo medí por la fecha de los nombres de fichero.
  Con `git log --diff-filter=A --since=14.days -- legacy/` en un clon completo se confirma. El revisor lo midió en
  `origin/main` desde el 16-11: 567 ficheros nuevos en legacy en 12 días, coherente con el ritmo por nombres.
- **Tamaño real de un clon nuevo y su tiempo.** No cloné (medio giga en una máquina compartida). Se mide con
  `time git clone --depth 1` desde un runner.
- **Fracción exacta de tests de texto.** Es análisis estático; el 21 % de las funciones quedó sin determinar.
  Con cobertura por test (`coverage` con contextos) se sabe qué tests no ejecutan ni una línea del proyecto.
- **Por qué son lentos los cuatro tests de más de 50 s.** No ejecuté la suite (límite de CPU). Con
  `python -m cProfile -m unittest tests.<módulo>`.
- **Carga dinámica.** La lista de código sin cita es por nombre de módulo; no detecta nombres construidos en ejecución.
- **Fuentes externas.** Citadas de memoria: `docs.github.com` y `testing.googleblog.com` no son accesibles desde la
  red de esta sesión. Convendría abrirlas antes de citarlas fuera.

## 8. Objeciones (D-216)

- **A la regla de copia en legacy.** No da lo que promete: cubre el 38 % de los ficheros, se prueba en 22, tiene un
  predecesor roto y 82 ficheros ya la sustituyen por un commit. Lo que el propietario quiere, saber qué versión
  había antes y por qué cambió, lo dan las cabeceras más git, con menos trabajo y sin errores.
- **A D-82 («lo antiguo se archiva, no se borra»).** Retirar del árbol con índice de sha y commit es archivar, no
  borrar: el contenido sigue en el historial. Conviene que el propietario lo confirme con esas palabras.
- **A las auditorías anteriores.** Señalaron legacy como el peso del repositorio. Medido en el clon, pesa 15 MB; los
  binarios de entrada y de una auditoría de octubre, 220 MB. El orden de la limpieza cambia.
- **Al encargo.** Pide mover a una estructura objetivo. Mover tests o módulos cuesta más de lo que da: 47 nombres en
  workflows, 26 rutas en N08. Propongo clasificar y retirar, no mover, salvo en la ventana ya aprobada de T-313.

## 9. Verificación independiente (28-11)

Cada hallazgo se reprodujo con comandos propios sobre el árbol y se comparó con `origin/main` (548968c47) y con
`docs/PLAN.md`. Ninguno está arreglado ya en `main` ni es una tarea T-xx del plan. El detalle está en el campo
`verificacion` del JSON.

| Id | Veredicto | Qué cambia |
|---|---|---|
| D-1 | CORREGIDO | Estudios 67 MB y 80 %; un test abre 5 ZIP de la auditoría; la comprobación de huellas va a la nocturna; impacto 4 → 3 |
| D-2 | CORREGIDO | `GovernanceHeaders` cubre 22 ficheros, no 25; 655 copias del registro; 1 predecesor roto, no 2; el escalón 2 puede cambiar la huella M05 |
| D-3 | CORREGIDO | Aserciones de texto entre el 17 y el 18 %; el guion debe estar en el repositorio; el coste no está medido; impacto 4 → 3 |
| D-4 | CORREGIDO | Cifras confirmadas; `.ignore` debe readmitir el legacy con carga, porque la búsqueda de los agentes no puede saltárselo |
| D-5 | CORREGIDO | En la imagen entran 32 ficheros de legacy, no 16 |
| D-6 | CORREGIDO | 384 ficheros revisados; 8 `auditar_*_m05`, no 10; de los 78, solo 49 aparecen únicamente en tests; solapa con T-254; criterio reescrito |
| D-7 | CONFIRMADO | — |
| D-8 | CORREGIDO | Cifras confirmadas; el desequilibrio no está medido; un robot no abre la PR; impacto 3 → 2 |
| D-10 | CORREGIDO | Las existencias se confirman, el crecimiento no (21 ficheros de evidencia desde el 16-11); impacto 3 → 2 |
| D-9 | CONFIRMADO | — |

## 10. Descartados en la verificación

Ningún hallazgo se descarta entero. Se retiran estas afirmaciones sueltas:

- «Tres tests leen JSON de esa auditoría, así que solo se retiran los ZIP» (D-1): `tests/test_f10_receipt_contract.py`
  abre los ZIP de `originales/` y comprueba su sha256.
- «`docs/ESTUDIOS`, unos 60 MB» y «79 %» (D-1): son 67 MB y 80 %.
- «`GovernanceHeaders` comprueba 20 ficheros de código y 5 documentos» (D-2): son 17 y 5.
- «Dos predecesores rotos» (D-2): es uno; el de `visor/v4/comprender.html` existe.
- «D-2 no toca huellas M05»: cierto para dejar de copiar y para retirar legacy; no para cambiar la línea ANTERIOR de
  un fichero del motor.
- «Parte de lo que encarece la CI y las PR» (D-3): no está medido.
- «`.dockerignore` readmite 16 ficheros» (D-5): readmite además una carpeta entera con otros 16.
- «Las diez `auditar_*_m05.py`», «391 ficheros» y «78 solo en su test» (D-6): son ocho, 384 y 49.
- «La evidencia crece dentro de git» (D-10): desde el 16-11 entraron 21 ficheros de evidencia; lo que hay es
  existencia acumulada.
- «El clon local no permite medir por semana» (D-10 y sección 7): desde el 16-11 sí se puede, con `git log
  --diff-filter=A`.
