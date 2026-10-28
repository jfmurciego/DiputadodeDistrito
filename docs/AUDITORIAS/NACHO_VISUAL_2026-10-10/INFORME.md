# DDD — Validación aislada del prototipo visual de Nacho

Versión: 1.0.0 · Fecha: 2026-10-10 · Alcance: validación local exclusivamente visual.
Estado: BLOQUEADO · Cambios: expediente nuevo de identificación, intentos de navegador y cotejo de datos.
Motivo: encargo Work tras GO_ACOTADO de la investigación. Origen: nuevo documento; sin predecesor sustituido.

**Dictamen: BLOQUEADO.** No se logró una sesión operativa de navegador ni una captura del prototipo. Carga real, renderizado, controles, consola y legibilidad siguen sin acreditar. El cotejo estático de entradas y artefactos pasa, pero no satisface la puerta visual solicitada.

## Prototipo exacto y conservación

Worktree `/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos`; rama `codex/distritos-autonomicos`; base/HEAD `42163cd8cebd120db9ab9fd1329c32ccdd87cf36`.

El candidato informativo es [diagnostico.html](../NACHO_VALIDACION_2026-10-10/visualizacion/diagnostico.html): mapas SVG A/B, tablas A/B/C, explicación de Pareto y procedencia. Se acompaña de [gallery/index.html](../NACHO_VALIDACION_2026-10-10/visualizacion/gallery/index.html), galería DDD generada con MapLibre, filtros y selección de alternativas. No se valida el visor productivo ni se reconstruye el prototipo.

**No existe commit del artefacto:** la carpeta original está sin seguimiento en Git. El HEAD es su base de código, no una identidad suficiente del prototipo. [IDENTIDAD.json](IDENTIDAD.json) registra hashes exactos de HTML, JS, CSS, datos y geometrías. El último commit que afecta al generador `ddd_ensemble/gallery.py` es `cb9b314350401fcc2f7003c65d4b4c0c18eaada5`.

| Pieza | SHA-256 |
|---|---|
| Diagnóstico offline | `bc358fb31d51465417e00c2820e0db7db46ba1dd7a9c3e932cecedeb2180d4e7` |
| HTML galería | `bdb698cfbc3d116bcf50a137b4c7eb12c0d3e036982579708169e9c1fce2f94d` |
| JS galería | `78850c345c48b487fa23fd8d5d2b89d220afa19d83ea1f04e564bb5d1f6e8ca9` |
| Datos galería | `35abdaf03d9bad98060fdafa39bc6a5c5e96e02e9167e96c78411504d661a2a6` |
| Resultados congelados | `3ef8b107c33fa923301fd56df1be83a82d0e8a726069fd54efa678d2a152e684` |

Los 201 archivos cubiertos por el manifiesto original se comprobaron antes de actuar y en el cotejo final. [BASELINE.json](BASELINE.json) conserva identidad Git, estado previo y hashes de 2.098 archivos, incluida la investigación y el trabajo previo de Madrid. No se reescribió ninguna evidencia anterior. La revisión [REVISION.md original](../NACHO_VALIDACION_2026-10-10/REVISION.md) conserva su GO_ACOTADO y sus exclusiones; no se extiende ese dictamen al navegador.

## Datos e información cotejada

Se reutilizan los tres candidatos congelados de la investigación: 16 celdas sintéticas, población total 4.000, K4, objetivo 1.000, floor800, cap1.750 y banda dura experimental800–1.200 (±20%). Perfil `controlled` y semilla0 son metadatos de fixture. El plano SVG es cartesiano local; el GeoJSON web usa una ilustración de 1m/unidad anclada cerca de −3,7/40,4. **No representa distritos reales de Madrid ni una fuente oficial.**

| Candidato | Poblaciones por distrito0–3 | Incumplimientos | Estado congelado |
|---|---|---|---|
| A_lower_L1 | 1.150 / 950 / 950 / 950 | Ninguno | Admisible; máximo15%, L1=300 |
| B_lower_max | 1.100 / 1.100 / 900 / 900 | Ninguno | Único Pareto/shortlist; máximo10%, L1=400 |
| C_hard_invalid | 2.000 / 100 / 950 / 950 | cap:0, floor:1, tolerance:0, tolerance:1 | Rechazado; fuera de selección |

[DATOS_RESULTADO.json](DATOS_RESULTADO.json) y [validar_evidencia.py](validar_evidencia.py) acreditan estáticamente: población por sección/asignación, tres hashes de asignación, 32 rectángulos SVG A/B, 12 filas HTML/CSV, límites/desviaciones, cero municipios divididos, cuatro causas C, métricas/metadatos de tarjetas concordantes con reportes, assets web copiados idénticos y enlaces locales existentes. No se invocó ensamblador, generador de distritos ni motor.

El diagnóstico distingue expresamente resultado sintético, incumplimiento y ausencia de certificación/promoción. `Outlier=true` de C describe desviación y se acompaña de fallos; **no concede una excepción**. No hay una excepción acreditada en este fixture: su visualización no puede darse por comprobada. La selección técnica B sigue separada de `PENDING_FIELD_REVIEW` y no cambia scores. La galería exporta el literal `SELECTED_FOR_PROMOTION`; esa solicitud no es una autorización ni certificación. No se efectuó ninguna descarga de selección.

## Navegador real: intentos y puerta fallida

Se intentó Firefox157.0.1 con perfil temporal aislado, headless y el diagnóstico original por `file://`. No se desactivó su sandbox ni se instaló software. [BROWSER_ATTEMPT.json](BROWSER_ATTEMPT.json) conserva comando, tiempo y resultado; [firefox.stderr.log](firefox.stderr.log) conserva la salida. El proceso terminó por SIGABRT (`returncode=-6`) en 0,315s y no creó `diagnostico.png`. El [extracto del crash](firefox.crash.extracto.log) muestra `EXC_CRASH (SIGABRT)` y la pila de inicialización macOS HIServices/XUL. No identifica una causa más específica; atribuirlo con certeza a un defecto del HTML o a un permiso concreto sería infundado.

