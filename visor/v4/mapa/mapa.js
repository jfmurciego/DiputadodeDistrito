/* Mapa V4 (T-413): página de ejemplo. Pinta lo que lee DV; no calcula ganadores. */
(function () {
  "use strict";
  var $ = function (i) { return document.getElementById(i); }, enlace = DV.leerEnlace(location.search), regla = enlace.regla, datos = null, sel = enlace.territorio;
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function pedir(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u + " " + r.status); return r.text(); }); }
  function pintarReglas() {
    $("reglas").innerHTML = DV.REGLAS.map(function (r) {
      var off = !datos && r.id !== "primero";
      return '<button type="button" data-r="' + r.id + '" aria-pressed="' + (r.id === regla) + '"' + (off ? ' disabled title="Aún no calculada en este territorio"' : "") + ">" + r.texto + "</button>";
    }).join("");
    $("ayuda").textContent = DV.REGLAS.filter(function (r) { return r.id === regla; })[0].ayuda;
    Array.prototype.forEach.call($("reglas").querySelectorAll("button"), function (b) { b.onclick = function () { regla = b.dataset.r; pintar(); }; });
  }
  function pintar() {
    pintarReglas();
    var ids = datos ? Object.keys(datos.porDistrito) : [], esc_ = DV.REGLAS.filter(function (r) { return r.id === regla; })[0].esc;
    $("rejilla").innerHTML = ids.map(function (id) {
      var f = datos.porDistrito[id][esc_];
      if (!f) return '<button class="d sin" type="button" disabled>' + esc(id) + "<small>sin dato</small></button>";
      var seg = String(f.vuelta_decisiva) === "2", margen = seg ? Math.abs(+f.votos_a_2v - +f.votos_b_2v) / (+f.votos_a_2v + +f.votos_b_2v) : 1;
      return '<button type="button" class="d ' + DV.claseBloque(f.bloque_ganador) + (margen < 0.05 ? " claro" : "") + (f.empate === "true" ? " empate" : "") + '" data-id="' + esc(id) + '" aria-pressed="' + (id === sel) + '" aria-label="Distrito ' + esc(id) + ", gana " + esc(f.bloque_ganador || "sin bloque") + '">' + esc(id) + "<small>" + esc(f.bloque_ganador || "sin bloque") + "</small></button>";
    }).join("");
    Array.prototype.forEach.call($("rejilla").querySelectorAll("button[data-id]"), function (b) { b.onclick = function () { sel = b.dataset.id; pintar(); }; });
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
    el.innerHTML = h + "<p class='mu'>Simulación sin valor oficial.</p>";
  }
  Promise.all([pedir("ejemplo/resultados_doble_vuelta.csv"), pedir("ejemplo/detalle.csv")]).then(function (t) { datos = DV.cargar(t[0], t[1]); pintar(); }).catch(function () { datos = null; regla = "primero"; pintar(); $("ayuda").textContent = "No se pudieron cargar los datos de ejemplo."; });
  pintarReglas();
})();
