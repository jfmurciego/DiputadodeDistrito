# T-465 · Diseño del piloto del banco (una página)

Fecha: 2026-11-26. Fijado **antes** de ver los resultados de GerryChain puro. Deslinde y el exacto ya se habían ejecutado
en cuatro territorios cuando llegó la precisión del Coordinador; se declara aquí para no esconderlo: ya se sabía que en Sevilla el exacto mejora al ganador
(6 demarcaciones partidas frente a 8), así que la regla de abajo no es ciega para ese caso.

## Pregunta de estudio

¿Qué calidad tiene Deslinde frente a GerryChain puro y frente al óptimo demostrado (CP-SAT), con las mismas reglas,
los mismos átomos y la misma clave D8?

## Alcance aprobado (piloto)

- Territorios: Burgos (nac09), Valladolid (nac47), La Rioja (nac26), Sevilla (nac41) y Madrid (nac28). Congreso.
- Métodos: Deslinde (competición local, `ddd_motor2.competir`, D8, cadenas por defecto); exacto (`optimo_d8.py` de T-296,
  120 s por etapa, 4 hilos); GerryChain puro (`gerrychain_puro.py`). En Madrid no hay exacto: solo GerryChain puro.
- Sin `redist` (fuera del piloto).

## Protocolo

1. Entradas: `bateria_motor.py entradas --desde-fuente --seccionado shapefile`, con las copias nacionales del INE
   verificadas por sha256 contra `orchestracion/fuentes_r2.json` (2023 y 2024 bajadas de ine.es, 2025 y 65034 de `inputs/partes`).
2. Instancia: la de `optimo_d8.py --exportar` (unidades de la composición M06 del canónico, átomos de
   `certificador_exacto.construir_atomos`, reglas `Reglas.desde_contrato`). Los tres métodos se juzgan con la misma
   `Natural.clave("D8")`.
3. GerryChain puro: semilla `recursive_tree_part` sobre los átomos (reintentos hasta la primera válida en el núcleo,
   contados); ReCom `district_pairs` con `evaluar(...).valido` como restricción dura; aceptación siempre; sin recargos ni
   generador «ponderado». Las 10 semillas públicas 1..10; cortes a 10³, 10⁴ y 10⁵ pasos en la misma cadena.
4. Métricas: clave D8 término a término (fuera, exceso sobre el 8 %, demarcaciones partidas, frontera, desvío);
   hueco al óptimo; paso del mejor; autobucles; CPU (`process_time` o `user` de `time`).

## Regla de decisión («seguir o no» con el banco completo)

- **Seguir** si en algún territorio del piloto el exacto o GerryChain puro encuentra un plan válido estrictamente mejor
  en D8 que el ganador de Deslinde (antes de la huella), **o** si el exacto no cierra el óptimo y GerryChain puro queda
  por delante de Deslinde: hay pérdidas que medir y el banco completo es la forma de saber dónde.
- **No seguir** (cerrar con el piloto) si Deslinde iguala el óptimo en todos los territorios con exacto y ninguna
  semilla de GerryChain puro lo mejora a 10⁵ pasos: el banco completo no cambiaría la decisión.
- En ambos casos, cada territorio en que Deslinde pierda abre su propia tarea (T-466).
