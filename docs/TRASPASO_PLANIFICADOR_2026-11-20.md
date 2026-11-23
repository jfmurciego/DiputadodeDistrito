# Traspaso del Planificador — 20-11-2026 (tarde)

VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ANTERIOR: ninguna (fichero nuevo; el anterior traspaso es docs/TRASPASO_PLANIFICADOR_2026-11-17.md)

Motivo: relevo por contexto lleno, ordenado por el propietario. Saliente: `session_01KQDtFswfpYv5Ea53uXQyJf` (profundidad 6).
Plan vigente: `docs/PLAN.md` 1.0.72 en la PR #958 (si no está fusionada, léelo de la rama `planificador/plan-1-0-72`). Decisiones hasta D-187. Siguiente id libre: T-435.

## Sesiones vivas
- Coordinador `session_01KQDtFreb8UioMtCpbadD3H` (Sonnet, profundidad 7: no puede crear chats; los crea el Planificador).
- Operador `session_01KQDtFrBdPomBp75jyMxBMm` (Opus).
- Implementadores: T-430 web editable `session_01KQDtFuyL5pbt5UfWdoL8g4` (turno sobre P40) · T-379c P00 3c `session_01KQDtFsyr3AziWWnFykCAQg` (borrador; 3c-ii tras T-430) · T-400 histórico 2011 `session_01KQDtFsCke8hnfmXq4acK2V` · T-432 inventario R2 `session_01KQDtFsMXjwSqawNscp6T11` · T-434 Zenodo/P50 `session_01KQDtFtncdvcNTrHbogWU9f` · T-429 textos V4 `session_01KQDtFsm36gbKwNTp3bytpm` (#949, no prioritaria).

## Estado (semáforo y %)
- V4 OFICIAL en la raíz, publicada y aceptada 🟢 100 %. Autonomías en la V4: 13 fijadas (#948); 15 tras relanzar P75 aut con Asturias y Murcia (#944) + nuevo pin + P40 🟡 85 %. Castilla-La Mancha: portal caído, el propietario busca el fichero (Wayback/datos.gob.es). Extremadura fuera (D-183).
- Zenodo 🔴: la prueba P50 (run 44748912809) falló por ZENODO_SIN_LINAJE y dejó PÚBLICA la Release `mapas-v1.0.0` (74 assets). T-434 arregla, permite retomar solo el depósito y prohíbe Release pública en prueba. No se borra nada; el Operador no relanza hasta T-434. El propietario debe hacer sus 4 pasos (integración GH–Zenodo off, `publicacion` solo main, tokens sandbox y real).
- Web editable (D-186) 🟡 10 %: ddd-web + Cloudflare Pages; GitHub = algoritmo, R2 = fuentes y mapas, la web lee de R2 vía índice «actual». Fase 1 en curso.
- Reorganización P00 🟡 90 %: #913, #938 en borrador; 3c en dos partes; nada se fusiona antes del 29-11. #888 (2a) espera los pasos del propietario en Settings (entornos + secretos; si no conserva la clave .pem, generar una nueva en la app).
- Histórico 2011 🟡 80 %: D-180 y D-185 en curso con T-400.
- R2: duplicados insignificantes; inventario completo en curso (T-432); limpieza aprobada (D-178) tras la regeneración posterior al 29-11.
- Aparcados: Datos y Fuentes (T-424, #950), textos V4 (#949), imagen 1200×630 para redes (la aporta el propietario).

## Cómo trabaja el propietario (lecciones de este turno)
1. Respuestas MUY cortas, de tú, en tabla cuando pide estado, con semáforo + porcentaje real (verde solo si está hecho; el % es pasos hechos/total).
2. Prioridades que fija él; una cosa a la vez cuando dice «siguiente». No preguntes por tareas: eres planificador; el Coordinador lleva el camino crítico. Solo pídele firmas (fusión de código, frases al Operador, publicar) y decisiones de criterio, en una sola ronda con recomendación.
3. Comprueba en `main`/GitHub ANTES de afirmar nada (fusiones por squash cambian el sha: comprobar contenido). Varias veces se le pidieron frases ya dadas o se dio por hecho algo no hecho: le irrita mucho.
4. Una sesión que se reinicia pierde turnos del contexto: antes de negar haber enviado algo, revisa tus eventos (`list_events` de tu propia sesión). Caso 20-11: se negó un «URGENTE» que sí se envió.
5. No inventar ni recomendar sin datos (caso padrón 2011, recomendado y retirado). Corregir en voz alta.
6. La web es para gente de la calle: sin jerga ni códigos (M0x/P2x) en lo visible; tests lo vigilan.
7. Nunca subir material de terceros sin permiso; el permiso puede ser la declaración literal del propietario.
8. Los chats implementadores se quedan parados sin aviso: comprobar con `list_sessions` y pedir al Coordinador vigilancia de >1 h.
9. Permisos: no prometer lo que no puedes conceder; la fusión de código siempre necesita frase literal del propietario en el chat del Coordinador (D-169 cubre solo diseño y plan).
10. Gasto: aviso de límite semanal activo; no abrir chats sin necesidad.
