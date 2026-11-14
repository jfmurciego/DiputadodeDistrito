// PROYECTO: Diputado de Distrito · COMPONENTE: contador de visitas sin datos personales (T-294, opción A)
// VERSIÓN: 1.0.0 · FECHA: 2026-11-14 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
// FUNCIÓN: suma 1 a (día UTC, ruta de la lista blanca). No lee ni guarda IP, user-agent, referente ni cabeceras
// (salvo Origin, solo para descartar orígenes ajenos); no usa cookies ni almacenamiento; no registra nada en logs.
export const RUTAS = ["/", "/v1/", "/v2/", "/v3/", "/tecnico/"];
export const ORIGENES = [
  "https://diputadodedistrito.es",
  "https://www.diputadodedistrito.es",
];
// Topes diarios: D1 gratuito admite ~100 000 filas escritas al día; el total corta antes de agotarlo.
export const TOPE_DIARIO_POR_RUTA = 20000;
export const TOPE_DIARIO_TOTAL = 40000;
export const RUTA_TOTAL = "*";

export const SQL_UPSERT =
  "INSERT INTO visitas (dia, ruta, n) VALUES (?1, ?2, 1) " +
  "ON CONFLICT (dia, ruta) DO UPDATE SET n = n + 1 WHERE n < ?3";

export async function manejar(request, env, ahora = new Date()) {
  const vacia = () => new Response(null, { status: 204 });
  if (request.method !== "POST") return vacia();
  if (!ORIGENES.includes(request.headers.get("Origin") || "")) return vacia();
  const ruta = (await request.text()).slice(0, 32);
  if (!RUTAS.includes(ruta)) return vacia();
  const dia = ahora.toISOString().slice(0, 10);
  try {
    const total = await env.DB.prepare(SQL_UPSERT).bind(dia, RUTA_TOTAL, TOPE_DIARIO_TOTAL).run();
    if (total?.meta?.changes === 0) return vacia();
    await env.DB.prepare(SQL_UPSERT).bind(dia, ruta, TOPE_DIARIO_POR_RUTA).run();
  } catch (_) {
    // un fallo de la base nunca se muestra al visitante
  }
  return vacia();
}

export default { fetch: (request, env) => manejar(request, env) };
