/* PROYECTO: Diputado de Distrito
 * CLASE: visor V3, galería fotográfica territorial (T-325)
 * VERSIÓN: 1.0.0
 * FECHA: 2026-11-15
 * ESTADO: candidato
 * CAMBIOS: una fotografía por provincia y comunidad desde un catálogo estático (catalogo.json) con autor, licencia libre,
 * ficha de origen y sha256. Las imágenes se sirven desde el propio sitio; el visitante no llama a ningún tercero.
 * Todo texto del catálogo entra en la página con textContent (nunca innerHTML).
 * MOTIVO: rehacer la PR #792 sin XSS, sin llamadas a Wikipedia/Commons al visitar y con licencia comprobada.
 * ANTERIOR: ninguna (fichero nuevo)
 * Una foto de la capital o de un lugar representativo ilustra el territorio; NO es un distrito ni una sección. */
"use strict";
(function () {
  const SCRIPT = document.currentScript && document.currentScript.src ? document.currentScript.src : "";
  const BASE = SCRIPT ? SCRIPT.replace(/[^/]*$/, "") : "../v2/galeria/";
  // Enlaces permitidos: solo la ficha de Commons y la licencia Creative Commons; cualquier otro valor se muestra como texto.
  const ORIGEN_OK = /^https:\/\/commons\.wikimedia\.org\/wiki\/File:[^\s"'<>]+$/;
  const LICENCIA_OK = /^https:\/\/creativecommons\.org\/(licenses|publicdomain)\/[A-Za-z0-9\/.\-]+$/;
  const IMG_OK = /^img\/[a-z0-9\-]+\.webp$/;
  let catalogo = null, cargando = null, ticket = 0;

  function cargar() {
    if (catalogo) return Promise.resolve(catalogo);
    if (!cargando) {
      cargando = fetch(BASE + "catalogo.json", { credentials: "omit" })
        .then(r => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
        .then(c => { catalogo = c; return c; })
        .catch(e => { cargando = null; throw e; });
    }
    return cargando;
  }

  function el(tag, cls, text) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function enlace(href, ok, texto) {
    if (!ok.test(String(href || ""))) return el("span", null, texto);
    const a = el("a", null, texto);
    a.href = href; a.target = "_blank"; a.rel = "noopener noreferrer";
    return a;
  }
  function aviso(contenedor, texto) {
    contenedor.replaceChildren(el("p", "gallery-unavailable", texto));
  }

  // Clave del catálogo para la selección: provincia, comunidad; distrito y sección usan su provincia.
  function clave(kind, props, provincia) {
    if (kind === "provincia" && props && props.cod) return { k: "provincia:" + props.cod, nombre: props.nombre, ref: false };
    if (kind === "comunidad" && props && props.cod) return { k: "comunidad:" + props.cod, nombre: props.nombre, ref: false };
    if ((kind === "distrito" || kind === "seccion") && provincia && provincia.cod)
      return { k: "provincia:" + provincia.cod, nombre: provincia.nombre, ref: true };
    return null;
  }

  function figura(img, nombre, ref) {
    const fig = el("figure", "gallery-figure");
    const foto = el("img");
    foto.src = BASE + img.archivo;
    foto.alt = "Fotografía de " + nombre + ": " + img.descripcion;
    foto.width = img.ancho; foto.height = img.alto;
    foto.loading = "lazy"; foto.decoding = "async";
    fig.append(foto);
    const cap = el("figcaption");
    cap.append(el("strong", null, nombre));
    cap.append(el("span", null, (ref ? "Referencia provincial · " : "") + "Imagen ilustrativa: " + img.descripcion));
    const cred = el("small", "gallery-credit");
    cred.append(document.createTextNode("Foto: " + img.autor + " · "));
    cred.append(enlace(img.licencia_url, LICENCIA_OK, img.licencia));
    cred.append(document.createTextNode(" · "));
    cred.append(enlace(img.origen_url, ORIGEN_OK, "Ficha en Wikimedia Commons"));
    cap.append(cred);
    fig.append(cap);
    return { fig, foto };
  }

  function render(kind, props, provincia) {
    const raiz = document.getElementById("territory-gallery");
    if (!raiz) return;
    const mio = ++ticket;
    const cab = raiz.querySelector(".gallery-heading"), cont = raiz.querySelector(".gallery-content");
    const sel = clave(kind, props, provincia);
    if (!sel) { raiz.hidden = true; cont.replaceChildren(); return; }
    raiz.hidden = false;
    cab.textContent = sel.ref ? "Imagen de la provincia" : "Conoce el territorio";
    cargar().then(c => {
      if (mio !== ticket) return;
      const id = c.territorios && c.territorios[sel.k];
      const img = id && (c.imagenes || []).find(x => x.id === id);
      if (!img || !IMG_OK.test(img.archivo)) return aviso(cont, "Sin fotografía acreditada para " + sel.nombre + ".");
      const f = figura(img, sel.nombre, sel.ref);
      f.foto.addEventListener("error", () => { if (mio === ticket) aviso(cont, "Fotografía no disponible para " + sel.nombre + "."); }, { once: true });
      cont.replaceChildren(f.fig);
    }).catch(() => { if (mio === ticket) aviso(cont, "Galería no disponible."); });
  }

  window.DDDGaleria = { render };
})();
