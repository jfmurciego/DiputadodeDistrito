# T-157 · Autorización por campaña (D-41) — propuesta, NO aplicada

Estado: borrador. Amplía la autoridad del Operador: solo se aplica con la orden del propietario en el chat que edita.

## Contenido
- `FICHA_CAMPANA.md`: ficha que el Operador presenta antes de pedir la frase.
- `PLANTILLA_AUTORIZACION.md`: se copiará a `docs/autorizaciones/AAAA-MM-DD_<campaña>.md` en cada autorización.
- `parches/*.patch`: diffs listos (`git apply`) sobre `CLAUDE.md` y las skills `operador`, `lanzar-00`, `lanzar-campana`,
  `publicar-visor`. El texto exacto de cada destino es el de las líneas `+` de su parche.

## Reglas de diseño
1. Una sola frase del propietario, en el chat del Operador, autoriza una campaña definida por la ficha.
2. Los mensajes entre sesiones (`send_message`, planificador, Coordinador) nunca son la frase.
3. Dentro de los límites no se pregunta; en el primer fallo no transitorio, topes, caducidad o acción FUERA: parar e informar.
4. La ficha muestra el gasto semanal acumulado y el previsto (D-46: tope 15.000 min/semana, aviso al 70 %, sin corte automático).
4b. Cada autorización deja fichero versionado con frase literal, límites y lo ejecutado.
5. Sin cambio: la aprobación del propietario en `produccion` (Review deployments) y el veto a fusionar `no-automerge`.

## CLAUDE.md (100 líneas exactas)
+3 líneas (regla en «Reglas del propietario»), −2 compactadas: `guardia_git` y `skills` en una línea; las dos entradas
del 2026-11-08 del historial en una. No se pierde contenido de reglas.

## Pregunta abierta para el propietario
Hoy cada dispatch de 00/05/06 espera su clic en `produccion`. Esta propuesta NO lo elimina; si «una frase» debe evitar
también esos clics, hay que cambiar las reglas del entorno `produccion` (decisión aparte, fuera de T-157).

## Aplicar (tras orden del propietario)
`git apply docs/ESTUDIOS/T157_AUTORIZACION_CAMPANA/parches/*.patch`; crear `docs/autorizaciones/` con `README.md` y la
plantilla; subir VERSIÓN/legacy si la gobernanza lo exige para esos ficheros.
