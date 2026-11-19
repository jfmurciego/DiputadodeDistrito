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
console.log("OK visor v4 mapa");
