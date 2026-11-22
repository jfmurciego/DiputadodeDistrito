/* PROYECTO: Diputado de Distrito · CLASE: prueba del vídeo de la portada V4 (T-423)
 * VERSIÓN: 1.0.0 · FECHA: 2026-11-19 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
 * CAMBIOS: el reproductor se ve desplegado sin pulsar nada (controles, primer fotograma o póster), sin reproducción automática ni sonido. */
"use strict";
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path"), vm = require("node:vm");
const src = fs.readFileSync(path.join(__dirname, "../visor/v4/app.js"), "utf8");
function nodo(tag) { return { tag, children: [], attrs: {}, textContent: "", appendChild(c) { this.children.push(c); return c; }, setAttribute(k, v) { this.attrs[k] = v; },
  addEventListener() {}, querySelector() { return null; }, querySelectorAll() { return []; }, classList: { add() {}, toggle() {}, remove() {}, contains() { return false; } } }; }
async function correr(cfg) {
  const cuerpo = nodo("div"), sec = { hidden: true, querySelector: q => (q === "[data-video-cuerpo]" ? cuerpo : null) };
  const document = { readyState: "complete", documentElement: nodo("html"), createElement: nodo, addEventListener() {},
    querySelector: q => (q === "[data-video]" ? sec : null), querySelectorAll: () => [] };
  const ctx = { document, window: {}, AbortController, console, fetch: async u => ({ ok: u === "video.json", json: async () => cfg }) };
  ctx.window = ctx; ctx.document.defaultView = ctx;
  vm.runInNewContext(src, ctx);
  for (let i = 0; i < 10; i++) await new Promise(r => setImmediate(r));
  return { sec, cuerpo };
}
(async () => {
  // 1. Sin póster: reproductor visible al cargar, con controles y el primer fotograma; sin autoplay, sin botón previo.
  let { sec, cuerpo } = await correr({ base: "https://media.diputadodedistrito.es/", video: "Video_DDD.mp4", poster: "", subtitulos: "", transcripcion: "" });
  assert.equal(sec.hidden, false, "el bloque del vídeo se ve sin pulsar nada");
  const v = cuerpo.children[0];
  assert.equal(v.tag, "video", "lo primero es el reproductor, no un botón");
  assert.equal(v.controls, true); assert.equal(v.preload, "none");  // T-442: nada se descarga hasta pulsar play assert.equal(v.playsInline, true);
  assert.equal(v.src, "https://media.diputadodedistrito.es/Video_DDD.mp4#t=0.1", "primer fotograma visible");
  assert.ok(!v.autoplay && !("autoplay" in v.attrs), "sin reproducción automática");
  assert.ok(!cuerpo.children.some(c => c.tag === "button"), "sin botón «Ver el vídeo»");
  // 2. Con póster: lo usa y no añade el fragmento de tiempo.
  ({ cuerpo } = await correr({ base: "https://media.diputadodedistrito.es", video: "/v.mp4", poster: "p.webp", subtitulos: "", transcripcion: "" }));
  assert.equal(cuerpo.children[0].poster, "https://media.diputadodedistrito.es/p.webp");
  assert.equal(cuerpo.children[0].src, "https://media.diputadodedistrito.es/v.mp4");
  // 3. Sin vídeo configurado o con URL no https: el bloque sigue oculto.
  ({ sec } = await correr({ base: "https://media.diputadodedistrito.es/", video: "", poster: "", subtitulos: "", transcripcion: "" }));
  assert.equal(sec.hidden, true);
  ({ sec } = await correr({ base: "http://x.es/", video: "v.mp4", poster: "", subtitulos: "", transcripcion: "" }));
  assert.equal(sec.hidden, true);
  console.log("OK vídeo de la portada V4 desplegado");
})().catch(e => { console.error(e); process.exitCode = 1; });
