/* PROYECTO: Diputado de Distrito
 * CLASE: prueba de comportamiento de la galería territorial V3 (T-325)
 * VERSIÓN: 1.0.0 · FECHA: 2026-11-15 · ESTADO: candidato
 * ANTERIOR: ninguna (fichero nuevo)
 * CAMBIOS: ejecuta visor/v2/galeria/galeria.js con un DOM simulado y el catálogo real; comprueba que el texto externo no se interpreta
 * como HTML, que solo se pide el catálogo del propio sitio, la selección por territorio, las carreras y los fallos. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ROOT = path.resolve(__dirname, "..");
const SRC = fs.readFileSync(path.join(ROOT, "visor/v2/galeria/galeria.js"), "utf8");
const CAT = JSON.parse(fs.readFileSync(path.join(ROOT, "visor/v2/galeria/catalogo.json"), "utf8"));
const BASE = "https://sitio.test/v2/galeria/";

class Nodo {
  constructor(tag) { this.tag = tag; this.hijos = []; this.attrs = {}; this.listeners = {}; this.hidden = false; this._t = ""; this.className = ""; }
  set innerHTML(_) { throw new Error("innerHTML prohibido"); }
  get textContent() { return this._t + this.hijos.map(h => h.textContent).join(""); }
  set textContent(v) { this._t = String(v); this.hijos = []; }
  append(...n) { n.forEach(x => this.hijos.push(x)); }
  replaceChildren(...n) { this.hijos = n; this._t = ""; }
  addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); }
  querySelector(sel) { return this.buscar(h => ("." + h.className.split(" ").join(".")).includes(sel)); }
  buscar(f) { for (const h of this.hijos) { if (f(h)) return h; const r = h.buscar && h.buscar(f); if (r) return r; } return null; }
  todos(tag) { const r = []; (function rec(n) { n.hijos.forEach(h => { if (h.tag === tag) r.push(h); rec(h); }); })(this); return r; }
}

function entorno(catalogo, opciones = {}) {
  const raiz = new Nodo("section"); raiz.hidden = true;
  const cab = new Nodo("h2"); cab.className = "gallery-heading";
  const cont = new Nodo("div"); cont.className = "gallery-content";
  raiz.hijos.push(cab, cont);
  const peticiones = [];
  const document = {
    currentScript: { src: BASE + "galeria.js" },
    getElementById: id => id === "territory-gallery" ? raiz : null,
    createElement: t => new Nodo(t),
    createTextNode: t => { const n = new Nodo("#texto"); n._t = String(t); return n; },
  };
  const fetch = async url => {
    peticiones.push(url);
    if (opciones.falla) throw new Error("red");
    return { ok: true, json: async () => catalogo };
  };
  const win = {};
  vm.runInNewContext(SRC, { window: win, document, fetch, URL, Promise }, { filename: "galeria.js" });
  return { G: win.DDDGaleria, raiz, cab, cont, peticiones };
}
const esperar = () => new Promise(r => setImmediate(r));
const prov = (cod, nombre) => ({ cod, nombre });

(async () => {
  // 1. Provincia: imagen del sitio, alt, atribución y enlaces del catálogo.
  {
    const e = entorno(CAT);
    e.G.render("provincia", prov("28", "Madrid"), null);
    await esperar();
    assert.equal(e.raiz.hidden, false);
    assert.equal(e.cab.textContent, "Conoce el territorio");
    const img = e.cont.todos("img")[0];
    const ficha = CAT.imagenes.find(i => i.id === CAT.territorios["provincia:28"]);
    assert.equal(img.src, BASE + ficha.archivo);
    assert.ok(img.src.startsWith(BASE), "imagen del propio sitio");
    assert.match(img.alt, /^Fotografía de Madrid: /);
    const pie = e.cont.textContent;
    assert.ok(pie.includes(ficha.autor) && pie.includes(ficha.licencia) && pie.includes("Wikimedia Commons"), "atribución visible");
    const hrefs = e.cont.todos("a").map(a => a.href);
    assert.deepEqual(hrefs.sort(), [ficha.licencia_url, ficha.origen_url].sort());
    e.cont.todos("a").forEach(a => assert.equal(a.rel, "noopener noreferrer"));
    // Solo se pidió el catálogo del sitio: nada de Wikipedia, Commons ni Wikidata.
    assert.deepEqual(e.peticiones, [BASE + "catalogo.json"]);
  }
  // 1b. Pie de atribución: cambios indicados siempre y «compartir igual» solo en BY-SA (CC BY y CC BY-SA exigen indicar los cambios).
  {
    const e = entorno(CAT);
    const casos = { "prov-28": null, "prov-24": "retocada", "prov-21": "recortada" };
    for (const [id, extra] of Object.entries(casos)) {
      const cod = id.split("-")[1];
      e.G.render("provincia", prov(cod, "T" + cod), null);
      await esperar();
      const ficha = CAT.imagenes.find(i => i.id === id);
      const t = e.cont.textContent;
      assert.ok(t.includes("Modificada: recomprimida (WebP), reescalada a 800 px de ancho"), id + ": cambios en el pie");
      if (extra) assert.ok(t.includes(extra), id + ": " + extra);
      assert.equal(t.includes("Compartir igual (CC BY-SA)"), ficha.licencia.includes("BY-SA"), id + ": compartir igual solo en BY-SA");
    }
    const bysa = CAT.imagenes.find(i => i.licencia.startsWith("CC BY-SA")), noSa = CAT.imagenes.find(i => !i.licencia.includes("BY-SA"));
    for (const f of [bysa, noSa]) {
      const k = Object.keys(CAT.territorios).find(k => CAT.territorios[k] === f.id).split(":");
      e.G.render(k[0], prov(k[1], "T"), null);
      await esperar();
      assert.equal(e.cont.textContent.includes("Compartir igual (CC BY-SA)"), f.licencia.includes("BY-SA"), f.id);
    }
    // Un catálogo sin campo de cambios sigue declarando la modificación.
    const sinC = JSON.parse(JSON.stringify(CAT)); delete sinC.imagenes[0].cambios;
    const e2 = entorno(sinC); e2.G.render("provincia", prov("01", "Álava"), null); await esperar();
    assert.ok(e2.cont.textContent.includes("Modificada:"));
  }
  // 2. Todas las provincias y comunidades del catálogo se resuelven con su imagen.
  {
    const e = entorno(CAT);
    for (const [k, id] of Object.entries(CAT.territorios)) {
      const [tipo, cod] = k.split(":");
      e.G.render(tipo, prov(cod, "T" + cod), null);
      await esperar();
      const ficha = CAT.imagenes.find(i => i.id === id);
      assert.equal(e.cont.todos("img")[0].src, BASE + ficha.archivo, k);
    }
    assert.equal(e.peticiones.length, 1, "el catálogo se pide una sola vez");
  }
  // 3. Distrito y sección usan la imagen de su provincia, señalada como referencia; el país oculta la galería.
  {
    const e = entorno(CAT);
    e.G.render("distrito", { distrito: "28-01" }, prov("08", "Barcelona"));
    await esperar();
    assert.equal(e.cab.textContent, "Imagen de la provincia");
    assert.ok(e.cont.textContent.includes("Referencia provincial"));
    assert.equal(e.cont.todos("img")[0].src, BASE + "img/prov-08.webp");
    e.G.render("seccion", { s: "0801" }, prov("08", "Barcelona"));
    await esperar();
    assert.equal(e.cont.todos("img")[0].src, BASE + "img/prov-08.webp");
    e.G.render("pais", {}, null);
    await esperar();
    assert.equal(e.raiz.hidden, true);
    assert.equal(e.cont.hijos.length, 0);
  }
  // 4. XSS: autor, descripción, licencia y enlaces hostiles se muestran como texto o se descartan; nunca se crea HTML.
  {
    const mal = JSON.parse(JSON.stringify(CAT));
    const f = mal.imagenes[0];
    f.autor = "<img src=x onerror=alert(1)>";
    f.descripcion = "</figcaption><script>alert(2)</script>";
    f.licencia = "<b>CC</b>";
    f.licencia_url = "javascript:alert(3)";
    f.origen_url = "https://evil.example/wiki/File:X.jpg";
    const e = entorno(mal); // innerHTML lanza: si el código lo usara, fallaría
    e.G.render("provincia", prov("01", "Álava"), null);
    await esperar();
    const t = e.cont.textContent;
    assert.ok(t.includes("<img src=x onerror=alert(1)>"), "el autor sale como texto literal");
    assert.ok(t.includes("<script>alert(2)</script>"));
    assert.equal(e.cont.todos("img").length, 1, "solo la fotografía: el autor no crea elementos");
    assert.equal(e.cont.todos("script").length, 0);
    assert.equal(e.cont.todos("a").length, 0, "enlaces no permitidos se muestran como texto");
    // Ruta de imagen fuera de img/*.webp: se rechaza.
    const mal2 = JSON.parse(JSON.stringify(CAT));
    mal2.imagenes[0].archivo = "https://upload.wikimedia.org/x.webp";
    const e2 = entorno(mal2);
    e2.G.render("provincia", prov("01", "Álava"), null);
    await esperar();
    assert.equal(e2.cont.todos("img").length, 0);
    assert.match(e2.cont.textContent, /Sin fotografía acreditada para Álava/);
  }
  // 5. Carrera: gana la última selección.
  {
    const e = entorno(CAT);
    e.G.render("provincia", prov("01", "Álava"), null);
    e.G.render("provincia", prov("28", "Madrid"), null);
    await esperar();
    assert.equal(e.cont.todos("img")[0].src, BASE + "img/prov-28.webp");
    assert.equal(e.cont.todos("img").length, 1);
  }
  // 6. Fallos: imagen que no carga y catálogo inaccesible.
  {
    const e = entorno(CAT);
    e.G.render("provincia", prov("28", "Madrid"), null);
    await esperar();
    e.cont.todos("img")[0].listeners.error[0]();
    assert.match(e.cont.textContent, /Fotografía no disponible para Madrid/);
    const e2 = entorno(CAT, { falla: true });
    e2.G.render("provincia", prov("28", "Madrid"), null);
    await esperar();
    assert.match(e2.cont.textContent, /Galería no disponible/);
  }
  // 7. Territorio sin entrada en el catálogo.
  {
    const e = entorno(CAT);
    e.G.render("provincia", prov("99", "Inexistente"), null);
    await esperar();
    assert.match(e.cont.textContent, /Sin fotografía acreditada para Inexistente/);
  }
  console.log("Galería territorial V3: PASS (catálogo real, escape, sin red externa, selección, carreras, fallos)");
})().catch(e => { console.error(e); process.exit(1); });
