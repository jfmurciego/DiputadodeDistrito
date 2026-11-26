<!--
Nombre: Plan de trabajo DDD
Versión: 1.0.78
Fecha: 2026-11-26
Alcance: Cola de tareas para chats implementadores y operadores
Estado: candidato
Cambios/motivo: D-205 a D-214 (mapa V4 y V5, bloques, sin firmas de IA, auditoría); T-456 a T-500; paquete de 2 días (26-11)
Anterior: legacy/docs/PLAN_v1.0.77_20261124.md
-->

# Plan de trabajo — Diputado de Distrito

## Reglas para todos los chats
- Un chat = una tarea. Coge la primera tarea libre de la cola cuyas dependencias estén en «Tareas hechas».
- **Una PR por objetivo, no por tarea** (07-11): las tareas de un mismo chat sobre ficheros propios van en una sola PR.
  Se separa solo si toca ficheros compartidos (motor, workflows, política) o si debe poder revertirse sola. Evita
  cadenas largas: con squash, cada fusión deja en conflicto a la siguiente y repite la CI (~15 min por eslabón).
- Respeta `CLAUDE.md` (topónimos en español, mínimo consumo, coordinación entre sesiones, gobernanza VERSIÓN/legacy).
- El implementador pasa la suite local completa (`python -m pytest -q`) antes de abrir la PR.
- Fusiona el propietario. Nadie lanza ejecuciones productivas ni publica sin su permiso explícito.
- Nada de vigilar runs en el chat: los lanzamientos largos se hacen con scripts en el Mac del propietario
  (rama `lanzadores-mac`).
- Al terminar: mover la tarea a «Tareas hechas» con su PR o run y, si hubo lección cara, `/cierre-sesion`.
- Coordinación: el chat planificador («DDD Plan») lista, describe y asigna; no implementa. Cada chat le manda una
  línea (`send_message`) al abrir PR, lanzar run o cerrar tarea: «T-xx · qué · PR/run · siguiente · bloqueo», y le
  avisa antes de tocar ficheros compartidos (workflows, política, catálogo, `herramientas/`, `modulos/`,
  `ddd_core/`, este plan). Antes de lanzar, preguntar si otro chat ya lo hizo (01-11: Huelva/Valencia duplicadas).
- Las órdenes de lanzar o fusionar las confirma el propietario en el chat que ejecuta, no por mensaje entre sesiones.
- Chat operador único: es el único que lanza ejecuciones (00, activaciones, publicaciones). Los implementadores no
  lanzan; piden el lanzamiento al planificador, que lo pasa al operador. El propietario da permiso por lote, una vez,
  en el chat operador.
- El operador identifica cada run por su territorio (entrada TERRITORY del job «Planificar»), nunca por el orden
  de lanzamiento, y cuenta también los encadenados de github-actions[bot]. No relanza un territorio con un run en curso.
- Primero en local: ninguna 00 sin evidencia del motor en local (o del diagnóstico automático de T-14). En un lote,
  primero un territorio de prueba y luego el resto.
- Infraestructura (workflows, ruleset, credenciales): se valida con una sola ejecución antes de abrir paso al resto.
- `docs/PLAN.md` solo lo edita el planificador; el número de `REGISTRO_DE_CAMBIOS.md` lo asigna el planificador al
  abrir la PR. Los chats le mandan su cierre de tarea y él lo anota.

## 0a. Plan vigente por temas (10-11)

Esta sección manda sobre las secciones 0 a 3, que quedan como historia. El planificador habla con el propietario por
temas y objetivos; las tareas las desglosa y sigue el Coordinador (D-39). Lanzar, publicar y borrar: solo el Operador,
con frase del propietario en su chat.

### Temas y objetivo de «verde»
| Tema | Objetivo | Estado (10-11) |
|---|---|---|
| Motor nuevo («el motor que demuestra», D-32, D-48, D-57) | Paquete nuevo al lado del actual; releva al viejo en el corte 5.0.0, por decisión del propietario | Competición aceptada en los 71: 71 válidos, mejora 21, empata 50, empeora 0, reproducible bit a bit, 5,6 veces más tiempo. Relevo en espera del piloto de naturalidad; pendientes: núcleos cerrados en el certificador, enumeración exacta en territorios pequeños, regla pública de elección |
| Ejecución autonómica (19) y nacional (52) | Territorial, electoral, ensemble 10 y 25 en verde; mapa de 350 completo | Territorial y electoral publicados; ensemble 25 habilitado en el 06; 13 comunidades bloqueadas por puentes y exención por partición hasta el motor nuevo |
| Gestor de campañas | Una orden lanza todo: nacional y autonómico, con o sin ensemble, con histórico | Campaña completa en seco e histórico conectados (T-123, T-130, T-133) |
| Histórico desde 2011 | 6 generales validadas y autonómicas de las 19 comunidades, cada una con su calendario (D-40) | Generales: datos 52 × 6, validación en curso; autonómicas: calendario y 3 comunidades (T-121, T-131) |
| Visor | v2 completo (electoral, territorial, secciones) publicado y verificado desde fuera; v1 intacto (D-26) | Código en main; publicación pendiente |
| Generales del 29-11-2026 | Camino listo para cuando Interior publique; resuelta la cuestión del censo | Nota del censo (T-129); sin datos de Interior no es un rojo |
| Credibilidad | Primera versión publicada con DOI | Metadatos y guía listos (T-127, D-28); Zenodo activado por el propietario |
| Archivo R2 | Solo entradas mínimas, productos y auditorías; sin estados redundantes (D-35) | Lista de poda aceptada (234 claves, 26 GB); herramienta de poda con simulación (T-145) |
| Notación de territorios | AUT01-AUT19 y NAC01-NAC52 con nombre en español (D-36) | Tabla maestra, inventario y capa visible en curso; identificadores internos, pendientes de plan |
| Notación de fases | P00 a P60 en decenas, camino único, archivo continuo ARC (D-37, D-47) | Solo ideas (borrador v5); se aplica en el corte 5.0.0 (D-45) |
| Lista de Actions | Solo lo que lanza el propietario, más un automático y las excepciones aceptadas (D-38, D-55, D-56) | De 36 a 33 ficheros; objetivo 23-24 tras la consolidación; los retirados desaparecen al borrar sus ejecuciones (D-58) |
| Temas nuevos (10-11) | Autorización por campaña (D-41), coste y presupuesto, uso y accesibilidad del visor, otros ámbitos en preparación (D-42), README (D-43) | Encargados al Coordinador |

### Decisiones del propietario (09 y 10-11)
- D-26. Visor v2 en `/v2/`, en paralelo con v1; prioridad máxima; con vista territorial y secciones censales.
- D-27. Retirar del registro del visor las dos entradas de `congreso350_valladolid` (excepción a «solo adición»); el mapa de 350 nunca se publica.
- D-28. Versión del proyecto 4.9.0. Zenodo: autor «Jesus», afiliación «Independent researcher»; el flujo de publicación no cambia.
- D-29. No se regenera el mapa de 407 por el cambio de motor 7.4.4.
- D-30. Ensembles: se arranca con un territorio de prueba; Barcelona entra con su exención (08073); se publican el hemiciclo y los ensembles de La Rioja y Sevilla (cierra D-7).
- D-31. Plan «todo verde» en ejecución autonómica y nacional, Gestor, histórico y ensembles 10 y 25; el ensemble 50 queda fuera del proyecto por ahora.
- D-32. Motor: opción B (endurecer) con la batería primero, y motor nuevo con los pilares certificado, universo de mapas, semilla pública, competición de generadores, movilidad y estabilidad. Sin retos ciudadanos. El motor de producción no se toca hasta el relevo, que decide el propietario.
- D-33. Donde el espacio de planes es pequeño (Álava, K ≤ 3) se enumera de forma exacta; no se rebajan los umbrales de calidad.
- D-34. Movilidad: piloto en 5 provincias como indicador, sin peso en la decisión.
- D-35. R2: poda de lo redundante con lista aprobada; la batería archiva solo la entrada mínima por territorio.
- D-36. Notación de territorios AUT01-AUT19 y NAC01-NAC52, siempre con el nombre en español; la migración de identificadores internos se decide con un plan de riesgos.
- D-37. Notación de fases: tema en fase de ideas; ninguna PR. Borrador v4: camino único (el territorio es un criterio), archivo continuo, publicación académica como P70, histórico dentro de P40, alternativas dentro de P33. Sustituido en la numeración por D-47.
- D-38. Lista de Actions limpia: sin guiones, subrayados ni desactivados; historial en `docs/HISTORIAL_WORKFLOWS.md`; la lista de borrado son los 222 runs de los 12 desactivados.
- D-39. El planificador trata con el propietario temas y objetivos, sin recados del Coordinador ni del revisor; las tareas son del Coordinador. Los mensajes entre sesiones nunca son permiso para lanzar.
- D-40. Histórico desde el 1-1-2011: las 6 generales y las autonómicas de cada comunidad con su propio calendario de legislaturas.
- D-41. Circuito de permisos: autorización por campaña. Una frase del propietario en el chat del Operador cubre una campaña definida (qué se lanza, territorios, tope de coste, caducidad y lo que queda fuera); dentro de esos límites el Operador no vuelve a preguntar.
- D-42. Otros ámbitos (municipales, europeas y Ecuador): solo preparar notas de fuentes y reglas; nada que necesite el motor.
- D-43. Se actualiza el README del repositorio. Corregido por D-51: la versión del proyecto se mantiene en 4.9.0.
- D-44. Núcleo único de reglas, criterios (provisionales hasta que la batería mida cuántos territorios cambian de veredicto): la tolerancia de población es un objetivo y los límites duros son solo suelo y techo; el máximo de distritos mixtos por municipio partido lo fija el contrato, con 1 por defecto; que un distrito no cruce provincias es obligatorio y explícito en el contrato; la exención del suelo por partición solo vale si todas las particiones del distrito están exentas; se enumeran todos los planes con un límite de esfuerzo y, si no termina, se muestrea.
- D-45. Renombrado del ciclo completo (solo estrategia, sin ejecutar): un único corte, coincidente con el relevo del motor, en el que todo se regenera ya con la notación de territorios, la de fases y los nombres nuevos de productos; ese corte es la versión 5.0.0. Lo anterior conserva su nombre como historia y no se reescribe; una tabla de equivalencias hace de traductor.
- D-46. Tope de gasto: 15.000 minutos de ejecución por semana, con aviso al 70 % y sin corte automático.
- D-47. Notación de fases (borrador v5, sigue en ideas y sin ejecutar hasta el corte 5.0.0): cadena sin huecos P00 Campaña, P10 Fuentes, P20 Base territorial, P30 Distritos, P40 Resultados electorales, P50 Publicación y P60 Publicación académica. El archivo no es una fase: es el servicio continuo ARC, con ARC-E (entradas verificadas, permanente), ARC-C (puntos de control, temporal) y ARC-P (productos y auditorías, permanente).
- D-48. Primera versión del motor nuevo: competición entre el canónico y GerryChain bajo el núcleo único de reglas, con semilla pública, quedándose con el mejor plan por territorio (nunca peor que el canónico). Evidencia de la batería: GerryChain desde la semilla canónica es válido en 71 de 71 y, con la mejor de 5 semillas, mejora 19, empata 45 y empeora 6; el arranque genérico por árboles no basta en 41 territorios, así que el constructor actual sigue como proveedor del punto de partida. Líneas de fondo: certificador con modelo ligero y constructor de semillas sobre el núcleo.
- D-49. Comprobaciones automáticas (frase del propietario en el chat del Coordinador): se cancelan las superadas en `main`; los apuntes de los robots pasan solo la comprobación de integridad, con la batería completa cada noche; todo cambio de código sigue exigiendo la batería completa.
- D-50. Semilla pública: sha256 del padrón y del seccionado oficiales de la edición, más el territorio.
- D-51. La versión del proyecto se mantiene en 4.9.0; el README lleva revisión propia.
- D-52. Autorización por campaña (D-41): se prepara como propuesta que el propietario revisa antes de fusionar (frase en el chat del Coordinador).
- D-53. Fusión automática y forense: se revisan en solo lectura; no se renombran ni se tocan sin autorización expresa.
- D-54. Identificadores internos AUT/NAC: se prepara el plan de migración y riesgos; se ejecutaría en el corte 5.0.0. La capa visible también espera al corte (D-45).
- D-55. Lista de Actions: el revisor de PR queda como flujo aparte, con nombre sin «_»; la lista queda en 22 elementos tras la consolidación. La regla activa de protección de `main` exige el check `veredicto`.
- D-56. Lista de Actions: se aceptan como excepción cuatro piezas internas con nombre «Interno · …» (generación territorial, publicador del sitio, incorporación electoral y puerta de validación); no se integran en quien las llama. Se revisan en el corte 5.0.0.
- D-57. El relevo del motor espera: el propietario quiere más pruebas y distritos más naturales. Piloto de naturalidad en seis territorios con tres funciones de calidad (solo población; población y, a igualdad, menos partidos judiciales y comarcas partidos y mejor forma; lo anterior con el grafo ponderado por vínculo y geografía física). Decide con los mapas delante. Condiciones previas al corte que siguen: núcleos cerrados en el certificador, enumeración exacta en territorios pequeños y regla pública de elección escrita.
- D-58. Respuestas del propietario (10-11, en el chat del Coordinador): sí a la poda del archivo (234 claves) y al borrado de las ejecuciones de los flujos retirados (222 y 844), que ejecuta el Operador con su frase; Zenodo: el propietario comprueba el DOI y el mapa de 350 se describe como «en desarrollo»; las descargas manuales las hace él; la naturalidad se decide con los mapas delante. Se dejan como están: fusión automática y forense (no se tocan), autorización por campaña (en borrador hasta su revisión) y publicación del visor (no se publica hasta que lo diga).
- D-59. Medición de uso del visor: Cloudflare Web Analytics, sin cookies. Se prepara sin publicar; el propietario crea el sitio y aporta el identificador.
- D-60. Corte 5.0.0, recomendaciones vigentes (`docs/ESTUDIOS/T170_MIGRACION_IDS/`): no cambiar la capa visible antes del corte; sufijo «-350» para el mapa de 350; nueve territorios duplicados entre AUT y NAC; primera prueba de la migración: el motor con identificador viejo y nuevo y la misma semilla debe dar el mismo mapa bit a bit.
- D-61. Especificación del corte 5.0.0 (`docs/ARQUITECTURA/CORTE_5_0_0.md`), decisiones cerradas: P20 Base territorial y P30 Distritos son dos flujos visibles y separados; la batería del motor es visible, bajo demanda, con código VER, fuera de las fases; el archivado diario va en ARC; el forense puede cambiar una sola línea (nombre del flujo P00) solo en el corte y con revisión independiente; productos «Mapa certificado», «Resultados por distrito» y «Alternativas», con el archivo en arc-e/, arc-c/ y arc-p/; identificador interno en minúsculas (`nac01`) y a la vista «NAC01 · Álava»; la semilla pública usa el código de la tabla maestra; el mapa de 350 y el histórico no entran en el corte; los nombres viejos conviven un ciclo de publicación completo sin lecturas antes de borrarlos, y ese borrado necesita frase del propietario. Antes de cambiar nombres de flujos hay que probar que la aprobación para publicar sigue siendo obligatoria.
- D-62. Naturalidad (piloto en seis territorios, `docs/ESTUDIOS/T172_naturalidad/`): al propietario le gustan los criterios B y C, sobre todo el C (población dentro de tolerancia y, a igualdad, menos partidos judiciales y comarcas partidos y mejor forma, cortando por donde hay menos vínculo). No está fijado: faltan las variantes con el desvío limitado al 5 % y al 8 % y el criterio C en los 71 territorios. Cantabria y Extremadura no se relanzan: esperan al motor nuevo.
- D-63. El número de cadenas de la competición es un parámetro y podrá ser una opción de la campaña, con un valor oficial fijado por edición antes de generar (forma parte de la regla pública, como la semilla). En curso la medición con 20 cadenas anidadas para saber a partir de cuántas deja de mejorar.
- D-64. Relevo del planificador (orden del propietario en el chat del Coordinador, 10-11): el sucesor arranca de este plan, de `docs/ESTADO.md` y del traspaso. Regla de comunicación con el propietario: temas y objetivos, lenguaje de arquitectura sin identificadores de tarea, y distinguir siempre entre decidido, construido, probado y publicado.
- D-65. Generales del 29-11-2026 (propietario, chat del planificador, «hay que ser fiel a la realidad»): la noche electoral usa los mapas vigentes (padrón y seccionado 2023) y lleva los resultados 2026 a ellos por equivalencia de secciones; las 52 se regeneran con el par 2025/2025 en el corte 5.0.0. El RD 806/2026 (BOE-A-2026-20742) no nombra el padrón; su reparto (Cádiz 9→8, Madrid 37→38) implica uno posterior a 2023. Los escaños no cambian los K de DDD (van por contrato). El aviso público sobre el padrón va a los textos de la web, que aprueba el propietario.
- D-66. Regla del núcleo (máximo 1 distrito mixto por municipio) sin admitir las infracciones que trae el mapa vigente; si un territorio es infactible por población, excepción explícita en su contrato con su motivo (máximo 2), que aprueba el propietario. Caso Ávila: el vigente incumple; los mapas nuevos la cumplen sin excepción.
- D-67. Número de cadenas provisional: 10 por edición (medición en 20 territorios: distritos fuera de tolerancia 172 sin cadenas, 126 con 5, 125 con 10, 124 con 20; `docs/ESTUDIOS/T180_CADENAS/`). Se fija como oficial cuando lo confirme la batería de los 71 con la función elegida.
- D-68. Función de calidad del motor nuevo: D8 = criterio C (población dentro de tolerancia y, a igualdad, menos partidos judiciales y comarcas agrarias partidos y mejor forma, cortando por donde hay menos vínculo) con el desvío máximo limitado al 8 % solo para elegir entre candidatos válidos; no es una regla del núcleo. En el Congreso logra el 86 % de la mejora de C con desvío medio 11,4 % frente a 16,4 % (`docs/ESTUDIOS/T179_naturalidad_nacional/`).
- D-69. Texto público aprobado para la elección 2026: «Los distritos de las generales de 2026 están trazados con el padrón y el seccionado de 2023; se actualizarán con el padrón de 2025.» Se añade a los textos de la web y al visor, sin publicar.
- D-70. Se acepta, documentada, la pérdida de votos 2011 en secciones sin geometría INE 2012 (Lugo, Alicante, León, Orense y Asturias; 0,2-0,54 %).
- D-71. La analítica sin cookies del visor se aplaza hasta publicar el visor v2. El visor v2 sigue sin publicarse.
- D-72. La batería de los 71 del motor nuevo (D8, 10 cadenas) corre en GitHub Actions, no en sesión: primero Soria y, si sale bien, los 71, por campaña autorizada en el chat del Operador (coste estimado 600-650 min).
- D-73. Línea de investigación tras el corte 5.0.0 («solo la excelencia es aceptable»): (1) del certificador exacto a resolver el óptimo demostrado con programación entera en los territorios pequeños y medianos; (2) comparación con `redist` (SMC) y GerryChain puro en los mismos territorios y reglas; (3) aportación propia: optimización con varios objetivos (población y naturalidad) bajo disciplina municipal con certificado del hueco al óptimo; después, publicación académica (P60). Forma de incorporarlo: no se sustituye el canónico; el resolutor exacto (abierto y determinista, HiGHS o CBC) entra como competidor y certificador, de los territorios pequeños hacia arriba hasta donde dé; el SMC de `redist` solo como comparación para el artículo; el canónico sigue como suelo de «nunca peor» y como mapa de los territorios grandes. Nada antes del corte.
- D-74. Zenodo: ahora, metadatos veraces (el depósito es el ZIP de código en la versión del mapa; el paquete firmado está en la Release; el DOI de concepto es la serie de mapas); en el corte 5.0.0, DOI de software por edición del motor y depósito de datos por mapa con el paquete firmado (token de Zenodo del propietario). Los dos DOI resuelven (comprobado por el propietario el 10-11).
- D-75. Plan del corte (10-11): primero lo reversible (pasos 0-2 y PR de workflows v5 sin fusionar) en paralelo con el arreglo de las autonómicas; relevo, workflows, pruebas, regeneración y archivo cuando la batería de las 19 cumpla «nunca peor que el vigente publicado»; regeneración nocturna por campaña; publicar solo con frase del propietario.
- D-76. El mapa de 350 queda fuera del corte 5.0.0.
- D-77. En el corte se regenera solo la legislatura vigente; el histórico después, como una elección más.
- D-78. Autorizado el cambio de una línea de `forense-00.yml` (nombre «P00 Campaña») dentro de la PR de workflows v5, con revisión independiente; la fusiona el propietario.
- D-79. Autonómicas «listas aunque haya que pasar a piezas pequeñas»: la competición usa la atomicidad municipal que declara cada contrato (como el laboratorio) y el mapa vigente publicado entra como candidato y punto de partida; no cambian suelo, techo, K, tolerancia ni la regla de un distrito mixto por municipio. La clave D8 implementada debe contar primero los distritos fuera de tolerancia (D-68); la aceptación exige clave nunca peor que el canónico y fuera de tolerancia nunca peor que el vigente.
- D-80. Los mapas van por legislatura: la del Congreso de 2023 termina y la nueva empieza tras el 29-11-2026. Los contratos de la edición 2026 de las 52 usan el par INE 2025/2025 (decisión tipo F10 en `configuracion/decisiones/`, con D-65); no se trasladan los resultados de 2023 al seccionado 2025.
- D-81. Regenerar las 52 del Congreso con el motor nuevo y sus contratos actuales (datos 2023) para publicarlas, por campaña en tandas de 5 (lección del 11-11: 51 a la vez saturan el estado operativo).
- D-82. Con el motor nuevo se regeneran todos los mapas; ningún mapa del motor antiguo queda vigente. Lo antiguo se archiva (no se borra). Relevo formal tras la regeneración: `motor` por defecto = motor2; el canónico solo como candidato dentro de la competición; su ruta autónoma pasa a legacy. Al publicar, el visor solo muestra productos del motor nuevo.
- D-83. Las Palmas (contrato 2026): excepción explícita para Lanzarote con La Graciosa (unidad insular atómica, 1,424 de la media frente al techo 1,40), con su motivo; el techo general sigue en 1,40.
- D-84. Nombre del algoritmo: «Deslinde» (delimitación reproducible de distritos uninominales). Deslinde 1.0 = trazado canónico + 10 cadenas ReCom + elección D8 + mapa vigente como candidato. No se renombra el código antes del corte.
- D-85. Fase de optimización tras el corte y antes de la investigación: medir (tiempo, código muerto, duplicados), optimizar con mismos mapas bit a bit en la batería de los 71, objetivos medibles y retirada al archivo de las reparaciones del motor viejo.
- D-86. Hoja de ruta de Deslinde para competir (tras la optimización): (1) paquete independiente instalable con documentación; (2) definición formal publicada (reglas, D8, semilla); (3) óptimo demostrado o cota con el resolutor exacto; (4) comparación en casos de referencia de la literatura (`redist`, GerryChain); (5) reglas generalizables a otros países; después, artículo (P60).
- D-87. (Sustituida por D-88.) Zenodo solo con los mapas publicados y el DOI de software más adelante.
- D-88. Zenodo: un único depósito «Deslinde 1.0.0 y mapas» cuando estén la optimización, el paquete independiente y la definición formal; hasta entonces no se deposita nada. El visor sí se publica.
- D-89 (11-11). Se levanta la veda del motor de producción (M04, M05, `ddd_core`, GerryChain) para optimizar, con la condición de mapas (composiciones) idénticos bit a bit; puede cambiar la huella del código o del resultado si queda registrada. La optimización (D-85) se adelanta a antes del corte 5.0.0, que espera. Los distritos quedan aparcados mientras tanto: no se lanza nada nuevo sin frase del propietario.
- D-90 (11-11). La semilla de Deslinde sale del código oficial del territorio en la tabla maestra (con su sha256), no del nombre de la carpeta. Cambio único y deliberado de los mapas: va tras las optimizaciones bit a bit y antes de regenerar las 71 y de renombrar las carpetas (T-220); su salida es la nueva referencia de «bit a bit».
- D-91 (14-11, propietario). El proyecto nació abierto; desde ahora no se quiere copia sin autorización. Un único repositorio de trabajo, el actual, PRIVADO (fuente única de todo: código, datos, Campañas, plan). Lo público va a un repositorio NUEVO de publicación, sin historial, que solo escribe el puente de publicación desde el privado. No se reescribe el historial del privado. (Sustituye la primera redacción de D-91 del mismo día, «el actual vuelve a ser público».)
- D-92 (14-11). Secretos: código de Deslinde (motor, competición, D8), su definición formal y los estudios y mediciones. Públicos: visor y sitio, mapas, resultados, datos abiertos, reglas y contratos (con un esquema y un validador propios, sin el núcleo), plan y arquitectura.
- D-93 (14-11). Las Campañas y la CI del privado corren en un runner propio del propietario (self-hosted); los artefactos pesados van a R2 (ARC). GitHub Actions de pago solo como puente temporal.
- D-94 (14-11). Zenodo: solo mapas, desde el repositorio público. Sustituye la parte de software de D-88; el paquete Deslinde (D-86.1) es privado; sin JOSS ni OSF. La investigación (D-73, D-86.3-5) sigue, sin publicar código.
- D-95 (14-11). Propiedad intelectual: el propietario la registra; el código del privado pasa a licencia propietaria desde ahora. Lo ya publicado bajo Apache-2.0 sigue bajo esa licencia (no es revocable); se intenta retirar lo antiguo accesible (copia de Zenodo del 9-11, releases antiguas) sin depender de ello.

