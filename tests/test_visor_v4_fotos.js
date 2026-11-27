// T-506 · 1.0.0 · 2026-11-26: galeria.js en el modo de Explorar (sinCreditos, soloProvincia) con el catálogo real, sin red.
const fs = require("fs"), path = require("path"), assert = require("assert");
const GAL = path.join(__dirname, "..", "visor", "v2", "galeria");
const cat = JSON.parse(fs.readFileSync(path.join(GAL, "catalogo.json"), "utf8"));
function nodo(tag) {
  return { tag, children: [], textContent: "", className: "", hidden: false,
    append(...c) { this.children.push(...c); }, replaceChildren(...c) { this.children = c; },
    addEventListener() {}, set href(v) { this._h = v; } };
}
function texto(n) { return (n.textContent || "") + (n.children || []).map(c => typeof c === "string" ? c : c.nodeValue != null ? c.nodeValue : texto(c)).join(""); }
function buscar(n, f, out = []) { if (f(n)) out.push(n); (n.children || []).forEach(c => c && c.tag && buscar(c, f, out)); return out; }
const cont = nodo("div"), cab = nodo("h2"), raiz = nodo("section");
raiz.querySelector = s => (s === ".gallery-heading" ? cab : cont);
global.document = { currentScript: { src: "http://x/v2/galeria/galeria.js" }, getElementById: () => raiz,
  createElement: nodo, createTextNode: t => ({ nodeValue: t }) };
global.window = {};
global.fetch = async () => ({ ok: true, json: async () => cat });
eval(fs.readFileSync(path.join(GAL, "galeria.js"), "utf8"));
const OP = { sinCreditos: true, soloProvincia: true };
(async () => {
  assert.strictEqual(Object.keys(cat.territorios).filter(k => k.startsWith("provincia:")).length, 52);
  for (let i = 1; i <= 52; i++) {
    const cod = String(i).padStart(2, "0");
    window.DDDGaleria.render("provincia", { cod, nombre: "P" + cod }, null, OP);
    await new Promise(r => setTimeout(r, 0));
    const img = buscar(cont, n => n.tag === "img")[0];
    assert(img, "sin foto en " + cod);
    const rel = img.src.split("/v2/galeria/")[1];
    assert(fs.existsSync(path.join(GAL, rel)), "no existe " + rel);
    const t = texto(cont), im = cat.imagenes.find(x => x.id === cat.territorios["provincia:" + cod]);
    assert(!t.includes(im.autor) && !/CC|Foto:|licencia|Modificada/i.test(t), "créditos en el panel " + cod);
    assert(buscar(cont, n => n.tag === "a").length === 0, "enlace en el panel " + cod);
  }
  window.DDDGaleria.render("comunidad", { cod: "01", nombre: "X" }, null, OP);
  assert.strictEqual(raiz.hidden, true);
  // sin opciones (V3) el pie de créditos sigue
  window.DDDGaleria.render("provincia", { cod: "01", nombre: "Álava" }, null);
  await new Promise(r => setTimeout(r, 0));
  assert(/Foto:/.test(texto(cont)));
  console.log("ok test_visor_v4_fotos.js");
})().catch(e => { console.error(e); process.exit(1); });
