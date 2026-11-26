/* PROYECTO: Diputado de Distrito
 * CLASE: prueba de interacción del Explorar de la V4 (T-423)
 * VERSIÓN: 1.2.0 · FECHA: 2026-11-26 · ESTADO: candidato · ANTERIOR: legacy/tests/test_visor_v4_explorar_v1.1.0_20261124.js
 * CAMBIOS: 1.2.0 (T-501): `flush` espera a que no haya fetch ni sha256 pendientes (10 vueltas seguidas, tope 15 s) en vez de 60 vueltas fijas, que a veces no bastaban. 1.1.0 (T-456): sin aviso ni leyenda «sin valor oficial». 1.0.0: el Explorar de la V4 (visor/v4/mapa/explorar.js, copia de la V3 + capa «Doble vuelta») con un navegador simulado,
 *   la cartografía real de provincias y comunidades, el índice real de los 52 nac (datos_abiertos/INDEX.json) y CSV de doble vuelta
 *   sintéticos con su sha256. Esperados: literales (bloques y reglas escritos a mano), no recalculados con el código del visor. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs"), path = require("node:path"), vm = require("node:vm"), crypto = require("node:crypto");
const ROOT = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(ROOT, "visor/v4/mapa/explorar.js"), "utf8");
const dvSource = fs.readFileSync(path.join(ROOT, "visor/v4/mapa/dv.js"), "utf8");
const provincias = JSON.parse(fs.readFileSync(path.join(ROOT, "visor/v2/datos/provincias.json"), "utf8"));
const comunidades = JSON.parse(fs.readFileSync(path.join(ROOT, "visor/v2/datos/comunidades.json"), "utf8"));
const index = JSON.parse(fs.readFileSync(path.join(ROOT, "datos_abiertos/INDEX.json"), "utf8"));
const NAC = Object.keys(index.territorios).filter(k => /^nac\d{2}$/.test(k)).sort();
assert.equal(NAC.length, 52, "el índice real trae los 52 territorios del Congreso");

// Distritos: un cuadrado diminuto por distrito, con el número público 1..K del índice real.
const sq = (x, y) => ({ type: "Polygon", coordinates: [[[x, y], [x + .01, y], [x + .01, y + .01], [x, y + .01], [x, y]]] });
const fixtures = {};
const bin = {};
const sha = b => crypto.createHash("sha256").update(b).digest("hex");
const CAB_R = "district_id,escenario,vuelta_decisiva,candidatura_ganadora,bloque_ganador,votos_1v,cuota_1v,finalista_a,finalista_b,votos_a_2v,votos_b_2v,cuota_ganador_2v,votos_abstencion,empate\n";
const CAB_D = "district_id,escenario,candidatura,partido,bloque,votos_1v,votos_candidatura\n";
// Por distrito, literal: dv_A gana Izquierdas en 2.ª vuelta 40-30 (los 15 nacionalistas se abstienen: 40/70 = 57,1 %); dv_B gana Patriotas en 1.ª; dv_base gana PSOE
// en 2.ª por 50,5-49,5 (ventaja < 5 puntos: color claro); primero gana PP.
function csvs(k) {
  let r = CAB_R, d = CAB_D;
  for (const x of index.territorios[k].distritos) {
    const i = x.distrito;
    r += `${i},dv_A,2,bloque:Izquierdas,Izquierdas,40,0.4,bloque:Izquierdas,bloque:Patriotas,40,30,0.571429,15,false\n`;
    r += `${i},dv_B,1,bloque:Patriotas,Patriotas,60,0.6,,,,,,0,false\n`;
    r += `${i},dv_base,2,PSOE,Izquierdas,40,0.4,PSOE,PP,505,495,0.505051,0,false\n`;
    r += `${i},primero,1,PP,Patriotas,41,0.41,,,,,,0,false\n`;
    d += `${i},dv_A,bloque:Izquierdas,PSOE,Izquierdas,40,40\n${i},dv_A,bloque:Patriotas,PP,Patriotas,30,30\n${i},dv_A,bloque:Nacionalistas,ERC,Nacionalistas,15,15\n`;
    d += `${i},dv_B,bloque:Patriotas,PP,Patriotas,60,60\n${i},dv_B,bloque:Izquierdas,PSOE,Izquierdas,40,40\n`;
    d += `${i},dv_base,PSOE,PSOE,Izquierdas,40,40\n${i},dv_base,PP,PP,Patriotas,35,35\n${i},dv_base,VOX,VOX,Patriotas,25,25\n`;
    d += `${i},primero,PP,PP,Patriotas,41,41\n${i},primero,PSOE,PSOE,Izquierdas,40,40\n`;
  }
  return [Buffer.from(r), Buffer.from(d)];
}
const dvIndex = { schema: "ddd.v4-doble-vuelta/1.0", eleccion: "2023-07", territorios: [] };
NAC.forEach((k, n) => {
  const t = index.territorios[k];
  fixtures["../datos/" + t.geojson.ruta] = { type: "FeatureCollection",
    features: t.distritos.map((x, j) => ({ type: "Feature", geometry: sq(n, j * .02), properties: { distrito: x.distrito, district_pop: x.poblacion, section_count: 1 } })) };
  const [r, d] = csvs(k);
  bin["datos/" + k + "/resultados_doble_vuelta.csv"] = r;
  bin["datos/" + k + "/detalle.csv"] = d;
  dvIndex.territorios.push({ id: k, nombre: t.provincia, distritos: t.distritos.length,
    resultados: { ruta: k + "/resultados_doble_vuelta.csv", sha256: sha(r) }, detalle: { ruta: k + "/detalle.csv", sha256: sha(d) },
    geometria: { ruta: k + "/distritos.geojson", sha256: "0".repeat(64) } });
});
// Un territorio con la huella mal: no debe pintarse (fallo cerrado), los otros 51 sí. Se usa en la última prueba.
bin["datos/INDEX.json"] = Buffer.from(JSON.stringify(dvIndex));
const prov28 = provincias.features.find(f => f.properties.cod === "28");
const clave28 = Object.entries(index.territorios).find(([, v]) => v.provincia === "Madrid")[0];
const d1 = index.territorios[clave28].distritos[0].distrito;
Object.assign(fixtures, {
  "../v2/datos/provincias.json": provincias, "../v2/datos/comunidades.json": comunidades, "../datos/INDEX.json": index,
  "../v2/datos/secciones/INDEX.json": { provincias: { "28": {} } },
  "../v2/datos/secciones/28.geojson": { type: "FeatureCollection", features: [{ type: "Feature", geometry: prov28.geometry, properties: { s: "2807912003", m: "Madrid", p: 1622, d: d1 } }] },
  "../v2/datos/territorial.json": { provincias: {} }, "calendario.json": {}
});

const el = {}, group = {};
function element(id) {
  if (id === "level" && !el[id]) el[id] = { id, value: "provincia", options: ["comunidad", "provincia", "distrito"].map(value => ({ value, disabled: false, removeAttribute(k) { delete this[k]; } })) };
  return el[id] || (el[id] = { id, value: "", hidden: false, checked: true, innerHTML: "", textContent: "", dataset: {}, style: {},
    setAttribute(k, v) { this[k] = v; }, addEventListener(k, fn) { this[k] = fn; }, replaceChildren(...c) { this.children = c; },
    appendChild(c) { (this.children ??= []).push(c); return c; }, querySelectorAll() { return []; } });
}
for (const [id, opts] of [["scope", ["nacional", "autonomico"]], ["system", ["proporcional", "mayoritario"]], ["view", ["territorial", "electoral"]], ["regla", ["tres", "dos", "base", "primero"]]])
  group["#" + id + " button"] = opts.map(value => ({ dataset: { value }, setAttribute(k, v) { this[k] = v; } }));
group["[data-panel]"] = ["territorio", "resultados", "comparar", "evolucion"].map(panel => ({ dataset: { panel }, setAttribute(k, v) { this[k] = v; } }));
const doc = { getElementById: element, querySelectorAll: q => group[q] || [], createElement: tag => ({ tag, textContent: "", setAttribute(k, v) { this[k] = v; } }),
  body: { dataset: {} }, documentElement: {} };
let map; const popups = [];
class Popup { constructor(o) { this.o = o; popups.push(this); } setLngLat(l) { this.l = l; return this; } setHTML(h) { this.html = h; return this; } addTo() { return this; } on() {} remove() { this.removed = true; } }
class FakeMap {
  constructor() { this.sources = new Map(); this.layers = new Map(); this.handlers = {}; this.hit = []; this.fitted = 0; map = this; queueMicrotask(() => this.handlers.load?.()); }
  addControl() {} on(ev, ...a) { this.handlers[ev] = a.at(-1); }
  addSource(id, s) { this.sources.set(id, { data: s.data, setData(n) { this.data = n; } }); } getSource(id) { return this.sources.get(id); }
  addLayer(l) { this.layers.set(l.id, { ...l, layout: { visibility: "visible", ...l.layout }, paint: { ...l.paint } }); } getLayer(id) { return this.layers.get(id); }
  getLayoutProperty(id, k) { return this.layers.get(id).layout[k]; } setLayoutProperty(id, k, v) { this.layers.get(id).layout[k] = v; }
  setPaintProperty(id, k, v) { this.layers.get(id).paint[k] = v; } fitBounds() { this.fitted++; } getZoom() { return 5; } setFilter(id, f) { this.layers.get(id).filter = f; } queryRenderedFeatures() { return this.hit; }
}
const libre = { Map: FakeMap, NavigationControl: class {}, Popup };
const ab = b => b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
// Trabajo asíncrono pendiente (fetch y sha256): `flush` espera a que no quede ninguno durante 10 vueltas seguidas del bucle de eventos, y falla si no se estabiliza en 15 s
// (T-501: antes eran 60 vueltas fijas y a veces no bastaban con la carga de la verificación de huellas).
let pendiente = 0;
const contar = p => { pendiente++; return Promise.resolve(p).finally(() => { pendiente--; }); };
const sandbox = { document: doc, maplibregl: libre, console, location: { search: "" }, history: { replaceState() {} }, TextDecoder, crypto: { subtle: { digest: (a, b) => contar(crypto.webcrypto.subtle.digest(a, b)) } },
  getComputedStyle: () => ({ getPropertyValue: () => "" }),
  fetch: key => contar((async () => {
    if (Object.hasOwn(bin, key)) return { ok: true, status: 200, arrayBuffer: async () => ab(bin[key]) };
    const ok = Object.hasOwn(fixtures, key); return { ok, status: ok ? 200 : 404, json: async () => fixtures[key] };
  })()) };
sandbox.window = sandbox; sandbox.globalThis = sandbox;
vm.runInNewContext(dvSource, sandbox, { filename: "dv.js" });
const marker = "  init();\n})();";
assert.ok(source.includes(marker), "cambió el arranque del Explorar");
vm.runInNewContext(source.replace(marker, "  globalThis.__T__={S,D,DVD,setRegla,renderDetail,openProvince};\n  init();\n})();"), sandbox, { filename: "explorar.js", timeout: 10000 });
const eq = (a, b, m) => assert.deepEqual(JSON.parse(JSON.stringify(a)), b, m); // objetos del contexto vm: otro prototipo de Array
const flush = async () => { const t0 = Date.now(); for (let quietas = 0; quietas < 10;) { if (Date.now() - t0 > 15000) throw new Error("el Explorar no se estabiliza: trabajo pendiente"); await new Promise(r => setImmediate(r)); quietas = pendiente === 0 ? quietas + 1 : 0; } };

(async () => {
  await flush();
  const t = sandbox.__T__;
  assert.equal(doc.body.dataset.ready, "1", "el mapa debe arrancar");
  // 1. Por defecto: capa «Doble vuelta», regla «Tres bloques», Congreso, mayoritario, electoral, 2023.
  eq([t.S.layer, t.S.regla, t.S.scope, t.S.system, t.S.view, t.S.election], ["doblevuelta", "tres", "nacional", "mayoritario", "electoral", "202307"]);
  assert.equal(element("regla-ayuda").textContent, "Izquierdas, Nacionalistas y Derecha nacional se presentan cada uno como una sola candidatura.");
  // 2. Vista nacional: los distritos de los 52 nac llevan su bloque en las cuatro reglas.
  const feats = map.getSource("distritos").data.features;
  const total = NAC.reduce((s, k) => s + index.territorios[k].distritos.length, 0);
  assert.equal(feats.length, total, "todos los distritos de los 52 nac");
  eq([...new Set(feats.map(f => f.properties.identity))].sort(), NAC, "los 52 nac en el mapa nacional");
  for (const f of feats) eq([f.properties.dv_tres, f.properties.dv_dos, f.properties.dv_base, f.properties.dv_primero],
    ["izq", "pat", "izq-claro", "pat"], f.properties.identity + "/" + f.properties.distrito);
  assert.equal(t.DVD.datos.size, 52); assert.equal(t.DVD.fallos.size, 0);
  // 3. Coloreado por bloque con la regla elegida; aviso fijo visible.
  const fill = () => map.getLayer("dist-fill").paint["fill-color"];
  eq(fill().slice(0, 2), ["match", ["coalesce", ["get", "dv_tres"], "nodato"]]);
  assert.equal(fill()[fill().indexOf("izq") + 1], "#d32b2b"); assert.equal(fill()[fill().indexOf("pat") + 1], "#1d6fb8");
  // T-459: sin aclarado; la variante «-claro» (ventaja < 5 puntos) lleva el mismo color pleno que su bloque.
  assert.equal(fill()[fill().indexOf("izq-claro") + 1], "#d32b2b"); assert.equal(fill()[fill().indexOf("pat-claro") + 1], "#1d6fb8");
  assert.equal(fill()[fill().indexOf("nac") + 1], "#0f7a52"); assert.equal(fill()[fill().indexOf("sin") + 1], "#5b6470");
  assert.doesNotMatch(element("legend").innerHTML, /sin valor oficial/);
  assert.match(element("map-caption").textContent, /Doble vuelta · Tres bloques/);
  t.setRegla("dos"); await flush();
  eq(fill()[1], ["coalesce", ["get", "dv_dos"], "nodato"]);
  eq(group["#regla button"].map(b => b["aria-pressed"]), ["false", "true", "false", "false"]);
  t.setRegla("tres"); await flush();
  // 4. Ficha de un distrito: primera y segunda vuelta, comparación entre reglas y aviso.
  t.openProvince("28", true); await flush();
  // T-459: cifras de la provincia, con el bloque ganador (Tres bloques: Izquierdas en todos sus distritos) y la población sumada.
  const nd = index.territorios[clave28].distritos.length;
  assert.match(element("context").innerHTML, new RegExp("<dt>Bloques ganadores · Tres bloques</dt><dd>Izquierdas " + nd + "</dd>"));
  assert.match(element("context").innerHTML, /<dt>Distritos DDD<\/dt>/);
  const dist = map.getSource("distritos").data.features.find(f => f.properties.distrito === d1);
  map.hit = [{ layer: { id: "dist-fill" }, geometry: dist.geometry, properties: dist.properties }];
  const fit0 = map.fitted; map.handlers.click({ point: {}, lngLat: { lng: 0, lat: 0 } }); await flush();
  assert.equal(element("dv-mode").hidden, false);
  const ficha = element("dv-content").innerHTML;
  assert.match(ficha, /Decide la segunda vuelta · gana Izquierdas \(bloque\) con el 57,1 %/);
  assert.match(ficha, /1\.ª vuelta/); assert.match(ficha, /2\.ª vuelta<\/h3><p>Izquierdas \(bloque\) 40 · Derecha nacional \(bloque\) 30 · abstención 15/);
  assert.match(ficha, /Nacionalistas \(bloque\)<\/td><td>→ abstención \(su bloque no tiene finalista\)/);
  for (const r of ["Tres bloques → Izquierdas (bloque)", "Dos bloques → Derecha nacional (bloque)", "Sin coaliciones → PSOE", "Mayoría simple en el distrito → PP"]) assert.ok(ficha.includes(r), r);
  assert.doesNotMatch(ficha, /sin valor oficial/);
  // 5. T-459: el clic resalta y abre la ventana con población, votos y bloque ganador con su %, en ese orden; sin zoom ni nivel de sección.
  assert.equal(map.fitted, fit0, "el clic en un distrito no acerca el mapa");
  assert.equal(map.getLayer("dist-sel").filter[0], "all");
  const pop = popups.at(-1).html, orden = ["Población", "Votos", "Bloque ganador"].map(w => pop.indexOf(w));
  assert.ok(orden[0] > 0 && orden[0] < orden[1] && orden[1] < orden[2], "orden población, votos, bloque: " + orden);
  assert.match(pop, new RegExp("<dt>Población</dt><dd>" + Number(index.territorios[clave28].distritos[0].poblacion).toLocaleString("es-ES")));
  assert.match(pop, /<dt>Votos<\/dt><dd>85<\/dd>/); // 40 + 30 + 15 de votos_1v del detalle
  assert.match(pop, /<dt>Bloque ganador<\/dt><dd>Izquierdas · 57,1 %<\/dd>/);
  assert.doesNotMatch(pop, /Ventaja/);
  assert.match(element("context").innerHTML, /<dt>Votos<\/dt><dd>85<\/dd>/);
  t.setRegla("base"); await flush();
  assert.match(popups.at(-1)?.html ?? "", /Población/); // la ventana anterior sigue siendo la del distrito
  t.renderDetail(); assert.match(element("dv-content").innerHTML, /Ventaja ajustada: menos de 5 puntos/);
  t.setRegla("tres"); await flush();
  map.hit = []; map.handlers.click({ point: {} }); await flush();
  assert.equal(popups.at(-1).removed, true, "clic fuera cierra la ventana");
  assert.equal(element("level").options.some(o => o.value === "seccion" || o.value === "municipio"), false);
  // 6. Salir a otra capa de la V3 devuelve la paleta de partidos; volver a la doble vuelta la recupera.
  element("layer").value = "ganador"; element("layer").onchange({ target: element("layer") }); await flush();
  assert.equal(element("dv-mode").hidden, true);
  element("layer").value = "doblevuelta"; element("layer").onchange({ target: element("layer") }); await flush();
  // 7. Otra elección: sin colores de doble vuelta (solo hay 2023) y la capa vuelve a «Partido más votado».
  element("elections").children.find(b => b.textContent === "nov. 2011").onclick(); await flush();
  assert.equal(t.S.layer, "ganador"); assert.equal(map.getLayer("dist-fill").paint["fill-color"], "#a8bac7");
  // 8. Huella que no coincide: ese territorio no se pinta (fallo cerrado) y se dice por qué.
  t.DVD.datos.delete(clave28); bin["datos/" + clave28 + "/detalle.csv"] = Buffer.from(CAB_D);
  element("elections").children.find(b => b.textContent === "jul. 2023").onclick(); await flush();
  element("layer").value = "doblevuelta"; element("layer").onchange({ target: element("layer") }); await flush();
  assert.match(t.DVD.fallos.get(clave28), /no coincide/);
  assert.ok(map.getSource("distritos").data.features.every(f => f.properties.dv_tres === "nodato"));
  console.log("OK visor v4 explorar (52 nac, cuatro reglas, ficha, ventana del distrito y fallo cerrado)");
})().catch(e => { console.error(e); process.exitCode = 1; });
