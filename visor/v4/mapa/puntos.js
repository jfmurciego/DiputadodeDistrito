/* PROYECTO: Diputado de Distrito
 * CLASE: visor V4 · Explorar · situación actual, un punto por diputado (T-500, diseño T-499 1.0.1)
 * VERSIÓN: 1.1.0
 * FECHA: 2026-11-26
 * ESTADO: candidato
 * ANTERIOR: legacy/visor/v4/mapa/puntos_v1.0.0_20261125.js
 * CAMBIOS: 1.1.0 (T-500, 26-11): `giro`: el mapa va girado y los racimos, placas, rótulos y el marco de Canarias se calculan en el marco de la pantalla (filas horizontales);
 *   `recolocarCanarias` desplaza Canarias sin tocar el fichero de provincias.
 *   1.0.0: fichero nuevo (sin clases de intensidad: el color de la provincia es el de la capa «Partido más votado»).
 * MOTIVO: T-500. Funciones puras (sin DOM ni MapLibre): racimo compacto ordenado por partido
 *   en una malla hexagonal (con placa y línea guía donde no cabe), y recuadros de Ceuta y Melilla. Los escaños y votos salen de
 *   puntos_v5_2023.json (herramientas/datos_puntos_v5.py, BOE-A-2023-18907); aquí no se calcula ningún dato electoral. */
