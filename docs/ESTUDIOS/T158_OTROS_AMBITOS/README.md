# T-158 · Otros ámbitos: solo preparar (D-42)

Fecha: 2026-11-10. Solo lectura de fuentes y notas; sin motor, workflows, PLAN ni datos generados.
Notas: `MUNICIPALES_ESPANA.md`, `EUROPEAS_ESPANA.md`, `ECUADOR_ASAMBLEA_NACIONAL.md`.

## Alcance de red (comprobado el 10-11 desde la sesión cloud)
| Host | Estado |
|---|---|
| `www.boe.es`, `www.ine.es` (ficheros `jaxiT3/files`) | alcanzables |
| Junta Electoral Central, Infoelectoral, CNIG (Centro de Descargas), datos.gob.es, EUR-Lex, Parlamento Europeo, results.elections.europa.eu, Eurostat, CNE Ecuador, INEC Ecuador, Asamblea Nacional de Ecuador, Registro Civil de Ecuador, Wikipedia, Zenodo | **rechazados por el proxy** (`connect_rejected`) |

Consecuencia: solo la LOREG (BOE) y una tabla del INE están verificadas con fichero y sha256. Todo lo demás va marcado
**NO VERIFICADO**: es conocimiento general que hay que contrastar con la fuente oficial antes de usarlo; no entra en ningún contrato.

## Evidencia obtenida (sha256 de lo descargado; los ficheros no se versionan)
- LOREG consolidada, XML de la API del BOE `https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-1985-11672/texto`,
  consulta 2026-11-10, sha256 `7377ee3fb6c7e9d703d8ad829269e5d6682f3c5f707a8356a5cd8d391ee27224`.
  Los artículos se numeran en letra en el XML («Artículo ciento setenta y nueve»).
- INE, tabla 2915 (CSV `https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/2915.csv`), consulta 2026-11-10,
  sha256 `95ccef1de7df09483b3cf4de26cb64278ff6709adb193d3757d8d210b31041f2`, 283.254 bytes; columnas: Comunidades y
  Ciudades Autónomas; Tamaño de los municipios; Periodo; Total (series 2011-2021 en la cabecera; solo muestra de accesibilidad, no se usa como población oficial).

## Resumen comparado
| | Municipales (España) | Europeas (España) | Ecuador (Asamblea Nacional) |
|---|---|---|---|
| Circunscripción | cada término municipal (art. 179 LOREG) | territorio nacional (art. 214) | provincias, exterior y nacional (NO VERIFICADO) |
| Reparto | D'Hondt, suelo 5 % (art. 180) | D'Hondt sin barrera del art. 163.1.a (art. 216) | métodos proporcionales por listas (NO VERIFICADO) |
| «Distrito uninominal» | partir el municipio en N distritos de 1 concejal | partir el país en 61 distritos de 1 eurodiputado | partir cada provincia/circunscripción en distritos de 1 asambleísta |
| Unidad mínima | sección censal (INE) | sección censal (INE) | parroquia / zona-recinto (NO VERIFICADO) |
| Esfuerzo (est.) | ALTO (8.000+ municipios; solo ~170 con ≥ 5 concejales tienen sentido) | BAJO-MEDIO (reutiliza el seccionado nacional) | ALTO (todo por adquirir) |
| Bloqueo principal | resultados por sección municipal no localizados; cartografía no alcanzable | decisión de K y de la partición dura nacional | ninguna fuente alcanzable |

## Reglas del núcleo que habría que parametrizar (común)
Detalle por ámbito en cada nota. Candidatas: (1) **partición dura** (`jerarquía`): hoy el distrito no cruza provincia; en
municipales sería el municipio, en europeas «ninguna», en Ecuador la circunscripción; (2) **K** (distritos por unidad):
aquí viene dado por la norma (escala art. 179; 61 eurodiputados; escaños por provincia), no por el reparto del motor;
(3) **suelo/techo** de población: el techo del contrato actual se mide sobre población de derecho; en municipales el
tamaño medio de un distrito sería de cientos a pocos miles de habitantes; (4) **atomicidad**: la sección censal ya es la unidad
mínima en el contrato nacional, pero en municipios pequeños una sección puede ser mayor que un distrito objetivo.
Ninguno de estos valores se fija aquí; son decisión del propietario.