Chrome no existe actualmente en `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`. Se conserva, sin alterarlo, el [log anterior Chrome](../NACHO_VALIDACION_2026-10-10/visualizacion/gallery_dom.stderr.log), donde sí constaba bootstrap/crashpad EPERM. Ese fallo histórico no se presenta como un intento nuevo.

Como alternativa instalada, Safari16.6.1: `/usr/bin/safaridriver --port 8766` terminó con código1 en 0,843s, sin diagnóstico stdout/stderr y antes de solicitar sesión. [SAFARI_ATTEMPT.json](SAFARI_ATTEMPT.json) y sus dos logs conservan el resultado. No se atribuye el fallo a «automatización remota desactivada», pues no hay evidencia de esa causa. No se cambiaron preferencias del usuario ni permisos del entorno.

Se intentó después abrir las aplicaciones en modo normal. Firefox157.0.1 se inició directamente con perfil temporal y terminó con SIGABRT (`returncode=-6`) a los0,091s, también sin captura. La apertura corregida `/Applications/Safari.app` con el HTML local falló en LaunchServices con `-10822 kLS...ServerCommunicationErr`: el proceso de registro/recent items no está disponible. El intento previo usando una URL `file://` con `open -a Safari` formó una ruta incorrecta; no se cuenta como carga de página. [GUI_ATTEMPTS.md](GUI_ATTEMPTS.md) conserva los comandos y resultados. Son bloqueos del lanzamiento de aplicaciones del entorno; no prueban un fallo del prototipo.

**Capturas: ninguna obtenida. Consola de página: no comprobada.** Los logs de lanzamiento son evidencia del bloqueo, no sustituyen capturas del prototipo. No se generaron imágenes para simular renderizado ni se reutilizó la simulación DOM/MapLibre como prueba de navegador.

| Comprobación solicitada | Resultado de esta sesión |
|---|---|
| Carga offline SVG / carga galería y CDN | BLOQUEADO: sin navegador operativo; CDN no solicitado |
| Mapas A/B, zoom, desplazamiento, cambio de alternativa | NO EJECUTADO en navegador |
| Leyenda | No existe leyenda explícita en el código de ninguna pieza; SVG tiene etiquetas sN/dN; equivalencia visual pendiente |
| Selección de distrito/popup | No está implementada en estas piezas; no se inventó ni se confundió con selección de candidato |
| Fronteras y mostrar/ocultar C | Controles presentes en diagnóstico; ejecución real NO COMPROBADA |
| Perfil/Pareto, selección A/B, responsable/justificación, exportación | Controles presentes en galería; ejecución real NO COMPROBADA |
| Información frente a datos | PASS ESTÁTICO delimitado en DATOS_RESULTADO.json |
| Excepciones | NO EVALUABLE: fixture sin excepción acreditada |
| Consola, legibilidad, vista estrecha, teclado | NO COMPROBADO en navegador |

## Hallazgos y corrección mínima propuesta

1. **Bloqueo ambiental de lanzamiento.** Remedio: repetir únicamente la validación visual en un entorno local con navegador operativo y captura/consola disponibles, manteniendo estos mismos hashes. No se requiere ni se propone tocar el motor. La causa precisa del aborto Firefox y de la salida SafariDriver permanece sin determinar.
2. **Riesgo de legibilidad identificable en el código.** Todos los textos SVG son blancos; contraste calculado frente a verde `#2a9d8f`:3,32; amarillo `#e9c46a`:1,67; naranja `#f4a261`:2,06, frente a10,08 en azul oscuro. Es un hallazgo estático, sin juicio acreditado sobre una captura. Corrección mínima propuesta: texto oscuro en los tres fondos claros, preservando texto blanco en azul oscuro; verificar después en navegador. No se aplicó el cambio al prototipo existente.
3. **Leyenda explícita ausente.** Si se necesita interpretar colores sin las etiquetas de cada celda, proponer sólo una clave estática color→distrito0–3 consistente entre A/B. La selección individual de distritos sería una ampliación funcional, no un requisito implementado que haya fallado; queda fuera de este encargo.

No se ha identificado por lectura una dependencia del prototipo respecto a cambios en M04/M05. Las piezas consumen HTML/JSON/GeoJSON congelados. No se reabrió la investigación algorítmica ni se ejecutó A2/A3.

## Utilidad, pendientes y entrega

La utilidad concreta conservada es comparar simultáneamente población por distrito y límites entre alternativas, ver las causas granulares del rechazo C y explicar la selección B sin cambiar el ranking. Esa aportación informativa tiene evidencia estática; su utilidad visual práctica sigue pendiente.

Para obtener **APTO PARA PROPONER INTEGRACIÓN VISUAL** faltan navegador operativo, capturas reales de A/B y C, comprobación de controles existentes, consola y legibilidad. [README.md](README.md) permite reproducir el cotejo y explica el procedimiento visual pendiente. No se declara integración realizada ni se aprueba el candidato de Madrid: su revisión independiente específica sigue siendo una puerta separada.

Cambios limitados a este expediente nuevo. Sin commit del prototipo o de la entrega; archivos conservados en disco. Push / PR / merge / workflows / ejecución territorial / publicación / modificación M04-M05 / A2-A3: **NO**. La política de versiones se aplica creando documentación/script nuevos con origen y versión; no se sustituye ningún fichero funcional ni se necesita un predecesor en legacy. CI territorial no procede para esta evidencia estática y no se ejecutó.
