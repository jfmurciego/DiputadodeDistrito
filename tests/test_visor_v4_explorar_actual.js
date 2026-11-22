/* PROYECTO: Diputado de Distrito
 * CLASE: prueba del origen de datos del Explorar de la V4 (T-430, D-186/D-188/D-194)
 * VERSIÓN: 1.0.0 · FECHA: 2026-11-22 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
 * CAMBIOS: reutiliza los datos y el navegador simulado de test_visor_v4_explorar.js (todo lo anterior a su `const sandbox`) y sirve
 *   los MISMOS datos desde un origen remoto `https://datos.example/web/actual/` con su `actual.json`. Esperados literales: (1) con
 *   `mapa/datos.json` apuntando al índice, ningún dato por ruta relativa y el calendario en local; (2) huella mal y el índice no cambia:
 *   recarga el índice una vez y rechaza; (3) huella mal la primera vez y bien después: acepta; (4) dato fuera del índice: rechaza. */
"use strict";
const fs = require("node:fs"), path = require("node:path"), vm = require("node:vm");
const base = fs.readFileSync(path.join(__dirname, "test_visor_v4_explorar.js"), "utf8");
const corte = base.indexOf("const sandbox = {");
if (corte < 0) throw new Error("cambió el montaje de test_visor_v4_explorar.js");
const propio = String.raw`
const R = "https://datos.example/web/actual/";
const pedidos = [];
const claveSitio = k => k.startsWith("../") ? k.slice(3) : "mapa/" + k;
const remoto = {}, ficheros = {};
for (const [k, v] of Object.entries(fixtures)) if (k !== "calendario.json") remoto[claveSitio(k)] = Buffer.from(JSON.stringify(v));
for (const [k, v] of Object.entries(bin)) remoto[claveSitio(k)] = v;
for (const [k, v] of Object.entries(remoto)) ficheros[k] = sha(v);
const indice = { version_formato: 1, comunes: { ficheros }, mapas: {} };
let manipular = null;
function servir(key) {
  if (key === "datos.json") return { ok: true, status: 200, json: async () => ({ actual: R + "actual.json" }) };
  if (key === R + "actual.json") return { ok: true, status: 200, json: async () => JSON.parse(JSON.stringify(indice)) };
  if (key === "calendario.json") return { ok: true, status: 200, json: async () => ({}) };
  if (typeof key === "string" && key.startsWith(R)) {
    const k = key.slice(R.length);
    if (!Object.hasOwn(remoto, k)) return { ok: false, status: 404 };
    let b = remoto[k];
    if (manipular && manipular.clave === k && manipular.veces > 0) { manipular.veces--; b = Buffer.from("manipulado"); }
    return { ok: true, status: 200, arrayBuffer: async () => ab(b) };
  }
  return { ok: false, status: 404 };
}
const sandbox = { document: doc, maplibregl: libre, console, location: { search: "" }, history: { replaceState() {} }, TextDecoder, crypto: crypto.webcrypto,
  getComputedStyle: () => ({ getPropertyValue: () => "" }), fetch: async key => { pedidos.push(key); return servir(key); } };
sandbox.window = sandbox; sandbox.globalThis = sandbox;
vm.runInNewContext(dvSource, sandbox, { filename: "dv.js" });
const marker = "  init();\n})();";
assert.ok(source.includes(marker), "cambió el arranque del Explorar");
vm.runInNewContext(source.replace(marker, "  globalThis.__T__={DVD};globalThis.__get__=getJson;\n  init();\n})();"), sandbox, { filename: "explorar.js", timeout: 10000 });
const flush = async () => { for (let i = 0; i < 60; i++) await new Promise(r => setImmediate(r)); };
(async () => {
  await flush();
  assert.equal(doc.body.dataset.ready, "1", "el mapa arranca con los datos remotos");
  assert.deepEqual(pedidos.filter(k => k.startsWith("../") || k.startsWith("datos/")), [], "ningún dato por ruta relativa");
  for (const k of ["v2/datos/provincias.json", "datos/INDEX.json", "mapa/datos/INDEX.json"]) assert.ok(pedidos.includes(R + k), k);
  assert.ok(pedidos.includes("calendario.json"), "el calendario es de la web: local");
  assert.ok(sandbox.__T__.DVD.indice, "índice de la doble vuelta leído desde el origen remoto");
  const ruta = "../datos/" + index.territorios[clave28].geojson.ruta, k = claveSitio(ruta);
  manipular = { clave: k, veces: 2 };
  let antes = pedidos.length;
  await assert.rejects(sandbox.__get__(ruta), /no coincide con el índice de datos/);
  assert.equal(pedidos.slice(antes).filter(x => x === R + "actual.json").length, 1, "recarga el índice una sola vez");
  manipular = { clave: k, veces: 1 };
  assert.equal((await sandbox.__get__(ruta)).type, "FeatureCollection", "tras recargar el índice, la huella casa");
  antes = pedidos.length;
  await assert.rejects(sandbox.__get__("../datos/no-existe.json"), /no está en el índice de datos/);
  assert.equal(pedidos.length, antes, "un dato fuera del índice no se pide");
})().catch(e => { console.error(e); process.exit(1); });
`;
vm.runInThisContext("(function(require,__dirname){" + base.slice(0, corte) + propio + "\n})", { filename: "test_visor_v4_explorar_actual.js" })(require, __dirname);
