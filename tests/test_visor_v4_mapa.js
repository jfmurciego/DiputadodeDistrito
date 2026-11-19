// Pruebas del mapa V4 con doble vuelta (T-413). Esperados: literales a mano (T-409 §7), no recalculados con el código.
const assert = require("assert"), fs = require("fs"), path = require("path");
const DV = require("../visor/v4/mapa/dv.js"), dir = path.join(__dirname, "../visor/v4/mapa/ejemplo/");
const rd = f => fs.readFileSync(dir + f, "utf8"), datos = DV.cargar(rd("resultados_doble_vuelta.csv"), rd("detalle.csv"));
// 1. Enlace profundo
assert.deepStrictEqual(DV.leerEnlace("?territorio=nac01&regla=dos"), { territorio: "nac01", regla: "dos" });
assert.strictEqual(DV.leerEnlace("").regla, "tres"); assert.strictEqual(DV.leerEnlace("?regla=zzz").regla, "tres");
// 2. Orden y textos de las reglas
assert.deepStrictEqual(DV.REGLAS.map(r => r.texto), ["Tres bloques", "Dos bloques", "Sin coaliciones", "Más votado"]);
// 3. Ejemplo T-409 §7 en «Tres bloques»: izq 45 – pat 40, nac 15 abstención, 52,9 %
let f = DV.ficha("EJ1", "tres", datos);
assert.strictEqual(f.titular, "Decide la segunda vuelta · gana Izquierdas (bloque) con el 52,9 %");
assert.deepStrictEqual(f.primera.map(c => [c.nombre, c.votos]), [["Izquierdas (bloque)", 45], ["Patriotas (bloque)", 40], ["Nacionalistas (bloque)", 15]]);
assert.deepStrictEqual(f.transferencias, [{ de: "Nacionalistas (bloque)", votos: 15, a: null, motivo: "su bloque no tiene finalista" }]);
assert.strictEqual(f.segunda.abstencion, 15);
// 4. «Sin coaliciones»: PSOE 30 + Sumar 15 = 45; PP 28 + VOX 12 = 40
f = DV.ficha("EJ1", "base", datos);
assert.deepStrictEqual(f.transferencias.map(t => [t.de, t.a, t.votos]), [["ERC", null, 15], ["Podemos–Sumar", "PSOE", 15], ["VOX", "PP", 12]]);
assert.deepStrictEqual([f.segunda.a.votos, f.segunda.b.votos], [45, 40]);
// 5. Mayoría en primera vuelta: sin segunda vuelta
f = DV.ficha("EJ2", "tres", datos); assert.strictEqual(f.vuelta, 1); assert.strictEqual(f.segunda, null);
assert.strictEqual(f.titular, "Gana Patriotas (bloque) en primera vuelta con el 52,0 %");
// 6. Empate marcado y aviso
f = DV.ficha("EJ4", "base", datos); assert.strictEqual(f.empate, true); assert.ok(f.avisoEmpate.includes("orden alfabético"));
// 7. «Más votado» no sale de este módulo; distrito inexistente: null
assert.strictEqual(DV.ficha("EJ1", "primero", datos), null); assert.strictEqual(DV.ficha("XX", "tres", datos), null);
// 8. Contrato: rechaza columnas que faltan y escenario desconocido
assert.throws(() => DV.cargar("district_id,escenario\nEJ1,dv_A\n", rd("detalle.csv")), /falta la columna/);
assert.throws(() => DV.cargar(rd("resultados_doble_vuelta.csv").replace(/dv_base/g, "dv_X"), rd("detalle.csv")), /escenario desconocido/);
// 9. Si las transferencias no cuadran con el CSV, no se muestran (nunca cifras inventadas)
const malo = rd("resultados_doble_vuelta.csv").replace("EJ1,dv_base,2,PSOE,Izquierdas,30,", "EJ1,dv_base,2,PSOE,Izquierdas,30,").replace(",45,40,0.529412,15,", ",44,40,0.529412,15,");
assert.strictEqual(DV.ficha("EJ1", "base", DV.cargar(malo, rd("detalle.csv"))).transferencias, null);
// 10. Cada ganador del visor coincide con el CSV
for (const id of Object.keys(datos.porDistrito)) for (const [r, e] of [["tres", "dv_A"], ["dos", "dv_B"], ["base", "dv_base"]]) {
  const x = DV.ficha(id, r, datos), fila = datos.porDistrito[id][e];
  assert.strictEqual(x.bloque, fila.bloque_ganador); assert.strictEqual(String(x.vuelta), fila.vuelta_decisiva);
}
// 11. «Más votado» dentro de los CSV (T-409 #927): escenario válido, primera vuelta, sin segunda vuelta
const cabR = "district_id,escenario,vuelta_decisiva,candidatura_ganadora,bloque_ganador,votos_1v,cuota_1v,finalista_a,finalista_b,votos_a_2v,votos_b_2v,cuota_ganador_2v,votos_abstencion,empate\n";
const cabD = "district_id,escenario,candidatura,partido,bloque,votos_1v,votos_candidatura\n";
const dp = DV.cargar(cabR + "1,primero,1,PSOE,Izquierdas,40,0.4,,,,,,,false\n", cabD + "1,primero,PSOE,PSOE,Izquierdas,40,40\n1,primero,PP,PP,Patriotas,35,35\n1,primero,VOX,VOX,Patriotas,25,25\n");
f = DV.ficha("1", "primero", dp);
assert.strictEqual(f.titular, "Gana PSOE con el 40,0 % de los votos, sin segunda vuelta");
assert.strictEqual(f.segunda, null); assert.strictEqual(f.nota1, "Gana la candidatura más votada: no hay segunda vuelta");
assert.deepStrictEqual(DV.comparacion("1", dp), [{ id: "primero", texto: "Más votado", ganador: "PSOE", bloque: "Izquierdas" }]);
// 12. Comparación entre reglas en el ejemplo: una entrada por regla con datos, en el orden de los botones; «Tres bloques» = Izquierdas (T-409 §7)
const cmp = DV.comparacion("EJ1", datos);
assert.deepStrictEqual(cmp.map(c => c.id), ["tres", "dos", "base"]);
assert.strictEqual(cmp[0].ganador, "Izquierdas (bloque)");
// 13. Índice publicado (T-409 #927): contrato literal
const H = "a".repeat(64), fich = r => ({ ruta: r, sha256: H });
const idx = { schema: "ddd.v4-doble-vuelta/1.0", territorios: [{ id: "nac01", nombre: "Albacete", distritos: 4, resultados: fich("nac01/resultados_doble_vuelta.csv"), detalle: fich("nac01/detalle.csv"), geometria: fich("nac01/distritos.geojson") }] };
assert.strictEqual(DV.leerIndice(idx).territorios[0].nombre, "Albacete");
assert.throws(() => DV.leerIndice({ ...idx, schema: "otro" }), /esquema desconocido/);
assert.throws(() => DV.leerIndice({ ...idx, territorios: [{ ...idx.territorios[0], id: "aut01" }] }), /id de territorio/);
for (const ruta of ["../secreto.csv", "/etc/passwd", "https://x.es/a.csv", "nac01/../../a.csv"]) assert.throws(() => DV.leerIndice({ ...idx, territorios: [{ ...idx.territorios[0], detalle: fich(ruta) }] }), /ruta no válida/, ruta);
assert.throws(() => DV.leerIndice({ ...idx, territorios: [{ ...idx.territorios[0], geometria: { ruta: "nac01/distritos.geojson", sha256: "xyz" } }] }), /sha256 no válido/);
console.log("OK visor v4 mapa");
