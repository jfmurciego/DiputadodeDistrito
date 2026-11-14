// Prueba del Worker con una base D1 simulada: solo debe recibir (día, ruta, tope).
import { manejar, TOPE_DIARIO_POR_RUTA } from "./worker.js";
import test from "node:test";
import assert from "node:assert/strict";

const AHORA = new Date("2026-11-20T23:59:59Z");
function entorno() {
  const llamadas = [];
  return { llamadas, DB: { prepare: (sql) => ({ bind: (...a) => ({ run: async () => { llamadas.push({ sql, a }); } }) }) } };
}
const pedir = (cuerpo, origen = "https://diputadodedistrito.es", metodo = "POST") =>
  new Request("https://contador.diputadodedistrito.es/v", {
    method: metodo, body: metodo === "POST" ? cuerpo : undefined,
    headers: { Origin: origen, "User-Agent": "secreto", Referer: "https://x.test/", "CF-Connecting-IP": "1.2.3.4" },
  });

test("cuenta una ruta válida: solo (día, ruta, tope)", async () => {
  const e = entorno();
  const r = await manejar(pedir("/v2/"), e, AHORA);
  assert.equal(r.status, 204);
  assert.equal(e.llamadas.length, 1);
  assert.deepEqual(e.llamadas[0].a, ["2026-11-20", "/v2/", TOPE_DIARIO_POR_RUTA]);
  assert.ok(!JSON.stringify(e.llamadas).match(/secreto|1\.2\.3\.4|x\.test/));
});
test("descarta ruta fuera de lista, origen ajeno y método distinto", async () => {
  const e = entorno();
  for (const rq of [pedir("/admin"), pedir("/v2/?x=1"), pedir("/v2/", "https://malo.example"), pedir("", undefined, "GET")]) {
    assert.equal((await manejar(rq, e, AHORA)).status, 204);
  }
  assert.equal(e.llamadas.length, 0);
});
test("la respuesta no lleva cabeceras ni cookies", async () => {
  const r = await manejar(pedir("/"), entorno(), AHORA);
  assert.equal([...r.headers].length, 0);
});
