# T-294 · Despliegue del contador en Cloudflare (pasos del propietario)

Código: `herramientas/contador_worker/` (`worker.js`, `schema.sql`, `wrangler.toml`). No es producción hasta que se
ejecuten estos pasos y se publique el visor con la línea del contador. Coste: 0 € (plan gratuito).

## Desplegar
1. Cuenta gratuita en cloudflare.com. Añadir `diputadodedistrito.es` como zona y **mover el DNS del dominio a Cloudflare**
   (cambiar los servidores de nombres en el registrador). La zona debe estar «Activa» antes de `wrangler deploy`;
   conservar en Cloudflare los registros actuales que apuntan a GitHub Pages.
2. En un ordenador con Node 20+: `npm i -g wrangler` y `wrangler login`.
3. `cd herramientas/contador_worker`
4. Base de datos: `wrangler d1 create ddd-contador` → copiar el `database_id` que imprime en `wrangler.toml`
   (sustituye `REEMPLAZAR_TRAS_wrangler_d1_create`).
5. Tabla: `wrangler d1 execute ddd-contador --remote --file schema.sql`
6. Publicar: `wrangler deploy` (crea el dominio personalizado `contador.diputadodedistrito.es`, con DNS y TLS
   automáticos si el dominio está en Cloudflare).
7. Variables y secretos: ninguno. `observability` queda desactivado en `wrangler.toml`; no activar «Workers Logs» ni
   Logpush en el panel.
8. Comprobar (solo funciona después del paso 6; el Worker no tiene dirección `workers.dev`): `curl -i -X POST -H "Origin: https://diputadodedistrito.es" --data "/v2/" https://contador.diputadodedistrito.es/v`
   debe dar `204` sin `Set-Cookie`.

## Leer el contador
`wrangler d1 execute ddd-contador --remote --command "SELECT dia, ruta, n FROM visitas ORDER BY dia DESC, ruta LIMIT 60"`
(o en el panel: Storage & Databases → D1 → ddd-contador → Explore data).

## Retirar
Quitar la línea del contador de los visores (PR), `wrangler delete`, `wrangler d1 delete ddd-contador` y borrar el
subdominio `contador` del DNS. Nada queda en los dispositivos de los visitantes.

## Límites y avisos
- Cuenta cargas de página, no personas. Topes diarios de 20 000 por ruta y 40 000 en total (D1 gratuito admite ~100 000 escrituras al día; un tercero que falsifique
  el origen podría agotar el tope total y parar el recuento ese día, sin más efecto). Rutas fuera de la lista blanca se descartan.
- Lista blanca de rutas y orígenes: constantes `RUTAS` y `ORIGENES` en `worker.js` (cambiarlas exige PR). Solo se acepta el dominio propio: el sitio en `jfmurciego.github.io/DiputadodeDistrito/` tiene subruta y
  no coincidiría con la lista.
- La línea del contador ya está en los visores V1, V2 y V3 (`/nacional/` no lleva contador); mientras el Worker no esté desplegado,
  el navegador envía la señal y el subdominio no responde: no afecta a la página. Publicar el sitio es un paso aparte.
- Línea del visor: `<script>navigator.sendBeacon&&navigator.sendBeacon("https://contador.diputadodedistrito.es/v",location.pathname.replace(/index\.html$/,""))</script>`.
  Los visores no tienen hoy CSP, así que no hay `connect-src` que ajustar; si se añade, incluir ese host.
