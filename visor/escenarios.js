/* Agrupación de resultados del visor por escenario (T-27 fase b). VERSIÓN 1.0.0 · 2026-11-02 · candidato.
   Un territorio puede tener varios resultados: el canónico (territorial y electoral), cada escenario de otro algoritmo
   (scenario_m06/scenario_m08, con strategy y scenario_id) y cada ensemble. El selector los agrupa en optgroups y un
   conmutador Territorial/Electoral elige la familia dentro de cada grupo. Funciones puras: sin DOM. */
(function (root) {
  "use strict";
  function stageOf(result) {
    return /_m08$/.test(String(result.kind || "")) ? "electoral" : "territorial";
  }
  function groupKey(result) {
    const kind = String(result.kind || "");
    if (kind === "scenario_m06" || kind === "scenario_m08") return "scenario:" + result.scenario_id;
    if (kind === "ensemble_candidate") return "ensemble:" + (result.ensemble_release_tag || result.ensemble_id || "");
    return "canonical";
  }
  function groupLabel(result) {
    const kind = String(result.kind || "");
    if (kind === "scenario_m06" || kind === "scenario_m08") return (result.strategy || "Escenario") + " · " + result.scenario_id;
    if (kind === "ensemble_candidate") return "Ensemble · " + (result.ensemble_release_tag || result.ensemble_id || "sin etiqueta");
    return "Canónico";
  }
  const ORDER = { canonical: 0, scenario: 1, ensemble: 2 };
  function groupResults(results) {
    const map = new Map();
    for (const result of results) {
      const key = groupKey(result);
      if (!map.has(key)) map.set(key, { key, label: groupLabel(result), items: [] });
      map.get(key).items.push(result);
    }
    return [...map.values()].sort((a, b) => {
      const rank = (g) => ORDER[g.key.split(":")[0]] ?? 9;
      return rank(a) - rank(b) || a.label.localeCompare(b.label, "es");
    });
  }
  function availableStages(results) {
    return { territorial: results.some((r) => stageOf(r) === "territorial"), electoral: results.some((r) => stageOf(r) === "electoral") };
  }
  /* Grupos con al menos un resultado de la familia pedida; cada grupo solo conserva esa familia. */
  function groupsForStage(results, stage) {
    return groupResults(results)
      .map((g) => ({ ...g, items: g.items.filter((r) => stageOf(r) === stage) }))
      .filter((g) => g.items.length);
  }
  const api = { stageOf, groupKey, groupLabel, groupResults, availableStages, groupsForStage };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.DDDEscenarios = api;
})(typeof window !== "undefined" ? window : globalThis);