"use strict";
(function (root) {
  // Dos disposiciones, en píxeles de Mercator al zoom `zr`: la nacional (paso 11 px) y la de cerca (paso 14 px a zoom 6,6), para que
  // al acercar el racimo quepa dentro de la provincia y desaparezca la placa. `ZC` es el zoom en que se pasa de una a otra.
  const ZC = 6.6;
  const DISPOSICIONES = {n: {zr: 5.3, sp: 11, r: 4.1, desp: {"08": [52, 22]}}, c: {zr: ZC, sp: 14, r: 5.6, desp: {}}};
  const SIN_PLACA_NI_PUNTOS = ["51", "52"]; // Ceuta y Melilla: recuadro propio

  // Más votado de la provincia (por votos, no por escaños) y su % sobre votos a candidaturas.
  function ganador(prov) {
    const g = prov.partidos.reduce((a, b) => b.votos > a.votos ? b : a);
    return {p: g.p, pct: 100 * g.votos / prov.votos_candidaturas};
  }

  const merc = (lng, lat) => [(lng + 180) / 360, .5 - Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)) / (2 * Math.PI)];
  const inv = (x, y) => [x * 360 - 180, (2 * Math.atan(Math.exp((.5 - y) * 2 * Math.PI)) - Math.PI / 2) * 180 / Math.PI];
  const poligonos = g => g.type === "MultiPolygon" ? g.coordinates : [g.coordinates];
  function dentro(x, y, poly) {
    let r = false;
    for (const ring of poly) for (let i = 0; i < ring.length; i++) {
      const [x1, y1] = ring[i], [x2, y2] = ring[i ? i - 1 : ring.length - 1];
      if ((y1 > y) !== (y2 > y) && x < (x2 - x1) * (y - y1) / (y2 - y1) + x1) r = !r;
    }
    return r;
  }
  function dBorde(x, y, polys) {
    let m = Infinity;
    for (const poly of polys) for (const ring of poly) for (let i = 0; i < ring.length; i++) {
      const [x1, y1] = ring[i], [x2, y2] = ring[i ? i - 1 : ring.length - 1], dx = x2 - x1, dy = y2 - y1, L = dx * dx + dy * dy || 1e-9;
      const t = Math.max(0, Math.min(1, ((x - x1) * dx + (y - y1) * dy) / L));
      m = Math.min(m, Math.hypot(x - x1 - t * dx, y - y1 - t * dy));
    }
    return m;
  }
  // Malla hexagonal de paso `sp` anclada en (cx, cy), dentro del rectángulo dado.
  function malla(x0, x1, y0, y1, cx, cy, sp) {
    const pts = [], dy = sp * .866;
    for (let y = cy - Math.ceil((cy - y0) / dy) * dy; y <= y1; y += dy) {
      const off = Math.round((y - cy) / dy) % 2 ? sp / 2 : 0;
      for (let x = cx + off - Math.ceil((cx + off - x0) / sp) * sp; x <= x1; x += sp) pts.push([x, y]);
    }
    return pts;
  }
  const dist = (p, c) => Math.hypot(p[0] - c[0], p[1] - c[1]);

  // Racimo de una provincia en la disposición `cfg`: {pts, placa (¿desborda?), guia (línea al centro si va desplazado)}.
  function racimo(cod, polysPx, n, cfg) {
    const sp = cfg.sp, R = cfg.r, big = polysPx.reduce((a, b) => b[0].length > a[0].length ? b : a);
    const xs = big[0].map(p => p[0]), ys = big[0].map(p => p[1]);
    const media = a => a.reduce((s, v) => s + v, 0) / a.length;
    const c0 = [media(xs), media(ys)];
    const cand = malla(Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys), c0[0], c0[1], sp).filter(p => dentro(p[0], p[1], big));
    // Centro: el punto interior más alejado del borde (no el centroide, que en provincias cóncavas cae fuera).
    let c = c0, mejor = -1;
    for (const p of cand) {const d = dBorde(p[0], p[1], [big]); if (d > mejor) {mejor = d; c = p;}}
    const w = sp * 11;
    let pts, placa, guia = null;
    if (cfg.desp[cod]) {
      const a = [c[0] + cfg.desp[cod][0], c[1] + cfg.desp[cod][1]];
      pts = malla(a[0] - w, a[0] + w, a[1] - w, a[1] + w, a[0], a[1], sp).sort((p, q) => dist(p, a) - dist(q, a)).slice(0, n);
      placa = true; guia = [c, a];
    } else {
      const m = malla(c[0] - w, c[0] + w, c[1] - w, c[1] + w, c[0], c[1], sp);
      const ins = m.filter(p => polysPx.some(q => dentro(p[0], p[1], q)) && dBorde(p[0], p[1], polysPx) >= R * .55).sort((p, q) => dist(p, c) - dist(q, c));
      if (ins.length >= n) {pts = ins.slice(0, n); placa = false;}
      else {pts = m.sort((p, q) => dist(p, c) - dist(q, c)).slice(0, n); placa = true;}
    }
    pts.sort((p, q) => (Math.round(p[1] * 10) - Math.round(q[1] * 10)) || p[0] - q[0]); // por filas, de arriba abajo y de izquierda a derecha
    return {pts, placa, guia, centro: c};
  }

  /* Disposición completa. `prov`: FeatureCollection de provincias (visor/v2/datos/provincias.json, propiedad `cod`);
   * `datos`: puntos_v5_2023.json; `familia`: nombre de partido → clave de paleta; `lays`: disposiciones a calcular (todas si se omite).
   * Devuelve {puntos, placas, guias, etiquetas, marcoCanarias} en lng/lat; cada elemento lleva `lay` ("n" nacional, "c" de cerca). */
  function disponer(prov, datos, familia, lays, giro) {
    const b = (giro || 0) * Math.PI / 180, cb = Math.cos(b), sb = Math.sin(b);
    const rota = (x, y) => [x * cb + sb * y, -x * sb + cb * y], desrota = (x, y) => [x * cb - sb * y, x * sb + cb * y];  // marco de la pantalla ↔ Mercator
    const out = {puntos: [], placas: [], guias: [], etiquetas: [], marcoCanarias: null};
    for (const [lay, cfg] of Object.entries(DISPOSICIONES)) {
      if (lays && !lays.includes(lay)) continue;
      const S = 512 * Math.pow(2, cfg.zr), R = cfg.r;
      const aLngLat = p => { const q = desrota(p[0], p[1]); return inv(q[0] / S, q[1] / S); };
      for (const f of prov.features) {
        const cod = f.properties.cod, d = datos.provincias[cod];
        if (!d || SIN_PLACA_NI_PUNTOS.includes(cod)) continue;
        const polys = poligonos(f.geometry).map(poly => poly.map(ring => ring.map(([lng, lat]) => { const m = merc(lng, lat); return rota(m[0] * S, m[1] * S); })));
        const k = racimo(cod, polys, d.escanos, cfg);
        const seq = d.partidos.flatMap(x => Array(x.escanos).fill(x.p));
        k.pts.forEach((p, i) => { const [lng, lat] = aLngLat(p); out.puntos.push({lay, cod, nombre: d.nombre, p: familia(seq[i]), partido: seq[i], lng, lat}); });
        const xs = k.pts.map(p => p[0]), ys = k.pts.map(p => p[1]), m = R + 3;
        const x0 = Math.min(...xs) - m, x1 = Math.max(...xs) + m, y0 = Math.min(...ys) - m, y1 = Math.max(...ys) + m;
        if (k.placa) out.placas.push({lay, cod, anillo: [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]].map(aLngLat)});
        if (k.guia) out.guias.push({lay, cod, desde: aLngLat(k.guia[0]), hasta: aLngLat(k.guia[1])});
        if (lay === "n" && (d.escanos >= 12 || cfg.desp[cod])) {
          const [lng, lat] = aLngLat([(x0 + x1) / 2, y0 - 2]);
          out.etiquetas.push({cod, texto: d.nombre + " " + d.escanos, lng, lat});
        }
      }
    }
    // Marco de Canarias, horizontal en la pantalla: rectángulo del marco girado que contiene sus islas, con un pequeño margen (0,001 del mundo ≈ 0,35° de longitud).
    const can = prov.features.filter(f => ["35", "38"].includes(f.properties.cod));
    if (can.length) {
      const c = can.flatMap(f => poligonos(f.geometry).flatMap(p => p.flat())).map(([lng, lat]) => { const m = merc(lng, lat); return rota(m[0], m[1]); }), pad = .001;
      const lo = Math.min(...c.map(p => p[0])) - pad, hi = Math.max(...c.map(p => p[0])) + pad, la = Math.min(...c.map(p => p[1])) - pad, lb = Math.max(...c.map(p => p[1])) + pad;
      out.marcoCanarias = [[lo, la], [hi, la], [hi, lb], [lo, lb], [lo, la]].map(([x, y]) => { const q = desrota(x, y); return inv(q[0], q[1]); });  // esquinas: sup. izq., sup. der., inf. der., inf. izq.
    }
    return out;
  }

  // Copia de la colección con Canarias desplazada `desp` = [dx, dy] en unidades del mundo (0-1) medidas en el marco de la pantalla (mapa girado `giro` grados); no modifica `prov`.
  // Sin `desp`, se calcula para cualquier giro: el marco de Canarias (con su margen) queda con su borde izquierdo en el de la península y su borde superior justo bajo ella.
  // `esCanarias` por defecto son las provincias de Canarias; para comunidades, f => f.properties.nombre === "Canarias". `ref` (la colección de provincias) da la península.
  function recolocarCanarias(prov, giro, desp, esCanarias, ref) {
    esCanarias = esCanarias || (f => ["35", "38"].includes(f.properties.cod));
    const b = giro * Math.PI / 180, cb = Math.cos(b), sb = Math.sin(b), pad = .001, hueco = .0006;
    if (!desp) {
      const caja = (fc, si) => fc.features.filter(f => si(f)).flatMap(f => poligonos(f.geometry).flatMap(p => p.flat())).map(([lng, lat]) => { const m = merc(lng, lat); return [m[0] * cb + sb * m[1], -m[0] * sb + cb * m[1]]; })
        .reduce((a, p) => [Math.min(a[0], p[0]), Math.max(a[1], p[1]), Math.min(a[2], p[1])], [1e9, -1e9, 1e9]);
      const base = ref || prov, pen = caja(base, f => !["35", "38", "51", "52"].includes(f.properties.cod)), can = caja(base, f => ["35", "38"].includes(f.properties.cod));
      desp = [pen[0] - (can[0] - pad), pen[1] + hueco - (can[2] - pad)];
    }
    const dx = desp[0] * cb - sb * desp[1], dy = desp[0] * sb + cb * desp[1];
    const mover = ring => ring.map(([lng, lat]) => { const m = merc(lng, lat); return inv(m[0] + dx, m[1] + dy); });
    return {...prov, features: prov.features.map(f => !esCanarias(f) ? f : {...f, geometry: {...f.geometry,
      coordinates: f.geometry.type === "MultiPolygon" ? f.geometry.coordinates.map(poly => poly.map(mover)) : f.geometry.coordinates.map(mover)}})};
  }

  // Recuadro de Ceuta o Melilla: su contorno ampliado ×8 (en píxeles de la disposición nacional) como camino SVG de 92 × 74.
  function recuadro(f) {
    const S = 512 * Math.pow(2, DISPOSICIONES.n.zr), ring = poligonos(f.geometry)[0][0].map(([lng, lat]) => { const m = merc(lng, lat); return [m[0] * S, m[1] * S]; });
    const mx = ring.reduce((s, p) => s + p[0], 0) / ring.length, my = ring.reduce((s, p) => s + p[1], 0) / ring.length;
    return "M" + ring.map(p => (46 + (p[0] - mx) * 8).toFixed(1) + "," + (40 + (p[1] - my) * 8).toFixed(1)).join("L") + "Z";
  }

  // Totales estatales por partido (votos y escaños) y votos que no fueron a partidos con escaño, a partir del JSON.
  function totales(datos) {
    const t = {};
    for (const d of Object.values(datos.provincias)) for (const x of d.partidos) {const a = t[x.p] || (t[x.p] = {p: x.p, votos: 0, escanos: 0}); a.votos += x.votos; a.escanos += x.escanos;}
    const lista = Object.values(t).sort((a, b) => b.escanos - a.escanos || b.votos - a.votos);
    const resto = datos.votos_candidaturas_estatal - lista.reduce((s, x) => s + x.votos, 0);
    return {lista, resto, estatal: datos.votos_candidaturas_estatal, escanos: lista.reduce((s, x) => s + x.escanos, 0)};
  }

  root.PUNTOS = {ZC, DISPOSICIONES, ganador, disponer, recolocarCanarias, recuadro, totales};
  if (typeof module !== "undefined" && module.exports) module.exports = root.PUNTOS;
})(typeof window !== "undefined" ? window : globalThis);
