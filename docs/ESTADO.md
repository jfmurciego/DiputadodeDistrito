# Estado operativo (mantiene el Coordinador)

Fecha: 2026-11-11 (madrugada) · Actualizar en cada PR de lecciones o de estado. Verde = cumple el criterio del propietario; amarillo = en marcha o a medias; rojo = bloqueado o fallando. Notación D-47: fases P00-P60 y archivo ARC; en lo que se cuenta al propietario, sin códigos antiguos, sin ids de tarea ni de PR.

## Tablero por tema (prioridad 1: el motor)
| Tema | Estado | Situación | Siguiente |
|---|---|---|---|
| 1. Motor nuevo (D-48) | amarillo | Competición «canónico + generador ponderado + vigente» con función D8 y N=10 en el motor y en la 00 (el motor nuevo corre dentro de la 00 como P30, motor viejo por defecto); certificación y evidencia de población leen el plan ganador; aceptación «nunca peor que el vigente publicado» con el recuento del contrato. Batería de las 19 autonómicas (fase 2): NO, por medida (recuento regional) y lector del vigente, ya corregidos en main | Repetir la batería de las 19 con frase nueva del propietario; si cumple, relevo único y regeneración nocturna; La Rioja del Congreso ya dio el mismo ganador y huella que la referencia |
| 1b. Certificador exacto | amarillo | Modelo ligero con unidades atómicas: Madrid minimax certificado 17.236 = publicado (hueco 3 hab.); Álava, Huesca y Cádiz ≤2 s. Cádiz con techo 115 % infactible (mínimo 1,15919×) | R-NUCLEO hecho; medir en Álava, Albacete, Burgos y Huesca en T-196 |
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

## Tareas del motor y derivadas (10-11)
| Tarea | Estado | Qué |
|---|---|---|
| T-132 a T-203, T-206, T-207, T-212, T-213 | hecha | Batería de los 71, certificador, núcleo único, naturalidad, ensayo de las generales 2026, elección como dimensión del registro, histórico autonómico, aceptación contra el vigente, congelación del corte (paso 0) |
| T-205, T-211, T-217, T-218 | hecha | D8 y el vigente (reparado, D-66) como candidato y semilla en la competición autonómica |
| T-214, T-215 | hecha | Corte 5.0.0 pasos 1-2 (ids, resolver) y paso 4 (nombres v5 de workflows) fusionados |
| T-216, T-221, T-223 | hecha | Motor nuevo como P30 en la 00, certificación con el plan ganador, P30 = misma competición que la batería |
| T-222, T-228, T-229 | hecha | Aceptación: recuento del vigente que compite, recuento regional del contrato, lector del vigente (Canarias, Cataluña, Extremadura, Asturias) |
| T-225 | en revisión (#698, no-automerge) | 52 contratos del Congreso 2026 con el par INE 2025/2025 y decisión tipo F10 (D-65, D-80); pendiente de anotar D-80 en el plan |
| T-224 | cola | Comparación con un vigente de otro seccionado (indicadores agregados) |
| T-226, T-227 | cola (mañana) | `modulos/01` decodificación incremental (Toledo, con plan de cachés); Madrid 2025 (resto de Leganés aislado) |
| T-220 | cola | `git mv territorios/` (corte 5.0.0, paso 5) con prueba A de Melilla y Ceuta |
| T-180, T-196 | en curso | Curva de cadenas y batería local de los 71 (ficha r5 y relevo condicionados a la aceptación de las 19) |

## Reglas vigentes
- Lanzar y publicar solo con la frase del propietario en el chat del Operador; el «sí» en otro chat no cuenta.
- Fusionar toda PR en cuanto esté verde (`pruebas` en success sobre el HEAD exacto y `main` en verde), actualizar las siguientes y cerrar los chats obsoletos guardando su aprendizaje (norma habitual, 10-11). Excepciones con frase del propietario: autoridad del Operador, fusión automática y forense, check `veredicto`.
- El ruleset `proteger-main` exige el check `veredicto` (Revisor), no `pruebas`.
- Revisión independiente (revisor) antes de fusionar PR de workflows, motor, resolutor de la 00 o muchos tests.

## Decisiones recientes (propietario)
D-44 criterios del núcleo · D-45 corte único 5.0.0 · D-46 tope de gasto · D-47 notación · D-48 motor nuevo · D-49 ahorro de CI · D-50 semilla pública · D-51 versión 4.9.0 · D-52 autorización por campaña · D-53 revisión de fusión automática y forense · D-54 plan de ids AUT/NAC · D-58 respuestas del 10-11 · D-65 generales 2026 con mapas de padrón 2023 hasta el corte (par 2025/2025) · D-66 regla del núcleo sin infracciones heredadas, excepción explícita máx. 2 · D-67 N=10 provisional · D-68 función D8 · D-69 texto público de las generales 2026 · D-70 pérdida de votos 2011 aceptada · D-71 analítica sin cookies aplazada · D-75 workflows v5 solo con la batería de las 19 cumplida (el propietario fusionó antes) · D-76 los gemelos de 350 quedan en 2023 · D-80 el Congreso no se regenera para 2023, se espera a la legislatura del 29-11 · D-61 corte 5.0.0: P20 visible y separado; batería del motor visible bajo demanda (VER, también automática si cambia el código del motor); archivado diario dentro de ARC; forense: cambio de una línea (nombre del flujo P00) solo en el corte con revisión independiente; ids internos en minúsculas (`nac01`) y a la vista «NAC01 · Álava»; semilla pública con el código de la tabla maestra; el mapa de 350 y el histórico NO entran en el corte; alias un ciclo completo con contador a cero antes del paso irreversible (frase del propietario); prueba explícita de la aprobación `produccion` con los nombres nuevos.

## Pendientes del propietario
Decisión de techos y exenciones con el padrón 2025 (Las Palmas 1,424 y Málaga 1,37 frente al techo 1,40) y frase nueva para repetir la aceptación de las 19 autonómicas. Sin urgencia: comprobar DOI, descargas manuales (municipales 2023, europeas 2024, Ecuador), token de Cloudflare cuando se publique el visor v2, histórico autonómico.

## Relevo 10-11
Coordinador nuevo desde las 11:15 del 10-11. Chats vivos: Planificador, Operador y T-225. Cerrados con lecciones guardadas (≤6 líneas cada uno): todos los anteriores más T-211, T-214, T-215, T-216, T-221, T-222, T-223, T-228 y T-229. Lecciones del motor nuevo y de la batería en `.claude/rules/motor2.md`; las anteriores en `diagnostico-local.md` y `workflows.md`.
