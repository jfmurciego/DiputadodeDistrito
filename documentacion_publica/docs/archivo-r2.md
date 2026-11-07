# Archivo con Cloudflare R2

**Estado: diseño de activación; cuenta, bucket e integración aún pendientes.** GitHub conserva el código y los metadatos; R2 conservaría los bytes pesados. Los archivos de documentación permanecen en Markdown y el portal publica enlaces al catálogo y a las descargas.

## Primera instalación

1. Acceder a una cuenta Cloudflare y activar R2, revisando la facturación mostrada por el proveedor.
2. Crear un bucket privado, por ejemplo `ddd-archivo`, preferiblemente en jurisdicción UE si responde a los requisitos del proyecto. Confirmar disponibilidad y endpoint correspondiente; no deducirlo a partir de un endpoint global.
3. Crear credenciales S3 limitadas al bucket de archivo y configurarlas en el entorno de CI. Separar escritor de archivo y lectura pública.
4. Probar con un archivo pequeño conocido: subir, descargar, comparar bytes y SHA-256. Registrar el recibo de la prueba.
5. Archivar el checkpoint piloto y verificarlo mediante descarga independiente antes de integrarlo en la 00.

No se ha creado ningún recurso ni activado gasto durante esta revisión. No se han recibido ni utilizado credenciales R2.

## Organización propuesta

| Prefijo | Contenido |
|---|---|
| `objects/sha256/<hash>` | Bytes deduplicados identificados por SHA-256 |
| `runs/<territorio>/<run>/<attempt>/manifest.json` | Identidad, fuentes, contratos y referencias a objetos |
| `receipts/<territorio>/<run>/<attempt>/` | Confirmaciones de escritura y comprobación |
| `published/` | Solo objetos cuya publicación y licencia hayan sido aprobadas |

Una clave por hash evita sobrescrituras accidentales por nombre, pero no constituye por sí sola almacenamiento inmutable. Usar escrituras condicionales y una política de retención explícita. Los bucket locks de R2 impiden sobreescritura y borrado durante la retención configurada; sus reglas pueden administrarse, por lo que debe delimitarse quién puede cambiarlas. No habilitar retención indefinida de forma automática.

## Contrato de archivado para la siguiente PR

El archivador debe ser idempotente y recibir los productos existentes, sin regenerarlos. No alterar los estados científicos de M06/M08. Emitir un recibo con tamaño, hash, clave, fecha, intento, resultado de comprobación y ubicación. Si un mismo hash apunta a bytes incompatibles, abortar.

La puerta de conservación del archivo debe fallar si falta cualquier objeto obligatorio o no se ha verificado. Eso no debe reescribir un manifiesto histórico ni convertir una validación fallida en correcta. Los lectores del motor seguirán usando el circuito actual hasta incorporar y probar un adaptador de recuperación.

## Coste orientativo

En la tarifa Standard consultada: 10 GB-mes incluidos; almacenamiento adicional a 0,015 USD/GB-mes, más operaciones. Con los aproximadamente 2,30 GB observados en Releases cabría esa muestra, pero no hemos medido el total de Actions ni el crecimiento de la plataforma.

Como escenario presupuestario, 100 GB mantenidos un mes completo serían aproximadamente 1,35 USD de almacenamiento tras los 10 GB incluidos; las operaciones, impuestos u otros servicios van aparte. No es una estimación de la factura real de DDD.

## Apertura pública posterior

Empezar con el archivo privado. Publicar únicamente una selección con metadatos y licencias resueltos; comprobar acceso desde una sesión sin credenciales. El catálogo puede ser JSON estático y Zensical puede enlazarlo. No hace falta montar CKAN o una API de consulta para este primer hito.

[Inicio R2](https://developers.cloudflare.com/r2/get-started/) · [Autenticación S3](https://developers.cloudflare.com/r2/api/tokens/) · [Bucket locks](https://developers.cloudflare.com/r2/buckets/bucket-locks/) · [Tarifas](https://developers.cloudflare.com/r2/pricing/)

*Versión 1.0.0 · 2026-11-03 · Archivo nuevo.*
