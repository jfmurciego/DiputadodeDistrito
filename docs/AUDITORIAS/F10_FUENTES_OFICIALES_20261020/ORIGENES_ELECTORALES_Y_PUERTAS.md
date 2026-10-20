# F10 — Fuentes electorales oficiales: comprobación de acceso (2026-10-20)

## Alcance y gobierno
Investigación de **Fuentes Oficiales**. No promueve fuentes, no modifica la pareja territorial, no crea correspondencias de votos, no ejecuta producción. Los correos institucionales de Andalucía, Aragón, Castilla y León y Extremadura fueron **enviados por el titular**, sin conservar en GitHub su dirección personal ni afirmar registros administrativos que no constan.

## Aragón: origen oficial granular localizado y accesible
Portal oficial: https://www.aragon.es/portal-de-elecciones/resultados-electorales (última actualización publicada 2026-06-04). Declara resultados definitivos de las elecciones autonómicas 2026 **desglosados por mesa**, descargables por circunscripción. URLs primarias localizadas en la página institucional:
- Zaragoza: https://www.aragon.es/documents/d/guest/datescrut_def_auto_2026_zaragoza
- Huesca: https://www.aragon.es/documents/d/guest/datescrut_def_auto_2026_huesca
- Teruel: https://www.aragon.es/documents/d/guest/datescrut_def_auto_2026_teruel

**Verificación realizada:** las tres URLs responden con contenido binario de hoja de cálculo; se verificó su disponibilidad mediante lector remoto, **no** el hash íntegro, estructura XLS, los valores ni su conciliación. La extracción textual automática no es válida para estos bytes. Para acreditar: descargar cada original sin recodificar, fijar SHA256 y longitud, identificar mesa/sección/CUSEC, contrastar totales con acta oficial y resolver correspondencia temporal oficial con INE 2025. La disponibilidad de XLS definitivos **no** demuestra crosswalk a 2025.

Relación oficial de secciones, mesas y locales de la elección 2026: https://www.aragon.es/portal-de-elecciones/mesas-electorales. El portal incorpora enlaces por provincia (incluidos boletines provinciales). Usar como fuente de identidad electoral efectiva, no como regla de trasvase de votos.

## Castilla y León: fuentes de escrutinio y correcciones localizadas
Portal institucional Junta Electoral: https://juntaelectoral.ccyl.es/resultadoselectorales.html.
Documentos oficiales de resultados generales/por circunscripción para elecciones de **15-03-2026**:
- Inicial, BOCYL 29-04-2026: https://bocyl.jcyl.es/boletines/2026/04/29/pdf/BOCYL-D-29042026-80-13.pdf
- Corrección 08-06-2026: https://bocyl.jcyl.es/boletines/2026/06/08/pdf/BOCYL-D-08062026-108-27.pdf
- Corrección 11-06-2026: https://bocyl.jcyl.es/boletines/2026/06/11/pdf/BOCYL-D-11062026-111-18.pdf

**Cautela:** esos documentos agregados no son un fichero definitivo desglosado por mesa y no acreditan por sí solos las correspondencias seccionales 2025–2026. Antes de conciliar votos granulares, aplicar las dos correcciones a los totales de control.

## Andalucía: estado contrastado con expediente F10
El expediente versionado `docs/AUDITORIAS/CIERRE_FUENTES_20261019/ANDALUCIA_SIEL_RIESGO_CONSOLIDADO_20261019.json` registra 67 secciones distintas en riesgo y 47.875 votos a candidaturas afectados, con SIEL definitivo ya conciliado. El TRAM oficial acredita variaciones administrativas, **no** permite distribuir votos proporcionalmente a 2025. Pendiente evidencia electoral competente para Sevilla, Cortegana y correspondencias parciales. No alterar `BLOCKED`.

## Extremadura: control definitivo y diferencia pendiente
Acta pública definitiva DOE de 14-01-2026: https://doe.juntaex.es/otrosFormatos/html.php?anio=2026&doe=80o&xml=2026AC0001.
Resultados a candidaturas Badajoz 326196 + Cáceres 198641 = **524837**. Fuente provisional granular ya estudiada 522418; diferencial **2419**. No desagregar ficticiamente esa diferencia. Pendiente fuente oficial definitiva granular por mesa o documentación de escrutinio general con trazabilidad de rectificaciones.

## Estado y siguiente ejecución reproducible
1. Aragón: conservar originales XLS oficiales por circunscripción, hashes y conciliación por mesa; cotejar relación electoral de secciones/mesas.
2. Castilla y León: conservar los tres BOCYL, identificar qué totales cambian y comprobar identidad del censo electoral por mesa ante INE 2025.
3. Andalucía: incorporar respuesta oficial sobre correspondencias, sin redistribución estimada.
4. Extremadura: incorporar respuesta con actas definitivas granulares y conciliar 2419.
5. Recalcular mediante `herramientas/estado_derivado_f10.py` **solo si la evidencia canónica cambia**; no editar `matriz_nacional_19.json` para reflejar una mera URL.

**Resultado de esta investigación:** nuevas ubicaciones primarias de documentos, sin cambios en admisibilidad. No afirmar que se han descargado binarios o calculado hashes desde un extractor que devuelve bytes corruptos en texto.
