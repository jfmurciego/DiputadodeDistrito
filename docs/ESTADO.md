# Estado operativo (mantiene el Coordinador)

Fecha: 2026-11-09 (noche) · Actualizar en cada PR de lecciones o de estado.

## PR abiertas
- Ninguna. Hoy en main: visor v2 (#550 #557 #562–#566 #569), registro (#561 #574 #575), Madrid M05 7.4.4 (#558), Barcelona en ensembles (#565), histórico y autonómicas (#567 #568 #570–#572), reintentos del preflight (#573), Zenodo 4.9.0 (#576), CLAUDE.md (#577).

## Runs
- Sin runs en curso conocidos. Pendiente de orden del propietario en el chat del Operador: 05 «solo sitio» (v2 completo; la anterior 42662842906 falló por un 504 transitorio), prueba y lote de ensembles (06 Huesca falló en el despliegue de Pages), Gestor histórico de las 49 provincias, repetir Cantabria/Extremadura.
- Gestor 350 de Madrid, Soria y Valladolid terminado (sin publicar); las 2 entradas de Valladolid 350 se retiraron del registro (T-126).

## Chats activos
| Chat | Tarea |
|---|---|
| Planificador (session_01KQDtFr7cZ5TWDRT9cJsn8m) | Cola y decisiones |
| Operador (session_01KQDtFu6vxTpgYigxhWadu7) | Lanza y publica solo con la orden del propietario en su chat |
| T-121 (session_01KQDtFuPYLxXGSCVojhrH77) | Histórico autonómico: calendario, datos y siglas de 3 comunidades; falta ampliar |
| T-123 (session_01KQDtFuY92M5qDmmeu3eRTo) | Gestor histórico; las autonómicas esperan el alcance del Planificador |
| T-127 (session_01KQDtFsMnNVzaReTZcZgK8n) | Zenodo; falta el DOI real y decisiones del propietario |

## Decisiones del propietario
- D-3 publicar por provincia; D-17 tolerancia ≤0,5 % (Valencia cumple: 0 % de partidas entre distritos); D-19 `congreso_350`; D-20 siglas; D-22 Gestor 2.0; D-23 limpieza de workflows reversible (el borrado del historial de los 12 workflows desactivados NO se hace sin su aprobación).
- Versión del proyecto: 4.9.0. Objetivo: motor repetible, no resultados antiguos. No se regenera el mapa de 407 por el cambio de motor 7.4.4.

## Pendientes del propietario
- Orden en el chat del Operador para la 05 del v2 completo y para los lotes que quiera.
- `web/textos.md`; Cantabria y Extremadura (receipt antiguo); revisor del entorno `publicacion`; Zenodo (afiliación, paquete firmado).
