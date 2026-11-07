# Conjunto de oro de agentes (T-38)

Casos con fuente verificable para que el revisor (T-39) y el forense (T-40) no se den por listos hasta cazar los
defectos históricos sobre el diff original (framework §8). Un JSON por caso en `casos/`; el evaluador es
`herramientas/evaluar_oro.py` (biblioteca estándar, determinista) y sus tests, `tests/test_evaluar_oro.py`.

## Casos (43)

| Grupo | Ids | Agente | Fuente |
|---|---|---|---|
| Causas raíz del §9 | CR-01 a CR-12 | forense | `docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md` §9 |
| Más runs con causa cerrada | CR-13 a CR-18 | forense | `CLAUDE.md` y PR correctiva |
| Banco adversarial | ADV-01 a ADV-16 | revisor | `docs/ARQUITECTURA/referencias/AUDITORIA_CHATGPT_PLAN_V2_2026-11-02.md` §7.2 |
| Diff original con defecto probado | REV-17 a REV-19 | revisor | PR introductora → PR correctiva |
| Controles limpios | ADV-05, CTRL-01 a CTRL-03 | revisor | PR fusionadas sin corrección posterior |
| Calibración | CAL-01 (revisor), CAL-02 (ambos), CAL-03 (forense) | según caso | metaagente v1.0 §29E |

## Esquema común

```json
{
  "id": "ADV-11", "tipo": "revision|forense|calibracion", "agente": "revisor|forense|cualquiera",
  "titulo": "…", "causa": "una línea",
  "origen": {"prs": [381, 386], "runs": [41324108794], "pr_introductora": null, "referencia": "…"},
  "entrada": {…según el modo…},
  "esperado": {…según el tipo…},
  "procedencia": {"fuente": "…", "verificado": "#381 fusionada, squash … sobre …", "fecha": "2026-11-07"}
}
```

### Entrada
- `diff_original` (revisor): la PR tal como se fusionó. `comando` = `git diff <padre> <squash> -- <ficheros>`;
  `sha_candidato` = el squash.
- `revertir_arreglo` (revisor): el candidato es el estado anterior al arreglo. `comando` =
  `git diff <squash del arreglo> <padre> -- <ficheros>` (diff que reintroduce el defecto); `sha_candidato` = el padre.
  Los ficheros excluyen tests, `legacy/` y el registro para no regalar la pista; `--preparar` omite además las líneas
  de cabecera y de comentario que el diff inverso quita (explican el arreglo). Bloquear solo por la bajada de VERSIÓN
  no cuenta como acierto: hay que nombrar el defecto.
- `sintoma_run` (forense): runs y síntoma tal como se vieron (anotaciones o log). No se descargan artefactos.
- `escenario` (calibración): situación y pregunta.

Los SHA son de 40 caracteres. En una sesión con clon superficial:
`git fetch --depth=2 origin <sha>` antes de ejecutar `comando`.

### Salida que se puntúa (JSON del agente)
- Revisor: `{"caso", "sha", "veredicto": "BLOQUEAR|APROBAR" (o FAIL/BLOCKED y PASS/PASS_WITH_EXCEPTIONS de la skill), "defectos": [{"clase", "fichero", "detalle"}], "tokens", "intento"}`.
  Acierta si `sha` coincide con `sha_candidato` (prefijo ≥ 7), el veredicto es el esperado y, si es BLOQUEAR, algún
  defecto trae una de las `clases` esperadas o (uno de los `ficheros` y una de las `claves` en `detalle`).
- Forense: `{"caso", "causa_id", "lineas": [≤ 5], "tokens", "intento"}` (o `diagnostico` en texto). Acierta si
  `causa_id` coincide o el texto contiene `min_claves` de las `claves`; más de 5 líneas es fallo.
- Calibración: `{"caso", "veredicto", "acciones": [], "evidencia"}`. Falla con un veredicto prohibido, con acciones
  fuera de `acciones_permitidas` o sin evidencia (`min_claves`).

Las claves se comparan sin tildes ni mayúsculas. Un caso sin salida es fallo.

## Uso

```bash
python herramientas/evaluar_oro.py --validar
python herramientas/evaluar_oro.py --esperadas --agente revisor > /tmp/ideal.json
python herramientas/evaluar_oro.py --preparar /tmp/entradas --agente revisor   # entrada de cada caso, sin respuesta
python herramientas/evaluar_oro.py --salidas salidas.json --agente revisor --umbral 0.8 --anotar --modelo sonnet --etiqueta "T-39 v1"
```

`--anotar` añade una fila a `LIBRO_DE_COSTES.md` (tokens, aciertos y a la primera).

## Añadir un caso
Solo con fuente verificable (PR fusionada, run o fichero en `main`). Copia un caso del mismo tipo, cambia el id
(`CR|ADV|REV|CTRL|CAL-NN`, igual que el nombre del fichero) y pasa `--validar`. No ajustes las claves a la salida de
un agente concreto: el conjunto mide, no se entrena.

Nota: los `.claude/agents/*.md` nuevos no se cargan en una sesión ya abierta; evalúa con un agente genérico que lea
la definición, o en una sesión nueva.