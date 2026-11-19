/* Geometría del mapa V4: de GeoJSON WGS84 (T-409 #927) a rutas SVG. Sin dependencias; funciona en navegador y en Node.
   Proyección equirrectangular con la longitud escalada por cos(latitud media): suficiente para distritos de una provincia
   o de una comunidad; el mapa es un esquema de lectura, no cartografía de medida. */
(function (root) {
  "use strict";
  function anillos(g) {
    if (!g) return [];
    if (g.type === "Polygon") return g.coordinates;
    if (g.type === "MultiPolygon") return g.coordinates.reduce(function (a, p) { return a.concat(p); }, []);
    return [];
  }

  /* fc: FeatureCollection con properties.district_id. ancho: ancho del viewBox. Devuelve {ancho, alto, distritos:[{id, d}]}.
     Lanza si falta district_id o una geometría válida: nunca se pinta a medias. */
  function caminos(fc, ancho) {
    if (!fc || fc.type !== "FeatureCollection" || !fc.features || !fc.features.length) throw new Error("geometría: vacía");
    var minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity, vistos = {};
    fc.features.forEach(function (f) {
      var id = f.properties && f.properties.district_id;
      if (!(id >= 1) || id !== Math.floor(id)) throw new Error("geometría: district_id no válido");
      if (vistos[id]) throw new Error("geometría: district_id repetido " + id);
      vistos[id] = 1;
      var a = anillos(f.geometry);
      if (!a.length) throw new Error("geometría: distrito " + id + " sin polígono");
      a.forEach(function (r) { r.forEach(function (p) { if (p[0] < minx) minx = p[0]; if (p[0] > maxx) maxx = p[0]; if (p[1] < miny) miny = p[1]; if (p[1] > maxy) maxy = p[1]; }); });
    });
    var k = Math.cos(((miny + maxy) / 2) * Math.PI / 180), w = (maxx - minx) * k, h = maxy - miny, esc = ancho / (w || 1), alto = Math.max(1, Math.round(h * esc * 10) / 10);
    function r1(n) { return Math.round(n * 10) / 10; }
    return {
      ancho: ancho, alto: alto,
      distritos: fc.features.map(function (f) {
        var d = anillos(f.geometry).map(function (r) {
          return "M" + r.map(function (p) { return r1((p[0] - minx) * k * esc) + " " + r1((maxy - p[1]) * esc); }).join("L") + "Z";
        }).join("");
        return { id: f.properties.district_id, d: d };
      })
    };
  }

  var API = { caminos: caminos };
  if (typeof module !== "undefined" && module.exports) module.exports = API; else root.GEO = API;
})(typeof window !== "undefined" ? window : this);