### Cola vigente del motor y de las generales 2026 (10-11)
| Id | Tarea | Estado |
|---|---|---|
| T-175 | Núcleos cerrados en el certificador y enumeración exacta en territorios pequeños | HECHA |
| T-179 | Naturalidad C y D8: 52 del Congreso y 12 autonómicas | HECHA |
| T-180 | Curva del número de cadenas (N = 1 a 20) en 20 territorios | HECHA (PR en revisión) |
| T-194 | Criterio automatizado de aceptación del relevo | HECHA; (a) con datos reales, en la batería |
| T-194b | Datos reales mínimos de Melilla y Soria en la CI, si caben (≤2 MB, ≤60 s) | PENDIENTE (P2, sin chat propio) |
| T-195 | Núcleos cerrados en la competición del motor nuevo | HECHA |
| T-196 | Batería de los 71 con D8 y N = 10 (ejecución) | PREPARADO; la lanza el Operador con frase del propietario |
| T-197 | Ensayo en seco de la noche electoral 2026 | HECHA |
| T-198 | Corte 5.0.0: tests de aprobación y de nombres de flujo; tabla de equivalencias | HECHA |
| T-199 | Dimensión de elección en el registro y fecha parametrizada | HECHA |
| T-200 | Homologación 2026 y equivalencia de secciones 2026 | HECHA |
| T-201 | Elección como dimensión en la lectura de publicaciones | HECHA |
| T-202 | Naturalidad en Castilla y León, Extremadura y Principado de Asturias | HECHA (PR en revisión) |
| T-203 | Catálogo de procedencia por elección | PENDIENTE (P3, límite 25-11) |
| T-204 | Actualización del plan (D-65 a D-68 y esta cola) | HECHA |
| T-205 | D8 y generador ponderado en la competición del motor nuevo | REVISIÓN |
| T-206 | Texto del padrón 2026 en la web y el visor (D-69) | PENDIENTE (P2, límite 25-11) |
| T-207 | Composición canónica de Andalucía, Aragón y Baleares desde el M06 publicado y reagregación de sus 12 elecciones | HECHA |
| T-208 | Modo motor nuevo en la batería de Actions | REVISIÓN |
| T-209 | Actualización del plan (D-69 a D-73) | HECHA |
| T-210 | Metadatos de Zenodo veraces | HECHA |
| T-211 | Competición autonómica: causa medida y recuento por circunscripción | REVISIÓN |
| T-212 | Aceptación «nunca peor que el vigente» e indicadores en el resumen | HECHA |
| T-213 | Corte, paso 0: congelación | HECHA (etiqueta pre-5.0.0 la crea el propietario) |
| T-214 | Corte, pasos 1-2: identificadores y prueba A | EN_CURSO |
| T-215 | Corte, paso 4: workflows v5 | REVISIÓN (borrador, la fusiona el propietario) |
| T-216 | Corte, paso 3: motor nuevo como P30 en producción | EN_CURSO |
| T-217 | Vigente publicado como candidato y punto de partida | EN_CURSO |
| T-218 | Atomicidad del contrato en la competición autonómica | EN_CURSO |
| T-219 | Actualización del plan (D-74 a D-79) | HECHA |
| T-220 | Carpetas de territorios con los nombres nuevos | PENDIENTE (tras la regeneración; lo decide el propietario) |
| T-221 a T-223 | Certificación con el ganador, recuento del vigente y misma competición en P30 y batería | HECHAS |
| T-225 | Contratos 2026 del Congreso con el par 2025/2025 | HECHA |
| T-226 | Decodificación incremental en M01 (Toledo) | PENDIENTE (P2) |
| T-227 | Diagnóstico de motor: Madrid (Leganés) y Málaga 2025 | PENDIENTE (P2) |
| T-228 a T-230b | Recuento regional, lector del vigente y registro del par idempotente | HECHAS |
| T-231 | Estado operativo con muchas ejecuciones a la vez | PENDIENTE (P2) |
| T-232 / T-233 | Diagnóstico de la adquisición de la batería y traza en el log | HECHA / PENDIENTE (P2) |
| T-234 | Relevo formal (motor2 por defecto, canónico a legacy) | PENDIENTE (tras la regeneración) |
| T-235 | Excepción insular de Las Palmas en el contrato 2026 | PENDIENTE (P2) |
| T-236 | Actualización del plan (D-80 a D-86) | HECHA |
| T-237 / T-239 | Publicación por lotes en P50 y descarga solo de lo que consume | HECHAS |
| T-238 | El informe de la 00 lee también `publicacion_visor_<run>.json` del lote | PENDIENTE (P3, con la próxima PR del informe) |
| T-240 / T-241 / T-243 / T-245 / T-250 | Diagnósticos de la nocturna, paquetes autonómicos y electorales vivos o caducados, fuente de Andalucía | HECHOS |
| T-242 | Discrepancia de huellas 057a/253f de Andalucía (solo lectura) | PENDIENTE (P3, tras el corte) |
| T-244 | Catálogo de Andalucía sin el receipt independiente purgado (#713) | HECHA |
| T-246 | «Planificar» comprueba al principio que el paquete electoral existe y falla pronto | EN_CURSO (P1) |
| T-247 | Tests de estado vivo (dashboard por linaje, #718) | HECHA |
| T-248 | README de la 5.0.0 | PENDIENTE (P2, se fusiona al final) |
| T-249 | Datos abiertos por linaje M06/M08 y guardia del INDEX (#717) | HECHA |
| T-251 | Puerta de descarga: 503 de cuota (reintento con espera) frente a caducado | EN_CURSO (P2) |
| T-252 | Check «Estado vivo» tras commits de robot en `main` (#720) | HECHA |
| T-253 | Tests que leen estado vivo a la raíz congelada | PENDIENTE (tras el corte) |
| T-254 | Medición de Deslinde: tiempo por fase, código muerto, duplicados (#721) | HECHA |
| T-255 | Definición formal de Deslinde 1.0 (#719) | HECHA |
| T-256 | Optimización 1: poda con constantes precalculadas en el exhaustivo (#722, bit a bit) | HECHA |
| T-257 | Paquete independiente instalable de Deslinde (D-86.1) | EN PAUSA (tras T-256 a T-265) |
| T-258 | Un único vigente (el publicado en el visor) en competición y aceptación; canónico de referencia el del run (P30) | PENDIENTE (P2) |
| T-259 | Campo para la excepción de D-66 (motivo, máx. 2) | PENDIENTE (P2) |
| T-260 | El exhaustivo elige por la función A y no por D8: medir si cambia alguna selección | PENDIENTE (P3, solo si cambia alguna) |
| T-261 | Optimización 2: no intentar el exhaustivo cuando una cota demuestra que no puede acabar | EN_CURSO |
| T-262 | Optimización 3: árbol ponderado y núcleo de las cadenas más baratos (mismo orden del RNG) | PENDIENTE |
| T-263 | Código muerto: M04 v745–v754 y M05 v740 a legacy (#723; cambia la huella M04 de checkpoints) | REVISIÓN |
| T-264 / T-264b | Puentes del contrato que el motor no leía: diagnóstico y prueba (mismos mapas en 4 territorios); parche mínimo | EN_CURSO (parche tras T-261) |
| T-265 | Semilla por código oficial (D-90) | PENDIENTE (tras T-261 a T-264) |
| T-266 | Actualización del plan (D-87 a D-90) | HECHA |
| T-267 | Puerta de validación bajo `bash -eo pipefail` (regresión de T-251) | HECHA |
| T-268 | La 00 rechaza al principio `congreso350_*` (D-76) | HECHA |
| T-269 | Relajación real de D-66 en el núcleo | PENDIENTE (P3, solo si aparece un territorio infactible) |
| T-270 | Medición de Deslinde optimizado en territorios grandes, utilidad del exhaustivo, función A frente a D8 | CERRADA sin terminar (D-110; informe parcial en su rama) |
| T-271 | CI: subir artefactos de diagnóstico solo al fallar, sin tumbar el veredicto | EN CURSO (P0) |
| T-272 | Inventario de la frontera privado/público | HECHA (rama `t272-frontera-inventario`) |

### Plan por fases del repositorio privado (14-11, D-91 a D-95)
Fase 0 — desbloquear (hoy):
| T-271 | Ver arriba | P0 |
| T-278 | Borrar los artefactos sobrantes (propuesta del Operador, 176 GB) y las releases borrador de ensembles | Frase del propietario al Operador |
| T-279 | Relevo del Operador (contexto al 65 %): traspaso escrito y chat nuevo | Planificador |
Fase 1 — privado operativo:
| T-274 | Runner propio: guía de registro (sistema del servidor) y CI y Campañas con `runs-on: [self-hosted, ddd]`; sin runner propio en ningún repositorio público | Coordinador; el propietario registra el runner |
| T-280 | Licencia propietaria del código en el privado (LICENSE, cabeceras, README interno) y nota de lo publicado antes bajo Apache-2.0 | Coordinador |
| T-281 | Paquete para el registro de la propiedad intelectual: instantánea del código de Deslinde, definición formal y estudios con sha256 y fecha | Coordinador; lo presenta el propietario |
Fase 2 — repositorio público de publicación:
| T-273 | Contenido inicial del público por lista blanca (inventario T-272), generado por script desde el privado; README y licencia de datos | Coordinador; el propietario crea el repositorio vacío |
| T-282 | Desacoplar del motor lo que se publica: el visor sin `ddd_ensemble`; validador de contratos con esquema JSON | Coordinador |
| T-275 | Puente de publicación: la P50 escribe en el público con un token fine-grained (solo `contents:write` en el público); `publicaciones_visor.json` apunta a ficheros del público, no a blobs del privado | Coordinador |
| T-283 | Pages y el dominio `diputadodedistrito.es` servidos desde el público | Coordinador; el propietario ajusta el dominio |
| T-276 | Zenodo solo mapas, desde el público (`.zenodo.json`, `CITATION.cff`) | Coordinador |
Fase 3 — retirar lo antiguo accesible:
| T-284 | Textos de solicitud a Zenodo (retirar o restringir la copia del repositorio del 9-11) y a Software Heritage si lo archivó | Planificador redacta; el propietario envía |
| T-285 | Borrar releases antiguas que no son de mapas (borradores de ensembles, `cyl-m06-checkpoint-temp`) | Frase del propietario al Operador |
Fase 4 — producto (en el privado):
| #740 / T-220 | Renombrado de carpetas | Poner al día y fusionar tras T-271 |
| T-257 | Paquete Deslinde (privado; mover, no copiar) | Tras T-220 |
| T-270 | Cerrada sin terminar (D-110) | — |
| T-286 | Batería de los 71 con el motor optimizado y la semilla oficial (fija N = 10) | Runner propio; frase del propietario |
| T-287 | Regenerar los 71 con la semilla oficial y publicarlos por el puente | Frase del propietario |
| T-288 | Corte 5.0.0 (README del público, etiqueta) | Al final |
| T-289 | Pendientes menores: T-206 y T-203 (límite 25-11), T-226, T-227, T-231, T-233, T-238, T-242, T-253 | Por prioridad |
| T-290 | Actualización del plan (D-91 a D-95) | ESTA PR |

### Reglas del propietario del 14-11 (traspaso del Planificador)
- Con el propietario: de tú, en español, corto, por temas (sin ids), semáforo y «decidido / construido / probado / publicado». Corregir en voz alta. No preguntar detalles: decidir con criterio y avisar. Nota «📌 Tema cerrado» al cerrar cada tema; cerrar temas antes de abrir nuevos.
- Nada de PR con fallos: más de tres commits de arreglo en una PR → se escribe una regla.
- Ahorro de cuota: Sonnet salvo motor y M07; un revisor por PR terminada; de dos a cinco chats; solo hitos.
- Motor repetible: relanzar desde el principio, nunca parches que acepten versiones antiguas (ids legacy).
- Tras cualquier renombrado o cambio de cadena: ensayo local de la cadena completa de un territorio y una P00 de prueba antes de campañas.
- Congelación del motor y de los workflows de producción durante cada campaña de regeneración, hasta la P50.

### Decisiones del 14-11 posteriores a 1.0.44 (D-96 a D-103)
- D-96 (14-11). Repositorio: el actual pasa a PRIVADO cuando acaben las pruebas (hoy público); el público nuevo, sin historial, solo de publicación (concreta D-91). Secretos según D-92. Registro de la propiedad intelectual el lunes 16-11 (T-281).
- D-97 (14-11, #744). Licencias: código propietario; mapas y resultados CC BY 4.0; código del visor, todos los derechos reservados; reglas y contratos CC BY 4.0; plan y arquitectura CC BY-NC 4.0.
- D-98 (14-11, #761). Deslinde 1.1: D8 con frontera compartida medida (`shared_border_m`), candidato exacto CP-SAT para K ≤ 4 y desempate por desvío máximo. Batería 1.1 aprobada 71/71.
- D-99 (14-11). Noche del 29-11: mapas vigentes de 2023; tabla 2026→2023; la sección partida va entera al distrito con más población, nunca se reparten votos; `minsait_provisional` esa noche (marca PROVISIONAL; se publica con frase del propietario esa noche) e `infoelectoral_mesas` como definitivo. Código en main; falta el ensayo en seco.
- D-100 (14-11). Fuentes una sola vez en P10 y R2 (ARC-E); la batería parte del paquete P10 y recalcula P21-P23.
- D-101 (14-11). Analítica: opción A (contador propio en un Cloudflare Worker, sin datos personales) y maplibre servido desde el sitio (sustituye el aplazamiento de D-71).
- D-102 (14-11). Notación interna M01-M08 → P21-P27/P41-P42 (T-313) después de publicar los 71: P22 = «Geometría y adyacencias», P27 = auditoría, ensemble25/50; alcance completo; alias solo de lectura para el histórico.
- D-103 (14-11, propietario; traspaso del Planificador). Histórico desde 2011 adelantado (inventario T-306, #770): matiza D-77, que dejaba la regeneración del histórico para después del corte. Zenodo solo mapas (confirma D-94).
- D-104 (14-11, propietario). Mapa de fondo de OpenStreetMap (visores inicial, nacional y del Congreso): se acepta y se declara en el texto de transparencia que OpenStreetMap sirve el fondo y ve la IP del visitante. Fondo propio servido desde Cloudflare: se reconsidera después del 29-11 (T-316).
- D-105 (14-11, propietario). Histórico desde 2011: mapa destino 2023 (como D-65) con la regla de M07 7.4.0, sin repartir votos (la sección partida va entera); se descargan los 5 seccionados que faltan y se re-cuadra (T-306 §4-5). Mantiene D-70: la pérdida de votos de 2011 sigue aceptada y se hereda tal cual.
- D-106 (14-11, propietario). Contador de Cloudflare: el propietario lo despliega antes del 29-11 con la guía de #780.
- D-107 (14-11, propietario). Propiedad intelectual: el paquete se regenera sobre main actual (con Deslinde 1.1) antes del registro del lunes 16-11.
- D-108 (14-11, propietario). Las 6 releases `almacen-m06-*` se borran, tras comprobar en vivo las 51 claves en R2 y una pasada `-WhatIf` limpia; el script lo ejecuta el propietario.
- D-109 (14-11, propietario). Repositorio privado, público nuevo y runner propio: aparcados hasta después del 29-11. Matiza D-91, D-93 y D-96: el paso a privado y el runner propio no empiezan antes del 30-11.
- D-110 (14-11, propietario). T-270 se cierra sin terminar: medía Deslinde antes de 1.1 y T-296/T-297 responden buena parte. La rama `t270-medicion-deslinde-optimizado` queda como referencia; función A frente a D8 y el exhaustivo en medianos pasan a la investigación del final, con Deslinde 1.1.
- D-111 (14-11, propietario). Excepción acotada a la congelación: #765 (T-300, la P50 copia el catálogo de procedencia al sitio) se fusiona cuando terminen las P00 de los 71 y antes del primer lote de P50, con revisión independiente; los 71 salen con su ficha de procedencia.
- D-112 (14-11, propietario). P10 en producción: lee las fuentes de la copia de R2 (ARC-E) y verifica su sha256; consulta el INE sin descargar (fecha y tamaño) y, si el fichero oficial ha cambiado, para y avisa al propietario, que decide si se adopta la versión nueva. Matiza D-100. Se implementa después de la P50 de los 71 (congelación de workflows).
- D-113 (14-11, propietario). Histórico autonómico: se publican solo las 54 elecciones con datos por sección; las 21 con fuente solo municipal o provincial (Aragón, Asturias, Cantabria, Castilla-La Mancha, Murcia, Extremadura; T-306 §2) se marcan «sin datos por sección». Nunca se reparten votos de municipio entre secciones.
- D-114 (15-11, propietario). Excepción a la regla «ensayo local de la cadena completa»: las sesiones de la nube no tienen R2 ni docker; vale el barrido de arranque de todos los entrypoints (T-338/T-339) y el segundo intento de la P00 de aut11 en r4, con parada al primer fallo, como ensayo.
- D-115 (15-11, propietario). Puerta del histórico (paso A): M07 PASS, o PASS_WITH_DECLARED_EXCEPTIONS solo con votos sin asignar ≤ 0,1 % (2011: los de D-70), y contraste por provincia con el CSV del BOE (T-330) dentro de la tolerancia CERA de 2019-11 y 2023; «ganador igual que B» solo informativo. Mapa 2023 (D-105).
- D-116 (15-11, propietario). Galería del visor V3: se permiten commons.wikimedia.org, upload.wikimedia.org y es.wikipedia.org en la red del entorno de la sesión que la construye (solo para preparar el catálogo; los visitantes no llaman a terceros).
- D-117 (15-11, propietario). Padrón 65034 (endpoint dinámico): el P10 lo descarga siempre, compara su sha256 con la copia de R2 y para si cambia; los ficheros con fecha fiable siguen con consulta sin descarga (matiza D-112).
- D-118 (15-11, propietario). Noche del 29-11: se ensaya con el formato Minsait supuesto (sin documento oficial); si esa noche el provisional no encaja, se publica solo con `infoelectoral_mesas` definitivo (matiza D-99).
- D-119 (15-11, propietario). La parada del padrón 65034 se aplica al sha256 del extracto filtrado que entra al motor (Periodo, Sexo y Edad del contrato), no al fichero nacional crudo, que crece con periodos que no se usan; el crudo se registra solo como información (matiza D-117). Hallazgo previo: el crudo cambió el 27-10 (+843 KB) y el extracto 2025 de aut11 es idéntico.
- D-120 (15-11, propietario). Histórico, alias de coaliciones: los alias del BOE que no coinciden con el espejo se acreditan con la composición de cada coalición tomada del BOE de candidaturas proclamadas (fichero con fuente y sha256), nunca de memoria (T-345).
- D-121 (15-11, propietario). Histórico, elección de 2015-12: en las 13 provincias donde el BOE nombra a la federación regional de IU, la candidatura se acepta como familia IU ↔ «IU-UPeC» del espejo. Es una equivalencia de familia política declarada por el propietario, no deducida de los votos. Provincias (código INE, según el informe de T-345): 04, 11, 14, 18, 21, 23, 29, 41 (IULV-CA), 38 (IUC), 03, 12, 46 («UNITAT POPULAR… (EUPV-UPeC)») y 52 Melilla (candidatura sin «UPeC»). Con D-120, las 312 provincias-elecciones quedan acreditadas.
- D-122 (15-11, propietario). Avisos: toda PARADA, fallo no transitorio o fin de tanda de una campaña, y toda PR del camino crítico fusionada o bloqueada, se avisan al momento al Planificador (send_message), que se lo pasa al propietario con una notificación al móvil.
- D-123 (15-11, propietario). LICENSE, apartado 3: «Material de terceros. Las fotografías de la galería territorial del visor (`visor/v2/galeria/`) no son obra del titular. Se rigen por su propia licencia Creative Commons (CC BY, CC BY-SA o CC0), indicada para cada una en `visor/v2/galeria/NOTICE.md`, y no por esta licencia.» + NOTICE con créditos y cambios (#820).
- D-124 (15-11, propietario). Tras cerrar r4 (P50 de los 71): primero el ensayo en seco del 29-11 y después la campaña histórica; el histórico SÍ se publica en el visor, con su fecha de elección; las fuentes del histórico van a R2 ya (los 17 seccionados INE 2010-2026, el Observatorio, la tabla 30832 y el Censo 2011); 2023 no entra en el histórico (lo cubre r4).
- D-125 (15-11, propietario). Histórico de las generales con la opción A: distritos generados con los datos de cada época (seccionado y padrón por sección del año de la elección, votos por sección de esa elección y K = escaños oficiales de esa elección según el BOE), sin traslado al mapa de 2023. Es un ejercicio retrospectivo («quién habría mandado en ese momento»), no una propuesta a futuro: cada mapa se publica con su fecha y su procedencia, separado del vigente. Sustituye a D-105 para las generales; la ficha #819 (paso A sobre 2023) queda obsoleta.
- D-126 (15-11, propietario). Población por sección del histórico: 2011-11 = Censo 2011 (1-11-2011); 2015-12, 2016-06 y 2019-04 = Atlas INE 30832 del año; 2019-11 = Atlas 2020. Sección sin dato («.»): valor de la misma sección en el año más cercano del Atlas (empate: el anterior), marcado sección a sección; % rellenado publicado por provincia; provincia con más del 1 % rellenado no se publica sin decisión del propietario. Nunca el censo electoral como población. Hallazgo (T-358, #832): el «.» es real del Atlas (34 provincias-elección por encima del 1 %; Sevilla 2016, 20,9 %). Pendiente del propietario: refinar el relleno (media de años vecinos y ajuste al total municipal oficial, recomendado), mantenerlo o subir el umbral.
- D-127 (16-11, propietario). El entorno `produccion` no exige revisor (lo quitó el propietario el 15-11 a las 21:49 UTC: aprobar a mano cientos de jobs es inviable). El único control de lanzar y publicar es la frase D-52 del propietario en el chat del Operador (#835, #837).
- D-128 (16-11, propietario). Relleno de población del histórico: interpolación lineal entre el año anterior y el siguiente del Atlas de la misma sección (si solo hay uno, el más cercano) y ajuste proporcional por municipio al padrón municipal oficial del INE del año; marca por sección; umbral del 1 % sobre la población estimada (#840). Reglas del Planificador (16-11): residuo ≤ 0 → aviso, valor interpolado sin ajuste («sin_ajuste_municipal»), nunca 0; secciones sin dato en ningún año → provincia-elección APARTADA; secciones del Atlas sin geometría del año → reasignadas enteras a la sucesora por la tabla de equivalencia («reasignada»), o provincia APARTADA si no hay sucesora única; secciones del seccionado no listadas en el Atlas → regla de D-128, marca «no_listada».
- D-129 (16-11, propietario). Diseño de workflows: 9 visibles, uno por familia y opciones dentro, todos con prefijo P: P00 Campaña (bloque completo), P10 Fuentes (P11 territoriales, P12 electorales), P20 Distritos (P21 base y población, P22 geometría y adyacencias, P23 grafo, P24 solución inicial, P25 optimización, P26 producto certificado, P27 auditoría, P28 alternativas), P30 Resultados electorales (P31 agregación, P32 resultados por distrito, P33 puerta), P40 Publicación (P41 sitio, P42 lotes, P43 histórico por fecha), P50 Publicación académica, P70 Archivo (P71 archivar, P72 recuperar, P73 podar, P74 listar), P80 Verificación del motor, P90 Automático (pruebas, revisor, fusión automática, forense, métricas; sin botón; checks `veredicto` y `pruebas` intactos). Nada «Interno»: lo compartido, como acciones compuestas. Carpetas de R2: entradas/, puntos-de-control/, productos/ (sin código P). Sustituye a D-61 (P20/P30 separados) y a la numeración de D-102/T-313. Orden de migración aprobado: ensayo del 29-11 en los workflows actuales; luego una PR por familia (fichero viejo borrado en la misma PR, test de equivalencia, revisor, la fusiona el propietario): 1 P90, 2 P70, 3 P80, 4 P50, 5 P40, 6 P10, 7 P30, 8 P20, 9 P00 (la nueva forma de trabajar —comprobación previa con semáforo, políticas de reintento y apartado, informe en un issue, versión fija, estado fuera de main— se presenta AL DETALLE al propietario antes de implementarla), 10 documentación renumerada; validación con una P00 de aut11 y un re-ensayo corto antes del 26-11. Cada encargo se presenta al detalle al propietario y no se implementa sin su aprobación.
- D-130 (16-11, propietario). Una campaña = una ejecución: P00 llama a P10/P20/P30/P40 solo como workflows reutilizables por dentro; nunca lanza ejecuciones por fuera. Parámetros visibles solo con opciones entendibles en español y territorios por código; nada de run ids, sha, rutas ni números técnicos (se resuelven en el código). Propuesta de botones (a confirmar en cada encargo): P00 territorios/elección/modo (solo comprobar | comprobar y lanzar)/publicar; P10 tipo/territorios/elección; P20 territorios/alternativas; P30 territorios/elección; P40 qué publicar/elección; P50 territorios; P70 acción/simular; P80 territorios/alcance; P90 sin botón. Límites de GitHub (jobs por matriz y por ejecución, concurrencia, anidamiento) a verificar en la documentación oficial antes del paso 9; alternativa: un job por provincia con P10-P30 como pasos.
- D-131 (16-11, propietario; paso 2 de D-129). P70 Archivo (`p70-archivo.yml`) sustituye a `podar-r2.yml`, `recuperar-producto-electoral-durable.yml` y a lo que quede de `mantenimiento-programado.yml` (`archivar_r2`, `extraer_m06`; T-366 se lleva `metricas`). Botón: acción (P71 archivar, P72 recuperar producto electoral o composición M06, P73 podar, P74 listar), simular, y territorios (código) y elección (AAAA-MM) solo para recuperar. P71 sin «caduca antes» (todo lo vivo; cron diario 05:17). P72 resuelve run, artefacto, sha y commit desde catálogo y manifiesto; mantiene `workflow_call` con entradas técnicas para la 00 (solo cambia su `uses:`). P73 sin sha256 en el botón: el sha aprobado de la lista va en un fichero versionado que solo cambia por PR revisada; borrado real solo con el entorno `produccion`. P74 nuevo, solo lectura: tamaño por carpeta y total frente a 10 GB. Un solo grupo de concurrencia. Renombrar carpetas de R2: tarea aparte tras el paso 9.
- D-132 (16-11, propietario; paso 3 de D-129). P80 Verificación del motor (`p80-verificacion-motor.yml`) sustituye a `bateria-motor.yml`. Botón: territorios (vacío = 71) y alcance «motor vigente» (competición Deslinde, D8 y 10 cadenas fijados en el código; por defecto) | «motor base M05» (7.4.4 fijada). Se retira `archivar_almacen_m06` (de un solo uso, hecho en T-302/T-302d); `archivar_p10` pasa a P71 como «paquete de fuentes de un territorio» (solo pide el territorio; el último paquete P10 se resuelve del catálogo). Sin cambios en `herramientas/bateria_motor.py` ni `ddd_motor2`.
- D-133 (16-11, propietario; paso 4 de D-129). P50 Publicación académica (`p50-publicacion-academica.yml`) sustituye a `publicar-version-mapa.yml`. Botón: territorios. Toma el M06 publicado en el visor (blob de `publicaciones_visor.json`, sha256 verificado), no el artefacto de Actions. Versión automática: 1.0.0 la primera, sube la menor si cambia el mapa y se niega sin cambios. Una Release por lote `mapas-v<versión>` con los territorios elegidos (un DOI por versión de la serie, D-88/D-94). La 05 deja de lanzar P50 (se quita el job `version_mapa` de `cadena-publicacion.yml`). Entorno `publicacion`, atestación y empaquetado determinista sin cambios. No se lanza P50 hasta cumplir D-88.
- D-134 (16-11, propietario; paso 5 de D-129). P40 Publicación (`p40-publicacion.yml`) sustituye a `desplegar-visor-publico.yml`, `cadena-publicacion.yml` y `_reutilizable-publicar-sitio.yml` (el publicador va dentro como jobs; desaparece el «Interno»). Mantiene `workflow_call` con entradas técnicas ocultas para la 00, las alternativas (ensemble) y el Gestor (que pasa a lanzar con el territorio). Botón: qué publicar «solo el sitio» (P41, sin tocar el registro) | «territorios» (P41+P42, todo o nada), territorios, simular (marcado por defecto). Sin run id: última 00 completa con la puerta 04 en verde por territorio, del registro durable. Siempre «Sitio completo». Escenarios solo por `workflow_call`. P43 (histórico por fecha) en tarea aparte tras el diseño del paso A. Tras fusionar, prueba real: P40 «solo el sitio» sin simular (Operador, con frase del propietario).
- D-135 (16-11, propietario). Excepción a D-129: la fusión automática queda como fichero propio sin botón (`auto-merge.yml` 1.3.0, disparado por `workflow_run` al terminar «P90 Automático»; jobs, permisos y concurrencia idénticos), porque GitHub rechaza un `workflow_run` sobre el propio workflow y fusionar desde el contexto de la PR ejecutaría su código con la app. Descartados: auto-merge nativo (T-54c), cron (vigilante) y `pull_request_target`. P90 sustituye a `pruebas-plataforma.yml`, `forense-00.yml` y el job `metricas`. `revisor-pr.yml` también queda aparte, idéntico a `main` (revisor independiente sobre T-366: con `labeled`/`ready_for_review` en el workflow de `pruebas`, GitHub crea un check-run `pruebas` skipped que cuenta como cumplido); migrará en un paso propio con su diseño (T-374).
- D-136 (16-11, propietario; paso 6 de D-129). P10 Fuentes (`p10-fuentes.yml`) sustituye a `preparacion-fuentes.yml` y `preparacion-resultados-electorales.yml`; `workflow_call` para la 00 con `tipo:`. Botón: tipo (territoriales P11 | electorales P12), territorios (matriz, exclusión por territorio a nivel de job), elección (vigente | ensayo 2026-11-29; solo P12), «regenerar aunque exista». Reutilizar automático (reutiliza si el paquete sigue descargable y compatible; si caducó, regenera). Edición fija (2025). No se fusiona hasta terminar el ensayo en seco; el re-ensayo corto, ya con la P10 nueva. T-347 va detrás.
- D-137 (16-11, propietario; paso 7 de D-129). P30 Resultados electorales (`p30-resultados-electorales.yml`) sustituye a `incorporacion-resultados-electorales.yml` y `_reutilizable-incorporacion-electoral.yml`. Botón: territorios (matriz); producto territorial y paquete electoral desde el catálogo; sin campo «elección» hasta el histórico; edición fija. La puerta de validación pasa a acción compuesta en el paso 9. No se fusiona hasta terminar el ensayo en seco.
- D-138 (16-11, propietario). Se retira P28 Alternativas: los ensembles salían del motor viejo y no son coherentes con los mapas de Deslinde (cuyas 10 cadenas arrancan del M04 y, si no es admisible, del canónico). Si vuelve, será con una tarea nueva que arranque del mapa de Deslinde (P26). `ddd_ensemble` se queda. Lo publicado del motor viejo se retira con T-380.
- D-139 (16-11, propietario; paso 8 de D-129). P20 Distritos (`p20-distritos.yml`) sustituye a `produccion-distritos.yml` y `_reutilizable-generacion-territorial.yml` (pasos P21…P27 en el log); `generar-alternativas-territoriales.yml` a legacy sin sustituto. Botón: territorios (matriz) y «empezar de cero». Fuera: estrategia de optimización (con motor2 solo vale Canónico), edición, confirmaciones, synthetic y republicar. El Gestor deja de lanzar ensembles. Implementador Opus. No se fusiona hasta terminar el ensayo en seco; prueba real: P20 de aut11 reutilizando, M06 bit a bit igual al vigente. La detección automática de puntos de control incompatibles va aparte (T-381).
- D-140 (16-11, propietario; paso 9 de D-129). P00 Campaña en dos partes: 9a diseño al detalle sin código (Opus, T-378) que compara dónde guardar el estado fuera de `main` (R2, rama dedicada, issue), verifica en la documentación oficial los límites de GitHub (alternativa: un job por provincia) y parte de 2 reintentos solo para fallos transitorios y parada sistémica con 3 o más territorios por la misma causa o el 20 %; 9b implementación (T-379) tras aprobarse el diseño. Gestor, legislatura y activación por elección se retiran absorbidos en P00. Respaldo: si el 24-11 P00 no está validada (aut11 y re-ensayo corto), la noche del 29-11 va con la 00 actual (que ya llama a los P10-P40 nuevos) y P00 se fusiona después del 29-11.
- D-141 (16-11, propietario). Retirar lo que queda de los ensembles del motor viejo (T-380): 3 ensembles de Congreso (La Rioja, Salamanca, Sevilla) del registro del visor y publicación (frase del propietario al Operador), y después sus 3 Releases (≈35 MB), las 31 configuraciones de `configuracion/ensemble/` y el selector de escenarios del visor v1 si queda sin uso.
- D-142 (16-11, propietario; paso 10 de D-129). Documentación renumerada (T-383, tras T-379, Sonnet): solo texto vivo (CLAUDE.md, `.claude/rules/`, skills, `docs/ARQUITECTURA/`, guías); lo histórico no se reescribe y el puente es `docs/ARQUITECTURA/EQUIVALENCIAS_D129.md`. `lanzar-campana` se funde en `lanzar-p00` (antes `lanzar-00`); `publicar-visor` pasa a `publicar-p40`. CLAUDE.md reescribe «Ejecución 00» y «Visor» en notación P y manda a legacy las lecciones sin objeto (< 100 líneas). Test que falla si un documento vivo cita un workflow inexistente. Guías retiradas a legacy con nota al sustituto. T-313 sigue aparte.
- D-143 (16-11, propietario). Diseño de P00 (T-378, `docs/ESTUDIOS/T378_P00_CAMPANA/`, #850) aprobado con las 11 recomendaciones: cadena A (matriz + reutilizable «cadena de un territorio» sin botón); estado en R2, informe en issue y un commit a `main` al cierre; grupos todos/congreso/autonómicas/códigos; elección vigente | AAAA-MM; ámbar se lanza y se marca; parada sistémica con mínimo de 3 apartados también en la regla del 20 %; se publican los que pasaron; paralelo fijo de 15 (cuenta Free, 20 jobs; quedan 5 para la CI; corregido por el propietario el 16-11); IA de cierre solo con apartados o parada; la validación desde la rama puede escribir su commit de cierre con el revisor conforme y la frase del propietario; revisor independiente del diseño antes de implementar. T-379 (Opus): PR 1 (estado de campaña, sin workflows) puede empezar con el revisor conforme, sin esperar a T-377; PR 2-4 tras T-377. D-14 (mismo source_sha que el visor) queda sustituida por D-133 en P50: LINAJE.json lleva por territorio blob_sha y sha256 del M06 del registro, el run de la 00 si consta y el sha del commit de la Release.
- D-144 (16-11, propietario). (a) T-374 se cierra: `revisor-pr.yml` queda aparte como excepción permanente, como la fusión automática (D-135); las opciones dentro de P90 reabren el check-run `pruebas` skipped. (b) El ruleset `proteger-main` hoy solo exige `veredicto` (verificado por el Coordinador): se añade `pruebas` a los checks requeridos, tras comprobar que P90 crea `pruebas` en todas las PR (también las de solo documentación); el cambio del ruleset lo hace el propietario o el Operador con su frase. Corrige D-129 («checks `veredicto` y `pruebas` intactos») y `.claude/rules/workflows.md`.
- D-145 (16-11, propietario; revisor del diseño de P00 con 2 bloqueantes). Corrige D-143: (A) la validación desde rama no escribe en `main`, el cierre de validación va a una rama/PR de cierre; (B) 15 territorios con `pre_m04_evidence` y `m04` en serie en la ruta de campaña (máximo 15 jobs, 5 para la CI), `fail-fast: false` y `max-parallel: 15`; (C) la noche del 29-11 va con la 00 actual como caso base y P00 se fusiona después del 29-11, sin borrar la 00 en la PR 3; (D) diseño 1.1 con todos los arreglos técnicos del revisor (T-387, Opus, solo documento) y nueva revisión; (E) T-379 PR 1 parada hasta el conforme del revisor a la 1.1.
- D-146 (16-11, propietario). Zenodo: se publican ya los mapas de Deslinde 1.1 (es estable: 71/71 válidos, bit a bit; las mejoras de la investigación serán versiones nuevas de la serie). Las condiciones de D-88 dejan de frenar el depósito de mapas. Solo mapas, sin motor, subidos por la API desde P50 (sin integración GitHub–Zenodo, que el propietario desactiva); licencia CC BY 4.0 para los mapas. El propietario borra el ZIP de código del registro 24093968 y conserva la publicación y los DOI; T-284 queda sin objeto. Encargo T-388: campo «destino» (prueba en sandbox por defecto | Zenodo), nueva versión del concepto 24093967 (o concepto nuevo si Zenodo no deja pasar de software a dataset), paquete firmado + SHA256SUMS + LINAJE.json + licencia + nota de fuentes, tokens `ZENODO_TOKEN` y `ZENODO_SANDBOX_TOKEN` como secretos del entorno `publicacion`, `.zenodo.json` a legacy y `CITATION.cff` a la serie de mapas.
- D-147 (16-11, propietario). Decisiones finales del diseño 1.1.1 de P00 (#858): una segunda P00 en curso se rechaza con aviso; `configuracion/catalogo_preparacion.yaml` fuera de RUTAS_ROBOT (el commit de cierre dispara la CI de `main`); el cierre de validación va a rama + PR en borrador; entorno `registro` limitado a `main` con los secretos de la app de registro (PR 2a de T-379), aunque haya que tocar unos 25 usos y separar el registro de los jobs de P40 que ya tienen entorno.
- D-148 (16-11, propietario). Corrige D-139 y D-137: los botones de P20 y P30 admiten un territorio por ejecución; varios en paralelo, con P00 (cadena de un territorio, D-143). GitHub no permite repetir en matriz una cadena de jobs sin un reutilizable ni los bucles entre workflows («Loops in the workflow tree are not permitted»). P10 mantiene la matriz directa (un job por territorio).
- D-149 (16-11, propietario). Prioridad máxima: terminar la migración de workflows; ninguna campaña hasta entonces. Se suspende el ensayo en seco con los workflows actuales (la frase D-52 del ensayo queda sin efecto; la ficha `2026-11-15_ensayo-noche-29-11` se adapta para el re-ensayo corto con los workflows nuevos, con frase nueva). Se levanta la condición «no fusionar hasta terminar el ensayo» de D-136, D-137 y D-139: T-375, T-376 y T-377 se fusionan con CI verde, revisor y orden del propietario, en el orden 375 → 376 → 377. Siguen permitidas, con su frase, las acciones que no son campaña (prueba de P40 «solo el sitio», T-380, sandbox de Zenodo). Riesgo aceptado: la noche del 29-11 puede ir sin ensayo previo sobre lo nuevo; la 00 vieja sigue disponible.
- D-150 (16-11, propietario). El histórico no espera al futuro: (1) alta de los territorios-elección `<t>_hAAAA_MM` (T-393) sin versionar los YAML generados (los escribe `materializar` desde los contratos y las fuentes; opción A del Planificador): resolución en `territorio_ids` y en el catálogo, con test que materializa con fuentes sintéticas y valida el contrato; solo son generables las provincias LISTA de cada época (D-126); (2) T-375, T-376 y T-377 aceptan esos ids; (3) P00 se fusiona en cuanto esté validada, sin esperar al 29-11, y la 00 vieja sigue viva hasta después del 29-11 (corrige D-145 C); (4) la validación de P00 incluye el piloto histórico nac22 2019-11; (5) la campaña histórica va con P00, por elecciones y dentro del tope semanal, con las fichas (#842, T-340) reescritas para P00.
- D-151 (17-11, propietario). Corrige D-136: P10 admite un territorio por ejecución, como P20 y P30 (D-148), sin matriz ni reutilizables (una matriz solo devuelve las salidas de su última fila); varios en paralelo, con P00.
- D-152 (17-11, propietario). Histórico (T-393, #873): id propio `<t>_hAAAA_MM` con la carpeta de la provincia y 260 filas generadas del catálogo (cifras de provincias generables derivadas del contrato); diseño de P43 (T-395); revisor del diseño antes de implementar. La matriz de una campaña histórica es la de P00; P20 y P30 se llaman con un territorio (D-148).
- D-153 (17-11, propietario). Secciones con población sin geometría en el seccionado de su año: se asignan a la sección del seccionado del año que las contiene, localizadas con la geometría de otro año (centroide, misma provincia, regla de sucesora de T-364b); sin geometría en ningún año, se excluyen declarando su población (T-396). Los 46 municipios con aviso ya los resolvió D-128 (a).
- D-154 (17-11, propietario). P43 (#875): el M06 de cada elección es el propio de su época (D-125), no el mapa 2023; etiqueta «distritos de <fecha>, con datos de esa época»; se publican las provincias en verde y las ámbar con aviso visible, nunca las rojas; primera entrega solo en el visor y en el catálogo de procedencia. Decisión del Planificador (17-11): kind propio para el histórico en el registro (aislamiento: ningún histórico sustituye al vigente).
- D-155 (17-11, propietario). Lista de Actions sin basura (T-397): «P90 Automático — Fusión automática» y «P90 Automático — Revisor de PR»; los ficheros sin botón de P00 se llaman «P00 Campaña — <qué hace>»; al terminar la migración se borran las ejecuciones de los workflows retirados (Operador, con frase); diagnóstico de los dinámicos de GitHub para el propietario. Además, el propietario adelanta T-379 PR 4 (IA de cierre en P90), autoriza al Coordinador a fusionar sin esperarle hasta las 10:00 del 17-11 las PR de la migración, del histórico y del plan con CI verde y revisor conforme (sin lanzar ni publicar), y ordena preparar las fichas del re-ensayo P00 2026-11 y del histórico 2019-11 (#876), con condición previa de migración terminada y P00 validada; las frases se repiten cuando estén fusionadas.
- D-156 (17-11; SUSTITUIDA por D-158). Histórico 2011-11: el seccionado 2012 duplica población en 63 secciones hijas (179.435 hab. ya en sus madres, T-399). Con el seccionado del Censo 2011 coinciden población y geometría pero no los votos (puerta M07 rota en 13 provincias, 16.418 votos fuera, máx. 0,58 %); con el de 2012, 5 provincias sobre 0,1 % (5.752 votos, máx. 0,54 %). El propietario elige B' en D-158.
- D-157 (17-11, propietario). Autorización al Coordinador hasta las 23:59 del 17-11 para fusionar sin esperarle, en su orden, las PR de la migración y del histórico (T-379 PR 2a, 2b y 3, T-383, T-393, T-395, T-396, T-397, T-399, T-400, P43) y las del plan, con CI verde en la PR y en `main` y revisor conforme; la PR 2a solo con el entorno `registro` ya con sus secretos y su primera prueba en verde; no autoriza lanzar ni publicar. El Planificador planifica y no da comandos: los pasos manuales al propietario los da el Coordinador.
- D-158 (17-11, propietario). Histórico 2011-11 con la opción B': seccionado 2012 y la población 2011 de cada sección madre repartida entre madre e hijas según las proporciones del Atlas 2015, conservando los totales del Censo. Las 5 provincias con más del 0,1 % de votos sin asignar (03, 24, 27, 32, 33) se apartan y se declaran; D-70 no cambia ni hay excepciones nuevas en la puerta. Las 42 secciones sin fila, con D-126 y ajuste municipal si aparece la tabla oficial. Geometrías inválidas del INE: normalización auditada en la materialización (T-402, decisión técnica del Planificador).
- D-159 (17-11, propietario). Nombres en Actions: los 9 workflows con botón empiezan por «P»; los que no tienen botón llevan «_» delante para salir al final de la lista («_P90 Automático — Fusión automática», «_P90 Automático — Revisor de PR», «_P00 Campaña — <qué hace>»). Los dinámicos de GitHub no se pueden renombrar (diagnóstico de T-397 c). Amplía T-397.
- D-158 confirmada literal por el propietario (17-11, «sí» en el chat del Planificador): seccionado 2012, población 2011 de cada madre repartida con las proporciones del Atlas 2015 conservando los totales del Censo; 03, 24, 27, 32 y 33 apartadas y declaradas (APARTADA_VOTOS).
- D-161 (17-11, propietario). Umbral del 1 % de D-126/D-128 en 2011-11 con B': cuenta como estimada solo la población movida de cada madre a sus hijas más la rellenada; la que permanece en la madre no. Con #883@a286b6c queda BLOQUEADA_RELLENO 51 (1,70 %); 36 queda BLOQUEADA_SIN_DATO (corregido 17-11); 15, 22, 29, 34 y 47 pasan. Sustituye en 2011-11 el cómputo conservador (madre e hijas enteras).
- D-163 (17-11, propietario). P00 llama a P10-P30 con `contents: read`: ningún job de P10-P30 ni del reutilizable de registro pide más que `contents: read`/`actions: read` (si no, startup_failure de toda la P00); el push va con el token de la app y se quita el respaldo `github.token`; sobra `issues: write` en P20 `resolver_interfaz`. 2b mínima (propietario, 17-11): sin reutilizable de registro ni partir P30; entrada oculta `campana` (solo `workflow_call`, vacía por defecto) y los 7 jobs de registro y los pasos de registro de P30 `incorporar` con `campana == ''` (sin campaña, idéntico a `main`); en campaña, P20 en serie y grupos globales saltados, con tests; el registro de la campaña lo hace P00 en la PR 3. Garantía «la campaña no escribe en main»: (a) jobs de registro saltados con `campana` no vacía, con test; (b) ningún `git push` ni herramienta de registro fuera de esa lista cerrada, con test y control negativo; (c) entorno `registro` con la 2a. Se declara que `contents: read` no es barrera para el push con la app.
- D-166 (17-11, propietario). Diseño de T-313 (#898) aprobado con sus 11 recomendaciones: ventana tras la noche del 29-11 y T-379 PR 3 (regenerar las 71); `modulos/p21_base_poblacion.py` … `p32_resultados_distrito.py` y `ddd_core/p24_*`, `p25_*`, `p26_schema`; `git mv` con `ANTERIOR:` y copia en `legacy/` solo de los 8 módulos y las huellas; prefijos en JSON con `normalizar_prefijo` en lectores; alias permanente de `ddd-minimo-…-M06/M08` y solo lectura sin reutilización de `ddd-state-…`; nombre nuevo de productos solo al regenerar; Deslinde sin tocar (adaptador en `ddd_motor2`); carpetas R2 con D-131; `pre_m04` → `pre_p24`; congelación solo de la capa en curso; visor: texto y constantes, `kind` solo con alias.
- D-169 (17-11, propietario, literal en el chat del Coordinador): «Fusiona #898, #900, #902, #899, #901 y todas las PR de diseño y plan que te pase el Planificador hasta el 30-11, con CI verde y revisor conforme.» No incluye #888, #892 ni lanzar o publicar.
- D-171 (17-11, propietario). La doble vuelta se implementa ya, como paso aparte tras P32 (`herramientas/doble_vuelta.py`, #904), sin tocar el cálculo del ganador actual. Lee la tabla por partido y distrito que 07 ya escribe. Esa tabla se archiva en origen en R2, en el mismo job y con sha256, dentro de la PR de enganche a P30 tras la 2b (#899); nunca con un archivista posterior. Los territorios publicados necesitan regenerarse para tener votos por partido; recomendación: una sola regeneración tras el 29-11 junto con T-313.
- D-173 (19-11, propietario). La doble vuelta y la portada van a una V4 nueva (`visor/v4/`), con la portada de Vanesa (autora; «Nessa» en los ficheros) como entrada y el mapa de T-413; la V3 no se toca (cambia el punto 3 de D-172). Permiso de la autora: decisión literal del propietario («Vanesa me los ha entregado para que los publique yo, tengo todo su permiso y su intención»). Originales en `docs/ESTUDIOS/T415_V4_PORTADA/` (#908, #916), sin enlaces privados.
- D-174 (19-11, propietario; diseño 2.0.1 de T-415, #909). V4 en `/v4/`, en paralelo a la V3; versión `web/` por ficheros; imágenes generadas con IA, aportadas por la autora y asumidas por el propietario, con nota de origen; matriz jurídica fuera de la V4 inicial (tarea aparte con cotejo oficial); portada oscura y mapa según T-413; catálogo DOI en el estudio hasta Zenodo; «metodología» solo a lo publicado; vídeo con póster, subtítulos y transcripción, URL configurable. Textos de protección jurídica y reserva de acciones: de trabajo hasta revisión.
- D-175 (19-11, propietario). Vídeo de presentación en un bucket R2 aparte y público, solo para vídeos, con subdominio propio; el bucket de trabajo sigue privado.
- D-176 (19-11, propietario). Limpieza de R2 en tres pasos: (a) inventario de solo lectura (P70 «listar», lo lanza el Operador con frase del propietario); (b) cruce de cada carpeta con su uso y propuesta borrar/renombrar/conservar (enlaza con D-131); (c) borrado por el Operador con permiso del propietario, nunca antes de la regeneración posterior al 29-11.
- D-178 (19-11, propietario). Propuesta de limpieza de R2 de T-416 (#920) aprobada tal cual: ~2,2 GB de restos se borran tras la regeneración posterior al 29-11 (Operador, permiso del propietario en ese momento); `arc-e` se conserva sin listado de 2.º nivel; excepción Asturias. Coste actual ~0,10 USD/mes. Bucket público de vídeos creado (URL provisional r2.dev; falta subdominio propio y mover el vídeo).
- D-180 (19-11, propietario; T-400, #932). Histórico 2011-11: (1) K por partición insular con Hamilton y población de la época (07, 35, 38); (2) exención de suelo de 35-C02 (Fuerteventura); (4) 03, 24, 27, 32 y 33 siguen apartadas (D-70 sin cambios). La (3), padrón municipal de 1-ene-2011 para 08/36/51, se RETIRA: el Planificador la recomendó por error (no cuadra con el Censo de 1-nov-2011). Pendiente del propietario: totales municipales del Censo 2011 del INE con huella para 08/36/51 y exención de suelo de 38-G01 (115.715 < 120.634).
- D-181 (19-11, propietario). V4 = portada de Vanesa + «Explorar» con la V3 COMPLETA (nacional, comunidad, provincia, distrito, municipio y sección censal) y la doble vuelta como capa electoral (Tres bloques por defecto). Corrige el error del Planificador que encargó un mapa simple (T-413). Menú único en todas las páginas: Inicio · Comprender · Explorar · Metodología (Datos y Fuentes fuera, T-424). Metodología «Cómo se hace este mapa» y Comprender para el público general: sin jerga ni códigos internos (tests). Ningún «M0x» visible. Vídeo desplegado por defecto (https://media.diputadodedistrito.es/Video_DDD.mp4). Pie único con la reserva de acciones legales visible (levanta en el pie la nota de D-174). Publicada el 20-11 (P40 run 44688525685, #939) y ACEPTADA por el propietario.
- D-183 (20-11, propietario). Doble vuelta autonómica: votos de la elección autonómica vigente sobre el mapa vigente (no las generales); Asturias por concejo y Castilla-La Mancha por municipio, repartidos a sección con la regla de 07 y marcados «aproximado_en_distrito»; Murcia por sección (CREM); Extremadura fuera hasta dato municipal oficial; Ceuta y Melilla sin autonómicas. Marcas regionales de partidos ya aprobados siguen su bloque (Podemos Asturies, V-Q, MR-VE → Izquierdas). Castilla-La Mancha: el portal oficial está caído; el propietario busca el fichero (copia archivada oficial o datos.gob.es).
- D-184 (20-11, propietario). La V4 es la versión OFICIAL: portada en la raíz del dominio, sin «index.html» en las URL y con rutas relativas; la V3 sigue en /v3/ (#947). Publicada el 20-11. Datos y Fuentes (T-424) aparcados: no son prioridad. Textos de la auditoría externa (T-429, #949): «Mayoría simple en el distrito», mayoría absoluta de votos a candidaturas, línea de hipótesis y etiquetas para redes; «No sabes qué diputado es el tuyo» se mantiene; no prioritarios.
- D-185 (20-11, propietario). Histórico 2011-11: totales municipales del Censo 2011 del INE (con huella) para cuadrar 08, 36 y 51, o siguen bloqueadas; exención de suelo de 38-G01 como la de 35-C02.
- D-186 (20-11, propietario; T-430, #951). Web editable en minutos: repositorio aparte `ddd-web` en Cloudflare Pages (publicación en cada commit, vista previa por rama, pruebas de segundos); la web es la V4 y solo se mantiene la V4; la V3 queda como archivo congelado. Reparto: GitHub = cálculos y algoritmo; R2 = fuentes y mapas generados; la web lee de R2 a través de un índice «actual» con sha256, de modo que una regeneración se ve sin tocar la web. Dominio en GoDaddy apuntado a Cloudflare. El espacio de la web en R2 entra en el presupuesto de D-176/D-178. Zenodo no espera a esto: el dominio no cambia.
- D-187 (20-11, propietario). R2: los duplicados son insignificantes (57 objetos, 0,001 GB); el propietario quiere el inventario completo de R2 (T-432, `--inventario` en P74).
- D-188 (20-11, propietario). Estructura de R2 clara y en español, sin códigos ni números de run en los nombres: `fuentes/<organismo>/<año>/`, `fuentes/por-territorio/<territorio>/`, `mapas/{nacionales,autonomicas,historicos}/…/<provincia>/`, `interno/` (checkpoints y auditorías); el run y la huella van en `manifiesto.json`. Solo la versión vigente (también la web: se escribe la nueva, se comprueba y se borra la vieja; caché de 60 s). `web/actual/` solo en el bucket público `ddd-web-datos`. La regeneración posterior al 29-11 escribe ya en la estructura nueva; lo viejo se borra después junto con D-178. Diseño: T-435 (#961, #962).
- D-189 (21-11, propietario). Toda PR de diseño lleva la etiqueta `no-automerge`: el bot fusionó #961 antes de las correcciones y de la conformidad de T-430. Las fusiona el Coordinador tras la aprobación del propietario (D-169).
- D-190 (21-11, propietario). R2: los 22 paquetes P10 antiguos (1,82 GB) que no cita ningún contrato vigente se borran con D-178 después del 29-11; `fuentes/por-territorio/` e `interno/` llevan subcarpeta de ámbito (`nacionales/`, `autonomicas/`). Cruce clave a clave en #968 (2.042 objetos).
- D-191 (21-11, propietario). R2 se queda en ~12,3 GB tras la limpieza (las fuentes vigentes pesan 9,3 GB): se asume el exceso sobre los 10 GB gratuitos (~0,04 USD/mes); no se comprimen ni se recortan los paquetes P10. #842 sigue en borrador hasta el 29-11 (P00 3c cambia las campañas); #950 sigue aparcada (D-184).
- D-192 (22-11, propietario). Carga ligera para el móvil (#971, «sí a todo»): vista rápida del mapa con botón «Abrir el mapa interactivo», solo en el móvil al principio; fotos en dos tamaños y vídeo al pulsar; tope de 100 KB comprimidos en la primera vista; compresión en R2 según T-440; todo con la web nueva salvo la portada (T-442, #972).
- D-193 (22-11, propietario). No se crea `ddd-web`: la web sigue en este repositorio, con entorno de pruebas, servida desde R2 (T-430b); la fase 2 de T-430 se anula.
- D-194 (22-11, propietario). «Sí a todo» a #973: tres buckets, regla de Cloudflare, pruebas públicas `noindex` con datos reales, borrado al cerrar la PR, atajo de CI, publicación al fusionar, retirar Pages a las 2 semanas, `nueva.diputadodedistrito.es`.
- D-195 (22-11, propietario). «Sí a todo» a las 7 preguntas de #975 (T-444, cierre de la migración de workflows); #888 se decide antes de R1.
- D-196 (22-11, propietario). El código de Deslinde está en el repositorio público (`paquetes/deslinde/`, también en el historial) y la definición formal también es pública; las versiones antiguas siguen bajo Apache-2.0. El repositorio SIGUE PÚBLICO: Deslinde se protege con la licencia propietaria y el registro de la propiedad intelectual (T-281). Sustituye al plan de pasar el repositorio a privado (22-11, 23:42) y deja sin efecto la parte de repositorio privado de D-91 a D-95. T-445 y T-446 se cancelan. El asset `ddd-deslinde-v1.0.0.tar.gz` de `mapas-v1.0.0` lo borró el propietario (comprobado el 22-11: no queda en ninguna Release).
- D-197 (23-11, propietario; histórico 2011-11, T-448). Ceuta (51) queda EXENTA del tope del 1 % de población estimada (D-161): elige un diputado, es un único distrito y el reparto interno no cambia el mapa; pasa de BLOQUEADA_RELLENO a LISTA, con la exención y su motivo en el contrato (#982). Barcelona (08): diagnóstico de la sección 0804703001 con opciones medidas y preguntas (#985). Espejo de `1mun00.csv` del INE con la misma huella (sha256 ad95479c…8267, 105.319.154 B); lo sube el Operador con la frase del propietario (concretado en D-202).
- D-198 (23-11, propietario; T-443, #988). R2 con candidato y promoción: `mapas/` solo lo escribe la publicación (P40 promueve lo fijado tras verificar el sha256); `interno/` guarda por territorio `publicado/` y `ultimo/`, con head-object antes de subir para no pisar un run mayor; P75 escribe en `interno/doble-vuelta/<ámbito>/<territorio>/`; `fuentes/` es inmutable (una clave existente con otro sha256 falla). Matiza D-188 en `interno/` (vigente = publicado + último). Paquetes P10 (criterio del Planificador dentro de D-198): uno inmutable por edición del contrato en `fuentes/por-territorio/<ámbito>/<territorio>/<edición>/paquete.zip` (edición = año del contrato; un cambio dentro de la misma edición falla); sha256 en el manifiesto; se conservan las ediciones citadas por algún contrato de `configuracion/` y el resto se borra con D-178/D-190; `arc-e/paquetes-p10/` no se borra hasta tener la copia por edición de cada paquete citado, comprobada por sha256.
- D-199 (23-11, propietario; T-450, #984). Cloudflare: mirar primero Security → Events; Bot Fight Mode desactivado (hecho: medir-web da 200 en todo); la medición pasa con la cabecera secreta `MEDICION_CDN` (#991); `datos.` y `media.` sin retos (solo GET, HEAD y OPTIONS); pasan los bots verificados; sin límite de peticiones por ahora. Los cambios en Cloudflare los hace el propietario (§3 y §4 de #984). El aviso «Dangling A Record» es una falsa alarma: el dominio está verificado en GitHub Pages.
- D-200 (23-11, propietario; T-448, #985). La sección 0804703001 recibe la población del Censo por secciones como «reasignada». Regla general (contenida al 100 %, centroide dentro, mismo municipio) con test; sin tarea aparte para el aviso de los códigos de Cardona.
- D-201 (23-11, propietario; T-448, #992). Opción (b): Las Palmas (35016) y Cardona (08047) usan el dato del Censo sin cuadre con `1mun00`, declarado en el contrato con su diferencia (951 y 67). El reparto por islas de Las Palmas sigue en 6/1/1. Sustituye a la opción (c) dada antes el mismo día.
- D-202 (23-11, propietario). El espejo de `1mun00` va en R2, `fuentes/ine/2011/` (estructura de D-188), con la misma huella, su entrada en el índice de fuentes y la lectura de la CI desde ahí. Lo sube el Operador con la frase del propietario.
- D-203 (23 y 24-11, propietario; T-449). El portal de datos abiertos de la Junta de Castilla-La Mancha cambió de plataforma y el fichero oficial de 2023 desapareció. Las autonómicas de 2023 por municipio salen de la copia de la Wayback del fichero oficial (`Resultados_CLM_2023.xlsx`, captura 20261023040608, 322.602 B, sha256 7591997d…47ca), declarada «copia archivada del fichero oficial (fuente no oficial)». Cuadre exacto contra el Observatorio (nazioenbehatokia.eus, sha256 fijado), por provincia y en los 33 escaños, porque el PDF oficial ya no existe. La copia va en R2 en `fuentes-archivadas/` (`fuentes/` queda solo para originales oficiales, D-198); la doble vuelta, a nivel municipio sobre el M08 43745006294, con el CERA fuera de distritos (#1002, #1005).
- D-204 (24-11, propietario). Castilla-La Mancha se publica con una P75 «aut» completa de 16 territorios y un informe único que se fija en el pin, sin cambiar el publicador (P75 45382110179, 0 % sin casar; #1006, #1007; P40 45411223365: 68 territorios).
- D-205 (24 y 25-11, propietario; T-456, T-458). Fuera de la web los carteles «Doble vuelta no disponible…», «Resultados oficiales 2023 · vista provincial», «Simulación sin valor oficial» y el de copia archivada de Castilla-La Mancha (#1011). El mapa sigue siendo el nuestro (no el del Observatorio), nítido y con colores firmes; sin nivel de sección ni votos por sección; al clicar un distrito, ventana con su información; panel derecho con los datos arriba, sin foto ni licencias. Mapa y doble vuelta salen siempre del mismo run.
- D-206 (25-11, propietario). Diseño T-458 1.4.0 (#1013) «todo como recomienda»: colores fijos de bloque, la ventaja solo en el texto, panel con cifras. Implementación en T-459 a T-462.
- D-207 (25-11, propietario). En la ventana del distrito, imagen DEL DISTRITO (Wikimedia Commons, P18 del municipio, CC0/DP preferidas, en R2; sin imagen si no hay licencia válida), sin pie; la atribución, solo si es imprescindible, al final del scroll.
- D-208 (25-11, propietario). Nombre del distrito: capital de partido judicial (fuente oficial con sha256) y, si no la hay, el municipio más poblado; si se repite, «Madrid N».
- D-209 (25-11, propietario). Datos del distrito, en este orden: población, votos y bloque ganador con su %.
- D-210 (25-11, propietario; actualiza D-167/D-182). «Patriotas» pasa a «Derecha nacional»; Izquierda sigue igual; los nacionalistas, de izquierda o de derecha, ya forman un bloque propio. En origen (tablas fechadas nuevas, herramientas y tests, T-460), después P75 nac y aut, pin y P40, con frases. La tabla de bloques se elige explícitamente por ámbito (nac/aut): bloques_vigente() no puede cruzarlas.
- D-211 (24-11, propietario). Commits, mensajes de squash, PR y textos de los robots, sin Co-Authored-By, Claude-Session ni nombres de IA o de modelo (T-457, #1012).
- D-212 (25-11, propietario; T-499, #1016). V5 de la vista «Congreso · 2023 · Provincia»: una bolita por diputado con los escaños oficiales de 2023 (BOE-A-2023-18907), racimo compacto por partido con placa en Madrid, Barcelona y Valencia, % sobre votos a candidaturas, intensidad en 4 clases, paleta V4. Se prueba en pruebas.diputadodedistrito.es y pasa a producción con P40 cuando el propietario la apruebe (T-500); no espera a la migración a Cloudflare.
- D-213 (25-11, propietario, en el chat de la auditoría). La desigualdad de población entre distritos se acepta; no se abren tareas para corregirla. El resto de ámbitos, «a nivel top mundial». Todo dentro del plan semanal, sin gasto adicional: lo que se pueda se hace y lo que no, espera. Objeción pendiente (no decisión): no esperar a marzo; la propuesta de orden por dependencias sin fechas está sin confirmar.
- D-214 (26-11, propietario). «Sí al paquete de 2 días»: de la auditoría (`docs/AUDITORIAS/PLAN_MEJORA_2026-11-25.md` 2.0.0) se aprueban A (T-463), B solo el piloto (T-465+T-466: Burgos, Valladolid, La Rioja, Sevilla y Madrid; GerryChain puro y exacto frente a Deslinde, con decisión de seguir o no), F solo la licencia (T-473), G (T-476), H solo los indicadores (T-478), I solo el diseño de T-482 y K solo T-491. Hasta 6 sesiones a la vez. El resto de la auditoría sigue como propuesta. Un solo escritor del plan (el Planificador); el chat de la auditoría confirma los fragmentos que salen de su informe. Orden de escritores en `explorar.js`: T-459 → T-500 → T-486 → T-485 → T-482 → T-483 → T-484.
- D-182 (19-11, propietario; T-421, #930, #933). Bloques de las autonómicas: Junts y Contigo-Zurekin, DO, 100x100, Aliança Catalana, UxGC, Andalucistas y Alhora en Nacionalistas; SALF en Patriotas; Drago Verdes Canarias en Izquierdas; resto sin bloque. Faltan datos por sección de Asturias, Castilla-La Mancha, Extremadura y Murcia.
- D-179 (19-11, propietario). PRIORIDAD: la V4 en producción. La doble vuelta se calcula desde los paquetes `ddd-minimo-<run>-M08` ya archivados en R2 de los 71 publicados (sin regenerar) con una opción nueva de solo lectura en P70 (T-418). La primera V4 lleva los 52 territorios del Congreso (`nac`); los 19 `aut` (elecciones autonómicas) van en una segunda tanda cuando la tabla de bloques cubra sus partidos. El Coordinador lleva el camino crítico; al propietario solo se le piden firmas (fusión de código, frase de lanzamiento, permiso de publicar). La limpieza de R2, la 2a y la PR 3 de P00 no lo bloquean.
- D-177 (19-11, Planificador, criterio técnico). Doble vuelta: tabla de alias id de fuente → partido homologado derivada de `datos/homologacion_siglas/` (#914; 100 % de votos 2011-2023; «LA IZQUIERDA PLURAL» 2011 declarada, sin efecto de bloque); la regeneración no empieza sin #911, #914 y el `--alias` en P30. En campaña, P30 archiva en R2 en el mismo job y solo se salta el registro en main (opción A de T-379); el modo de inicio de P20 es una opción de la campaña (por defecto «Generar desde fuente territorial acreditada»); la campaña no publica salvo opción expresa del propietario (por defecto «No publicar») y siempre con la aprobación de `produccion`.
- D-172 (18-11, propietario; diseño de T-413, #905). Visor V3: la doble vuelta es lo principal, por defecto «Tres bloques» (dv_A); botones «Tres bloques», «Dos bloques», «Sin coaliciones» y «Más votado» (la mayoría simple queda secundaria, para comparar); coloreado por bloque, con alternativa por partido; modo oscuro solo en lo nuevo; línea de comparación entre reglas en la ficha; ventaja pequeña < 5 puntos; bloque y votos por partido de dv_A en el detalle (T-409); aviso fijo «simulación sin valor oficial». Publicar, decisión aparte.
- D-170 (17-11, propietario). Doble vuelta: unio.cat en Nacionalistas; JXC, JxG, CCD y CCD-CI sin bloque (abstención); T-409 comprueba con los datos que no cambian ningún ganador antes de implementar.
- D-168 (17-11, propietario; diseño de T-409, #901). Escenarios: A = los tres bloques coaligados a la vez; B («4») = solo Izquierdas y Patriotas, nacionalistas por partido; `dv_base` = doble vuelta sin coaliciones. PP en Patriotas. Dudosos: Cs, UPyD, EXISTE, PAR, CpM, Caballas, MDyC, PACMA, PIRATA y PT sin bloque; UPN/Navarra Suma, FAC y FE en Patriotas; PRC, Adelante Andalucía y Ahora Canarias en Nacionalistas; En Marea, CHA-IU, Verdes/LV-GV en Izquierdas; JXC, JxG, unio.cat y CCD, a desambiguar con la fuente; resto de menores sin bloque (abstención). Base: votos a candidaturas; empate alfabético con marca; dos finalistas del mismo bloque → al más votado; solo Congreso; campo `bloque_ddd`.
- D-167 (17-11, propietario). Escenario de doble vuelta con coaliciones (T-409, solo diseño ahora): bloques 1 Izquierdas, 2 Nacionalistas, 3 Patriotas; escenario adicional «4» = solo se coaligan 1 y 3 y los nacionalistas van por partido. Por distrito: primera vuelta por partido con votos reales; >50 % gana; si no, segunda entre los dos más votados y cada partido eliminado transfiere sus votos al finalista de su bloque (sin finalista de su bloque → abstención); sin tasas de trasvase inventadas. Cada partido en un solo bloque (los de izquierda nacionalista, en Nacionalistas), editable por el propietario. Tabla partido→bloque de todas las candidaturas 2011-2023 desde la homologación de siglas, con bloque «propuesta» que aprueba el propietario, en un fichero fechado. Escenario adicional junto a «gana el primero», que se conserva; visor, decisión aparte. Implementación tras la migración y T-313.
- D-165 (17-11, propietario). Renombrado M01-M08 → nomenclatura P de D-129 (T-313, actualiza D-102): 01→P21 Base y población, 02→P22 Geometría y adyacencias, 03→P23 Grafo, 04→P24 Solución inicial, 05→P25 Optimización, 06→P26 Producto certificado; auditoría P27 (P28 alternativas retirada por D-138); 07→P31 Agregación, 08→P32 Resultados por distrito; puerta P33. Datos guardados no se reescriben; lo nuevo con nombres nuevos y lectores que aceptan ambos (alias únicos). Los checkpoints con nombre viejo dejan de reutilizarse y se regeneran (inventario de lo reutilizable y test de flujo antes de reanudar). Diseño ya (solo documento); implementación tras T-379 PR 3 y T-383, una PR por capa.
- D-164 (17-11, propietario). T-379 PR 2a (#888) y lo que dependa de ella quedan en pausa; la migración sigue con el resto. La 2b y la 3 van sobre `main` en PR propias sin declarar `environment: registro` (GitHub lo crearía sin la regla «solo main»); la 2a se rebasa al final con la validación desde rama (aut11). Histórico congelado hasta terminar la migración.
- D-157 aclarada (17-11, propietario, en el chat del Planificador, por tercera vez): no habrá más frases de fusión; todas las PR están en la lista que dio al Coordinador. Nadie le pide «fusiona N»: el Coordinador fusiona bajo D-157 con CI verde en la PR y en `main` y el revisor conforme.
- D-162 (17-11, propietario). T-379 PR 2a (#888), opción A: P40 `publicar` y P70 `podar` NO se parten (un job y su grupo de concurrencia, como en `main`); los 2 secretos de la app van a los entornos `registro`, `github-pages` y `produccion`, los tres limitados a `main`; `preparar` usa `produccion` para personas y `registro` para robots. Cambia el §10 del diseño («se parten»). Consecuencia declarada en la PR: una 00 desde rama ≠ `main` falla en `actualizar_estado` y `manifestar`. Antes de fusionar, el propietario crea/revisa los 3 entornos (solo `main`) y copia los secretos.
- D-160 (17-11, propietario). Relevo automático de chats sin intervención del propietario (T-403): cada sesión de rol comprueba su contexto al empezar cada turno y, al 70 % del umbral, guarda lecciones, escribe su traspaso, crea su sucesora y avisa; la sucesora archiva a la predecesora. Con profundidad de linaje 7 o más (tope 8), avisa al propietario al móvil para que abra un chat nuevo. El Operador anota en la ficha las frases D-52 vigentes; el sucesor solo las acepta si el propietario ha dicho una vez en el chat del Operador que valen para el sucesor.

### Cola T-291 a T-367 (14 a 16-11)
| Id | Qué | Estado |
|---|---|---|
| T-291 | Equivalencia de seccionados 2026→2023 en M07 7.4.0, adaptador, 03 y votos por partido de 2026 (D-65, D-99) | HECHA (#749 #750 #752 #754) |
| T-292 | Sin uso (no consta en el traspaso ni en el repositorio) | — |
| T-293 | Revisor de PR solo con la etiqueta `revisar-ia` | HECHA (#769); activar el robot exige frase del propietario en su chat |
| T-294 | Analítica sin cookies: propuesta, Worker contador (#780) y contador en los visores (#783); guía de Cloudflare | EN CURSO (#778 y #783 abiertas; despliegue del propietario) |
| T-295 | Accesibilidad WCAG 2.1 AA del visor V3 | HECHA |
| T-296 | Óptimo exacto de D8 y hueco del ganador (estudio privado) | HECHA |
| T-297 | Deslinde 1.1 (D-98) | HECHA (#761) |
| T-298 | La batería sin INE: fuentes nacionales en R2 (ARC-E) | HECHA |
| T-299 | ZIP de Infoelectoral en R2 (ARC-E) e inventario de releases | HECHA (#757) |
| T-300 | Ficha de procedencia en el visor V3; la copia del catálogo en la P50 | HECHA la ficha; #765 RETENIDA hasta el fin de las P00 de los 71 y antes de la primera P50 (D-111) |
| T-301 | La P50 versiona la composición vigente de cada M06 | HECHA (#758) |
| T-302 | Almacen-m06-* a R2, permisos, lista BORRAR/CONSERVAR y script; índice (T-302d) | REVISIÓN (#785); luego script de borrado del propietario |
| T-303, T-304 | La batería parte del paquete P10 y su seguimiento | HECHA (#756 #759) |
| T-305 | La P50 restaura de R2 el estado M08/M06 podado | HECHA (#762) |
| T-306 | Inventario del histórico desde 2011 | HECHA (#770); plan del histórico pendiente |
| T-307 | El registro de la preparación escribe el id canónico; puerta estricta | HECHA (#776) |
| T-308 | Revertir los commits de robots de la tanda 1 de r2 | HECHA (#777) |
| T-309 | Endurecer las comparaciones `mismo_territorio` con ids legacy | PENDIENTE (después de la P50) |
| T-310 | maplibre-gl servido desde el sitio | HECHA (#781) |
| T-311, T-312 | Id canónico al reutilizar P10 (también en el contrato resuelto copiado) y revert de r3 tanda 1 | HECHA (#786) |
| T-313 | Migración de notación P (D-102, D-165): inventario #784; diseño aprobado (#898, D-166); implementación tras el 29-11 y T-379 PR 3 | ESPERA (ventana) |
| T-314 | ¿Bloquea `DURABLE_LINEAGE_INCOMPATIBLE` (CLM) «Generar desde fuente»? No: transitorio, solo bloquea «Reutilizar» (lectura de código sobre main actual). Orden: P10 → P00 por territorio seguidos | REVISIÓN (#788); camino crítico |
| T-315 | Declarar el fondo de OpenStreetMap en el texto de transparencia del contador (D-104); va en #783 (T-294 parte 2) | LISTA (Coordinador) |
| T-316 | Fondo de mapa propio servido desde Cloudflare, sin terceros (D-104) | PENDIENTE (después del 29-11) |
| T-317 | Actualización del plan 1.0.45 | HECHA (#787) |
| T-318 | Plan del histórico desde 2011 sobre 2023 (D-105): pasos 1-6 de T-306 §5 con coste; el paso A es campaña con ficha | LISTA (Coordinador; tras la P50 de los 71) |
| T-319 | Paquete de propiedad intelectual regenerado sobre main con `preparar_paquete_pi.py` (D-107), con sha256, para el propietario | HECHA (entregado al propietario; sha256 8bd30078…) |
| T-320 | Almacén M06: comprobación en vivo de las 51 claves en R2 y `-WhatIf` del script; el propietario borra (D-108) | PENDIENTE (tras la P50 de los 71: job de solo lectura nuevo, sin tocar workflows durante la congelación) |
| T-321 | Actualización del plan 1.0.46 | HECHA (#789) |
| T-322 | Tests de estado vivo (p. ej. `test_reanudacion_m08_huerfano`, CLM) con fixture congelado, sin skip condicional, y barrido de los que rompe la regeneración; sin tocar motor ni workflows | EN CURSO (Coordinador); bloquea la tanda 2 de r3 |
| T-323 | P10 desde R2 con aviso de cambios del INE (D-112) | PENDIENTE (después de la P50 de los 71) |
| T-324 | Actualización del plan 1.0.47 | HECHA (#791) |
| T-325 | Galería fotográfica territorial del visor V3 (PR #792, borrador hecho fuera de este sistema con ChatGPT). Revisión del Planificador (14-11): CI en rojo (guardian y 4 suites); `plain()` mete metadatos HTML de Commons en el `innerHTML` de un div suelto (un `<img onerror>` en el campo de autor se ejecuta: XSS; usar `DOMParser` o solo texto); el navegador de cada visitante llama en directo a es.wikipedia.org y commons.wikimedia.org y baja la foto de upload.wikimedia.org (ven su IP), contra el texto de transparencia («no comparte datos con terceros»); acepta cualquier licencia no vacía (no comprueba que sea libre); sin cabecera de versión ni copia en `legacy/` de `v3.js`, `v3.css` e `index.html`; los tests solo buscan cadenas con regex. Criterio de hecho: catálogo estático versionado (una foto por provincia y comunidad, con autor, licencia libre comprobada, enlace a Commons y sha256), imágenes servidas desde el propio sitio, sin llamadas a terceros al visitar; créditos solo como texto; topónimos en español; tests de comportamiento y CI en verde; revisor independiente. Se rehace en una PR nueva; #792 se cierra sin fusionar. | PENDIENTE (P2, propietario 14-11: justo después de la P50 de los 71; no entra en esa P50; se publica luego con una P50 «solo sitio» con frase del propietario) |
| T-326 | `test_catalogo_procedencia::test_versionado_coincide`: en PR compara contra `generar()` sobre raíz congelada; la comparación con el fichero vivo solo en el job «Estado vivo» de main (toca workflow/gating) | PENDIENTE (después de la P50 de los 71) |
| T-328 | Histórico, preparación sin CI (D-105, D-113; T-306 §5 pasos 2 y 4): (a) tablas de equivalencia año→2023 de 2011, 2015, 2016, 2019-04 y 2019-11 con la regla de M07 7.4.0 (sección entera al distrito de más población, sin repartir votos), reutilizando `herramientas/equivalencia_seccionados.py`, con los seccionados INE verificados por el sha256 de T-306 §3 (si la sesión no llega al INE, se para y se pide la descarga al Operador tras las P10 de r3); (b) identificadores BOE de las resoluciones de 2011, 2015, 2016 y 2019-04, de ficheros con fuente y sha256, nunca de memoria; (c) ficha de campaña `docs/autorizaciones/` del paso A (49 provincias × 6) con topes y reintentos. Sin lanzar nada; sin tocar motor ni workflows. | HECHA (#796) |
| T-327 | Actualización del plan 1.0.48 | HECHA (#795) |
| T-329 | `historico_campana.py` consume las tablas año→2023 | HECHA (#799) |
| T-330 | CSV de resultados de los BOE de 2011, 2015, 2016 y 2019-04 | HECHA (#802) |
| T-331 | Respuesta en solo lectura sobre el ensayo del 29-11 (flujo, modo, entradas) | HECHA |
| T-332 | Ensayo del 29-11: la 03 elige la elección 2026-11-29 sin cambiar la vigente, contratos de ensayo de nac22/nac42/nac52, `persist_state`, terminal verde propio, columna `ensayo` (D-118) | REVISIÓN (#800, borrador hasta tras la P50) |
| T-333 | Datos de ensayo por mesa con claves de sección 2026 (≥1 `partida` por provincia), marcados ENSAYO | REVISIÓN (#801, borrador hasta tras la P50); luego el Operador sube al release y copia sha256 |
| T-334 | Seguimiento de T-329: clave neutra `seccionado`, PUERTA con `m07` y `perdidos`, verificación de la tabla contra su fichero, KeyError de nacNN | HECHA (#804) |
| T-335 | Barrido único de tests de estado vivo antes de seguir r3 | HECHA (#803) |
| T-336 | P10 y P00 rechazan paquete o checkpoint con id no canónico y adquieren de verdad; el P10 informa ADQUIRIÓ/REUTILIZÓ | HECHA (#806) |
| T-337 | `preflight_preparacion_fuente` (l.110) acepta variantes de id en nombres de artefacto: estricto, sin alias | PENDIENTE (tras la P50) |
| T-338 | Cargador de `ddd_core/territorio_ids.py` sin `sys.modules` (rompía M02 en la P00) y barrido de arranque de 96 entrypoints | REVISIÓN (#808) |
| T-339 | Test de CI: `--help` de todos los entrypoints por ruta en subproceso limpio | LISTA (Coordinador) |
| T-342 | Puerta del histórico en código (≤0,1 %, 2011 con los valores de D-70 por provincia, contraste BOE por partido con tolerancia 0,10, cobertura total) | HECHA (#812) |
| T-343 | Mapa espejo→sigla BOE por elección y provincia para el contraste, con fuente y sha256 (no toca D-20) | LISTA (Coordinador) |
| T-344 | Solo lectura: por qué cambió el seccionado 2025 de aut11 en r4 y si cambia M06 | HECHA: no bloquea r4 (cada P00 usa su P10); sigue en T-347 |
| T-345 | Alias de coaliciones acreditados con la composición del BOE (D-120) y la equivalencia de D-121 | HECHA (#816) |
| T-346 | Transparencia: el sitio lo sirve Cloudflare (NEL/Report-To) en V1/V2/V3 y sitio | HECHA (#814) |
| T-347 | P10: fuentes ogc_features copiadas en R2, comparadas y con parada si cambian CUSEC o geometría (amplía D-112/D-117) | PENDIENTE (tras la P50) |
| T-348 | La misma frase de Cloudflare en nacional y Congreso | HECHA (#815) |
| T-349 | Ninguna rama reutiliza lo registrado con id no canónico (paquete electoral, población, M06, M08, par, composición); prepara de nuevo | HECHA (#818) |
| T-350 | Actualización del plan 1.0.50 | HECHA (#817) |
| T-351 | Ficha de la campaña histórica sobre 2023 | HECHA (#819); OBSOLETA por D-125 |
| T-352 | Traspaso del Coordinador (relevo 15-11) | HECHA (#821) |
| T-353 | Contratos electorales con id canónico en aut02, aut03, aut06, aut07, aut09, aut11, aut12 y test de guarda | HECHA (#824) |
| T-354 | Espejo en R2 de las 4 fuentes de mesas de Galicia (Xunta bloquea runners y nube) | HECHA (#827); subido por el propietario |
| T-355 | Publicación del histórico con fecha de elección (P50 y paso A con M08) | CERRADA sin fusionar (#830); la sustituye P43 (D-129) |
| T-356 | Fuentes del histórico a R2: 17 seccionados, Observatorio, 30832 y Censo 2011, con modo reanudar | HECHA (#829); faltan 10 piezas + 30832/Censo por subir (propietario, Windows) |
| T-357 | Estudio del padrón por sección 2011-2020 | HECHA (#831) |
| T-358 | Población por sección por elección con la regla de D-126 e informe por provincia | HECHA (#832) |
| T-359 | Rojo de main por carrera del catálogo de procedencia | NO NECESARIA (se cura sola) |
| T-360 | Paralelismo de la cadena: jobs de grupo único (estado operativo, promoción del catálogo) y catálogo en el mismo commit del registro | HECHA (#839) |
| T-361 | Catálogo de procedencia publicado por lista blanca, validación JSON y test de la copia en la P50 | HECHA (#765) |
| T-362 | Tests que leían INDEX/registros vivos con ids viejos | HECHA (#836) |
| T-363 | Actualización del plan 1.0.51 | HECHA (#838) |
| T-364 | Relleno refinado de la población del histórico (D-128) | HECHA (#840); T-364b (reglas del Planificador del 16-11) EN CURSO |
| T-365 | Histórico por época (D-125): contrato por elección, K por elección en el catálogo, piloto nac22 2019-11 | HECHA (#841); fichas #842 en borrador (se reescriben para la P00 nueva) |
| T-366 | Migración paso 1: P90 Automático (D-129) | HECHA (#845) |
| T-367 | Actualización del plan 1.0.52 y traspaso del Planificador | HECHA (#843) |
| T-368 | Migración paso 2: P70 Archivo (D-131, D-132) | HECHA (#851) |
| T-369 | Migración paso 3: P80 Verificación del motor (D-132) | HECHA (#853) |
| T-370 | Migración paso 4: P50 Publicación académica (D-133) | HECHA (#855) |
| T-371 | Actualización del plan 1.0.53 | HECHA (#846) |
| T-372 | Migración paso 5: P40 Publicación (D-134) | HECHA (#862); prueba real «solo el sitio» CONFIRMADA (run 43983546261; visor revisado por el propietario) |
| T-373 | Actualización del plan 1.0.54 | HECHA (#847) |
| T-374 | Revisor de PR dentro de P90 sin check-run `pruebas` skipped (D-135): diseño al detalle para el propietario | HECHA (#852; D-144) |
| T-375 | Migración paso 6: P10 Fuentes (D-136) | HECHA (#874) |
| T-376 | Migración paso 7: P30 Resultados electorales (D-137) | HECHA (#866) |
| T-377 | Migración paso 8: P20 Distritos (D-138, D-139), Opus | HECHA (#880) |
| T-378 | Migración paso 9a: diseño al detalle de P00 Campaña y la nueva forma de trabajar (D-140), Opus, sin código | HECHA (#850); decisiones en D-143 |
| T-379 | Migración paso 9b: implementación de P00 Campaña (D-140) | EN CURSO: PR 1 (#861) y PR 4 (#882) HECHAS; PR 2a (#888) con D-162 (sin partir P40/P70; 3 entornos con secretos), 2b y 3 (Opus) |
| T-380 | Retirada de los ensembles del motor viejo (D-141): registro del visor y publicación, luego Releases, configuraciones y selector v1 | ESPERA_APROBACIÓN (#849 fusionada): faltan publicación «solo sitio» y borrado de 3 Releases (frase del propietario); configuraciones con T-377 |
| T-381 | Detección automática de puntos de control incompatibles con el contrato vigente (sustituiría «empezar de cero»): diseño al detalle para el propietario | PENDIENTE (tras T-377) |
| T-383 | Migración paso 10: documentación renumerada (D-142) | PENDIENTE (tras T-379) |
| T-384 | Mensajes BATERIA_FALTA_PAQUETE_P10 y BATERIA_PAQUETE_P10_CORRUPTO de `bateria_motor.py` remiten a P70 · P71 (remate de D-132) | HECHA (#854) |
| T-386 | Comprobar en solo lectura que P90 crea el check-run `pruebas` en toda PR (código, solo docs, borrador, etiquetas) y preparar el cambio del ruleset `proteger-main` para exigir `pruebas` (D-144) | HECHA (Coordinador): `pruebas` existe en toda PR; falta el cambio del ruleset (propietario) |
| T-387 | Diseño 1.1 de P00 con D-145 y los arreglos del revisor; nueva revisión (Opus, solo documento) | HECHA (#858, diseño 1.1.4) |
| T-388 | P50 sube los mapas a Zenodo por la API (D-146) | HECHA (#859); faltan la integración desactivada, la política de ramas de `publicacion`, los tokens y la prueba en sandbox (propietario y Operador) |
| T-389 | Regenerar los 5 contratos de `configuracion/historico_epoca/` con las tablas de T-364b (T-365b; consecuencia de D-128) | HECHA (#865) |
| T-390 | Actualización del plan 1.0.57 | HECHA (#860) |
| T-391 | Rellenar los source_sha256 PENDIENTE_T333 de los contratos de ensayo con las huellas del release `fuente-ensayo-congreso-2026-11-29` y reanclar F10 | HECHA (#867) |
| T-392 | Actualización del plan 1.0.58 | HECHA (#869) |
| T-393 | Alta de los territorios-elección `<t>_hAAAA_MM` (D-150): resolución en `territorio_ids` y catálogo, sin versionar los YAML generados; test con fuentes sintéticas | HECHA (#873, diseño; implementación tras T-377) |
| T-394 | Actualización del plan 1.0.59 | HECHA (#872) |
| T-395 | Diseño de P43, publicación del histórico por fecha (D-152, D-154) | HECHA (#875, diseño; implementación tras la PR 3 de P00) |
| T-396 | Secciones con población sin geometría: asignación por centroide con geometría de otro año (D-153) | HECHA (#881) |
| T-397 | Lista de Actions sin basura (D-155) | EN CURSO: (a) HECHA (#877); amplía D-159 (prefijo «_»); (b) borrado de ejecuciones de retirados al terminar la migración; (c) diagnóstico de los dinámicos |
| T-398 | Actualización del plan 1.0.60 | HECHA (#879) |
| T-399 | Histórico 2011-11 con el seccionado del Censo 2011 y relleno de las 42 secciones sin fila (D-156) | EN CURSO: #883 con B' (D-158) y cómputo del 1 % de D-161; tras #886 (T-402) |
| T-400 | Provincia 35, 2011-11: puente topológico de La Graciosa (3502401010) ausente del seccionado; diagnóstico y PR | LISTA tras T-399 |
| T-401 | Actualización del plan 1.0.61 | HECHA (#885) |
| T-402 | Normalización auditada de geometrías inválidas del INE en la materialización del histórico, con huella e informe (D-158) | LISTA (Sonnet), coordinada con T-399 |
| T-403 | Relevo automático de chats: sección «Relevo» en las skills de rol y línea en CLAUDE.md (D-160) | LISTA (Sonnet) |
| T-405 | Histórico 2011-11, provincia 14 (Córdoba, `nac14`): M04 «invalid administrative component source binding»; solo diagnóstico y una PR por causa (Sonnet) | LISTA tras #886 (T-402) |
| T-397c | «_» en `auto-merge.yml` e inventario en solo lectura de ejecuciones de workflows retirados (D-159) | EN CURSO (session_01KQDtFsHKjJ6KXAcAdTMT6G) |
| T-407 | Actualización del plan 1.0.64 | HECHA (#896) |
| T-409 | Doble vuelta con coaliciones (D-167, D-168, D-170, D-171): diseño (#901) y herramienta (#904) HECHOS; detalle dv_A para el visor y enganche a P30 con archivo en origen (tras #899) | EN CURSO |
| T-408 | Actualización del plan 1.0.65 | HECHA (#897) |
| T-410 | Actualización del plan 1.0.66 | HECHA (#902) |
| T-411 | Permisos de comunicación entre sesiones sin pregunta (`.claude/settings.json`, lista cerrada de 6 y test) | REVISIÓN (#900) |
| T-413 | Visor V3 con escenarios de doble vuelta (D-172): diseño (#905) e implementación; sin publicar | EN CURSO |
| T-415 | V4: portada de Vanesa (D-173, D-174): originales (#908, #916), diseño (#909) e implementación (#918, #919, #924, #929) | HECHA |
| T-416 | Limpieza de R2 (D-176, D-178): inventario (run 44541851289) y propuesta (#920) HECHOS; borrado tras la regeneración | ESPERA |
| T-418 | Doble vuelta desde R2 para la V4: P75 en P70 (#923, #925, #928) | HECHA (52/52) |
| T-420 | Duplicados en R2 (listar_r2 1.1.0 #926, P74 --duplicados #935) | ESPERA (listado del Operador) |
| T-421 | Doble vuelta en las 19 autonomías: bloques (D-182) y datos de las 4 comunidades sin sección | EN CURSO |
| T-422 | Publicador V4: id de distrito de nac02 (#937) | HECHA |
| T-423 | V4 = portada + V3 completa con capa de doble vuelta (D-181, #939) | HECHA (publicada y aceptada) |
| T-424 | Datos y Fuentes para el público (#950, diseño) | APARCADA (D-184) |
| T-426 | Datos autonómicos de Asturias y Murcia (#944) | HECHA (Castilla-La Mancha espera fichero) |
| T-427 | Doble vuelta autonómica en P75 y en la V4 (#945, #946, #948) | HECHA (13 aut fijadas; 15 tras relanzar P75) |
| T-428 | V4 en la raíz del dominio (#947) | HECHA |
| T-429 | Textos de la V4 de la auditoría externa (#949) | REVISIÓN (no prioritaria) |
| T-430 | Web desde R2 en este repositorio (D-186, D-193, D-194; #951, #957, #973, #974, #976) | EN CURSO (P40 ya sube la web a R2; falta retirar Pages, D-194) |
| T-440 | Medir la web a petición desde P90 (#970, #983, #991) | HECHA (medir-web en 200 tras D-199) |
| T-441 | Diseño de la carga ligera para el móvil (D-192, #971, #994) | HECHA |
| T-442 | Portada ligera en `visor/v4/` (#972) | HECHA (falta P40 «Solo el sitio», con T-451) |
| T-443 | Aplicar la estructura de R2 (D-188, D-190, D-198), 5 PR (#977, #978, #988, #997, #998) | HECHA |
| T-444 | Cierre de la migración de workflows (D-195, #975) | HECHA (diseño fusionado) |
| T-445 | Repositorio público de publicación | CANCELADA (D-196) |
| T-446 | Comprobar que no queda código público | CANCELADA (D-196) |
| T-447 | Actualización del plan 1.0.75 | HECHA (#981) |
| T-448 | Histórico 2011-11: Ceuta exenta, Barcelona y Las Palmas, espejo de 1mun00 (D-197, D-200 a D-202; #982, #985, #992, #1001) | HECHA (espejo confirmado, run 45171401935) |
| T-449 | Autonómicas de Castilla-La Mancha 2023 por municipio (D-183, D-203; #986, #999, #1002, #1005) | HECHA (publicada con P40 45411223365) |
| T-450 | Bloqueo 403 de Cloudflare (D-199; #984, #991) | HECHA |
| T-451 | Vista previa al compartir: imagen, iconos y `twitter:*` (#993) | HECHA (publicada) |
| T-452 | Actualización del plan 1.0.76 | HECHA (#1000) |
| T-453 | Clave fija del informe de P75 y pin «autonomicas» con aut08 (D-204; #1006, #1007) | HECHA |
| T-454 | P40: reintento de deploy-pages ante la carrera del artefacto (#1008) | HECHA (validada en real) |
| T-455 | Actualización del plan 1.0.77 | HECHA (#1010) |
| T-456 | Visor V4: doble vuelta por los dos ids y fuera cuatro carteles (D-205; #1011) | HECHA (P40 45440595789) |
| T-457 | Sin nombres de IA en commits y robots (D-211; #1012) | HECHA |
| T-458 | Diseño del mapa V4 1.4.0 (D-205 a D-210; #1013) | HECHA |
| T-459 | Visor: panel con cifras, colores fijos, ventana del distrito, sin sección (#1014) | REVISIÓN |
| T-460 | Bloques: «Derecha nacional» en origen y tabla por ámbito (D-210; #1015) | REVISIÓN (luego P75 nac y aut, pin y P40) |
| T-461 | Nombres de distrito (D-208) | EN CURSO |
| T-462 | Imágenes de distrito desde Wikimedia (D-207) | EN CURSO |
| T-463 | Textos públicos veraces y DOI de la serie (D-214) | EN CURSO (publicación «solo el sitio» con frase) |
| T-464 | Actualización del plan 1.0.78 | REVISIÓN (esta PR) |
| T-465 | Banco de comparación: piloto de 5 territorios, diseño y ejecución (T-466) (D-214) | EN CURSO |
| T-473 | Página de opciones de licencia (D-214) | PENDIENTE (tanda 2) |
| T-476 | Datos abiertos 2: votos por partido y distrito (D-214) | PENDIENTE (tanda 2) |
| T-478 | Indicadores por mapa (D-214) | PENDIENTE (tanda 2) |
| T-482 | Diseño de «busca tu distrito» por calle (D-214) | PENDIENTE (tanda 2) |
| T-491 | A la primera: medir y reducir los fallos repetidos (D-214) | PENDIENTE (tanda 2) |
| T-499 | Diseño de la V5 con bolitas (D-212; #1016) | HECHA |
| T-500 | Implementación de la V5 (D-212) | PENDIENTE (tras #1014) |
| T-281 | Registro de la propiedad intelectual de Deslinde 1.0 (D-196; #995) | HECHA (presentado el 23-11 como «Programa de ordenador», con copia identificativa, memoria y declaración de IA) |
| T-379c | P00 3c (manifiesto por territorio, P40 desde campaña), relevo de T-379 | REVISIÓN (3c completa en #956, borrador; no se fusiona antes del 29-11) |
| T-432 | Inventario completo de R2 (#952, P74 44751091049) | HECHA |
| T-434 | P50 sin código de Deslinde, «Retomar» el depósito, prueba sin Release (#960) | HECHA (Zenodo real publicado: run 45066466320, DOI 10.5281/zenodo.24448721) |
| T-435 | Diseño de la estructura de R2 (D-188, D-190; #961, #962, #968) | HECHA (aplicarlo tras el 29-11: tarea nueva) |
| T-437 | P74 imprime el inventario en el log (#966; run 44871986746, 2.042 objetos, 16,47 GB) | HECHA |
| T-438 | P50 imprime el informe del depósito en el log (#967) | HECHA |
| T-439 | Actualización del plan 1.0.74 | HECHA (#969) |
| T-436 | Actualización del plan 1.0.73 | HECHA (#964) |
| T-433 | Actualización del plan 1.0.72 (#958) y pin de 15 aut (#955) | HECHA (P40 44869459141: 67 territorios en la V4) |
| T-425 | Actualización del plan 1.0.71 | HECHA (#940) |
| T-419 | Actualización del plan 1.0.70 | HECHA (#922) |
| T-417 | Actualización del plan 1.0.69 | HECHA (#917) |
| T-414 | Actualización del plan 1.0.68 | HECHA (#906) |
| T-412 | Actualización del plan 1.0.67 | HECHA (#903) |
| T-406 | Actualización del plan 1.0.63 | HECHA (#891) |
| T-404 | Actualización del plan 1.0.62 y traspaso del Planificador | HECHA (#887) |
| T-385 | Actualización del plan 1.0.56 | HECHA (#856) |
| T-382 | Actualización del plan 1.0.55 | REVISIÓN (esta PR) |
| T-340 | Ficha del paso A del histórico con Condición previa, Puerta y Mapa según D-115 (si el código no implementa la puerta, abre tarea) | EN CURSO (Coordinador) |
| T-341 | Actualización del plan 1.0.49 | REVISIÓN (#810) |

### Frentes y camino crítico (14-11)
1. Regeneración Deslinde 1.1: CERRADA y PUBLICADA (r4: 71/71 cadenas, P50 6/6 el 16-11 a las 12:03; Galicia con su espejo en R2). Se levanta la congelación. Siguiente: ensayo en seco del 29-11 (#800, #801) → T-360 paralelismo de la cadena → histórico D-125 (fuentes en R2, decisión del relleno de D-126, ficha por elección, #830 replanteada).
2. Ensayo en seco de la noche del 29-11, tras la regeneración.
3. Entre las P00 y la primera P50: fusionar #765 con revisión (D-111). Tras la P50: T-313 y T-309.
4. Almacenes M06: #785 y el script de borrado para el propietario.
5. Analítica (#778, #783) con la guía de Cloudflare; robot revisor (frase en su chat).
6. Histórico: T-318 tras la P50 (mapa 2023, D-105; autonómicas solo las 54 con datos por sección, D-113).
7. Aparcados hasta cerrar el repositorio: público nuevo, puente, Pages, Zenodo y runner propio (T-273, T-275, T-276, T-282, T-283, T-274B).
8. Al final: investigación (óptimo en medianos, `redist`, función A frente a D8 y exhaustivo con Deslinde 1.1, D-110) y corte 5.0.0; legislatura nueva tras el 29-11.

Frase de reanudación de r3: DADA en el chat del Operador, condicionada a #786 y T-314 en main con CI verde. Pendiente del propietario: Cloudflare del contador, registro de la propiedad intelectual (lunes 16-11), y crear el repositorio público y el runner cuando se cierre el actual.

### Identificadores
T-116 a T-127 los dio el planificador (despliegue de `/v2/`, registro, visor v2, Barcelona, histórico autonómico, fixture,
Gestor histórico, reintentos, mapa 350 fuera del registro, Zenodo). T-128 a T-170 están delegados al Coordinador, que los
asigna y los anota en `docs/ESTADO.md` (ampliado hasta T-190). Las actualizaciones del plan son T-171, T-191, T-192, T-193, T-204, T-209, T-219, T-236, T-266, T-290, T-317, T-321, T-324, T-327, T-341, T-350, T-363, T-367, T-371, T-373, T-382, T-385, T-390, T-392, T-394, T-398, T-401 y T-404. El planificador ha dado T-194 a T-404 (10 a 16-11; T-277 y T-292 sin usar; T-331 a T-340 y T-342 a T-362 los dio el Coordinador con acuerdo del Planificador). Siguiente libre: T-405.

## 0. Estado al cierre del 07-11 (17:15)
- En `main`: agentes (oro, revisor, forense), registro por ficheros (T-46), delegación, CI en paralelo (4 min, T-50),
  Environments (T-41), archivista R2 (T-47 + reintentos #447), revisor y forense en CI (T-48), exenciones gobernadas
  (T-49), huella de checkpoint (T-51), cadenas sin Mac (T-52), resultados ligeros (T-53), motor 7.6.7 + Fuengirola
  (T-44), hemiciclo con el BOE (T-42/T-45). PR #431 a #448 cerradas.
- En curso: T-54 auto-merge (escrito; espera la autorización del propietario en «Implementador nuevo»), revisión de
  #425 con el revisor, T-55 elección anterior del hemiciclo (BOE 2019-11), relanzamiento del archivista.
- Pendiente del propietario: entorno `produccion` con revisor, secreto `CLAUDE_CODE_OAUTH_TOKEN`, permiso de las 00
  de Barcelona, Alicante y Málaga («Ejecutar desde el principio») y Andalucía («Generar desde fuente territorial
  acreditada»); con ellas, 52/52 provincias y 19/19 autonómicas.

## 1. Estado (2026-11-07)
- Autonómicas: 18/19 completas; Andalucía aparcada (T-07).
- Nacional (52): **49 completas** (del 02 al 03-11 cerraron Las Palmas, Baleares, Cádiz, Madrid y Murcia; #419, M04 7.6.6,
  fusionada; Madrid y Murcia en el visor). **Bloqueadas: Málaga, Barcelona y Alicante** (M04 7.6.6 no las cierra; sin
  contradicción aritmética probada) → T-44.
- Ensembles publicados como escenario: Salamanca (run 41614546499), La Rioja (42384534739) y Sevilla (42385012998) (T-43).
- Arquitectura de agentes (`docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md`, §11 y §12):
  - **Paso 0** (framework P00-P60) · PR #427 · registro 1.0.95 · fusionada.
  - **Paso 1** · bloque 1 CI guardián de `main` · PR #428 · 1.0.96 · bloque 2 `CLAUDE.md`, `rules/` y hook de git ·
    PR #429 · 1.0.97 · bloque 3 skills de rol · PR #430 · 1.0.98. Hechos, **pendientes de fusión en orden
    #428 → #429 → #430** (encadenadas) y después la PR de este plan (1.0.99).
  - Siguientes del §12: (4) conjunto de oro → T-38; (5) revisor y forense → T-39, T-40; (6) Environments con
    aprobación → T-41.
- PR abierta sin tarea: #425 (portal Zensical y auditoría de archivo, Cantabria 50 verificado). Se revisa con T-39
  cuando exista; no se fusiona antes.
- Registro: 1.0.95 en `main` (#427); 1.0.96-1.0.98 en la cadena; 1.0.99 este plan; reservados 1.0.100 (T-38),
  1.0.101 (T-39) y 1.0.102 (T-40), 1.0.103 (T-42, #435), 1.0.104 (T-44, #436) y 1.0.105 (T-46, último manual).

### Asignaciones vigentes (07-11)
| Chat | Rol | Tarea | Siguiente |
|---|---|---|---|
| «Implementador nuevo» | constructor de agentes (Opus) | cadena #429-#430 al día; T-38 hecha en rama (PR tras #431) | T-39 + T-40 |
| «Implementador Motor» | ingeniero de motor (Opus) | T-44: Barcelona bien con `main`; Alicante (M04 7.6.7) y Málaga (exención) en una PR | 00 de las tres vía Operador |
| «T-42 Hemiciclo» | implementador (Sonnet) | T-42 (M08 desde blobs de `publicaciones_visor.json`) | — |
| «Implementador» | — | sesión inactiva | — |
| «Operador» | operador único (Sonnet) | T-43 hecha; **en pausa** | 00 de T-44, prueba de T-41 |
| «Paso 1 agentes DDD» | — | sesión inactiva; T-38 a T-40 pasan a «Implementador nuevo» | — |
| «DDD Plan» (este) | planificador | cola, registro, `PLAN.md` | — |

El propietario habla solo con el planificador para el qué; los permisos de lanzar, publicar y fusionar los da en el chat
que ejecuta (regla de siempre). Cada chat manda su línea de cierre al planificador (`send_message`).

### Ficheros con turno exclusivo (07-11)
- `ddd_core/m04_seed_engine.py`, `modulos/04_generar_semillas.py`, `modulos/05_optimizar_distritos.py`: «Implementador Motor» (T-44).
- `.claude/agents/`, `.claude/agent-memory/`, `evals/`: «Paso 1 agentes DDD» (T-38 a T-40).
- `herramientas/generar_hemiciclo.py` (nuevo) y plantillas del visor: «Implementador» (T-42).
- `.github/workflows/` lanzables y de publicación: «Implementador» solo para T-41, tras cerrar T-42; nadie más.
- `configuracion/politica_generacion_territorial_2025.yaml` y contratos `territorios/congreso_*`: libres; T-44 los pide
  al planificador si su tope agota el motor (decisión D-6).
- `docs/PLAN.md`: planificador. `docs/REGISTRO_DE_CAMBIOS.md`: número lo asigna el planificador al abrir cada PR.

## 2. Decisiones del propietario
### Tomadas (07-11 noche)
- D-8. El Observatorio Electoral de las Naciones (`nazioenbehatokia.eus`; Ion Ansa, Nora Galparsoro) se acepta como
  **fuente secundaria** para el histórico de generales (2011-2023, votos por partido y sección, seccionado INE de cada año),
  con contraste por muestreo frente a Infoelectoral y espejo propio con sha256 en el catálogo de procedencia (T-89).
  Se usa ya como contraste de T-71. Se pide permiso de reutilización a los autores (lo envía el propietario).
  La red del entorno Default permite `nazioenbehatokia.eus` (07-11).
- D-9. Histórico: las 6 generales al Congreso de 2011-11, 2015-12, 2016-06, 2019-04, 2019-11 y 2023-07; las autonómicas, después.
- D-10. Método: votos de cada elección pasada trasladados a los distritos vigentes (sin redibujar distritos por elección).
- D-11. T-81 y T-85 empiezan ya, sin esperar al cierre de la ola 2 (no lanzan ni tocan territorios); T-83 y T-84 después;
  T-82 (espejo de Infoelectoral desde el Mac) aparcada: solo si falla el contraste de T-89 o falta una elección.
- D-12. T-83 en dos pasos: primero (B) herramienta fuera de línea, sin lanzar, validada con 3 provincias; para publicar,
  (A) por la cadena M07/M08 con puerta 04, una elección por universo, lanzada por el Operador con permiso del propietario.
- D-13 (08-11). Peso de T-85 para secciones partidas: población de la sección vigente (padrón de M01); el área solo si la pieza
  no tiene población o falta el dato. Se confirma con la prueba del censo: el censo electoral de cada elección pasada llevado a
  las secciones vigentes con los dos pesos frente al censo real; si gana el área, se vuelve al propietario.
- D-14 (08-11). El entorno `produccion` ya no pide aprobación y `main` exige el veredicto del revisor (ruleset). La puerta humana
  de publicación es el permiso del propietario en el chat del Operador; T-87 se rediseña así.
- D-15 (08-11). Al cerrar la ola 2, el Operador lanza los ensembles de 10 (06, `ensemble_10`) de todos los territorios y provincias (T-91).
- D-16 (08-11). Visor en dos vistas (opción B): Nacional (Congreso, generales) y Autonómica (19 parlamentos), cada una con barra
  temporal y capas ganador por distrito, ganador por sección, rotación y participación; solo división administrativa oficial
  (Estado, comunidades, provincias, municipios, secciones). Comparador lado a lado (opción C) después. Difusión: LinkedIn,
  divulgación y revistas, con el visor estable, `/docs` y el DOI de Zenodo antes de la primera publicación.
- D-17 (08-11). El archivo en origen (T-72) tolera desajustes de códigos de sección entre el ZIP de Interior y el M06 si no
  superan el 0,5 % de los votos de la provincia: los reparte con la tabla de T-85 (D-13, población) y lista las secciones en la
  evidencia. Por encima del tope, fallo estricto.
- D-18 (08-11). **Autorización de estudios y difusión.** Ningún estudio ni análisis se encarga sin que el propietario apruebe antes
  la pregunta, y ningún resultado sale del repositorio sin su aprobación después. Los temas y textos de difusión (LinkedIn, prensa,
  revistas) los decide el propietario; los chats solo preparan, si él lo pide, datos técnicos verificados con fuente. El planificador
  propone y presenta el criterio técnico; el criterio político y de comunicación es del propietario. Cancelada T-100; el kit de
  comunicación (#514) queda como borrador sin uso hasta que el propietario lo revise.
- D-19 (08-11). Pregunta de estudio aprobada (D-18): «¿Cómo habría quedado el Congreso de 2023 con 350 distritos uninominales
  mayoritarios, con los mismos escaños por provincia, frente al reparto real?». Opción C: cada provincia se divide en tantos distritos
  como escaños reales de 2023 (`configuracion/resultados_oficiales_congreso_2023.csv`, BOE-A-2023-18907). Los 407 siguen siendo la
  propuesta del proyecto; los 350 son solo para este estudio. Se avisa de que es una simulación mecánica con los votos de 2023.
- D-20 (08-11). Las 83 filas de certeza BAJA de T-97 (`datos/homologacion_siglas/homologacion_siglas_generales.csv`, #524) se resuelven así:
  A) PODEMOS, EN COMÚ, PODEMOS-COM y PODEMOS-En (2015) → familia «Podemos–Sumar», con la sigla real de cada año en el mapa;
  B) CiU (2011), DL (2015) y CDC (2016) → familia «CiU–Junts»; C) UPN-PP (2011-2016) y NA+ (2019) → familia «UPN y coaliciones»;
  D) CHA-IU (2011) → «CHA-IU»; E) PDeCAT-E-CiU → PDeCAT, PSM-IV-EXM-EQUO → MÉS, EN MAREA → EN MAREA, Caballas y MDyC → sí mismos.
  Con D-20 la tabla puede aplicarse a la capa de rotación (T-84).
- D-21 (08-11). Tras T-91: publicación de los ensembles por el Operador con permiso del propietario, tras su revisión de lo que se
  muestra (D-18). Ensemble autonómico (diseño y lanzamientos): aparcado.
- D-22 (08-11). El propietario quiere lanzar a mano, sin chats, todo el Congreso (50 provincias, Ceuta y Melilla) o cualquier parte con
  un solo «0 Gestor de Campañas» y parámetros claros, en este orden: (1) elección: legislatura vigente o histórico (y cuál);
  (2) tipo: nacional o autonómico; (3) territorios: todos o lista de partes (provincias o comunidades por nombre, código o matrícula);
  (4) inicio: desde el principio, aprovechar fuentes o reutilizar progreso; (5) publicar en el visor: sí/no; (6) ensemble GerryChain:
  ninguno, 10 o 25. Lanzarlo él mismo equivale a su permiso para ese lanzamiento y esa publicación.
- D-23 (08-11). La lista de Workflows de Actions solo debe mostrar lo que el propietario lanza. Se eliminan los 12 desactivados
  (los «tachados»: F10, diagnóstico de fuentes, verificaciones de Andalucía, Cataluña y EleccionesDB), se archivan en `legacy/workflows/`
  los obsoletos y los internos que deben quedarse se agrupan al final con un prefijo común. El tamaño de letra es de GitHub (zoom del navegador).
- D-24 (08-11). Visor v2: el propietario aprueba la maqueta combinada (portada «Mapa» con vistas Congreso y Parlamentos autonómicos
  separadas + pestañas Nacional, Autonómico, Elecciones y Método de su modelo v3), especificada en `docs/ARQUITECTURA/visor_v2/`.
  Se avanza por versiones: la v1 de T-84 ya está en producción. Los textos los escribe el propietario en `web/textos.md`.
- D-25 (08-11). Generales del 29-11-2026: el RD 806/2026 (BOE-A-2026-20742, comprobado) cambia Cádiz 9→8 y Madrid 37→38. El propietario
  aprueba (1) una variante del mapa de 350 con los escaños de 2026 (solo Cádiz y Madrid se rehacen) y (2) adquirir ya candidaturas y siglas.
  Los 407 distritos no cambian (padrón INE 2025).

### Pendientes (08-11)
- D-7 (T-42, T-43). Permiso de publicación del hemiciclo y de los ensembles de La Rioja y Sevilla (en el chat operador).
- C-13 (T-64, #469). Alcance de comunidades de interés con partidos judiciales.
- Correo de permiso de reutilización al Observatorio Electoral de las Naciones (D-8): lo envía el propietario.
- Condicionadas: D-6 si el motor no cierra Alicante o Málaga (exención, techo propio o bloqueada); T-90 si el BOE cambia
  escaños; T-85 si la prueba del censo da ventaja al área.
- Superadas (08-11): D-1 y D-4 (la ola 2 completa los territorios), D-5 (D-14: `produccion` sin aprobación).

### Tomadas (07-11 noche)
- D-8. El Observatorio Electoral de las Naciones (`nazioenbehatokia.eus`; Ion Ansa, Nora Galparsoro) se acepta como
  **fuente secundaria** para el histórico de generales (2011-2023, votos por partido y sección, seccionado INE de cada año),
  con contraste por muestreo frente a Infoelectoral y espejo propio con sha256 en el catálogo de procedencia (T-89).
  Se usa ya como contraste de T-71. Se pide permiso de reutilización a los autores (lo envía el propietario).
  La red del entorno Default permite `nazioenbehatokia.eus` (07-11).
- D-9. Histórico: las 6 generales al Congreso de 2011-11, 2015-12, 2016-06, 2019-04, 2019-11 y 2023-07; las autonómicas, después.
- D-10. Método: votos de cada elección pasada trasladados a los distritos vigentes (sin redibujar distritos por elección).
- D-11. T-81 y T-85 empiezan ya, sin esperar al cierre de la ola 2 (no lanzan ni tocan territorios); T-83 y T-84 después;
  T-82 (espejo de Infoelectoral desde el Mac) aparcada: solo si falla el contraste de T-89 o falta una elección.
- D-12. T-83 en dos pasos: primero (B) herramienta fuera de línea, sin lanzar, validada con 3 provincias; para publicar,
  (A) por la cadena M07/M08 con puerta 04, una elección por universo, lanzada por el Operador con permiso del propietario.
- D-13 (08-11). Peso de T-85 para secciones partidas: población de la sección vigente (padrón de M01); el área solo si la pieza
  no tiene población o falta el dato. Se confirma con la prueba del censo: el censo electoral de cada elección pasada llevado a
  las secciones vigentes con los dos pesos frente al censo real; si gana el área, se vuelve al propietario.
- D-14 (08-11). El entorno `produccion` ya no pide aprobación y `main` exige el veredicto del revisor (ruleset). La puerta humana
  de publicación es el permiso del propietario en el chat del Operador; T-87 se rediseña así.
- D-15 (08-11). Al cerrar la ola 2, el Operador lanza los ensembles de 10 (06, `ensemble_10`) de todos los territorios y provincias (T-91).
### Pendientes
- D-5 (T-41). Crear en Settings → Environments el entorno `produccion` con el propietario como revisor requerido
  (repositorio público: disponible en cualquier plan). Sin él, T-41 se queda en el código.
- D-6 (T-44). Si tras el tope el motor no cierra una provincia: exención municipal, techo propio o documentarla
  como bloqueada (con la evidencia de T-44 delante).
- D-7 (T-42, T-43). Permiso de publicación en el visor del hemiciclo y de los ensembles de La Rioja y Sevilla
  (se da en el chat operador).
- D-4. Un cambio de M04 (T-44) invalida los checkpoints pre-M04 de los contratos con islas (Canarias, Islas Baleares,
  nacional Baleares, Las Palmas, Santa Cruz de Tenerife): visto bueno antes de que T-44 abra PR que toque M04.
- D-1. Completar Cantabria y Vizcaya por provincia o esperar a la activación por elección (T-04).

### Tomadas (07-11 noche)
- **R2:** se poda para quedar bajo los 10 GB gratuitos (T-76); el borrado solo con lista aprobada por el propietario.
  T-72 archiva solo el producto final.
- **Arquitectura de agentes (T-75, #474):** sí a los tres cambios: revisor obligatorio, allowlist de herramientas por rol en
  runtime y medir al Coordinador durante dos olas (coste por ola y fallos de coordinación).
- Red del entorno Default: `www.ine.es`, `www.mapa.gob.es`, `www.idescat.cat` (además de `boe.es`). `www.mapa.gob.es` resetea
  la conexión desde el proxy.
- **D-3:** se publica en el visor cada provincia al terminar su 00 (permiso por provincia en el chat del Operador).
- Secreto `CLAUDE_CODE_OAUTH_TOKEN` actualizado por el propietario (comprobar que el revisor corre en la próxima PR).
- Histórico 2019-11: todavía no. T-70 (D'Hondt): descartada.
- Archivo: R2 para el archivo de trabajo y Zenodo para versiones cerradas. Portal Zensical publicado en `/docs` del sitio.
- **T-64 (decisión del propietario):** nos quedamos con los partidos judiciales. #462 se reaplica en #470; la decisión de C-13
  sigue pendiente (#469).

### Tomadas (07-11)
- **Roles (07-11 noche):** el Coordinador (chat «Coordinador», Sonnet) es el socio operativo del propietario: recibe
  los cierres, sigue PR, CI y runs, archiva chats, junta lecciones y mantiene `docs/ESTADO.md`. El planificador solo
  planifica, por olas: cada ola, un chat nuevo que lee `PLAN.md` y `ESTADO.md`.
- **T-64 redefinida:** sin partidos judiciales de entrada. Estudio de comarcas no oficiales frente a partidos judiciales;
  si encajan razonablemente, se usan los partidos. #462 queda abierta sin fusionar hasta esa decisión.
- Cambios de criterio (unidades, fuentes, reglas): siempre se consultan al propietario antes de encargarlos.
- **Senado: descartado.** No tiene sentido para el proyecto; no se planifica ni se dedica tiempo alguno a él.
- D-4: visto bueno a M04 7.6.7 (Alicante); la próxima 00 de los territorios con islas empieza de cero.
- D-6 Málaga: exención de suelo municipal de Fuengirola (29054) en el contrato; techo y atomicidad sin cambios
  (Fuengirola 85.136 solo linda con Mijas y Benalmádena, atómicos; con cualquiera supera el techo).
- Una PR por objetivo, no por tarea (ver reglas).
- Fusiones sin intervención del propietario: el Operador fusiona por squash cada PR con `pruebas` en verde en la PR y en
  `main`, en el orden de la cola, y pone al día la siguiente (merge de `main`, sin force). Fallo de CI: no relanza; informa al
  planificador.
- Hemiciclo: primera entrega con las tres sumas sobre las 49 provincias completas, marcando las tres que faltan, con
  script y página en el visor (la publicación sigue necesitando permiso, D-7).
- Plan inmediato: §12 del framework en orden (oro, revisor y forense, Environments); producto en paralelo, a demanda
  y con tope.

### Tomadas (01-11)
- D-2: INE canónico; matrículas como alias, en español.
- #380 Cádiz y Barcelona: exención municipal en contrato y lanzamiento de 00.
- Álava: arreglar M04 para transferir varias secciones fronterizas (no exención ni aparcar).
- Madrid y Málaga: se mantiene la regla «un municipio que cabe bajo el techo no se divide»; reparación de población
  más profunda en contrato; si no basta, documentar como bloqueadas.
- Alicante: reparación más profunda (contrato). Pontevedra: reparación más profunda; si no basta, exención municipal.
- Las Palmas: exención municipal en contrato (no de toda Gran Canaria, 35-C01).
- Baleares: reparación más profunda (el reparto por islas no es viable: Ibiza+Formentera 1,41 de la media).
- Republicar en el visor La Rioja, Lugo, Santa Cruz de Tenerife y Tarragona.
- Ruleset: `puerta_admision` fuera de checks obligatorios (solo corre si la PR toca contratos).

## 3. Cola de tareas (07-11)
**Prioridad del propietario (07-11): poner en uso los agentes; nada le interrumpe hasta lograrlo.** Camino crítico:
fusionar #428 → #429 → #430 → #431 → T-38 (1.0.100) → T-39 (1.0.101) y T-40 (1.0.102). Producto (T-42 a T-44) en
pausa: sin PR, sin preguntas al propietario y sin lanzamientos hasta que el revisor y el forense estén en `main`.
T-41 va después. Las dudas de los chats van al planificador, no al propietario.

### T-38 · Conjunto de oro para revisor y forense (P1, §12 paso 4)
- Alcance: casos de evaluación en `evals/oro/`: las 12 causas raíz del §9 del framework (run o PR de referencia,
  síntoma, causa esperada en una línea) y ADV-01 a ADV-16 de `docs/ARQUITECTURA/referencias/AUDITORIA_CHATGPT_PLAN_V2_2026-11-02.md`
  §7.2 (diff o PR original, defecto esperado), más los casos de calibración 29E del metaagente («candidato modificado
  tras la revisión», «reparaciones agotadas con criterio fallido»). Un JSON por caso con esquema común y
  `herramientas/evaluar_oro.py` (biblioteca estándar) que puntúa una salida JSON de agente contra lo esperado y anota en
  `evals/oro/LIBRO_DE_COSTES.md` tokens, acierto y si fue a la primera.
- Fuera: crear agentes (T-39, T-40); lanzar nada; descargar artefactos (los casos citan PR, runs y `diagnostico/*`).
- Dependencias: #427-#430 fusionadas.
- Turno exclusivo: `evals/`, `herramientas/evaluar_oro.py` (nuevo).
- Chat: «Paso 1 agentes DDD». Modelo: Opus.
- Hecho: ≥ 30 casos con fuente verificable (PR, run o fichero en `main`); el evaluador da 100 % con la salida esperada y
  0 % con una vacía (test en `tests/`); gobernanza R015 y guardián de `main` en verde; PR con su número de registro.

### T-39 · Subagente revisor independiente (P1, §12 paso 5)
- Alcance: `.claude/agents/revisor.md` (Sonnet, solo lectura, salida JSON con veredicto ligado al SHA del HEAD:
  unidades y CRS, gobernanza VERSIÓN/legacy, huellas M05/N08, numeración del registro, tests rojo/verde); la skill
  `revisar-pr` lo invoca.
- Dependencias: T-38.
- Turno exclusivo: `.claude/agents/revisor.md`, `.claude/skills/revisar-pr/`.
- Chat: «Paso 1 agentes DDD».
- Hecho: sobre el diff original de los casos de revisión del oro caza ≥ 80 % de los defectos y no bloquea ninguna de
  tres PR limpias ya fusionadas; resultados y coste en el libro; primera revisión real: #425.

### T-40 · Subagente forense de runs (P1, §12 paso 5)
- Alcance: `.claude/agents/forense.md` (Sonnet, solo lectura; dado un run da la causa en cinco líneas) y
  `.claude/agent-memory/forense/MEMORY.md` con el catálogo de causas del §9; la skill `diagnosticar-run` lo invoca.
  Lee anotaciones (`check-runs/<job>/annotations`) y `diagnostico/auto/`, nunca artefactos.
- Dependencias: T-38. En paralelo con T-39 (ficheros distintos).
- Turno exclusivo: `.claude/agents/forense.md`, `.claude/agent-memory/forense/`, `.claude/skills/diagnosticar-run/`.
- Chat: «Paso 1 agentes DDD».
- Hecho: causa correcta en ≥ 10 de los 12 runs del oro, en ≤ 5 líneas; coste por diagnóstico anotado en el libro.

### T-41 · Lanzamientos y publicaciones con Environments y aprobación (P2, §12 paso 6)
- Alcance: los jobs con efecto (00 manual, «Activación por Elección», «05 Publicación del Visor», publicación de
  ensembles) declaran `environment: produccion`, de modo que cada dispatch espera el clic del propietario en GitHub
  (sin modelo). Los encadenados de `github-actions[bot]` y los registros con la app `ddd-registro` no deben quedar
  esperando: el entorno se aplica solo al dispatch manual (expresión en `environment`) o se documenta la excepción.
  Actualizar las skills `operador`, `lanzar-00` y `publicar-visor` (el operador pasa a preparar y verificar).
- Dependencias: D-5; T-42 cerrada (mismo chat); Paso 1 fusionado.
- Turno exclusivo: `.github/workflows/ejecucion-completa-proyecto.yml`, `activacion-*`, `desplegar-visor-publico.yml`,
  `_reutilizable-publicar-sitio.yml`, workflow de escenarios/ensembles; skills citadas.
- Chat: «Implementador» (código) + «Operador» (una sola prueba con permiso).
- Hecho: un dispatch manual queda en «Waiting» hasta aprobar y corre tras el clic; una 00 encadenada por el bot no
  espera; los robots registran en `main` sin `GH013`; suite de gobernanza de workflows en verde; validado con una sola
  ejecución antes de abrir paso al resto (regla de infraestructura).

### T-42 · Hemiciclo y tabla de resultados (P2, producto; alcance confirmado 07-11)
- Alcance: `herramientas/generar_hemiciclo.py` lee los M08 registrados de las 49 provincias completas y suma escaños de
  tres maneras: (a) reparto real 2023 (D'Hondt oficial), (b) elección anterior (generales 2019-11, si el repositorio
  tiene sus resultados; si no, la columna queda marcada «sin fuente» y se abre subtarea), (c) uninominal propio
  (ganador por distrito DDD). Salida JSON y CSV con totales de España por partido y lista de provincias que faltan
  (Málaga, Barcelona, Alicante); página del visor con hemiciclo SVG y tabla, conmutando las tres sumas.
- Fuera: publicar (D-7, chat operador); cambiar M08 o el motor.
- Dependencias: ninguna de código (puede empezar ya; la PR va tras la cadena #427-#430).
- Turno exclusivo: `herramientas/generar_hemiciclo.py`, plantilla/página nueva del visor.
- Chat: «Implementador». Modelo: Sonnet.
- Hecho: (a) en las 49 provincias coincide escaño a escaño con el oficial por provincia; (c) suma exactamente los
  distritos de esas 49 (uno por distrito); test con dos provincias sintéticas; página revisada en local con captura;
  topónimos en español y etiqueta «Nacional»; registro con su número.

### T-43 · Publicar los ensembles de La Rioja y Sevilla (P3, operador)
- Alcance: con la skill `publicar-visor`, republicación de ensemble con `ensemble_sha256` (#418, #421, #424) para
  `congreso_la_rioja` y `congreso_sevilla`; primero La Rioja como prueba, luego Sevilla. Solo añade en `ensembles`.
- Dependencias: D-7 (permiso en el chat operador). Sin código.
- Turno exclusivo: ninguno (escribe el workflow en `orchestracion/publicaciones_visor.json`).
- Chat: «Operador». Modelo: Sonnet.
- Hecho: `publicaciones_visor.json` con las dos entradas de ensemble y el visor mostrando 10 candidatos en cada una;
  línea de cierre al planificador con los runs.

### T-44 · Málaga, Barcelona y Alicante: estudio de motor con tope (P2, producto)
- Alcance: diagnóstico y arreglo del motor en local con los volcados de `diagnostico/auto/` (o pedir M01+M03 al Mac):
  Barcelona primero (hard=1, la más cerca), luego Alicante y Málaga. Sin cambiar suelo, techo, K ni atomicidad.
- **Tope**: dos ciclos de reparación por provincia (regla de la auditoría) y ninguna 00 sin M05 hard=0 y M06 OK en
  local. Agotado el tope, informe de factibilidad (¿existe partición sin partir municipios que caben bajo el techo?)
  y la provincia pasa a D-6.
- Dependencias: ninguna; si toca M04, D-4 antes de la PR.
- Turno exclusivo: `ddd_core/m04_seed_engine.py`, `modulos/04_generar_semillas.py`, `modulos/05_optimizar_distritos.py`.
- Chat: «Implementador Motor». Modelo: Opus.
- Hecho: por provincia, M05 hard=0 y M06 OK en local con el motor nuevo, o informe de factibilidad para D-6; sin
  regresión (GeoJSON e informe idénticos en Pontevedra, Álava y Cádiz); suite completa en local; una PR por causa.
  Luego la 00 «Ejecutar desde el principio» la pide al planificador (lanza el operador con permiso, un territorio de prueba primero).

### Lote del 07-11 (tarde) · autorizado por el propietario; sin intervenir hasta el final
Orden de fusión (Operador): #430 → #436, luego T-46 y el resto según lleguen. Al final, una sola lista para el
propietario: ajustes de Settings y permiso de las 00.

| Id | Objetivo | Chat | Turno exclusivo | Hecho |
|---|---|---|---|---|
| T-46 | Registro por ficheros (`docs/registro/`, número asignado por la CI al fusionar) y delegación del qué en el planificador dentro de `CLAUDE.md` | «Implementador nuevo» (Opus) | guardián, reglas y skills de registro, `CLAUDE.md` | Dos PR en paralelo no chocan en el registro; última PR con número manual (1.0.105) |
| T-48 | Revisor en cada PR y forense en cada 00 fallida, en CI (`claude-code-action`) | «Implementador nuevo» | dos workflows nuevos | Sin secreto se saltan limpiamente; con él, veredicto en la PR e issue con la causa |
| T-47 | Archivista R2: copia con sha256 de los artefactos antes de caducar, manifiesto `orchestracion/archivo_r2.json` | «T-47 Archivista R2» (Sonnet) | `archivar-artefactos-r2.yml`, herramienta nueva | Idempotente y con tests; una ejecución tras fusionar (permiso dado) |
| T-41 | Environments con aprobación solo en el dispatch manual | «T-42 Hemiciclo» (Sonnet), tras T-45 | workflows lanzables y de publicación | Los encadenados del bot no esperan; gobernanza de workflows en verde |
| T-45 | Proclamación oficial de 2023 (BOE) como dato para el hemiciclo | «T-42 Hemiciclo» | datos del hemiciclo | Contraste por provincia; diferencia CERA ubicada |
| T-49 | `decided_at`, `reason` y `evidence` en las 17 exenciones, comprobador en CI y `CONTRACT_POLICY_STALE` | «T-49 Exenciones gobernadas» (Sonnet) | política y contratos (salvo Málaga hasta #436) | Exención sin metadatos = CI en rojo |
| T-07 | Andalucía en local (motor) | «Implementador Motor» (Opus), tras #436 | motor | M05 hard=0 y M06 OK en local o evidencia para decisión |

Pendiente para la lista final del propietario: «Allow auto-merge» (P2), entorno `produccion` con revisor (D-5),
secreto `CLAUDE_CODE_OAUTH_TOKEN` (T-48) y permiso de las 00 de Barcelona, Alicante, Málaga y Andalucía.
La red del entorno Default ya permite `www.boe.es` y `boe.es` (07-11).

### Ola 2 (07-11 noche) · solo completar territorios y dejar el Gestor listo para la legislatura vigente
Histórico aplazado hasta entonces (T-81 a T-85 no se encargan); los votos por partido de 19 provincias esperan. R2: el
sobrecoste es de unos 23 céntimos al mes; no se poda (T-76 cerrada, #480 sin fusionar). Hecho de la ola: 52/52 y 19/19
«Cadena completa validada» y en el visor.

| Id | Objetivo | Quién | Estado |
|---|---|---|---|
| T-79 | Nacional: Alicante y Málaga (00 en `produccion`; si fallan: forense, reparación con el tope de T-44 en chat Opus de motor); Barcelona: completar electoral; Ceuta: 00 según forense (pob. INE 3826 ≠ M06 3723). Cada uno se publica al terminar (D-3) | Coordinador + Operador | Barcelona territorial success; Alicante en curso; Málaga en cola |
| T-80 | Andalucía autonómica: 03 falló por paquete electoral caducado (run 37150399030); preparar con `reutilizar=false`, `prepare_one`, 00 Reutilizar y publicar | Coordinador + Operador | Pendiente de permiso del propietario |
| T-86 | Gestor listo para la legislatura vigente | chat Opus del planificador | En curso |

### Ola del 07-11 noche
Cierres al Coordinador. Alcance y criterio de hecho: los del encargo de cada chat.

| Id | Objetivo | Chat | Hecho |
|---|---|---|---|
| T-72 | Archivo en origen: M06/M08 a R2 con sha256 en `registrar`, composición y votos por run | session_01KQDtFtH5s6XFb1sTEQE75B (Opus) | Fusionada (#471); falta una 00 de prueba (Operador, permiso del propietario) |
| T-71 | Recuperar composición y votos por partido de las 47 provincias sin ejecuciones (centroides INE 2023 sobre el M06 publicado) | session_01KQDtFtsKtpcWSzdeGAmwMS (Sonnet) | ≥ 40 de 47 exactas; las que no cuadren, a 00 con motivo. Añadido (D-8): contrastar los votos por partido y sección de 2023 con `nazioenbehatokia.eus/data/202307/sekzioa/{cpro}.json` e informar de las discrepancias |
| T-74 | Catálogo de procedencia único (`orchestracion/catalogo_procedencia.json`, derivado de 5 ficheros) | session_01KQDtFs6b53QY496wZn2gSX (Opus) | PR #473; check en CI |
| T-73 | Portal Zensical público (P3) en `/docs` del sitio, dentro de `_reutilizable-publicar-sitio.yml` | por abrir, tras T-71 (Sonnet) | `zensical build --strict` en verde, enlaces comprobados; sin publicar |
| T-75 | Aplicar el metaagente a DDD (solo documentación) | session_01KQDtFvFEZ1wPrxBQpGsj9w (Opus) | En curso |
| T-76 | Podar R2 bajo 10 GB; borrado solo con lista aprobada | session_01KQDtFtGG21KnDVVU6JUnni | En curso |
| T-77 | Incorporar T-75: estado de tarea y de efecto externo, línea de cierre ampliada, ficha del ingeniero de motor, topes y libro de costes por chat | session_01KQDtFsDv6WYYdvBHC1Ji7t (Sonnet) | Skills y fichas coherentes; PR con registro |
| T-78 | Gobierno de agentes en runtime: allowlist por rol y revisor como check obligatorio (JSON del ruleset, lo aplica el propietario) | session_01KQDtFru1JVfTuBosCwaVsu (Opus) | Herramienta denegada se bloquea; PR no-automerge |
| T-87 | Cadena de publicación con un solo lanzamiento (D-14): al cerrar la puerta 04 de una 00, el Operador, con permiso del propietario en su chat, lanza una sola orden que dispara juntos la 05 del visor con `production_run_id` de esa 00 y `publicar-version-mapa.yml` (Release, Zenodo); el archivo R2 lo cubre T-72 y los resultados ligeros ya se encadenan con `publicaciones_visor.json`. Toca workflows compartidos: avisar al Coordinador | por abrir (Opus), después de la 00 de prueba de T-72 | PR no-automerge; sin el lanzamiento del Operador no publica nada; probado con un territorio y sin publicar hasta el permiso del propietario |
| T-88 | Revisar las skills de verificación de plan y TDD de `mattpocock/skills` (MIT) y, ampliada (07-11), los plugins oficiales de revisión de PR y de desarrollo por fases de `anthropics/claude-code` frente a `revisar-pr`, el revisor de CI e `implementador`; llevar a `implementador` y `planificador` solo lo que falte, con el criterio de `disenar-agente`; sin instalar skills externas | por abrir (Sonnet), después de T-77 | Una PR con la comparación (qué se toma, qué no y por qué) y las skills ajustadas; sin aumentar el contexto cargado por defecto |
| T-89 | Espejo del Observatorio Electoral de las Naciones (D-8): bajar `data/index.json`, `data/{k}/sekzioa/{cpro}.json` de las 6 generales y `geo/sekzioak/{año}/{cpro}.json` de sus 6 seccionados, con fecha, URL y sha256 por fichero, a R2 (no a git); entrada en el catálogo de procedencia; contraste por muestreo (3 provincias × 2 elecciones) con Infoelectoral 2023 del release espejo y un lector Python del formato compacto (`s`,`k`,`f`,`b`,`r`) | por abrir (Sonnet) | Espejo completo y verificable; informe del contraste; sin publicar ni tocar el visor |
| T-85 | Equivalencia de secciones (D-9, D-10): tabla de cada seccionado de elección (INE 2012, 2015, 2016, 2019, 2020) al seccionado de los distritos vigentes, desde las geometrías del espejo T-89 o del INE (CC BY 4.0); 1:1 cuando código y geometría coinciden; si una sección se parte, peso por población de la sección vigente y área de reserva (D-13), con la prueba del censo de ambos pesos; se informa del % de votos no 1:1 por provincia y elección | por abrir (Opus), ya | Tabla versionada con sha256 y fuente; pesos que suman 1 por sección; tests; sin lanzar ni publicar |
| T-81 | Inventario de fuentes del histórico (D-9): por elección y provincia, qué da el Observatorio (generales por sección; autonómicas por municipio y, donde existan, por sección), qué da Infoelectoral y el seccionado de cada una; huecos y discrepancias del contraste de T-89; propuesta de autonómicas para después | por abrir (Sonnet), ya | Documento en `docs/ESTUDIOS/` y JSON con fuente, fecha y sha256; sin datos de memoria |
| T-83 | Reagregación (D-10, D-12): paso B, herramienta fuera de línea que lleva los votos de cada general 2011-2023 (espejo T-89) a los distritos vigentes con la tabla de T-85; ganador y votos por partido por distrito en `datos/resultados/historico/`; validada con 3 provincias (una con muchas secciones partidas) y cuadre de totales provinciales con Infoelectoral; el paso A (M07/M08, puerta 04) se encarga al validar B | por abrir (Sonnet), tras T-85 (peso fijado en D-13) | Totales provinciales cuadran al voto; tests; sin lanzar ni publicar |
| T-90 | Preparar las generales del 29-11-2026 (anunciadas por Interior; fecha y convocatoria se confirman en el BOE, nunca de memoria): (1) del real decreto de convocatoria, escaños por provincia en un CSV con fuente y sha256, y diferencias con 2023; si cambia alguno, se para y se presenta al propietario (afecta al número de distritos); (2) universo electoral nuevo (como 02202307) en contratos y catálogo; (3) espejo del ZIP por mesa de Infoelectoral en un release, como `fuente-infoelectoral-02202307`, en cuanto se publique; (4) prueba en local de la 03 y M07/M08 con una provincia. No altera la legislatura vigente hasta decisión del propietario | por abrir (Sonnet), ya | Pasos 1 y 2 en una PR antes del 29-11; 3 y 4 cuando Interior publique; sin lanzar ni publicar |
| T-91 | Ensembles de 10 (06, `ensemble_10`) de los 52 territorios nacionales y las 19 autonómicas, por orden del propietario (D-15); primero uno de prueba y luego el resto por lotes; el 50 sigue bloqueado | Coordinador + Operador, al cerrar la ola 2 | Ensembles de todos los territorios registrados; publicar, solo con permiso |
| T-92 | Resultados de las generales del 29-11-2026 sobre los distritos vigentes: paso A (03, M07/M08, puerta 04) de las 52 provincias y publicación (D-14). Se encarga cuando T-90 confirme los escaños del BOE; si cambian, antes decide el propietario. Orden de la cola tras T-92: T-83, T-87, T-91, T-83 A y T-84, autonómicas del histórico | en espera de T-90 paso 1 | 52/52 con M08 2026 y en el visor con permiso del propietario |
| T-84 | Visor en dos vistas (D-16): Nacional y Autonómica, barra temporal, capas ganador por distrito y por sección, rotación y participación; geometría por provincia cargada una vez y color por `feature-state`; secciones en PMTiles. Empieza ya con 2023 (M08 publicados y composición) y suma el histórico al cerrar T-83 | por abrir (Sonnet), ya | Vista Nacional funcionando en local con 2023; capturas en móvil y escritorio; sin publicar |
| T-93 | Kit de comunicación (D-16): nota metodológica de una página, ficha de prensa, 5-6 textos de LinkedIn para revisión del propietario e imágenes generadas desde el visor; aviso «mapa de investigación sin valor oficial» y DOI; cifras solo de productos con fuente y sha256 | por abrir (Sonnet), tras la vista Nacional de T-84 | Borrador hecho (#514, «T-93b»); sin uso hasta la revisión del propietario (D-18) |
| T-94 | Artículo para JOSS: requisitos (licencia, tests, documentación, instalación, ejemplo reproducible), `paper.md` y `paper.bib`, huecos a cubrir | por abrir (Sonnet), ya | Borrador y lista de requisitos con estado; el envío lo hace el propietario |
| T-100 | Estudio de rotación para la difusión | — | **Cancelada (D-18)** |
| T-101 | Archivista con D-17: desajuste de secciones ZIP↔M06 (Málaga, run 42490329631: 2900701022 sin distrito, 2908405001 ausente del ZIP; Alicante y Barcelona, previsiblemente igual); tolerancia ≤ 0,5 % de votos, reparto con la tabla de T-85, lista en la evidencia; tests con el caso de Málaga | por abrir (Opus), ya; toca herramienta compartida | PR con tests; la 00 de Málaga sale verde al relanzarla (Operador) |
| T-102 | Comparativa 2023 (D-19): campaña nueva `congreso_350` en el Gestor con K por provincia = escaños reales de 2023 (CSV con fuente y sha256), reutilizando M01-M03 y regenerando M04-M06; primero 3 provincias de prueba (una de 2 escaños, una media y Madrid) y luego el resto en lote por el Operador con permiso; votos de 2023 a los 350 distritos con la herramienta de T-83 B; ganador por distrito y escaños por partido frente al reparto real; selector «Real / 350 distritos» en la vista Nacional de T-84. Resultados y visor, solo tras aprobación del propietario (D-18) | por abrir (Opus), ya | Contrato y configuración en una PR; 3 provincias en verde; luego 52/52; tabla comparativa con fuente; sin publicar |
| T-103 | Desajuste ZIP↔M06 por encima del tope D-17 (Badajoz 0,87 %, Valencia 0,77 %, Albacete 0,63 %, Almería 0,52 %): clasificar cada sección en recodificada (misma geometría o cruce oficial del INE, código distinto) o partida/unida; las recodificadas se asignan 1:1 con la tabla de T-85 y no cuentan para el tope; solo lo partido/unido cuenta. Sin regenerar M06 (cambiaría el producto territorial: decisión del propietario). Si tras clasificar alguna provincia sigue por encima del 0,5 %, se para y se presenta al propietario | por abrir (Opus), ya; toca el archivista | PR con tests de las cuatro provincias; porcentajes antes y después en la evidencia; sin lanzar |
| T-104 | M06 de Valencia (autorizado por el propietario el 08-11: «regenera el M06 de Valencia»; T-103: «descuenta las contenidas»): antes de lanzar, (1) confirmar el seccionado del contrato de Valencia y cuál daría desajuste 0 con el ZIP de Interior de 2023; (2) cuantificar qué cambia (distritos de los 407, huellas M04/M05, checkpoints, M08 y publicación de Valencia) y la incoherencia de usar un seccionado distinto del INE 2025 del resto; (3) proponer el modo de 00. Se presenta al propietario antes de cualquier lanzamiento | por abrir (Opus), ya | Informe con las tres respuestas; sin lanzar |
| T-105 | Gestor de Campañas 2.0 (D-22), sobre T-86: `workflow_dispatch` con 6 entradas en el orden de D-22 (desplegables con nombres en español; lista de partes en texto), más `mapa` (407 o 350 de T-102) y una entrada «solo plan (en seco)» activada por defecto que muestra qué se lanzaría; opciones no disponibles (histórico antes de T-83 A, GerryChain 25 sin validar) fallan al planificar con un mensaje claro, sin lanzar; encadena 00 → par → electoral → publicación → ensemble sin chats; guía de una página en `docs/` con capturas | por abrir (Opus), ya; toca workflows compartidos: coordinar con el chat de T-86 | Hecha (#542) |
| T-106 | Limpieza de la lista de Workflows (D-23): (1) inventario de los 37 activos y 12 desactivados (`gh api .../actions/workflows`), con quién llama a quién; (2) los 12 desactivados ya no tienen fichero: borrar su historial de runs (irreversible) tras comprobar que su evidencia está en git, con la lista final presentada al propietario en una línea antes de borrar; (3) obsoletos sin llamadas (p. ej. `r2-test.yml`) a `legacy/workflows/` con su historial borrado del mismo modo; (4) internos que deben seguir (reutilizables, auto-merge, numeración, revisor, forense…) renombrados con prefijo común para que queden al final; los lanzables, con número y nombre claro | por abrir (Sonnet), tras T-105; toca workflows: coordinar | Hecha (#543) |
| T-109 | Visor v2 (D-24) según `docs/ARQUITECTURA/visor_v2/`: portada «Mapa» y pestañas del modelo v3, con la geometría y los datos de producción (M06/M08 publicados, CSV del BOE); textos leídos de `web/textos.md` (vacíos hasta que los escriba el propietario) y editor `?edit=1`; recoge el selector de T-102 y la capa de rotación cuando existan | por abrir (Sonnet), ya; toca `visor/` | Vista previa privada para que el propietario la pruebe ANTES de fusionar; nada se fusiona ni publica sin su visto bueno sobre la versión real |
| T-107 | (id del Coordinador) Castilla y León: M05 7.4.3 | — | Hecha (#546) |
| T-108 | (id del Coordinador) Huella M05 | — | Hecha (#547) |
| T-110 | Empujón al histórico (orden del propietario, 08-11): extender el paso B de T-83 (hoy validado en Álava, Badajoz y Huesca) a las 52 provincias × 6 generales 2011-2023 con la tabla de T-85 (D-13) y las siglas de T-97 (D-20); rotación por distrito de toda España en `datos/resultados/historico/rotacion/`; cuadre de totales provinciales con Infoelectoral y contraste con el Observatorio; lista de provincias que no cuadren con su motivo. Salida lista para la capa de rotación de T-109. Después, el paso A (cadena con puerta 04) por elección empezando por 2019-11, lanzado con el Gestor por el propietario o por el Operador con permiso | por abrir (Sonnet), ya | 52/52 × 6 en el repositorio con manifiesto y sha256; tests; sin lanzar ni publicar; nada sale del repositorio sin el propietario (D-18) |
| T-111 | Mapa de 350 con escaños de 2026 (D-25): campaña `congreso_350_2026` = la de T-102 salvo Cádiz (K=8) y Madrid (K=38), con K de `configuracion/escanos_oficiales_congreso_2026.csv`; reutiliza las otras 50 del mapa de 350 de 2023; lanzamiento de las dos provincias por el Operador con permiso del propietario | por abrir (Sonnet), tras las 3 de prueba de T-102 | Contrato en una PR; Cádiz y Madrid en verde; sin publicar |
| T-112 | Candidaturas y siglas de las generales 2026 (D-25): proclamación de candidaturas en el BOE (todas las circunscripciones), CSV con fuente y sha256; extender la tabla de T-97 a 2026 con sus familias (D-20); las de certeza baja se presentan al propietario antes de usarlas | por abrir (Sonnet), ya | CSV y tabla ampliada en una PR con tests; sin publicar |
| T-113 | Paso A del histórico en el Gestor 2.0: conectar `reagregacion_historico --paquete` e `historico_m07m08.py` (hoy solo Álava, Badajoz y Huesca) a la opción «histórico» del Gestor (#542), para las 52 provincias y las 6 generales, con puerta 04; primero 2019-11 | por abrir (Opus), ya; toca workflows compartidos | PR no-automerge; plan en seco correcto para 2019-11 × 52; prueba real con una provincia lanzada por el Operador con permiso |
| T-114 | **Prioridad 1: `main` en rojo.** `test_acreditacion_historica_territorial.test_planner_reuses_both_real_m06_from_durable_sealed_evidence` (castilla_y_leon) cae con DURABLE_LINEAGE_INCOMPATIBLE desde que la 00 de CyL 42521090842 (M05 7.4.3) registró un M06 nuevo. Diagnosticar si el test lee evidencia viva del repositorio (entonces fijar la evidencia sellada en una fixture inmutable) o si el resolver es demasiado estricto (entonces corregirlo con un test del caso). Prohibido saltar, desactivar o relajar el test para ponerlo en verde | por abrir (Opus), ya | Causa en una línea; PR con el arreglo; `pruebas` en verde en la PR y en `main` |
| T-115 | Madrid en el mapa de 350 (K=37, run 42522378370): POPULATION_HARD_BLOCK, distrito 33 con 303.941 hab frente a techo 213.586 (+63,6 %), reparación IMPROVED_NOT_REPAIRED; en local T-102 dio PASS (−14,3/+14,5 %). Reproducir con el M01 de `diagnostico/auto/congreso350_madrid/42522378370` (sha ff17a366…), ver la composición del distrito 33 y por qué producción y local difieren (fuente, semilla u orden). Defecto de motor → PR de motor; estructural → al propietario, sin tocar suelo, techo ni K. Cubre también Madrid K=38 (T-111) | por abrir (Opus, ingeniero de motor), ya | Causa en una línea con evidencia; PR o decisión presentada; sin lanzar |

Tras T-84 (orden del propietario, 08-11): revisión del kit T-93 por el propietario → publicación del visor nuevo por el Operador con permiso del propietario, con `/docs` (T-73) y DOI de Zenodo ya disponibles → difusión que decida el propietario (D-18). T-99 (comparador lado a lado, opción C de D-16) se propone con el visor publicado y la respuesta del público; no se encarga antes.

Abiertas el 08-11 (frentes en paralelo, orden del propietario): T-97 (Sonnet) homologación de siglas 2011-2026 para la capa de rotación, tabla con fuente y sha256, se presenta al propietario antes de usarla; T-98 (Opus, motor) Cádiz en el ensemble con la exención de San Fernando, una PR, sin lanzar; T-94c (Sonnet) LICENSE y requisitos pendientes de JOSS. Aplazados: ensemble autonómico (tras T-91 nacional) e histórico autonómico (tras T-83 A).

Conciliación de ids (08-11): el Coordinador usó ids propios que chocan con este plan. Equivalencias, todas hechas salvo indicación: T-93 del Coordinador = `retrieved_at` del contrato SIEL de Andalucía (#508); T-94 del Coordinador = persistencia pre-M04 con error visible y reintentos (#509); T-95 = la 05 sobre una 00 «Reutilizar» nombra el run de origen (#510); T-96 = credencial de registro en los pushes pre-M04 con el ruleset `veredicto` (#516); T-91b = receipts electorales huérfanos (#497; en curso, decisión A/B del propietario); T-92 del Coordinador = configuraciones de ensemble, 24 lanzables (#500); T-72b = paquete mínimo (#478). Este plan: T-90 preparación = T-90b (#501, espera a Interior); T-93 kit = T-93b (#514, hecha); T-94 JOSS = T-94b (#512, borrador hecho). El comparador lado a lado pasa a T-99 (propuesta). En adelante los ids los asigna solo el planificador.
| T-64 | Estudio comarcas frente a partidos judiciales | cerrado; PR #469 | Pendiente: C-13 (decisión del propietario) |

## 3b. Histórico de la cola (01 a 03-11)

### T-15 · Las Palmas falla en M08 tras #394 (P0, BUG)
- Run 00 41358199178: reutiliza el M06 de 41336103808, M07 queda OK y la validación da «distritos bajo límite poblacional=1» (exit 3).
- Causa 1: las secciones M06 de Mogán (35012) no traen `DDD_MUNICIPALITY_PARTITION`; el validador lo resuelve con respaldo a CUMUN/CUSEC · PR #398 · registro 1.0.70.
- Causa 2 (reproducida en local con M01/M03 del run): la reparación M05 movía Mogán (exento) al distrito deficitario y dejaba sin exención al que lo perdía. Las unidades de municipios exentos quedan ancladas · PR #399 (fusionada) · registro 1.0.71.
- #398 y #399 fusionadas; Las Palmas relanzada con la 00 «Ejecutar desde el principio» (M05 está en la huella).

### T-16 · Endurecer el diagnóstico automático de T-14 (P1)
- T14-01 linaje por rutas del contrato (sin mtime) · T14-02 paquete PARTIAL · T14-03 `MANIFEST.json` con sha256 · T14-04 resultado del rebase · T14-05 `DIAG_PUBLISH_FAILED` · PR #401 (fusionada) · registro 1.0.72.
- Pendiente: una 00 de prueba que falle a propósito (permiso del propietario).

### T-17 · Tabla de las 52 provincias (operador, solo lectura)
- Estado por provincia (M06, electoral, visor, causa de PARADA) a partir de `estado_operativo.json` y los manifiestos de ejecución. Sin lanzar nada.

### T-18 · Causa de Cádiz y Baleares (operador)
- Runs 41417528357 (Cádiz) y 41417532454 (Baleares): `POPULATION_HARD_BLOCK` con techo 1,15 en lugar del de la política. Se leen los informes M05 de `diagnostico/auto/<territorio>/<run>/`.
- Resuelta por T-20.

### T-19 · Factibilidad de Madrid y Málaga (solo lectura)
- Calcular si existe alguna partición sin partir municipios enteros bajo el techo (distritos 52 y 10 de T-02b). Sin 00. Alimenta el estudio de motor (sección 5).

### T-20 · Techo de Cádiz y Baleares (RESUELTA)
- Causa: `materialize` trataba como `already_complete` los contratos con M01–M06 y no reaplicaba `population_limits` de la política (el contrato conservaba 1,15). Arreglo: `apply_policy_population_limits` · PR #403 · registro 1.0.74. Baleares pasa a 1,28 (T-24).

### T-21 · Inventario de excepciones gobernadas (solo lectura, hecha)
- 71 contratos, 165 entradas. `limits_profile: exception` marca en 53 territorios la regla del Congreso (1,15) y no una desviación real; desviaciones reales: techos de Cádiz, Baleares y Las Palmas; atomicidad de Andalucía, Cataluña, País Vasco y Valencia; suelo de Melilla. Las 9 exenciones municipales de suelo no tienen `decided_at`/evidencia estructurada (pendiente de prioridad baja: moverlas a la política).

### T-22 · Estudio de motor (en curso, PR #419)
- M04 7.6.6, alivio de residuos municipales sobre el techo (`m04_overcap_residual_relief`): residual → núcleo, municipio entero → distrito del residual vecino y núcleo → núcleo, siempre dentro del mismo municipio dividido y con conexidad comprobada. No cambia suelo, techo, K ni atomicidad; no toca M05. Resuelve Murcia (con la exención de Águilas) y Madrid en local; mejora Alicante y Barcelona sin cerrarlas; Málaga queda igual.

### T-23 · Murcia (hecha, sin PR)
- INE: Águilas 30003, Puerto Lumbreras 30033. Con la exención de Águilas desaparece el bloqueo de Lorca; queda el distrito 4 (Murcia residual + Alcantarilla + Beniel = 171.010 > 137.265): bloqueo del motor → T-22.

### T-24 · Baleares 1,28, gate de Cádiz y cierre de Las Palmas (hecha)
- Baleares techo 1,28 (política 1.7.4) y M05 7.8.7 (exención municipal por el campo de municipio, Cádiz) · PR #404; tests negativos de Las Palmas y decisión de 35012 · PR #405.

### T-25 · Escenarios de otro algoritmo: lectura (hecha)
- Una 00 del Gestor con otro algoritmo sobre una provincia completa registraba su producto como el canónico (`persist_state` verdadero). Recomendación: ensemble por territorio (vía A) y escenarios que no registran.

### T-26 · Ensemble genérico por territorio (hecha, #406)
- «06 Escenarios y Ensembles» (workflow_dispatch) con configuración por territorio; Aragón idéntico; el resto obtiene M01–M05 sin registrar; fase `ensemble_10`, el 50 sigue bloqueado.

### T-27 · Todos los escenarios en el visor (en curso, 3 fases)
- **(a) Registro** con `scenario_m06/m08`, `scenario_id`, `strategy`, `scenario_kind`, `canonical` · PR #413 · **fusionada**.
- **(b) Selector** con `optgroup` por escenario y conmutador Territorial/Electoral · PR #414 · **fusionada**.
- **(c) Escenarios sin catálogo**: `persist_state` falso en campañas de otro algoritmo sobre territorio certificado y promoción como escenario (`scenario_id`, `scenario_strategy`) · PR #415 · **fusionada**.
- Pendiente tras las tres: una ejecución real de un escenario completo (territorial y electoral) y su publicación en el visor.

### T-28 · Cádiz: receipt electoral sin linaje (hecha, #407)
- `electoral_product_available: false`; la 00 «Reutilizar» rehace 03/04 sobre el M06 vigente.

### T-29 a T-33 · Piloto de ensemble de Salamanca (hechas)
- T-29 poda de aristas débiles (#408); T-30 lectura: las geometrías del Congreso están en grados; T-31 medir la frontera compartida en metros (#409); T-32 el runner del ensemble ya no sale en verde con fallos (#410); T-33 unir las piezas de secciones MultiPolygon como M06 (#411). Resultado: Salamanca ensemble_10, 10/10 candidatos (run 41543954069).

### T-34 · Ensemble en La Rioja y Sevilla (hecha, #417)
- `configuracion/ensemble/congreso_la_rioja.json` (K=3) y `congreso_sevilla.json` (K=16; Valencia descartada por su puente gobernado). Resultado: 10/10 candidatos en las dos (Sevilla con 4 hashes únicos).

### T-35 · Publicación de ensembles con `ensemble_sha256` (hecha, #418)
- El publicador único exige el hash del zip del release; `publish` y `republish` lo calculan, lo exponen y los despliegues lo pasan. La publicación de Salamanca (run 41592019959) fallaba con exit 56. La republicación sin recalcular vale para cualquier territorio con configuración (ensemble_10), no solo Aragón-10; el 50 sigue bloqueado. Solo añade en `ensembles`.

### T-14 · Diagnóstico automático sin el Mac (máxima prioridad tras T-13)
- Objetivo: cuando una 00 falla en M04, M05 o en la puerta de certificación, el propio workflow sube a la rama
  `diagnostico/auto` (carpeta `<territorio>/<run>/`) el M01, el grafo M03 (gz) y el informe M05, para que los
  chats ejecuten el motor en local sin descargar artefactos (403 desde la nube) ni depender del Mac.
- Rol: implementador. Modelo: Opus.
- Ficheros afectados: `_reutilizable-generacion-territorial.yml` (paso `if: failure()` tras M04/M05/certificación),
  herramienta nueva en `herramientas/` para empaquetar y publicar con la credencial de registro (#386), test.
  Workflow compartido: turno del planificador.
- Criterio de aceptación: una 00 que falle en M05 deja en `diagnostico/auto` los tres ficheros en menos de 5 minutos;
  con ellos `python -m ddd_core.m04_seed_engine` y `modulos/05_optimizar_distritos.py` reproducen el fallo en local;
  una 00 correcta no sube nada; tamaño por territorio < 50 MB.
- Prueba local exigida: suite completa + test del empaquetado + una 00 de prueba que falle a propósito (con permiso).
- Dependencias: ninguna. Sustituye a `lanzadores/subir_diagnostico_t02.sh`.

### T-08 · Proteger `main` con CI obligatoria
- Objetivo: impedir fusionar sin «pruebas» en verde y con la rama al día con `main` (lo que ocurrió con #374).
- Rol: operador (lo aplica el propietario: requiere permisos de administrador). Modelo: Haiku.
- Ficheros afectados: ninguno; ajuste del repositorio (Settings → Branches o ruleset sobre `main`):
  check obligatorio `pruebas`, «Require branches to be up to date», sin push directo. Comprobar antes que
  los robots de registro (catálogo, `estado_operativo.json`, activos del visor) que escriben en `main`
  quedan exentos o pasan por PR; si no, la protección los bloquea.
- Criterio de aceptación: una PR con «pruebas» en rojo o pendiente no se puede fusionar; los robots siguen
  registrando sin fallos durante una ejecución 00.
- Prueba local exigida: ninguna; verificación con `gh api repos/jfmurciego/DiputadodeDistrito/branches/main/protection`
  (o rulesets) y una ejecución 00 posterior con registro correcto.
- Dependencias: T-10 para reactivar. Máxima prioridad.
- Estado (2026-11-01): ruleset `proteger-main` (id 26311854) creado con PR obligatoria, check `pruebas` y rama
  al día (`puerta_admision` retirado: solo corre si la PR toca contratos y dejaba las demás en espera eterna).
  **Desactivado**: la app GitHub Actions no se puede añadir a los exentos y los robots de registro
  (`git push origin main` en 00, generación, operación, publicación del sitio y orquestación) quedarían bloqueados.
  Se reactiva al cerrar T-10.


### T-10 · Robots de registro con token propio (desbloquea T-08)
- Objetivo: que los workflows que hacen `git push origin main` lo hagan con un token de GitHub App propia
  (o PAT de grano fino) que pueda figurar como exenta en el ruleset, para reactivar `proteger-main`.
- Rol: implementador (workflows) + propietario (crear la app o el PAT y el secreto). Modelo: Opus.
- Ficheros afectados: `.github/workflows/ejecucion-completa-proyecto.yml`, `orquestacion-durable.yml`,
  `_reutilizable-generacion-territorial.yml`, `_reutilizable-operacion-territorial.yml`,
  `_reutilizable-publicar-sitio.yml` (paso de checkout/push con el token del secreto). Workflows compartidos:
  avisar a las demás sesiones antes.
- Criterio de aceptación: con el ruleset activo y la app exenta, una 00 registra en `main` sin
  «rule violations»; una PR sin `pruebas` en verde no se puede fusionar.
- Prueba local exigida: suite completa (incluye tests de gobernanza de workflows) + `actionlint` si está disponible.
- Dependencias: el propietario crea la GitHub App o PAT y el secreto. No reactivar el ruleset con 00 en curso.

### Resultado de T-01 (2026-11-01, `estado_operativo.json` de las 11:06 + anotaciones y logs de los jobs)
- Completas (32): Albacete, Almería, Ávila, Cáceres, Castellón, Ciudad Real, Córdoba, La Coruña, Cuenca, Gerona,
  Granada, Guadalajara, Huesca, Jaén, León, La Rioja, Lugo, Orense, Asturias, Palencia, Salamanca,
  Santa Cruz de Tenerife, Segovia, Sevilla, Soria, Tarragona, Teruel, Toledo, Zamora, Zaragoza, Ceuta, Melilla.
  En Huesca, La Rioja, Lugo, Santa Cruz de Tenerife y Tarragona el último run falló solo en 05 (visor), sin efecto en M08.
- M06 sin electoral (8): Badajoz, Burgos, Guipúzcoa, Lérida, Navarra, Cantabria, Valladolid, Vizcaya
  (lanzadas con alcance territorial; `main` registra después ejecuciones completas de Badajoz, Burgos, Lérida,
  Navarra y Valladolid: confirmar en el próximo estado operativo).
- PARADA (12), por causa:

| Causa | Provincia | Run | Detalle |
|---|---|---|---|
| Población (M05 `POPULATION_HARD_BLOCK`) | Alicante | 41293667422 | hard=1, desviación máx. 0,36 |
| | Barcelona | 41244711464 | hard=2, 0,30 |
| | Cádiz | 41243953699 | hard=2, 0,18 |
| | Madrid | 41244835816 | hard=1, 0,56 |
| | Málaga | 41293427148 | hard=1, 0,38 |
| | Pontevedra | 41293311168 | hard=1, 0,25 |
| | Baleares | 41250230577 | hard=2, 0,67 (con #370; revisar `component_districts`/exenciones) |
| | Las Palmas | 41250283081 | hard=1, 0,46 (con #370; techo 1,40 insuficiente o reparto no aplicado) |
| Población (M04, estructural) | Álava | 41240137880 | residual de Vitoria (01059) 0,72 bajo suelo; sin sección transferible |
| Conectividad (pre-M04) | Murcia | 41293548832 | «grafo territorial no supera conectividad administrativa», ya con #371 |
| Geometría fuente (01) | Huelva | 41292468775 | `GEOMETRY_INVALID_AUDITED`: secciones INE con huecos interiores sin máscara de cobertura |
| | Valencia | 41293787892 | ídem |

### T-02 · Diagnosticar y relanzar las PARADA
- Objetivo: corregir la causa de cada grupo de PARADA (empezando por M02 con puentes heredados 2024/2025,
  Huelva y Valencia) y dejar un script de relanzamiento para el Mac.
- Rol: implementador (corrección) + operador (relanzamiento por script). Modelo: Opus.
- Ficheros afectados: probablemente `herramientas/generar_provincias_congreso.py`, contratos
  `territorios/congreso_*/config/`, `particiones_insulares_2025.json`,
  `configuracion/politica_generacion_territorial_2025.yaml`; script en rama `lanzadores-mac`.
  Avisar antes de tocar `herramientas/`, `modulos/`, `ddd_core/` o la política.
- Criterio de aceptación: cada provincia PARADA llega al menos a M06 validado en un run nuevo; ninguna
  regresión en las 28 completas.
- Prueba local exigida: suite completa + diagnóstico local de M02/M04/M05 por provincia afectada con el grafo
  subido a `diagnostico/…` (ver `CLAUDE.md`, «Diagnóstico local»).
- Dependencias: T-01. Una PR por causa, no por provincia.

### T-02b · Bloqueos de población M05 (2026-11-01)
Runs 00 de las 16:40 (reparación profunda: profundidad 6, conjunto 3, 500.000 candidatos, 300 s). La reparación no mejoró ningún exceso: el bloqueo es estructural (municipios enteros indivisibles bajo el techo, regla del propietario).

| Provincia | Run | Distrito | Población | Límite | Exceso | Municipios enteros |
|---|---|---|---|---|---|---|
| Madrid | 41327479240 | 52 | 181.853 | techo 133.943 | +47.909 | Pozuelo (28115, 88.504), Boadilla (28022, 64.635) y 28181 (28.714) |
| Málaga | 41327483858 | 10 | 161.454 | techo 134.376 | +27.078 | 29054 (85.136) y 29025 (76.318) |
| Alicante | 41327488604 | 12 | 156.889 | techo 132.268 | +24.620 | trozo de 03065 (119.050) y 03121 (37.839) |
| Barcelona | 41327510776 | 31 | 150.148 | techo 133.339 | +16.809 | 08015 (112.242) y 08194 (37.906); el distrito 40 (08073) va exento del suelo |

**Estado: BLOQUEADAS por estructura (Madrid, Málaga, Alicante, Barcelona y Murcia).** Quedan para un futuro estudio de motor. Palancas descartadas: bajar `municipality_atomicity_limit_ratio` (contradice la regla de no partir un municipio que cabe bajo el techo) y subir el techo (Barcelona 31 está a 1,29 de la media).

Resueltas por decisión del propietario: Cádiz (techo 116 % solo en Cádiz, política 1.7.3, distrito 8 a 1,159 de la media), Pontevedra (exención municipal 36008), Las Palmas (exención municipal 35012). Baleares: techo 127 % solo en Baleares (política 1.7.3; distrito 5 de Mallorca a 1,261 de la media, la reparación profunda no lo mejoró).

### T-09 · Huella de puentes heredados antes de M02
- Objetivo: comprobación previa que detecte puentes municipales heredados de 2024/2025 que ya no casan con el
  inventario municipal y la geometría vigentes, y bloquee con mensaje claro antes de lanzar M02 (evita PARADA).
- Rol: implementador. Modelo: Opus.
- Ficheros afectados: `herramientas/generar_provincias_congreso.py` (o nueva herramienta de comprobación en
  `herramientas/`), paso previo del workflow que lanza M02, tests nuevos en `tests/`. Avisar antes de tocar
  `herramientas/` y workflows.
- Criterio de aceptación: para cada provincia nacional, informe de puentes (válido / municipio inexistente /
  municipios no colindantes ni enlazables / código INE cambiado); las provincias que pararon en M02 por
  puentes (T-01/T-02) salen marcadas; las 28 completas salen limpias.
- Prueba local exigida: suite completa + ejecución de la comprobación sobre todos los contratos
  `territorios/congreso_*` + test con un puente roto sintético.
- Dependencias: T-01 (causas de PARADA). Va detrás de T-02 en prioridad; si T-02 corrige puentes, se apoya en ello.

### T-04 · Completar electoral de las provincias con M06
- Objetivo: llevar las 11 provincias con M06 (y las que salgan de T-02) a M08 con la activación por elección.
- Rol: operador. Modelo: Sonnet.
- Ficheros afectados: ninguno de código; script de lanzamiento en `lanzadores-mac`.
- Criterio de aceptación: 52/52 provincias nacionales con «Cadena completa validada» en el estado operativo.
- Prueba local exigida: ninguna (lanzamiento); comprobación del estado con `generar_estado_operativo.py`.
- Dependencias: T-02, T-03, D-1, permiso explícito del propietario.

### T-05 · Renombrado visible a «nacional»
- Objetivo: en visor, dashboard, informes y textos públicos, «nacional» en lugar de «congreso»; sin
  «circunscripción» en lo visible; topónimos en español. Los identificadores internos (`congreso_*`) no cambian.
- Rol: implementador. Modelo: Sonnet.
- Ficheros afectados: `herramientas/generar_estado_operativo.py`, plantillas del visor, generadores de
  nombres visibles (`display_name`), documentos públicos.
- Criterio de aceptación: `grep -ri "congreso\|circunscripci"` sobre las salidas visibles (visor, dashboard,
  `estado_operativo.json` campos `name`/`display_name`) sin coincidencias; claves internas intactas.
- Prueba local exigida: suite completa + regenerar estado operativo y visor en local y revisar el grep.
- Dependencias: ninguna (mejor tras T-03 si toca los mismos generadores).

### T-06 · Gestor de Campañas con provincias
- Objetivo: el selector del Gestor admite las elecciones nacionales por provincia además de las 19 autonómicas.
- Rol: implementador. Modelo: Sonnet (Opus si exige cambiar el modelo de datos).
- Ficheros afectados: módulo/plantillas del Gestor de Campañas y su catálogo de ámbitos.
- Criterio de aceptación: el selector lista las 52 provincias con nombre en español y etiqueta «nacional»;
  abrir una provincia completa carga sus distritos y resultados.
- Prueba local exigida: suite completa + prueba del selector con una provincia (Huesca).
- Dependencias: T-03 (clave de elección), T-05. Prioridad secundaria.

### T-07 · Andalucía (al final)
- Objetivo: generar y validar distritos de Andalucía y completar su cadena.
- Rol: implementador + operador. Modelo: Opus.
- Ficheros afectados: contrato de Andalucía, política (`population_limits`, exenciones), lanzador del Mac.
- Criterio de aceptación: Andalucía con «Cadena completa validada»; 19/19 autonómicas.
- Prueba local exigida: suite completa + diagnóstico local M04/M05 con el grafo de Andalucía.
- Dependencias: T-04 terminada.

## 4. Tareas hechas
<!-- Formato: T-xx · resumen · PR #nnn / run nnnnnnnnnn · fecha -->
- T-43 · Ensembles de La Rioja y Sevilla publicados como escenario (`ensembles=3`, 157 productos, canónicos intactos) · runs 42384534739 42385012998 · 2026-11-07
- Paso 0 y Paso 1 (bloques 1-3) · framework, guardián de `main`, `CLAUDE.md`/`rules/`/hook y skills de rol · PR #427 #428 #429 #430 · 2026-11-07 (pendientes de fusión)
- T-22 · M04 7.6.6, alivio de residuos sobre el techo; cierra Madrid y Murcia · PR #419 · 2026-11-03
- T-23 · Murcia: exención de suelo de Águilas (30003) · 2026-11-03
- T-35, T-36, T-37 · publicación de ensembles: `ensemble_sha256`, candidatos en WGS84, una feature por distrito · PR #418 #421 #424 · 2026-11-03
- T-14 · Diagnóstico automático: M01, grafo M03 e informe M05 a `diagnostico/auto/<territorio>/<run>/` si falla M04, M05 o la certificación · PR #397 · 2026-11-01
- T-02 · Huelva y Valencia (CRS 25830, #374) y Álava (M04 7.6.0 multisección, #383; 00 41346917857) completas.
  Murcia BLOQUEADA por estructura (objetivo 119.361, suelo 101.457, techo 137.265): Lorca 97.904 + Águilas 36.684 +
  Puerto Lumbreras 17.507 = 152.095 (Águilas y Puerto Lumbreras solo lindan con Lorca; atomicidad 0,80 aborta M04);
  residual de Murcia 116.508 + Alcantarilla 43.040 + Beniel 11.462 = 171.010 (1,43), enclaves sin cabida en núcleos
  cerrados exclusivos. Pasa al estudio de motor (sección 5) · PR #374 #383 · 2026-11-01
- T-08 · Ruleset `proteger-main` activo (PR obligatoria, check `pruebas`, rama al día; exentos administrador y app `ddd-registro`) · ajuste del propietario · 2026-11-01
- T-05 · Nombres visibles «Nacional …» en estado operativo, dashboard y visor; identificadores sin cambios · PR #385 · 2026-11-01
- T-06 · Gestor de Campañas con «Nacional 2023» (52 provincias por INE, matrícula o nombre) · PR #388 · 2026-11-01
- T-09 · Comprobación de puentes heredados antes de M02 (28 puentes en 20 provincias, válidos) · PR #390 · 2026-11-01
- T-10 · Robots de registro con app propia `ddd-registro` (exenta en el ruleset); probado en Baleares 41339398026 · PR #381 + #386 · 2026-11-01
- T-11 · Dashboard sin PARADA falsas y reintentos del estado compartido; arreglo del manifiesto al reanudar desde M05 · PR #387 · 2026-11-01
- T-12 · El encadenado par+04 exige la 02 en success · PR #389 · 2026-11-01
- T-01 · Clasificación de las 52 provincias y causas de PARADA (tabla antes de T-02) · 2026-11-01
- T-03 · Activación por elección: clave `ES-NAC|AUT-[unidad-]AAAAMMDD` (INE canónico, matrícula alias; D-2 según
  recomendación), workflow «Activación por Elección» (plan/activar/electoral/completa, filtro `solo`) y 00 v1.4.6
  con `lanzado_por_eleccion` · PR #376 · 2026-11-01

## 5. Propuestas sin asignar (planificador, 01-11)
### Operación
- Fusión automática: activar «Allow auto-merge» en el repositorio; cada PR se fusiona sola con `pruebas` en verde
  (ruleset activo). Reduce las fusiones manuales del propietario.
- Reactivar `proteger-main` en cuanto no haya 00 en curso (app de registro ya exenta y probada, T-10).
- Estudio de motor para provincias BLOQUEADAS por estructura (Madrid, Málaga, Alicante, Barcelona, Murcia; enclaves en núcleos cerrados): M04/M05 capaces de
  reorganizar distritos alrededor de municipios grandes sin partir los que caben bajo el techo. Opus, tras T-14.

### Extensiones (tras cerrar la elección nacional 2023)
- Histórico de legislaturas: generales 2019-11, 2019-04 y 2016 con la clave por elección (T-03); autonómicas del
  ciclo anterior; inventario municipal y espejo de Interior por año.
- Comparador entre legislaturas en el visor (cambios de distritos y resultados).
- Europeas: solo como agregación de resultados sobre los distritos existentes.
- Municipales en ciudades grandes (Madrid, Barcelona, Valencia, Sevilla): distritos por sección censal; cambia la
  unidad atómica de M04 (Opus, largo).
- Ensembles con GerryChain (`docs/ENSEMBLES_GERRYCHAIN.md`) para medir el sesgo de cada plan.
- Simulación de escaños: uninominal frente a D'Hondt real, por provincia y agregado nacional.
- Comunidades de interés y nombres de distrito para el nacional (auditorías C12/C13).
- Ficha pública por distrito y datos abiertos (GeoJSON/CSV con licencia y huella).
