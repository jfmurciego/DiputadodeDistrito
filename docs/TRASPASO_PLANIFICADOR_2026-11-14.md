# Traspaso del Planificador — 14-11-2026 (21:35)

VERSIÓN: 1.0.0 · FECHA: 2026-11-14 · ANTERIOR: ninguna (fichero nuevo) · Recogido en PLAN 1.0.45

Sesiones: Coordinador `session_01KQDtFsbpUK9cTihvWUce6g` (Sonnet) · Operador `session_01KQDtFqw1LBgGn6nCuxP8Yx` (Opus).
Plan vigente: `docs/PLAN.md` 1.0.44 (D-91 a D-95, plan por fases T-267 a T-290). Siguiente id libre: **T-315**.

## Reglas del propietario (además de CLAUDE.md)
- Tú, español, corto, temas (no ids), semáforo, decidido/construido/probado/publicado. Corregir en voz alta. No preguntar detalles: decidir con criterio y avisar.
- Dejar una nota «📌 Tema cerrado» cada vez que se cierra un tema.
- Cerrar temas antes de abrir nuevos. Nada de PR con fallos (lección: >3 commits de arreglo → regla).
- Ahorro de cuota: Sonnet salvo motor/M07; un revisor por PR terminada; ≤2-5 chats; solo hitos.
- Motor repetible: relanzar desde el principio, nunca parches que acepten versiones antiguas (14-11, ids legacy).
- Tras cualquier renombrado o cambio de cadena: ensayo local de la cadena completa de 1 territorio y una P00 de prueba antes de campañas.
- Congelación del motor y de workflows de producción durante cada campaña de regeneración, hasta la P50.

## Decisiones del 14-11 posteriores al plan 1.0.44 (añadir al plan como D-96…)
- Repositorio: el actual queda PRIVADO cuando acaben las pruebas (hoy público); público nuevo sin historial solo de publicación. Secretos: código Deslinde, definición formal, estudios. Registro de PI el lunes 16-11.
- Licencias aprobadas: código propietario; mapas y resultados CC BY 4.0; código del visor todos los derechos reservados; reglas y contratos CC BY 4.0; plan y arquitectura CC BY-NC 4.0 (#744).
- Deslinde 1.1 (#761, en main): D8 con frontera compartida (shared_border_m), candidato exacto CP-SAT K≤4, desempate por desvío máximo. Batería 1.1 aprobada 71/71.
- Noche 29-11: mapas vigentes 2023; tabla 2026→2023; sección partida entera al distrito de mayor población, nunca repartir votos; minsait_provisional la noche (marca PROVISIONAL, publicar con frase esa noche), infoelectoral_mesas definitivo. Código en main; falta el ensayo en seco.
- Fuentes una sola vez en P10 y R2 (ARC-E); la batería parte del paquete P10 y recalcula P21-P23.
- Analítica: opción A (contador propio Cloudflare Worker, sin datos personales) + maplibre servido desde el sitio.
- Migración de notación interna M01-M08 → P21-P27/P41-P42 (T-313) tras publicar los 71; P22 = «Geometría y adyacencias»; P27 auditoría; ensemble25/50; alcance completo, alias solo de lectura para histórico.
- Histórico desde 2011 adelantado (T-306 inventario en #770).
- Zenodo solo mapas.

## Frentes abiertos
1. **Regeneración Deslinde 1.1 (ficha r3, PARADA):** #786 (T-311: el registro escribe el id canónico + revert de la tanda 1) en revisión/CI; T-314 investiga si DURABLE_LINEAGE_INCOMPATIBLE (CLM) bloquea «Generar desde fuente». Luego: frase del propietario para reanudar r3 desde el paso 1 → P10 de los 71 → archivado → P00 de prueba aut11 → tandas de 5 → P50 lotes ≤12 (sube V3, padrón, ficha de procedencia, composiciones).
2. Ensayo en seco de la noche 29-11 tras la regeneración.
3. T-313 migración P (después de la P50).
4. T-309 endurecer comparaciones mismo_territorio legacy (después de la P50).
5. Almacenes M06: índice en #785; luego script de borrado para el propietario.
6. Analítica #780/#783 + guía de Cloudflare para el propietario; maplibre #781; robot revisor #769 (frase del propietario en su chat).
7. Histórico: plan tras #770.
8. Aparcados hasta cerrar el repo: público nuevo, puente, Pages, Zenodo, runner propio (T-273/275/276/282/283/274B).
9. Investigación (óptimo en medianos, `redist`) y corte 5.0.0 al final; legislatura nueva tras 29-11.

## Pendiente del propietario
Frase de reanudación r3 (cuando esté #786); frase del robot revisor; Cloudflare del contador; registro PI lunes; crear repo público y runner cuando cierre el repo.
