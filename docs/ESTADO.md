# Estado operativo (mantiene el Coordinador)

Fecha: 2026-11-09 (noche) · Actualizar en cada PR de lecciones o de estado. Verde = cumple el criterio del propietario; amarillo = en marcha o a medias; rojo = bloqueado o fallando.

## Tablero por tema (prioridad 1: el motor)
| Tema | Estado | Situación | Siguiente |
|---|---|---|---|
| 1. MOTOR (T-132, prioridad máxima; opción B: endurecer, batería primero) | amarillo | Banco de pruebas viable en cloud: 71 entradas reconstruibles desde fuente (Huesca: 9 s M01-M06, PASS, partición idéntica). Ampliado: A) Canónico vs GerryChain vs GerryChain por árboles; B) certificador exacto en 3 provincias; C) inventario de reglas. Motor de producción vedado sin visto bueno del Planificador | Herramienta + archivo R2; primera pasada ~45-75 min |
| 2. Autonómica (19) territorial + electoral | amarillo | Publicadas las 19; Cantabria y Extremadura con receipt antiguo; Gestor 42705439861 (Cantabria/Extremadura) FALLÓ, en diagnóstico | Causa del forense; sin relanzar |
| 2b. Autonómica ensemble 10/25 | rojo | Configs solo de Aragón + Ceuta, Melilla, Madrid, La Rioja, Asturias (#584); 13 comunidades bloqueadas por puentes topológicos o exención por partición (decisión de motor) | Decisión del Planificador |
| 3. Nacional (52) territorial + electoral | verde | 52 circunscripciones con M06 y M08; Madrid, Soria y Valladolid del 350 generados sin publicar | — |
| 3b. Nacional ensemble 10/25 | amarillo | Publicados La Rioja, Salamanca, Sevilla; en curso Huesca (42699103956), Barcelona (42699130014, exención 08073, #565) y Álava (42705496971, causa del fallo); ensemble 25 habilitado (#583), prueba pendiente en La Rioja | Resultados de los runs; medir minutos |
| 4. Gestor de campañas | amarillo | «Campaña completa» en una orden, en seco (#582) y paso A autonómico cableado (#586 #587); Gestor sigue la 00 de prueba (#579); 2011 en cola (42693060899); 2019-11 de las 49 en success | Campaña completa de prueba y históricos restantes |
| 5. Histórico | amarillo | 5 generales vía Gestor (2019-11 hecho, 2011 en cola); autonómico: calendario (#568), 6 comunidades de lote 1 (#585) y paso A (#586) | Andalucía, Aragón y Baleares sin composición M06; 140 siglas sin regla (propietario, otro chat) |
| 6. Visor v2 | amarillo | Desplegado completo (05 42694296247 success: Territorial, secciones, botones, rotación); registro sin entradas del 350 (#574 #575) | El propietario debe ver `/v2/` y la raíz (nadie lo comprueba desde cloud); `web/textos.md` vacío |
| 7. Generales 29-N | amarillo | Escaños 2026 en el repo (Madrid 38, Cádiz 8); nota del censo (#581): el reparto usa población de derecho; padrón 2025 reproduce 48/50 provincias (difieren Ciudad Real y Tenerife) | Cifra del RD sin acreditar; población 2022 del INE; datos de Interior cuando publique (no es rojo) |
| 8. Credibilidad / Zenodo | amarillo | Metadatos y versión 4.9.0 (#576) | Primera versión publicada y DOI, cuando el propietario lo ordene |
| 9. Plataforma | verde | `main` en verde, sin PR abiertas | No prioritaria |

## Reglas vigentes
- Lanzar y publicar solo con la frase del propietario en el chat del Operador. Con el campo `production_run_id` vacío la 05 es «solo sitio».
- Ensemble 50 excluido. Siglas autonómicas: el propietario, por otro chat.

## Chats vivos
Planificador (session_01KQDtFr7cZ5TWDRT9cJsn8m) · Operador (session_01KQDtFu6vxTpgYigxhWadu7) · T-132 motor (session_01KQDtFvU4yQajUv8BjHG1vr) · T-128 ensembles (session_01KQDtFrbvteSJYjqJAiosET) · T-123 Gestor (session_01KQDtFuY92M5qDmmeu3eRTo) · T-121 histórico autonómico (session_01KQDtFuPYLxXGSCVojhrH77) · T-129 censo (session_01KQDtFuFyvFbqPPYSCgaHX9) · T-127 Zenodo (session_01KQDtFsMnNVzaReTZcZgK8n).

## Pendientes del propietario
- Ver `/v2/` y la raíz; `web/textos.md`; siglas autonómicas (140); revisor del entorno `publicacion`; Zenodo (afiliación, paquete firmado, DOI).
