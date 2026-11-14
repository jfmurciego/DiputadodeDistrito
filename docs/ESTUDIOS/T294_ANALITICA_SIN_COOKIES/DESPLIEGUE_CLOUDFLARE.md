# T-294 · Despliegue del contador en Cloudflare (pasos del propietario)

Código: `herramientas/contador_worker/` (`worker.js`, `schema.sql`, `wrangler.toml`). No es producción hasta que se
ejecuten estos pasos y se publique el visor con la línea del contador. Coste: 0 € (plan gratuito).

## Desplegar
1. Cuenta gratuita en cloudflare.com. Añadir el dominio `diputadodedistrito.es` a Cloudflare (o, si el DNS está en otro
   proveedor, usar solo el subdominio: crear la zona y delegar `contador` por NS; la vía más simple es mover el DNS).
2. En un ordenador con Node 20+: `npm i -g wrangler` y `wrangler login`.
3. `cd herramientas/contador_worker`
4. Base de datos: `wrangler d1 create ddd-contador` → copiar el `database_id` que imprime en `wrangler.toml`
   (sustituye `REEMPLAZAR_TRAS_wrangler_d1_create`).
5. Tabla: `wrangler d1 execute ddd-contador --remote --file schema.sql`
6. Publicar: `wrangler deploy` (crea el dominio personalizado `contador.diputadodedistrito.es`, con DNS y TLS
   automáticos si el dominio está en Cloudflare).
7. Variables y secretos: ninguno. `observability` queda desactivado en `wrangler.toml`; no activar «Workers Logs» ni
   Logpush en el panel.
8. Comprobar: `curl -i -X POST -H "Origin: https://diputadodedistrito.es" --data "/v2/" https://contador.diputadodedistrito.es/v`
   debe dar `204` sin `Set-Cookie`.

## Leer el contador
`wrangler d1 execute ddd-contador --remote --command "SELECT dia, ruta, n FROM visitas ORDER BY dia DESC, ruta LIMIT 60"`
(o en el panel: Storage & Databases → D1 → ddd-contador → Explore data).

## Retirar
Quitar la línea del contador de los visores (PR), `wrangler delete`, `wrangler d1 delete ddd-contador` y borrar el
subdominio `contador` del DNS. Nada queda en los dispositivos de los visitantes.

## Límites y avisos
- Cuenta cargas de página, no personas. Tope de 100 000 por ruta y día; rutas fuera de la lista blanca se descartan.
- Lista blanca de rutas y orígenes: constantes `RUTAS` y `ORIGENES` en `worker.js` (cambiarlas exige PR).
- La línea del visor y el texto del pie se añaden en una segunda tanda de la PR, tras fusionarse T-310.
- Línea del visor: `<script>navigator.sendBeacon&&navigator.sendBeacon("https://contador.diputadodedistrito.es/v",location.pathname)</script>`.
  Los visores no tienen hoy CSP, así que no hay `connect-src` que ajustar; si se añade, incluir ese host.
