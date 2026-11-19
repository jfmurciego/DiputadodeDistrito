/* Mapa V4 (T-413 / T-415): pinta lo que publica P40 en datos/ (T-409 #927). No calcula ganadores: lee los CSV y la geometría,
   verifica su sha256 contra datos/INDEX.json y, si no casa, no muestra la regla. */
(function () {
  "use strict";
  var $ = function (i) { return document.getElementById(i); }, enlace = DV.leerEnlace(location.search);
  var regla = enlace.regla, sel = "", indice = null, terr = enlace.territorio, datos = null, geo = null, ejemplo = false;
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function pedir(u) { return fetch(u, { cache: "no-cache" }).then(function (r) { if (!r.ok) throw new Error(u + " " + r.status); return r.arrayBuffer(); }); }
  function texto(b) { return new TextDecoder("utf-8").decode(b); }
  function huella(b) {
    if (!(window.crypto && crypto.subtle)) return Promise.reject(new Error("sin verificación de huella"));
    return crypto.subtle.digest("SHA-256", b).then(function (h) { return Array.prototype.map.call(new Uint8Array(h), function (x) { return ("0" + x.toString(16)).slice(-2); }).join(""); });
  }
  function verificado(ruta, sha) { return pedir("datos/" + ruta).then(function (b) { return huella(b).then(function (h) { if (h !== sha) throw new Error("la huella de " + ruta + " no coincide"); return b; }); }); }
  function estado(t) { $("estado").textContent = t || ""; }
  function esquema() { return DV.REGLAS.filter(function (r) { return r.id === regla; })[0]; }
  function url() {
    var u = "?" + (terr ? "territorio=" + encodeURIComponent(terr) + "&" : "") + "regla=" + regla;
    try { history.replaceState(null, "", u); } catch (e) { /* sin historial: la página sigue funcionando */ }
  }

  function pintarReglas() {
    $("reglas").innerHTML = DV.REGLAS.map(function (r) {
      return '<button type="button" data-r="' + r.id + '" aria-pressed="' + (r.id === regla) + '"' + (datos ? "" : ' disabled title="Aún no calculada en este territorio"') + ">" + r.texto + "</button>";
    }).join("");
    $("ayuda").textContent = esquema().ayuda;
    Array.prototype.forEach.call($("reglas").querySelectorAll("button"), function (b) { b.onclick = function () { regla = b.dataset.r; pintar(); url(); }; });
  }
  function clase(f) {
    if (!f) return "sin";
    var seg = String(f.vuelta_decisiva) === "2", margen = seg ? Math.abs(+f.votos_a_2v - +f.votos_b_2v) / (+f.votos_a_2v + +f.votos_b_2v) : 1;
    return DV.claseBloque(f.bloque_ganador) + (margen < 0.05 ? " claro" : "") + (f.empate === "true" ? " empate" : "");
  }
  function etiqueta(id, f) { return "Distrito " + id + (f ? ": gana " + DV.ficha(id, regla, datos).ganador : ": sin dato"); }
  function elegir(id) { sel = String(id); pintar(); var h = $("ficha"); if (!h.hidden) h.scrollIntoView({ block: "nearest" }); }

  function pintar() {
    pintarReglas();
    var e = esquema().esc, ids = datos ? Object.keys(datos.porDistrito).sort(function (a, b) { return a - b; }) : [];
    var sv = $("mapa"), nom = indice && terr ? (indice.territorios.filter(function (t) { return t.id === terr; })[0] || {}).nombre : "";
    $("titulo-mapa").textContent = datos ? (nom ? nom + " · " : "") + esquema().texto : "";
    if (datos && geo) {
      sv.setAttribute("viewBox", "0 0 " + geo.ancho + " " + geo.alto);
      sv.hidden = false;
      sv.innerHTML = geo.distritos.map(function (d) {
        var f = datos.porDistrito[d.id] && datos.porDistrito[d.id][e];
        return '<path class="p ' + clase(f) + '" d="' + d.d + '" data-id="' + d.id + '" tabindex="0" role="button" aria-pressed="' + (String(d.id) === sel) + '" aria-label="' + esc(etiqueta(d.id, f)) + '"></path>';
      }).join("");
      Array.prototype.forEach.call(sv.querySelectorAll("path[data-id]"), function (p) {
        p.onclick = function () { elegir(p.dataset.id); };
        p.onkeydown = function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); elegir(p.dataset.id); } };
      });
    } else { sv.hidden = true; sv.innerHTML = ""; }
    $("rejilla").innerHTML = ids.map(function (id) {
      var f = datos.porDistrito[id][e];
      if (!f) return '<button class="d sin" type="button" disabled>' + esc(id) + "<small>sin dato</small></button>";
      return '<button type="button" class="d ' + clase(f) + '" data-id="' + esc(id) + '" aria-pressed="' + (id === sel) + '" aria-label="' + esc(etiqueta(id, f)) + '">' + esc(id) + "<small>" + esc(DV.ficha(id, regla, datos).ganador) + "</small></button>";
    }).join("");
    Array.prototype.forEach.call($("rejilla").querySelectorAll("button[data-id]"), function (b) { b.onclick = function () { elegir(b.dataset.id); }; });
    fichaPintar();
  }
  function fichaPintar() {
    var el = $("ficha"), f = sel && datos ? DV.ficha(sel, regla, datos) : null;
    if (!f) { el.hidden = true; return; }
    el.hidden = false;
    var h = "<h2>Distrito " + esc(f.distrito) + " · " + esc(f.regla) + "</h2><p>" + esc(f.titular) + "</p><h3>1.ª vuelta</h3><p class='mu'>" + esc(f.nota1) + "</p><table><tr><th>Candidatura</th><th class='n'>Votos</th><th class='n'>%</th></tr>" +
      f.primera.map(function (c) { return "<tr><td><span class='sw " + DV.claseBloque(c.bloque) + "'></span>" + esc(c.nombre) + (c.partidos.length > 1 ? " <span class='mu'>(" + c.partidos.map(function (p) { return esc(p.partido) + " " + p.votos; }).join(" + ") + ")</span>" : "") + "</td><td class='n'>" + c.texto + "</td><td class='n'>" + c.pct + "</td></tr>"; }).join("") + "</table>";
    if (f.segunda) {
      h += "<h3>Finalistas</h3><p>" + f.finalistas.map(esc).join(" y ") + "</p>";
      h += f.transferencias ? "<h3>Transferencias</h3><table>" + f.transferencias.map(function (t) { return "<tr><td>" + esc(t.de) + "</td><td>" + (t.a ? "→ " + esc(t.a) : "→ abstención (" + esc(t.motivo) + ")") + "</td><td class='n'>" + t.votos + "</td></tr>"; }).join("") + "</table>" : "<p class='mu'>Cuadro de transferencias no disponible para este distrito.</p>";
      h += "<h3>2.ª vuelta</h3><p>" + esc(f.segunda.a.nombre) + " " + f.segunda.a.votos + " · " + esc(f.segunda.b.nombre) + " " + f.segunda.b.votos + " · abstención " + f.segunda.abstencion + "</p>";
    }
    if (f.avisoEmpate) h += "<div class='aviso'>" + esc(f.avisoEmpate) + "</div>";
    h += "<h3>Con otra regla</h3><p class='comp'>" + DV.comparacion(sel, datos).map(function (c) {
      return "<button type='button' class='chip' data-r='" + c.id + "' aria-pressed='" + (c.id === regla) + "'><span class='sw " + DV.claseBloque(c.bloque) + "'></span>" + esc(c.texto) + " → " + esc(c.ganador) + "</button>";
    }).join(" ") + "</p>";
    el.innerHTML = h + "<p class='mu'>Simulación sin valor oficial.</p>";
    Array.prototype.forEach.call(el.querySelectorAll(".chip"), function (b) { b.onclick = function () { regla = b.dataset.r; pintar(); url(); }; });
  }

  function sinDatos(msg) { datos = null; geo = null; if (regla !== "primero") regla = "primero"; estado(msg); pintar(); }
  function cargarTerritorio(id) {
    terr = id; sel = ""; datos = null; geo = null; estado("Cargando…"); pintar();
    var t = indice.territorios.filter(function (x) { return x.id === id; })[0];
    if (!t) return sinDatos("Territorio no disponible.");
    Promise.all([verificado(t.resultados.ruta, t.resultados.sha256), verificado(t.detalle.ruta, t.detalle.sha256), verificado(t.geometria.ruta, t.geometria.sha256)]).then(function (b) {
      var d = DV.cargar(texto(b[0]), texto(b[1])), g = GEO.caminos(JSON.parse(texto(b[2])), 800);
      g.distritos.forEach(function (x) { if (!d.porDistrito[x.id]) throw new Error("distrito " + x.id + " sin datos"); });
      datos = d; geo = g; estado(""); pintar(); url();
    }).catch(function (e) { sinDatos("No se muestra este territorio: " + e.message + "."); });
  }
  function arrancar() {
    pedir("datos/INDEX.json").then(function (b) { indice = DV.leerIndice(texto(b)); }).then(function () {
      var s = $("territorio");
      s.innerHTML = indice.territorios.map(function (t) { return '<option value="' + esc(t.id) + '">' + esc(t.nombre) + "</option>"; }).join("");
      s.disabled = false;
      if (!indice.territorios.some(function (t) { return t.id === terr; })) terr = indice.territorios[0].id;
      s.value = terr; s.onchange = function () { cargarTerritorio(s.value); };
      $("cobertura").textContent = "Reglas de doble vuelta disponibles en " + indice.territorios.length + " de 52 territorios del Congreso (primera tanda de la V4).";
      cargarTerritorio(terr);
    }).catch(function () {
      /* Sin datos publicados: en desarrollo local se usan los ejemplos ficticios; en el sitio público no existen y se avisa. */
      Promise.all([pedir("ejemplo/resultados_doble_vuelta.csv"), pedir("ejemplo/detalle.csv")]).then(function (b) { ejemplo = true; datos = DV.cargar(texto(b[0]), texto(b[1])); estado("Datos de ejemplo ficticios, sin valor oficial."); pintar(); })
        .catch(function () { sinDatos("Aún no hay datos de doble vuelta publicados."); });
    });
  }
  pintarReglas();
  arrancar();
})();
