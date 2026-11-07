# Libro de costes del conjunto de oro

Una fila por evaluación de un agente sobre `evals/oro/casos/`. La añade
`python herramientas/evaluar_oro.py --salidas <fichero> --agente <revisor|forense> --anotar --modelo <m> --etiqueta <t>`.
«Tokens» suma el campo `tokens` de cada salida; «A la primera» cuenta las salidas con `intento: 1` sobre las que
declaran `intento`. Umbrales (PLAN, T-39 y T-40): revisor ≥ 80 % de defectos y 0 controles limpios bloqueados;
forense ≥ 10 de las 12 causas del §9 en ≤ 5 líneas.

| Fecha | Agente | Modelo | Etiqueta | Casos | Aciertos | % | Tokens | A la primera |
|---|---|---|---|---|---|---|---|---|
