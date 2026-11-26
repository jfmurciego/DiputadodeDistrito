/* PROYECTO: Diputado de Distrito
 * CLASE: prueba de la capa «Situación actual · puntos» del Explorar de la V4 (T-500, diseño T-499 1.0.1)
 * VERSIÓN: 1.0.0 · FECHA: 2026-11-25 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
 * FUNCIÓN: (A) la disposición de puntos.js con la geometría real de provincias y el JSON real de escaños: 350 puntos (348 + Ceuta y Melilla en recuadro),
 *   cada provincia con sus escaños, agrupados por partido, placa solo en Madrid, Barcelona, Vizcaya y Tenerife, línea guía solo en Barcelona, nada
 *   que desborde en la disposición de cerca. (B) el visor con un navegador simulado:
 *   capa por defecto, colores, leyenda, ventana de la provincia, salidas a otras capas y vuelta a la doble vuelta si faltan los datos.
 *   Esperados: literales del BOE-A-2023-18907 (escaños y votos) y de la tabla del diseño, no recalculados con el código. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs"), path = require("node:path"), vm = require("node:vm");
const ROOT = path.resolve(__dirname, "..");
const leer = f => fs.readFileSync(path.join(ROOT, f), "utf8");
const provincias = JSON.parse(leer("visor/v2/datos/provincias.json")), comunidades = JSON.parse(leer("visor/v2/datos/comunidades.json"));
const datos = JSON.parse(leer("visor/v4/mapa/puntos_v5_2023.json"));
const puntosSrc = leer("visor/v4/mapa/puntos.js"), explorarSrc = leer("visor/v4/mapa/explorar.js"), dvSrc = leer("visor/v4/mapa/dv.js");
const eq = (a, b, m) => assert.deepEqual(JSON.parse(JSON.stringify(a)), b, m);
const sandbox0 = {}; vm.runInNewContext(puntosSrc, Object.assign(sandbox0, {window: sandbox0}));
const PT = sandbox0.PUNTOS;
const familia = p => ({"EH Bildu": "EH BILDU", CCa: "CC"})[p] || p;

// ---- A. Disposición ----
const L = PT.disponer(provincias, datos, familia);
const por = (lay, cod) => L.puntos.filter(q => q.lay === lay && q.cod === cod);
for (const lay of ["n", "c"]) {
  assert.equal(L.puntos.filter(q => q.lay === lay).length, 348, "350 diputados menos Ceuta y Melilla (recuadro) en " + lay);
  // Escaños literales del BOE-A-2023-18907, cuadro II.
  for (const [cod, n] of [["28", 37], ["08", 32], ["46", 16], ["03", 12], ["41", 12], ["48", 8], ["38", 7], ["42", 2], ["22", 3]]) assert.equal(por(lay, cod).length, n, lay + " " + cod);
}
const nombresPlaca = lay => L.placas.filter(q => q.lay === lay).map(q => q.cod).sort();
eq(nombresPlaca("n"), ["08", "28", "38", "48"], "placa en Madrid, Barcelona, Vizcaya y Santa Cruz de Tenerife; Valencia cabe dentro");
eq(nombresPlaca("c"), [], "al acercar el racimo cabe dentro y no hay placa");
eq(L.guias.map(g => [g.lay, g.cod]), [["n", "08"]], "línea guía solo en Barcelona, a zoom nacional");
eq(L.etiquetas.map(e => e.texto).sort(), ["Alicante 12", "Barcelona 32", "Madrid 37", "Sevilla 12", "Valencia 16"], "rótulo en las de 12 o más escaños");
// Agrupados por partido: en cada provincia, los puntos (por filas) llevan los partidos en el orden de escaños del BOE, y cada partido tantos como escaños.
const p28 = por("n", "28");
eq(Object.fromEntries([...new Set(p28.map(q => q.partido))].map(p => [p, p28.filter(q => q.partido === p).length])).PP, 16, "Madrid: 16 del PP");
let cambios = 0; for (let i = 1; i < p28.length; i++) if (p28[i].partido !== p28[i - 1].partido) cambios++;
assert.equal(cambios, new Set(p28.map(q => q.partido)).size - 1, "cada partido forma un bloque contiguo");
// Dentro de su provincia: Valencia entera en la disposición nacional.
const val = por("n", "46"), f46 = provincias.features.find(f => f.properties.cod === "46");
assert.ok(val.every(q => ptoDentro(q.lng, q.lat, f46.geometry)), "los 16 de Valencia caen dentro de su provincia");
function ptoDentro(x, y, g) {
  const polys = g.type === "MultiPolygon" ? g.coordinates : [g.coordinates];
  return polys.some(poly => { let r = false; for (const ring of poly) for (let i = 0; i < ring.length; i++) { const [x1, y1] = ring[i], [x2, y2] = ring[i ? i - 1 : ring.length - 1]; if ((y1 > y) !== (y2 > y) && x < (x2 - x1) * (y - y1) / (y2 - y1) + x1) r = !r; } return r; });
}
eq(PT.ganador(datos.provincias["28"]).p, "PP"); assert.equal(Math.round(PT.ganador(datos.provincias["28"]).pct * 100), 4087);
// Totales estatales literales: PP 137, PSOE 121 (con PSC), Vox 33, Sumar 31, ERC 7, Junts 7, EH Bildu 6, PNV 5, BNG 1, CC 1, UPN 1; 24 487 414 votos a candidaturas.
const T = PT.totales(datos);
eq(Object.fromEntries(T.lista.map(x => [x.p, x.escanos])), {PP: 137, PSOE: 121, VOX: 33, SUMAR: 31, ERC: 7, JUNTS: 7, "EH Bildu": 6, "EAJ-PNV": 5, BNG: 1, CCa: 1, UPN: 1});
assert.equal(T.escanos, 350); assert.equal(T.estatal, 24487414); assert.equal(T.resto, 606450);
// Ganadores por provincia: PP 40, PSOE 10, PNV 1 (Vizcaya), EH Bildu 1 (Guipúzcoa).
const gan = {}; for (const d of Object.values(datos.provincias)) { const g = PT.ganador(d).p; gan[g] = (gan[g] || 0) + 1; }
eq(gan, {PP: 40, PSOE: 10, "EAJ-PNV": 1, "EH Bildu": 1});

function anguloCosta() {  // grados: pendiente (en Mercator, y hacia el norte) entre el punto más al norte de Galicia y el de Gerona
  const norte = cods => provincias.features.filter(f => cods.includes(f.properties.cod)).flatMap(f => (f.geometry.type === "MultiPolygon" ? f.geometry.coordinates : [f.geometry.coordinates]).flat(2)).reduce((a, p) => p[1] > a[1] ? p : a);
  const my = lat => Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)), g = norte(["15", "27", "32", "36"]), r = norte(["17"]);
  return Math.atan2(my(r[1]) - my(g[1]), (r[0] - g[0]) * Math.PI / 180) * 180 / Math.PI;
}
// Racimos con el mapa girado: las filas de puntos quedan horizontales en la pantalla y Canarias se recoloca sin tocar el original.
{
  const G = 10.65, b = G * Math.PI / 180, merc = (lng, lat) => [(lng + 180) / 360, .5 - Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)) / (2 * Math.PI)];
  const rot = q => { const m = merc(q.lng, q.lat); return [m[0] * Math.cos(b) + m[1] * Math.sin(b), -m[0] * Math.sin(b) + m[1] * Math.cos(b)]; };
  const LG = PT.disponer(provincias, datos, familia, ["n"], G), filas = new Set(LG.puntos.filter(q => q.cod === "28").map(q => Math.round(rot(q)[1] * 1e6 / 40)));
  assert.ok(filas.size <= 8, "Madrid: 37 puntos en pocas filas horizontales: " + filas.size);
  assert.equal(LG.puntos.length, 348); eq(LG.placas.map(q => q.cod).sort(), ["08", "20", "28", "35", "38", "48"], "con el giro, también desbordan Guipúzcoa y Las Palmas");
  const antes = JSON.stringify(provincias.features.find(f => f.properties.cod === "35").geometry), R = PT.recolocarCanarias(provincias, G, [.0047, .0006]);
  assert.equal(JSON.stringify(provincias.features.find(f => f.properties.cod === "35").geometry), antes, "no modifica el original");
  assert.notEqual(JSON.stringify(R.features.find(f => f.properties.cod === "35").geometry), antes);
  assert.equal(JSON.stringify(R.features.find(f => f.properties.cod === "28").geometry), JSON.stringify(provincias.features.find(f => f.properties.cod === "28").geometry), "el resto, igual");
  const mc = PT.disponer(R, datos, familia, ["n"], G).marcoCanarias, ys = mc.slice(0, 4).map(q => Math.round(rot({lng: q[0], lat: q[1]})[1] * 1e6));
  assert.equal(ys[0], ys[1], "el marco de Canarias es horizontal en la pantalla"); assert.equal(ys[2], ys[3]);
}

// ---- B. Visor ----
const el = {}, group = {};
function element(id) {
  if (id === "level" && !el[id]) el[id] = {id, value: "provincia", options: ["comunidad", "provincia", "distrito"].map(value => ({value, disabled: false, removeAttribute(k) { delete this[k]; }}))};
  return el[id] || (el[id] = {id, value: "", hidden: false, checked: true, innerHTML: "", textContent: "", dataset: {}, style: {}, className: "",
    setAttribute(k, v) { this[k] = v; }, addEventListener(k, fn) { this[k] = fn; }, replaceChildren(...c) { this.children = c; },
    appendChild(c) { (this.children ??= []).push(c); return c; }, querySelectorAll() { return []; }});
}
for (const [id, opts] of [["scope", ["nacional", "autonomico"]], ["system", ["proporcional", "mayoritario"]], ["view", ["territorial", "electoral"]], ["regla", ["tres", "dos", "base", "primero"]]])
  group["#" + id + " button"] = opts.map(value => ({dataset: {value}, setAttribute(k, v) { this[k] = v; }}));
group["[data-panel]"] = ["territorio", "resultados", "comparar", "evolucion"].map(panel => ({dataset: {panel}, setAttribute(k, v) { this[k] = v; }}));
const doc = {getElementById: element, querySelectorAll: q => group[q] || [], createElement: tag => ({tag, textContent: "", setAttribute(k, v) { this[k] = v; }}), body: {dataset: {}}, documentElement: {}};
let map; const popups = [];
class Popup { constructor(o) { this.o = o; popups.push(this); } setLngLat(l) { this.l = l; return this; } setHTML(h) { this.html = h; return this; } addTo() { return this; } on() {} remove() { this.removed = true; } }
class FakeMap {
  constructor(o) { this.o = o; this.fits = []; this.sources = new Map(); this.layers = new Map(); this.handlers = {}; this.hit = []; this.fitted = 0; map = this; queueMicrotask(() => this.handlers.load?.()); }
  addControl() {} on(ev, ...a) { this.handlers[ev] = a.at(-1); }
  addSource(id, s) { this.sources.set(id, {data: s.data, setData(n) { this.data = n; }}); } getSource(id) { return this.sources.get(id); }
  addLayer(l) { this.layers.set(l.id, {...l, layout: {visibility: "visible", ...l.layout}, paint: {...l.paint}}); } getLayer(id) { return this.layers.get(id); }
  getLayoutProperty(id, k) { return this.layers.get(id).layout[k]; } setLayoutProperty(id, k, v) { this.layers.get(id).layout[k] = v; }
  setPaintProperty(id, k, v) { this.layers.get(id).paint[k] = v; } fitBounds(b, o) { this.fitted++; this.fits.push([b, o]); } getZoom() { return this.zoom ?? 5; } setFilter(id, f) { this.layers.get(id).filter = f; } queryRenderedFeatures() { return this.hit; }
}
const fixtures = {"../v2/datos/provincias.json": provincias, "../v2/datos/comunidades.json": comunidades, "calendario.json": {}};
const sandbox = {document: doc, maplibregl: {Map: FakeMap, NavigationControl: class {}, Popup}, console, location: {search: ""}, history: {replaceState() {}}, TextDecoder,
  getComputedStyle: () => ({getPropertyValue: () => ""}),
  fetch: async key => { const ok = Object.hasOwn(fixtures, key); return {ok, status: ok ? 200 : 404, json: async () => fixtures[key]}; }};
sandbox.window = sandbox; sandbox.globalThis = sandbox;
async function arrancar(conDatos) {
  for (const k of Object.keys(el)) delete el[k];
  popups.length = 0; doc.body.dataset = {};
  if (conDatos) fixtures["puntos_v5_2023.json"] = datos; else delete fixtures["puntos_v5_2023.json"];
  const ctx = Object.assign({}, sandbox); ctx.window = ctx; ctx.globalThis = ctx;
  vm.runInNewContext(dvSrc, ctx, {filename: "dv.js"}); vm.runInNewContext(puntosSrc, ctx, {filename: "puntos.js"});
  const marker = "  init();\n})();"; assert.ok(explorarSrc.includes(marker), "cambió el arranque del Explorar");
  vm.runInNewContext(explorarSrc.replace(marker, "  ctxT.__T__={S,D,renderDetail};\n  init();\n})();").replace("(function () {", "(function () {const ctxT=globalThis;"), ctx, {filename: "explorar.js", timeout: 20000});
  for (let i = 0; i < 60; i++) await new Promise(r => setImmediate(r));
  return ctx.__T__;
}
const flush = async () => { for (let i = 0; i < 40; i++) await new Promise(r => setImmediate(r)); };

(async () => {
  let t = await arrancar(true);
  assert.equal(doc.body.dataset.ready, "1");
  // 1. Por defecto: capa de puntos, Congreso, actual proporcional, electoral, 2023; 348 puntos en el mapa; Ceuta y Melilla, en recuadro.
  eq([t.S.layer, t.S.scope, t.S.system, t.S.view, t.S.election, t.S.level], ["puntos", "nacional", "proporcional", "electoral", "202307", "provincia"]);
  // Giro fijo (T-500): el valor sale de las geometrías (Estaca de Bares frente al punto más al norte de Gerona), no del código; sin rotación del usuario.
  const giro = Number(/GIRO_NAC=([\d.]+)/.exec(explorarSrc)[1]);
  assert.equal(giro, Math.round(-anguloCosta() * 100) / 100, "constante calculada con las geometrías");
  assert.equal(map.o.bearing, giro); assert.equal(map.o.dragRotate, false); eq(map.o.fitBoundsOptions.bearing, giro);
  element("reset-map").onclick(); assert.equal(map.fits.at(-1)[1].bearing, giro, "«Volver a España» restaura el mismo giro"); map.fitted = 0;
  assert.equal(doc.body.dataset.puntos, "348");
  assert.equal(map.getLayer("v5-n").layout.visibility, "visible"); assert.equal(map.getLayer("prov-fill").layout.visibility, "visible"); assert.equal(map.getLayer("dist-fill").layout.visibility, "none");
  assert.equal(map.getSource("distritos").data.features.length, 0, "no se cargan distritos para esta capa");
  // 2. Relleno de provincia: el mismo que la capa proporcional «Partido más votado» (sin aclarar) y con su misma opacidad y trazo.
  const relleno = JSON.stringify(map.getLayer("prov-fill").paint["fill-color"]), opac = map.getLayer("prov-fill").paint["fill-opacity"];
  assert.equal(relleno.slice(0, 24), '["match",["get","party"]'); assert.ok(relleno.includes('"#1d6fb8"') && relleno.includes('"#d32b2b"'), "paleta de partidos plena");
  assert.ok(map.getSource("prov").data.features.every(f => f.properties.v5color === undefined), "sin color propio ni aclarado");
  assert.equal(opac, .88); eq([map.getLayer("prov-line").paint["line-color"], map.getLayer("prov-line").paint["line-width"]], ["#fff", 1]);
  assert.equal(map.getLayer("v5-placa-fill").paint["fill-opacity"], 1, "la placa no es translúcida");
  // 3. Leyenda: % sobre votos a candidaturas, escaños, resto y total; fuente y escala.
  const ley = element("v5-content").innerHTML;
  for (const s of ["33,3 %", "31,9 %", "12,5 %", "PSOE (con PSC)", "Resto (sin escaño)", "2,5 %", "<td>350</td>", "% sobre votos a candidaturas", "BOE-A-2023-18907", "partido más votado"]) assert.ok(ley.includes(s), s);
  assert.equal(element("v5-mode").hidden, false); assert.equal(element("legend").innerHTML, "", "el mapa queda libre");
  // 4. Clic en Madrid: resalta, abre la ventana con la tabla (votos, %, escaños) y no acerca el mapa.
  const f28 = provincias.features.find(f => f.properties.cod === "28");
  map.hit = [{layer: {id: "prov-fill"}, geometry: f28.geometry, properties: f28.properties}];
  map.handlers.click({point: {}, lngLat: {lng: -3.7, lat: 40.4}}); await flush();
  assert.equal(map.fitted, 0); assert.equal(t.S.province, null);
  assert.equal(JSON.stringify(map.getLayer("prov-sel").filter), JSON.stringify(["==", ["get", "cod"], "28"]));
  const pop = popups.at(-1).html;
  for (const s of ["Madrid · 37 escaños", "<td>PP</td><td>1.463.183</td><td>40,9 %</td><td>16</td>", "% sobre votos a candidaturas"]) assert.ok(pop.includes(s), s);
  for (const s of ["<dt>Escaños 2023</dt><dd>37</dd>", "<dt>Votos a candidaturas</dt><dd>3.579.713</dd>", "<dt>Más votado</dt><dd>PP · 40,9 %</dd>"]) assert.ok(element("context").innerHTML.includes(s), s);
  map.hit = []; map.handlers.click({point: {}}); await flush();
  assert.equal(popups.at(-1).removed, true); assert.equal(map.getLayer("prov-sel").filter[2], "");
  // 5. Al acercar (zoom ≥ 6,1) se calcula y se usa el racimo de cerca; los puntos de cerca solo se ven desde el zoom 6,6.
  assert.equal(map.getSource("v5pts").data.features.filter(f => f.properties.lay === "c").length, 0);
  map.zoom = 7; map.handlers.zoom(); await flush();
  assert.equal(map.getSource("v5pts").data.features.filter(f => f.properties.lay === "c").length, 348);
  assert.equal(map.getLayer("v5-c").minzoom, 6.6); assert.equal(map.getLayer("v5-n").maxzoom, 6.6); map.zoom = 5;
  // 6. Otra capa: los puntos se ocultan. Doble vuelta: sistema mayoritario. Volver a «puntos»: Congreso, proporcional, electoral.
  element("layer").value = "ganador"; element("layer").onchange({target: element("layer")}); await flush();
  assert.equal(JSON.stringify(map.getLayer("prov-fill").paint["fill-color"]), relleno, "es el mismo relleno que «Partido más votado»");
  assert.equal(map.getLayer("v5-n").layout.visibility, "none"); assert.equal(element("v5-mode").hidden, true);
  element("layer").value = "doblevuelta"; element("layer").onchange({target: element("layer")}); await flush();
  eq([t.S.layer, t.S.system], ["doblevuelta", "mayoritario"]);
  element("layer").value = "puntos"; element("layer").onchange({target: element("layer")}); await flush();
  eq([t.S.layer, t.S.scope, t.S.system, t.S.view, t.S.province], ["puntos", "nacional", "proporcional", "electoral", null]);
  assert.equal(map.getLayer("v5-n").layout.visibility, "visible");
  // 7. Sistema «Mayoritario DDD», ámbito «Autonómico» o una elección que no es 2023 sacan de la capa de puntos (no se mezclan datos).
  group["#system button"][1].onclick(); await flush(); assert.equal(t.S.layer, "ganador");
  element("layer").value = "puntos"; element("layer").onchange({target: element("layer")}); await flush();
  group["#scope button"][1].onclick(); await flush(); assert.equal(t.S.layer, "ganador");
  element("layer").value = "puntos"; element("layer").onchange({target: element("layer")}); await flush();
  element("elections").children.find(b => b.textContent === "nov. 2011").onclick(); await flush(); assert.equal(t.S.layer, "ganador");
  // 8. Sin el fichero de datos: vuelve a la doble vuelta y lo dice (fallo cerrado, sin puntos inventados).
  t = await arrancar(false);
  eq([t.S.layer, t.S.system], ["doblevuelta", "mayoritario"]); assert.equal(element("layer").value, "doblevuelta");
  assert.equal(map.getLayer("v5-n"), undefined); assert.match(element("map-notice").textContent, /situación actual no están disponibles/);
  console.log("OK visor v4 puntos (350 diputados por provincia, placas, relleno de la capa proporcional, leyenda, ventana y salidas)");
})().catch(e => { console.error(e); process.exitCode = 1; });
