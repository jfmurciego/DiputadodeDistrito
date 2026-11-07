# Ejecuciones y escenarios

## Caso comprobado: Cantabria · 41037133327

El 3 de noviembre se descargó el checkpoint M05, se contrastó el SHA-256 del ZIP con el manifiesto del productor y se abrieron los 50 ZIP de candidatos. Se recalculó también la identidad de cada asignación unidad→distrito.

| Comprobación | Resultado |
|---|---:|
| Checkpoint M05 descargado | 102.460.319 bytes |
| Candidatos presentes | 50 |
| SHA-256 de candidatos verificados | 50/50 |
| Asignaciones recalculadas y distintas | 50 |
| Secciones por candidato | 460 |
| Tamaño conjunto de los ZIP de candidatos | 24.735.141 bytes |
| Caducidad declarada del checkpoint | 13 de noviembre de 2026 |

**Conclusión:** los 50 candidatos están materialmente conservados y recuperables en ese checkpoint a la fecha de comprobación. No son solo hashes o contadores. Esto corrige la incertidumbre de una revisión anterior que no había inspeccionado esos archivos.

La comprobación acredita integridad y recuperabilidad. No repite la optimización ni certifica de nuevo las restricciones geográficas de cada candidato, la representatividad estadística del ensemble o su publicación ciudadana.

## Dos identidades diferentes

El hash del ZIP de un artefacto, el de un ZIP de candidato y el de una asignación territorial identifican objetos diferentes. Un archivo puede cambiar de empaquetado sin cambiar la asignación. Guardar los tres evita confundir integridad de transporte con identidad científica.

## Estados separados

La ficha propuesta debe indicar por separado:

- **Generación:** calculado o fallido, con parámetros y semilla.
- **Validación:** controles realizados, resultado y excepciones.
- **Conservación:** ubicación, integridad comprobada y retención.
- **Publicación:** accesibilidad pública y licencia.
- **Citación:** versión estable, autores y DOI cuando exista.

Estos campos requieren evidencia propia; no conviene resumirlos en un único estado verde. Cincuenta asignaciones distintas tampoco demuestran por sí solas una muestra estadística representativa: hay que documentar diseño de cadenas, restricciones, autocorrelación, burn-in y criterio de selección según la pregunta científica.

[Run original](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/41037133327) · [Manifiesto del productor](https://github.com/jfmurciego/DiputadodeDistrito/blob/11f0ba2b775a889f2316e31ebdbd859cbc50ab13/territorios/cantabria/evidencia/generaciones_m06/41037133327.json)

*Versión 1.0.0 · 2026-11-03 · Archivo nuevo.*
