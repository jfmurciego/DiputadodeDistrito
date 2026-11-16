# Traspaso del Planificador — 16-11-2026 (14:00 Madrid)

VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ANTERIOR: docs/TRASPASO_PLANIFICADOR_2026-11-14.md

Sesiones: Planificador saliente `session_01KQDtFsURitLodmiR3KkgF3` · Coordinador `session_01KQDtFvHdfhWXuS4s8HXzdv` (Sonnet) · Operador `session_01KQDtFqw1LBgGn6nCuxP8Yx` (Opus).
Plan vigente: `docs/PLAN.md` 1.0.52 (D-119 a D-130, cola hasta T-367). Siguiente id libre: **T-368**.

## Reglas del propietario que más pesan (además de CLAUDE.md y del traspaso del 14-11)
- **Diseño antes que implementación, al detalle.** Ningún encargo se implementa sin que el propietario apruebe el detalle (D-129). No proponer acciones cuando pide un plan; no abrir PR ni cambiar nada sin aprobación.
- **Aquí solo se planifica:** comandos, scripts y pasos manuales al propietario los da el Coordinador en su chat, no el Planificador.
- Sin trucos de nombres (p. ej. «P70-E»): si no es un paso, no lleva código de paso.
- Workflows: uno por familia, opciones dentro, nada «Interno», nada de parámetros técnicos visibles (D-129, D-130). Esta migración debe ser la última.
- Avisos: toda PARADA/fallo no transitorio/fin de tanda/PR del camino crítico, al momento y con notificación al móvil (D-122). No reenviar estado sin valor.
- Ahorro: pocos chats vivos (Planificador, Coordinador, Operador + ≤4 implementadores), un revisor por PR, Sonnet salvo núcleo.
- Fiabilidad sobre velocidad: nada de lanzar a ciegas; inventario/test de flujo antes de reanudar.
- Antes de afirmar un dato, comprobarlo (ids: `aut11` = Extremadura; Melilla = 52). Corregir en voz alta.

## Estado al 16-11 14:00
- **Regeneración Deslinde 1.1: CERRADA Y PUBLICADA** (71/71, P50 6/6 a las 12:03). Congelación levantada.
- **Fusionadas hoy:** #800, #801 (ensayo 29-11), #839 (paralelismo T-360), #840 (población D-128), #841 (histórico por época T-365), #797, #765, #827, #829, #831, #832, #835-#838.
- **Abiertas:** #820 (galería + LICENSE D-123; T-325 en curso), #842 (fichas del histórico, BORRADOR: se reescriben para la P00 nueva). #830 cerrada.
- **En curso:** T-364b (reglas de población del 16-11, ver D-128); T-366 (P90) arranca al fusionarse #820.

## Frentes, en orden
1. **Ensayo en seco del 29-11** sobre los workflows actuales: falta rellenar los source_sha256 de T-333 en los contratos; ficha del Operador `docs/autorizaciones/2026-11-15_ensayo-noche-29-11.md` (con las dos condiciones del Planificador: pasa por la tabla 2026→2023 e informa de secciones partidas; no toca el registro del visor). Luego frase del propietario.
2. **Migración de workflows (D-129):** pasos 1 a 10; presentar AL DETALLE cada encargo y esperar aprobación. Paso 1 (P90) ya aprobado y encargado (T-366). Siguiente a presentar: paso 2, P70 Archivo (absorbe Poda de R2, Recuperar producto y las tareas archivar_r2/extraer_m06 del Mantenimiento; parámetros visibles: acción y simular).
3. **Histórico de las generales (D-125, D-126, D-128):** fuentes a R2 (faltan 10 piezas y 30832/Censo 2011: el propietario las sube desde su Windows con el script de #829 en modo reanudar); T-364b; después, la campaña irá con la P00 nueva (un botón por elección: territorios=Congreso, elección=AAAA-MM).
4. **Nueva forma de trabajar** (presentada al propietario el 16-11, aprobada en lo esencial dentro de D-129/D-130, a detallar en el paso 9): comprobación previa con semáforo, políticas de reintento/apartado y parada sistémica, informe en un issue, versión fija por campaña, estado fuera de main, una sesión de IA al cierre.
5. Después: P10 desde R2 para ogc_features (T-347), T-309, repositorio privado y público/runner (aparcados hasta el 30-11; recordatorio programado el 30-11 para el fondo de mapa propio, T-316).

## Pendiente del propietario
Registro de la propiedad intelectual (16-11); revisar el visor publicado; subir a R2 las piezas que faltan; confirmar en cada encargo de la migración; frase del ensayo del 29-11.
