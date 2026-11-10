# Estado operativo (mantiene el Coordinador)

Fecha: 2026-11-10 (tarde) · Actualizar en cada PR de lecciones o de estado. Verde = cumple el criterio del propietario; amarillo = en marcha o a medias; rojo = bloqueado o fallando. Notación D-47: fases P00-P60 y archivo ARC; en lo que se cuenta al propietario, sin códigos antiguos, sin ids de tarea ni de PR.

## Tablero por tema (prioridad 1: el motor)
| Tema | Estado | Situación | Siguiente |
|---|---|---|---|
| 1. Motor nuevo (D-48) | amarillo | Competición «canónico + GerryChain» bajo el núcleo único de reglas; R-NUCLEO ya en el certificador y en la competición; enumeración exacta fusionada; aceptación del relevo escrita (huella real de Soria/Álava/Melilla pendiente de la batería). Naturalidad medida en las 52 y las 12 autonómicas, más Castilla y León, Extremadura y Asturias. D-68: función D8; D-67: N=10 provisional (curva: 172→126 con N=5, 125 con 10, 124 con 20) | T-205 D8 en la competición (generador ponderado, clave D8 compartida); T-196 batería local de los 71 con D8 y N=10 y comparación con lo medido; después relevo y corte 5.0.0 |
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
| T-132, T-136, T-137, T-160, T-163, T-164, T-172, T-175 | hecha | Batería de los 71, certificador exacto y ligero, núcleo único, competición v1.1, naturalidad, R-NUCLEO y enumeración exacta |
| T-194, T-195 | hecha | Aceptación del relevo (T-194b: entradas reales de Melilla/Soria en CI si ≤2 MB y ≤60 s, para la próxima PR del motor); R-NUCLEO en la competición (falta medir qué territorios cambian, en T-196) |
| T-179, T-202 | hecha | Naturalidad C y D8 en 52 + 12 autonómicas + CyL, Extremadura y Asturias (D-66: Ávila sin excepción, vigente reparado) |
| T-180 | en curso (#670, borrador) | Curva de cadenas: 20 representativos entregados; faltan 51 |
| T-205 | en curso | D8 en la competición del motor nuevo (opción b); chat de T-179 |
| T-196 | preparada | Batería local de los 71 con D8 y N=10, tandas reanudables; chat de T-180; si la mejora real es <½ de la medida, parar y avisar |
| T-197, T-199, T-200, T-201, T-201b | hecha | Ensayo de las generales de 2026 y sus huecos: registro con elección, fecha, homologación y equivalencia 2026 bloqueada hasta el ZIP de Interior |
| T-203, T-206 | sin chat | Catálogo de procedencia por elección; texto público D-69 en web y visor (sin publicar), junto a la próxima PR del registro |

## Reglas vigentes
- Lanzar y publicar solo con la frase del propietario en el chat del Operador; el «sí» en otro chat no cuenta.
- Fusionar toda PR en cuanto esté verde (`pruebas` en success sobre el HEAD exacto y `main` en verde), actualizar las siguientes y cerrar los chats obsoletos guardando su aprendizaje (norma habitual, 10-11). Excepciones con frase del propietario: autoridad del Operador, fusión automática y forense, check `veredicto`.
- El ruleset `proteger-main` exige el check `veredicto` (Revisor), no `pruebas`.
- Revisión independiente (revisor) antes de fusionar PR de workflows, motor, resolutor de la 00 o muchos tests.

## Decisiones recientes (propietario)
D-44 criterios del núcleo · D-45 corte único 5.0.0 · D-46 tope de gasto · D-47 notación · D-48 motor nuevo · D-49 ahorro de CI · D-50 semilla pública · D-51 versión 4.9.0 · D-52 autorización por campaña · D-53 revisión de fusión automática y forense · D-54 plan de ids AUT/NAC · D-58 respuestas del 10-11 · D-65 generales 2026 con mapas de padrón 2023 hasta el corte (par 2025/2025) · D-66 regla del núcleo sin infracciones heredadas, excepción explícita máx. 2 · D-67 N=10 provisional · D-68 función D8 · D-69 texto público de las generales 2026 · D-70 pérdida de votos 2011 aceptada · D-71 analítica sin cookies aplazada · D-61 corte 5.0.0: P20 visible y separado; batería del motor visible bajo demanda (VER, también automática si cambia el código del motor); archivado diario dentro de ARC; forense: cambio de una línea (nombre del flujo P00) solo en el corte con revisión independiente; ids internos en minúsculas (`nac01`) y a la vista «NAC01 · Álava»; semilla pública con el código de la tabla maestra; el mapa de 350 y el histórico NO entran en el corte; alias un ciclo completo con contador a cero antes del paso irreversible (frase del propietario); prueba explícita de la aprobación `produccion` con los nombres nuevos.

## Pendientes del propietario
Nada que bloquee el motor: el motor nuevo depende de T-205 y T-196 (de nuestro lado). Sin urgencia: comprobar DOI, descargas manuales (municipales 2023, europeas 2024, Ecuador, fuentes de naturalidad), token de Cloudflare cuando se publique el visor v2, frase al Operador para el histórico autonómico (Andalucía, Baleares, Aragón) y relevo del motor/corte 5.0.0 al final de T-196.

## Relevo 10-11
Coordinador nuevo desde las 11:15. Chats vivos: Planificador, Operador, T-179 (T-205) y T-180 (#670, luego T-196). Cerrados con lecciones guardadas: T-175, T-194, T-195, T-197, T-198, T-199, T-200, T-201, T-132. Lecciones de esta tanda en `.claude/rules/diagnostico-local.md` y `workflows.md`.
