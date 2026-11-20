/* PROYECTO: Diputado de Distrito
 * CLASE: prueba de interacción del Explorar de la V4 en el ámbito «Autonómico» (T-427)
 * VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
 * CAMBIOS: navegador simulado (mismo arnés que test_visor_v4_explorar.js) con un índice 1.1 sintético: Andalucía con doble vuelta (run 500),
 *   Asturias declarada sin doble vuelta con su motivo y Canarias con el mapa publicado de OTRA ejecución. Esperados literales: id público =
 *   district_id interno + 1; ningún color sin dato ni con otro mapa; la elección es la autonómica vigente del índice. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs"), path = require("node:path"), vm = require("node:vm"), crypto = require("node:crypto");
const ROOT = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(ROOT, "visor/v4/mapa/explorar.js"), "utf8");
const dvSource = fs.readFileSync(path.join(ROOT, "visor/v4/mapa/dv.js"), "utf8");
const provincias = JSON.parse(fs.readFileSync(path.join(ROOT, "visor/v2/datos/provincias.json"), "utf8"));
const comunidades = JSON.parse(fs.readFileSync(path.join(ROOT, "visor/v2/datos/comunidades.json"), "utf8"));
const index = JSON.parse(fs.readFileSync(path.join(ROOT, "datos_abiertos/INDEX.json"), "utf8"));
const sq = (x, y) => ({ type: "Polygon", coordinates: [[[x, y], [x + .01, y], [x + .01, y + .01], [x, y + .01], [x, y]]] });
const sha = b => crypto.createHash("sha256").update(b).digest("hex");
const CAB_R = "district_id,escenario,vuelta_decisiva,candidatura_ganadora,bloque_ganador,votos_1v,cuota_1v,finalista_a,finalista_b,votos_a_2v,votos_b_2v,cuota_ganador_2v,votos_abstencion,empate\n";
const CAB_D = "district_id,escenario,candidatura,partido,bloque,votos_1v,votos_candidatura\n";
// Distrito público 1: Izquierdas gana en 1.ª con dv_A (60 %); distrito público 2: Patriotas en 1.ª (70 %). Las demás reglas, igual.
let r = CAB_R, d = CAB_D;
for (const [i, b, o] of [[1, "Izquierdas", "Patriotas"], [2, "Patriotas", "Izquierdas"]]) {
  for (const e of ["dv_A", "dv_B", "dv_base", "primero"]) r += `${i},${e},1,${b === "Izquierdas" ? "PSOE" : "PP"},${b},${b === "Izquierdas" ? 60 : 70},0.6,,,,,,0,false\n`;
  for (const e of ["dv_A", "dv_B", "dv_base", "primero"]) d += `${i},${e},${b === "Izquierdas" ? "PSOE" : "PP"},${b === "Izquierdas" ? "PSOE" : "PP"},${b},${b === "Izquierdas" ? 60 : 70},${b === "Izquierdas" ? 60 : 70}\n${i},${e},X,X,${o},40,40\n`;
}
const bin = { "datos/aut01/resultados_doble_vuelta.csv": Buffer.from(r), "datos/aut01/detalle.csv": Buffer.from(d),
  "datos/aut05/resultados_doble_vuelta.csv": Buffer.from(r), "datos/aut05/detalle.csv": Buffer.from(d) };
const ent = (id, clave, ele, run) => ({ id, ambito: "AUT", nombre: clave, etiqueta: clave, clave_visor: clave, eleccion: ele, distritos: 2, run_m08: run,
  aproximado_en_distrito: false, nivel: "seccion",
  resultados: { ruta: id + "/resultados_doble_vuelta.csv", sha256: sha(bin["datos/" + id + "/resultados_doble_vuelta.csv"]) },
  detalle: { ruta: id + "/detalle.csv", sha256: sha(bin["datos/" + id + "/detalle.csv"]) } });
bin["datos/INDEX.json"] = Buffer.from(JSON.stringify({ schema: "ddd.v4-doble-vuelta/1.1", eleccion: "2023-07", territorios: [
  ent("aut01", "andalucia", "2026-05", "500"), ent("aut05", "canarias", "2023-05", "999")],
  sin_doble_vuelta: [{ id: "aut03", clave_visor: "principado_de_asturias", estado: "SIN_VOTOS_AUTONOMICOS", motivo: "sin votos por distrito de su autonómica" }] }));
const prod = (t, run) => ({ territory_id: t, kind: "canonical_m08", viewer_path: "data/" + t + ".geojson", publication_status: "PUBLICABLE", run_id: run, label: "M08" });
const capa = n => ({ type: "FeatureCollection", features: [0, 1].map(i => ({ type: "Feature", geometry: sq(n + i * .02, 37), properties: { district_id: i, winner_party: "PP" } })) });
const fixtures = {
  "../../v2/datos/provincias.json": provincias, "../../v2/datos/comunidades.json": comunidades, "../../datos/INDEX.json": index,
  "../../v2/datos/secciones/INDEX.json": { provincias: {} }, "../../v2/datos/territorial.json": { provincias: {} },
  "calendario.json": { andalucia: [["202206", "jun. 2022"], ["202605", "may. 2026"]], canarias: [["202305", "may. 2023"]], principado_de_asturias: [["202305", "may. 2023"]] },
  "../../data/viewer-results.json": { results: [prod("andalucia", "500"), prod("canarias", "700"), prod("principado_de_asturias", "600")] },
  "../../data/andalucia.geojson": capa(-5), "../../data/canarias.geojson": capa(-15), "../../data/principado_de_asturias.geojson": capa(-6)
};

const el = {}, group = {};
function element(id) {
  if (id === "level" && !el[id]) el[id] = { id, value: "provincia", options: ["comunidad", "provincia", "distrito", "municipio", "seccion"].map(value => ({ value, disabled: false, removeAttribute(k) { delete this[k]; } })) };
  return el[id] || (el[id] = { id, value: "", hidden: false, checked: true, innerHTML: "", textContent: "", dataset: {}, style: {},
    setAttribute(k, v) { this[k] = v; }, addEventListener(k, fn) { this[k] = fn; }, replaceChildren(...c) { this.children = c; },
    appendChild(c) { (this.children ??= []).push(c); return c; }, querySelectorAll() { return []; } });
}
for (const [id, opts] of [["scope", ["nacional", "autonomico"]], ["system", ["proporcional", "mayoritario"]], ["view", ["territorial", "electoral"]], ["regla", ["tres", "dos", "base", "primero"]]])
  group["#" + id + " button"] = opts.map(value => ({ dataset: { value }, setAttribute(k, v) { this[k] = v; } }));
group["[data-panel]"] = ["territorio", "resultados", "comparar", "evolucion"].map(panel => ({ dataset: { panel }, setAttribute(k, v) { this[k] = v; } }));
const doc = { getElementById: element, querySelectorAll: q => group[q] || [], createElement: tag => ({ tag, textContent: "", setAttribute(k, v) { this[k] = v; } }),
  body: { dataset: {} }, documentElement: {} };
let map;
class FakeMap {
  constructor() { this.sources = new Map(); this.layers = new Map(); this.handlers = {}; this.hit = []; map = this; queueMicrotask(() => this.handlers.load?.()); }
  addControl() {} on(ev, ...a) { this.handlers[ev] = a.at(-1); }
  addSource(id, s) { this.sources.set(id, { data: s.data, setData(n) { this.data = n; } }); } getSource(id) { return this.sources.get(id); }
  addLayer(l) { this.layers.set(l.id, { ...l, layout: { visibility: "visible", ...l.layout }, paint: { ...l.paint } }); } getLayer(id) { return this.layers.get(id); }
  getLayoutProperty(id, k) { return this.layers.get(id).layout[k]; } setLayoutProperty(id, k, v) { this.layers.get(id).layout[k] = v; }
  setPaintProperty(id, k, v) { this.layers.get(id).paint[k] = v; } fitBounds() {} getZoom() { return 5; } queryRenderedFeatures() { return this.hit; }
}
const libre = { Map: FakeMap, NavigationControl: class {} };
const ab = b => b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
const sandbox = { document: doc, maplibregl: libre, console, location: { search: "" }, history: { replaceState() {} }, TextDecoder, crypto: crypto.webcrypto,
  getComputedStyle: () => ({ getPropertyValue: () => "" }),
  fetch: async key => {
    if (Object.hasOwn(bin, key)) return { ok: true, status: 200, arrayBuffer: async () => ab(bin[key]) };
    const ok = Object.hasOwn(fixtures, key); return { ok, status: ok ? 200 : 404, json: async () => fixtures[key] };
  } };
sandbox.window = sandbox; sandbox.globalThis = sandbox;
vm.runInNewContext(dvSource, sandbox, { filename: "dv.js" });
const marker = "  init();\n})();";
assert.ok(source.includes(marker), "cambió el arranque del Explorar");
vm.runInNewContext(source.replace(marker, "  globalThis.__T__={S,D,DVD,setRegla,renderDetail,openProvince};\n  init();\n})();"), sandbox, { filename: "explorar.js", timeout: 10000 });
const eq = (a, b, m) => assert.deepEqual(JSON.parse(JSON.stringify(a)), b, m); // objetos del contexto vm: otro prototipo de Array
const flush = async () => { for (let i = 0; i < 60; i++) await new Promise(r => setImmediate(r)); };

(async () => {
  await flush();
  const t = sandbox.__T__;
  assert.equal(doc.body.dataset.ready, "1", "el mapa debe arrancar");
  const region = async v => { element("election-region").value = v; element("election-region").onchange({ target: { value: v } }); await flush(); };
  // 1. Ámbito «Autonómico» con la capa «Doble vuelta»: se mantiene (no se fuerza el Congreso).
  group["#scope button"][1].onclick(); await flush();
  assert.equal(t.S.scope, "autonomico"); assert.equal(t.S.layer, "doblevuelta");
  // 2. Andalucía: autonómica vigente (may. 2026); id público = interno + 1: el interno 0 es el distrito 1 (Izquierdas), el 1 el 2 (Patriotas).
  await region("andalucia");
  eq([t.S.scope, t.S.region, t.S.layer, t.S.election], ["autonomico", "andalucia", "doblevuelta", "202605"]);
  const feats = map.getSource("distritos").data.features;
  eq(feats.map(f => [f.properties.district_id, f.properties.dvDistrito, f.properties.dv_tres, f.properties.dv_primero]), [[0, 1, "izq", "izq"], [1, 2, "pat", "pat"]]);
  eq(map.getLayer("dist-fill").paint["fill-color"].slice(0, 2), ["match", ["coalesce", ["get", "dv_tres"], "nodato"]]);
  assert.match(element("map-caption").textContent, /Doble vuelta · Tres bloques · autonómicas · Andalucía · simulación/);
  assert.equal(element("dv-aviso").hidden, false);
  // 3. Ficha del distrito público 2 con la elección autonómica.
  map.hit = [{ layer: { id: "dist-fill" }, geometry: feats[1].geometry, properties: feats[1].properties }];
  map.handlers.click({ point: {} }); await flush();
  assert.equal(element("dv-mode").hidden, false);
  assert.match(element("dv-heading").textContent, /distrito 2/);
  assert.match(element("dv-content").innerHTML, /Elecciones autonómicas de 05\/2026/);
  assert.match(element("dv-content").innerHTML, /Gana PP en primera vuelta con el 60,0 %/);
  assert.match(element("dv-content").innerHTML, /Simulación sin valor oficial/);
  // 4. Otra elección de Andalucía: sin doble vuelta (solo la vigente) y la capa vuelve a «Partido más votado».
  element("elections").children.find(b => b.textContent === "jun. 2022").onclick(); await flush();
  assert.equal(t.S.layer, "ganador");
  element("elections").children.find(b => b.textContent === "may. 2026").onclick(); await flush();
  element("layer").value = "doblevuelta"; element("layer").onchange({ target: element("layer") }); await flush();
  assert.equal(t.S.scope, "autonomico"); assert.equal(map.getSource("distritos").data.features[0].properties.dv_tres, "izq");
  // 5. Asturias: declarada sin doble vuelta; se dice el motivo y no se pinta.
  await region("principado_de_asturias");
  assert.equal(t.DVD.fallos.get("principado_de_asturias"), "sin votos por distrito de su autonómica");
  assert.ok(map.getSource("distritos").data.features.every(f => f.properties.dv_tres === "nodato"));
  assert.notEqual(map.getLayer("dist-fill").paint["fill-color"][0], "match");
  assert.match(element("legend").innerHTML, /no disponible en Principado de Asturias: sin votos por distrito de su autonómica/);
  // 6. Canarias: el mapa publicado es de otra ejecución que la del índice: fallo cerrado con la causa.
  await region("canarias");
  assert.match(t.DVD.fallos.get("canarias"), /no es el de la doble vuelta \(999\)/);
  assert.ok(map.getSource("distritos").data.features.every(f => f.properties.dv_tres === undefined));
  assert.equal(t.DVD.datos.has("canarias"), false);
  // 7. Lector del índice 1.1: un aut sin motivo, un aut incompleto o un aut en un índice 1.0 se rechazan.
  const idx = JSON.parse(bin["datos/INDEX.json"].toString());
  assert.throws(() => sandbox.DV.leerIndice({ ...idx, sin_doble_vuelta: [{ id: "aut03", motivo: "" }] }), /sin motivo/);
  assert.throws(() => sandbox.DV.leerIndice({ ...idx, territorios: [{ ...idx.territorios[0], eleccion: "" }] }), /aut incompleto/);
  assert.throws(() => sandbox.DV.leerIndice({ ...idx, schema: "ddd.v4-doble-vuelta/1.0" }), /id de territorio no válido/);
  console.log("OK visor v4 explorar autonómico (vigente, id público, sin datos declarado y mapa de otra ejecución)");
})().catch(e => { console.error(e); process.exitCode = 1; });
