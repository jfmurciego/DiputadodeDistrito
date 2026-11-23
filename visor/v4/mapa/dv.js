/* Doble vuelta en el visor V4 (T-413): lectura y presentación de lo que genera herramientas/doble_vuelta.py.
   T-427: el índice 1.1 añade los aut (autonómica vigente; `clave_visor`, sin geometría) y `sin_doble_vuelta` con su motivo; el 1.0 sigue valiendo.
   El visor NO decide ganadores: solo lee resultados_doble_vuelta.csv y detalle.csv. Sin dependencias; funciona en navegador y en Node. */
(function (root) {
  "use strict";
  var REGLAS = [
    { id: "tres", esc: "dv_A", texto: "Tres bloques", ayuda: "Izquierdas, Nacionalistas y Patriotas se presentan cada uno como una sola candidatura." },
    { id: "dos", esc: "dv_B", texto: "Dos bloques", ayuda: "Solo Izquierdas y Patriotas se presentan juntos; los nacionalistas, partido a partido." },
    { id: "base", esc: "dv_base", texto: "Sin coaliciones", ayuda: "Cada partido se presenta por separado." },
    { id: "primero", esc: "primero", texto: "Mayoría simple en el distrito", ayuda: "Gana el partido con más votos en el distrito, sin segunda vuelta. No es el sistema actual: hoy los escaños se reparten de forma proporcional por listas provinciales." }
  ];
  var COLUMNAS = ["district_id", "escenario", "vuelta_decisiva", "candidatura_ganadora", "bloque_ganador", "votos_1v", "cuota_1v",
    "finalista_a", "finalista_b", "votos_a_2v", "votos_b_2v", "cuota_ganador_2v", "votos_abstencion", "empate"];
  var COLUMNAS_DETALLE = ["district_id", "escenario", "candidatura", "partido", "bloque", "votos_1v", "votos_candidatura"];

  function parseCSV(texto) {
    var filas = [], f = [], c = "", q = false, i, ch;
    texto = String(texto).replace(/^﻿/, "");
    for (i = 0; i < texto.length; i++) {
      ch = texto[i];
      if (q) { if (ch === '"') { if (texto[i + 1] === '"') { c += '"'; i++; } else q = false; } else c += ch; }
      else if (ch === '"') q = true;
      else if (ch === ",") { f.push(c); c = ""; }
      else if (ch === "\n" || ch === "\r") { if (ch === "\r" && texto[i + 1] === "\n") i++; f.push(c); c = ""; if (f.length > 1 || f[0] !== "") filas.push(f); f = []; }
      else c += ch;
    }
    if (c !== "" || f.length) { f.push(c); filas.push(f); }
    if (!filas.length) return [];
    var cab = filas[0];
    return filas.slice(1).map(function (r) { var o = {}; cab.forEach(function (k, j) { o[k] = r[j] === undefined ? "" : r[j]; }); return o; });
  }

  function exigir(filas, columnas, nombre) {
    if (!filas.length) throw new Error(nombre + ": vacío");
    columnas.forEach(function (c) { if (!(c in filas[0])) throw new Error(nombre + ": falta la columna " + c); });
  }

  /* Devuelve {porDistrito: {id: {escenario: fila}}, detalle: {id: {escenario: [filas]}}}. Rechaza columnas que faltan y escenarios desconocidos. */
  function cargar(csvResultados, csvDetalle) {
    var res = parseCSV(csvResultados), det = parseCSV(csvDetalle), validos = { dv_A: 1, dv_B: 1, dv_base: 1, primero: 1 }, out = { porDistrito: {}, detalle: {} };
    exigir(res, COLUMNAS, "resultados"); exigir(det, COLUMNAS_DETALLE, "detalle");
    res.forEach(function (r) {
      if (!validos[r.escenario]) throw new Error("escenario desconocido: " + r.escenario);
      (out.porDistrito[r.district_id] = out.porDistrito[r.district_id] || {})[r.escenario] = r;
    });
    det.forEach(function (d) {
      if (!validos[d.escenario]) throw new Error("escenario desconocido: " + d.escenario);
      d.votos_1v = +d.votos_1v; d.votos_candidatura = +d.votos_candidatura;
      ((out.detalle[d.district_id] = out.detalle[d.district_id] || {})[d.escenario] = out.detalle[d.district_id][d.escenario] || []).push(d);
    });
    return out;
  }

  function nombreCandidatura(k) { return k.indexOf("bloque:") === 0 ? k.slice(7) + " (bloque)" : k; }
  function num(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
  function pct(x) { return (Math.round(x * 1000) / 10).toFixed(1).replace(".", ",") + " %"; }

  /* Candidaturas de primera vuelta: [{k, nombre, bloque, votos, partidos:[{partido,votos}]}], de más a menos votos. */
  function candidaturas(filasDetalle) {
    var m = {}, orden = [];
    filasDetalle.forEach(function (d) {
      if (!m[d.candidatura]) { m[d.candidatura] = { k: d.candidatura, nombre: nombreCandidatura(d.candidatura), bloque: d.bloque, votos: d.votos_candidatura, partidos: [] }; orden.push(d.candidatura); }
      m[d.candidatura].partidos.push({ partido: d.partido, votos: d.votos_1v });
    });
    return orden.map(function (k) { return m[k]; });
  }

  /* Transferencias de las candidaturas eliminadas: se aplica la regla publicada a los datos publicados y se COMPRUEBA contra
     los votos de segunda vuelta del CSV. Si no cuadra, devuelve null y la ficha no muestra el cuadro (nunca cifras inventadas). */
  function transferencias(fila, cands) {
    if (String(fila.vuelta_decisiva) !== "2") return [];
    var fa = cands.filter(function (c) { return c.k === fila.finalista_a; })[0], fb = cands.filter(function (c) { return c.k === fila.finalista_b; })[0];
    if (!fa || !fb) return null;
    var tot = { a: fa.votos, b: fb.votos }, filas = [], abst = 0;
    cands.forEach(function (c) {
      if (c === fa || c === fb) return;
      var mismos = [fa, fb].filter(function (f) { return c.bloque && f.bloque === c.bloque; });
      mismos.sort(function (x, y) { return y.votos - x.votos || (x.k < y.k ? -1 : 1); });
      if (mismos.length) { filas.push({ de: c.nombre, votos: c.votos, a: mismos[0].nombre }); tot[mismos[0] === fa ? "a" : "b"] += c.votos; }
      else { filas.push({ de: c.nombre, votos: c.votos, a: null, motivo: c.bloque ? "su bloque no tiene finalista" : "sin bloque" }); abst += c.votos; }
    });
    if (tot.a !== +fila.votos_a_2v || tot.b !== +fila.votos_b_2v || abst !== +fila.votos_abstencion) return null;
    return filas;
  }

  /* Ficha de un distrito: objeto de texto plano, listo para pintar (y para probar). */
  function ficha(id, regla, datos) {
    var r = REGLAS.filter(function (x) { return x.id === regla; })[0];
    if (!r) return null;
    var fila = datos.porDistrito[id] && datos.porDistrito[id][r.esc], det = datos.detalle[id] && datos.detalle[id][r.esc];
    if (!fila || !det) return null;
    var cands = candidaturas(det), total = cands.reduce(function (s, c) { return s + c.votos; }, 0), segunda = String(fila.vuelta_decisiva) === "2";
    var gana = nombreCandidatura(fila.candidatura_ganadora), primero = r.esc === "primero";
    return {
      regla: r.texto, distrito: id, vuelta: +fila.vuelta_decisiva, ganador: gana, bloque: fila.bloque_ganador, empate: fila.empate === "true",
      titular: primero ? "Gana " + gana + " con el " + pct(+fila.cuota_1v) + " de los votos, sin segunda vuelta"
        : segunda ? "Decide la segunda vuelta · gana " + gana + " con el " + pct(+fila.cuota_ganador_2v) : "Gana " + gana + " en primera vuelta con el " + pct(+fila.cuota_1v),
      primera: cands.map(function (c) { return { nombre: c.nombre, bloque: c.bloque, votos: c.votos, texto: num(c.votos), pct: pct(c.votos / total), partidos: c.partidos }; }),
      nota1: primero ? "Gana la candidatura más votada: no hay segunda vuelta" : segunda ? "Nadie pasa del 50 %" : "Supera el 50 %: no hay segunda vuelta",
      finalistas: segunda ? [nombreCandidatura(fila.finalista_a), nombreCandidatura(fila.finalista_b)] : [],
      transferencias: transferencias(fila, cands),
      segunda: segunda ? { a: { nombre: nombreCandidatura(fila.finalista_a), votos: +fila.votos_a_2v }, b: { nombre: nombreCandidatura(fila.finalista_b), votos: +fila.votos_b_2v }, abstencion: +fila.votos_abstencion } : null,
      avisoEmpate: fila.empate === "true" ? "Empate: se resuelve por orden alfabético y se marca; es una regla fija, no un sorteo." : ""
    };
  }

  /* Enlace profundo ?territorio=<id>&regla=tres|dos|base|primero. Sin regla: «tres». Con regla desconocida: «tres». */
  function leerEnlace(search) {
    var p = {}; String(search).replace(/^\?/, "").split("&").forEach(function (kv) { if (kv) { var a = kv.split("="); p[decodeURIComponent(a[0])] = decodeURIComponent(a[1] || ""); } });
    var ok = REGLAS.some(function (r) { return r.id === p.regla; });
    return { territorio: p.territorio || "", regla: ok ? p.regla : "tres" };
  }

  /* Índice publicado (datos/INDEX.json, T-409 #927). Devuelve {territorios:[{id,nombre,distritos,resultados,detalle,geometria}], aviso}
     y rechaza esquemas desconocidos, rutas con «..», absolutas o externas y huellas que no sean sha256 hexadecimal. */
  function leerIndice(json) {
    var idx = typeof json === "string" ? JSON.parse(json) : json, hex = /^[0-9a-f]{64}$/;
    if (!idx || (idx.schema !== "ddd.v4-doble-vuelta/1.0" && idx.schema !== "ddd.v4-doble-vuelta/1.1") || !Array.isArray(idx.territorios)) throw new Error("índice: esquema desconocido");
    var v11 = idx.schema === "ddd.v4-doble-vuelta/1.1";
    idx.territorios.forEach(function (t) {
      var aut = v11 && /^aut\d{2}$/.test(t.id);
      if (!aut && !/^nac\d{2}$/.test(t.id)) throw new Error("índice: id de territorio no válido: " + t.id);
      if (aut && (t.ambito !== "AUT" || !/^[a-z_]+$/.test(t.clave_visor || "") || !/^\d{4}-\d{2}$/.test(t.eleccion || ""))) throw new Error("índice: aut incompleto: " + t.id);
      (aut ? ["resultados", "detalle"] : ["resultados", "detalle", "geometria"]).forEach(function (k) {
        var f = t[k];
        if (!f || typeof f.ruta !== "string" || /(^|\/)\.\.(\/|$)|^\/|^[a-z]+:/i.test(f.ruta)) throw new Error("índice: ruta no válida en " + t.id + "/" + k);
        if (!hex.test(f.sha256 || "")) throw new Error("índice: sha256 no válido en " + t.id + "/" + k);
      });
    });
    idx.sin_doble_vuelta = v11 ? (idx.sin_doble_vuelta || []) : [];
    idx.sin_doble_vuelta.forEach(function (t) {
      if (!/^aut\d{2}$/.test(t.id) || typeof t.motivo !== "string" || !t.motivo) throw new Error("índice: territorio sin doble vuelta sin motivo: " + t.id);
    });
    return idx;
  }

  /* Entrada del índice por id (nacNN/autNN) o por la clave del visor (`clave_visor`); null si no hay. */
  function entrada(idx, clave) {
    return (idx && idx.territorios.filter(function (t) { return t.id === clave || t.clave_visor === clave; })[0]) || null;
  }

  /* Motivo declarado de un territorio sin doble vuelta (T-427), o "". */
  function motivoSin(idx, clave) {
    var t = idx && (idx.sin_doble_vuelta || []).filter(function (x) { return x.id === clave || x.clave_visor === clave; })[0];
    return t ? t.motivo : "";
  }

  /* Comparación entre reglas de un distrito (T-413 §3.7): [{id, texto, ganador, bloque}] con lo que dice el CSV. */
  function comparacion(id, datos) {
    return REGLAS.map(function (r) {
      var f = datos.porDistrito[id] && datos.porDistrito[id][r.esc];
      return f ? { id: r.id, texto: r.texto, ganador: nombreCandidatura(f.candidatura_ganadora), bloque: f.bloque_ganador } : null;
    }).filter(Boolean);
  }

  /* Color por bloque: clase CSS de cada candidatura ganadora. */
  function claseBloque(b) { return { Izquierdas: "izq", Nacionalistas: "nac", Patriotas: "pat" }[b] || "sin"; }

  var API = { entrada: entrada, motivoSin: motivoSin, leerIndice: leerIndice, comparacion: comparacion, REGLAS: REGLAS, parseCSV: parseCSV, cargar: cargar, ficha: ficha, leerEnlace: leerEnlace, claseBloque: claseBloque, transferencias: transferencias, candidaturas: candidaturas };
  if (typeof module !== "undefined" && module.exports) module.exports = API; else root.DV = API;
})(typeof window !== "undefined" ? window : this);
