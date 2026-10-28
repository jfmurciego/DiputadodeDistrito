# Matriz de experimentos de reparación — País Vasco

Entrada común para los ensayos 01–10: M04 auténtico del run `37458584767`, K=75, hard inicial=2 (distritos 30 y 66), 1.713 secciones, 281 unidades, 2.227.684 habitantes; identificadores exactos y SHA constan en cada preregistro. Ningún experimento produjo una candidata completa que habilitara los validadores oficiales.

| Ensayo | Mecanismo | Cobertura/resultado | Estado interpretativo |
|---|---|---|---|
| 01 | M05 v7.8.4 `private_annealing` | 800.000 propuestas; sin hard=0 | `NEGATIVE_BOUNDED`; no infactibilidad |
| 02 | Control base M05 | Establece estado recibido por la búsqueda privada | Control, no método de reparación |
| 03 / 03 v1.1 | MILP global con flujo; raíz fija inicial descartada, luego variable | Timeout sin incumbent bajo 120 s / 100k nodos | `NEGATIVE_BOUNDED` |
| 04 | MILP separado por provincia | Dos timeouts bajo 90 s/provincia | `NEGATIVE_BOUNDED` |
| 05 | Parches simultáneos de 3 distritos | Ambos subproblemas infeasible bajo dominio restringido | No extrapolar a problema global |
| 06 | Anillos operativos internos de 1 salto | Dos timeouts sin incumbent, 60 s por patch | `NEGATIVE_BOUNDED` |
| 07 | MILP relajado sin conectividad | Factibilidad poblacional con 2 movimientos, pero distritos 30 y 66 desconectados | Diagnóstico; mapa rechazado |
| 08 / PV-CUT-01 | Corte de componentes sin raíz | Revisión independiente probó que el corte puede excluir una partición conectada válida; además el primer run no fijaba congelaciones individuales | `NO_GO_ALGORITHM_INVALID_CUT`; no inferencia global |
| 09 / PV-EDGE-01 | Prioridad lexicográfica de compactación por aristas | Supervisor externo cortó a 130 s; no reporte ni asignación | Sin conclusión de factibilidad; no repetir mismo modelo |
| 10 / PV-CUT-02 | Cortes de conectividad enraizados | 3 tests PASS; 10 incumbents desconectados; 42 cortes, 49 nodos; presupuesto de 120 s agotado | Formulación revisada `PASS_ACOTADO`; búsqueda `NEGATIVE_BOUNDED`, no infactibilidad |

No se lanzaron M06, `validar_ejecucion.py` ni auditoría geométrica sobre estados desconectados. No se reutilizó el testigo manual. El siguiente avance algorítmico requeriría una hipótesis diferente y preregistro nuevo; no se amplían automáticamente los presupuestos ni se repiten modelos equivalentes.
