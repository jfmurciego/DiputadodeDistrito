# Estado operativo (mantiene el Coordinador)

Fecha: 2026-11-10 (relevo de chats principales) · Actualizar en cada PR de lecciones o de estado. Verde = cumple el criterio del propietario; amarillo = en marcha o a medias; rojo = bloqueado o fallando. Notación D-47: fases P00-P60 y archivo ARC; en lo que se cuenta al propietario, sin códigos antiguos, sin ids de tarea ni de PR.

## Tablero por tema (prioridad 1: el motor)
| Tema | Estado | Situación | Siguiente |
|---|---|---|---|
| 1. Motor nuevo (D-48) | amarillo | Primera versión = competición «canónico + GerryChain» bajo el núcleo único de reglas, con semilla pública (D-50: sha256 del padrón/seccionado oficial + territorio). Batería de los 71: 71/71 válidos, mejora 21, empata 50, empeora 0; 221 min (×5,6 el motor actual; Cataluña 992 s); reproducible bit a bit. El propietario NO releva aún el motor | Naturalidad: al propietario le gustan B y C (sobre todo C); término medio D5/D8 en 6 territorios y C/D8 en los 71 en curso. Medida de cuántas cadenas hacen falta (N=1…20) en curso. R-NUCLEO fusionado; enumeración exacta en revisión |
| 1b. Certificador exacto | amarillo | Modelo ligero con unidades atómicas: Madrid minimax certificado 17.236 = publicado (hueco 3 hab.); Álava, Huesca y Cádiz ≤2 s. Cádiz con techo 115 % infactible (mínimo 1,15919×) | Núcleos cerrados (R-NUCLEO) |
| 2. Autonómica (19) | amarillo | Publicadas las 19. Cantabria y Extremadura: distritos nuevos certificados pero SIN resultados por distrito (la cadena electoral falló por linaje durable); el público ve el par anterior coherente | Arreglo del linaje (PR en revisión) y relanzado con frase del propietario; no publicar el distrito nuevo sin sus resultados |
| 2b. Autonómica, alternativas 10/25 | rojo | 13 comunidades bloqueadas por puentes topológicos o exención por partición | Decisión de motor |
| 3. Nacional (52) | verde | 52 circunscripciones con distritos certificados y resultados; Madrid, Soria y Valladolid de 350 sin publicar | — |
| 4. Gestor y histórico | verde/amarillo | Gestores históricos 2015, 2016 y 2019-04 en éxito; autonómico en éxito; histórico autonómico por lotes | Datos fuera de la nube (municipales, europeas) |
| 5. Visor | amarillo | Visor v2 desplegado; auditoría de accesibilidad entregada | Publicar numeración 1..K y mejoras: NO por decisión del propietario (D-58); analítica sin cookies pendiente de elegir |
| 6. Lista de Actions | verde | De 36 a 24 ficheros (23 sin la Poda de R2). Excepción aceptada: cuatro «Interno ·» (generación territorial, publicador del sitio, incorporación electoral, puerta de validación). Revisor de PR aparte; ruleset exige `veredicto` | Fusión automática y forense: no se tocan (D-58) |
| 7. Gasto de CI | amarillo | Tope 15.000 min/semana, aviso al 70 %; 72 % del gasto son pushes a main; aprobadas: cancelar comprobaciones superadas y robots solo integridad + batería nocturna (se implementa con la consolidación) | Redefinir «main en verde» en CLAUDE.md |
| 8. Archivo ARC | amarillo | Batería relanzada con éxito; simulación de la poda limpia (234 claves, 26,09 GB); borrado real lanzado por el Operador | Verificar el resultado de la poda |
| 9. Zenodo y README | amarillo | DOI de concepto 24093967 y de versión 24093968 (solo mapa de Huesca); proyecto en 4.9.0, README rev. 4.9.0-r1 | El propietario comprueba que resuelven |
| 10. Autorización por campaña | verde | Regla de autorización por campaña fusionada (D-52) con la frase del propietario | — |
| 11. Otros ámbitos (D-42) | amarillo | Notas de municipales, europeas y Ecuador (fuentes no verificadas desde la nube) | Descargas manuales del propietario |
| 12. Plataforma | verde | `main` en verde | — |

## Reglas vigentes
- Lanzar y publicar solo con la frase del propietario en el chat del Operador; el «sí» en otro chat no cuenta.
- Fusionar toda PR en cuanto esté verde (`pruebas` en success sobre el HEAD exacto y `main` en verde), actualizar las siguientes y cerrar los chats obsoletos guardando su aprendizaje (norma habitual, 10-11). Excepciones con frase del propietario: autoridad del Operador, fusión automática y forense, check `veredicto`.
- El ruleset `proteger-main` exige el check `veredicto` (Revisor), no `pruebas`.
- Revisión independiente (revisor) antes de fusionar PR de workflows, motor, resolutor de la 00 o muchos tests.

## Decisiones recientes (propietario)
D-44 criterios del núcleo · D-45 corte único 5.0.0 · D-46 tope de gasto · D-47 notación · D-48 motor nuevo · D-49 ahorro de CI · D-50 semilla pública · D-51 versión 4.9.0 · D-52 autorización por campaña · D-53 revisión de fusión automática y forense · D-54 plan de ids AUT/NAC · D-58 respuestas del 10-11 · D-61 corte 5.0.0: P20 visible y separado; batería del motor visible bajo demanda (VER, también automática si cambia el código del motor); archivado diario dentro de ARC; forense: cambio de una línea (nombre del flujo P00) solo en el corte con revisión independiente; ids internos en minúsculas (`nac01`) y a la vista «NAC01 · Álava»; semilla pública con el código de la tabla maestra; el mapa de 350 y el histórico NO entran en el corte; alias un ciclo completo con contador a cero antes del paso irreversible (frase del propietario); prueba explícita de la aprobación `produccion` con los nombres nuevos.

## Pendientes del propietario
analítica sin cookies · comprobar DOI · descargas manuales (municipales 2023, europeas 2024, Ecuador, fuentes de naturalidad) · criterio de naturalidad con los mapas · corte 5.0.0 (mayúsculas/minúsculas del id, alias, relevo del motor).


## Relevo 10-11
Los tres chats principales (Planificador, Operador, Coordinador) se relevan por orden del propietario. Tareas abiertas: enumeración exacta (PR en revisión), naturalidad D5/D8 y los 71 territorios, medida de cadenas. Esperan al propietario: analítica, DOI, descargas manuales, criterio de naturalidad, decisiones del corte, publicación del visor.
