# Diputado de Distrito · Estructura de portada (para Murciego)

Este paquete contiene un prototipo HTML autónomo que reproduce la jerarquía del esquema aprobado:

1. Portada: identidad, introducción y acceso a contenidos.
2. Dos recorridos paralelos: «Comprender» y «Explorar».
3. Investigación verificable: método M01–M08, fuentes, datos abiertos y limitaciones.

## Archivos

- `index.html`: abrir con doble clic para ver la maqueta. Funciona sin servidor ni librerías externas.
- `matriz_juridico_electoral_v1.json`: datos territoriales de trabajo, conservados aparte para la futura integración.
- `Matriz_juridico_electoral_DDD_v1.xlsx`: hoja de trabajo jurídica inicial.
- `referencia_estructura.png`: esquema original de arquitectura de navegación.

## Comportamiento

- Presentación inicial en pantalla completa: texto del proyecto, 6 segundos, sin audio, con botón «Saltar». Se muestra una sola vez por sesión de navegador (sessionStorage); puede repetirse con «Ver presentación inicial».
- Si el sistema indica preferencia por movimiento reducido, no se reproduce la apertura animada.
- «Comprender»: tres pestañas activas, navegación con teclado y enlaces a normativa.
- «Explorar»: botón real que abre `https://diputadodedistrito.es/v3/` sin intentar embeber ni reemplazar el mapa.
- «Investigación verificable»: cuatro componentes y un selector de comunidades y ciudades autónomas.
- «Matrices»: 19 ámbitos; el selector emplea la base jurídica de trabajo anterior. No confundir normas identificadas con comprobación de artículos y efectos concretos.

## Propuesta de integración

- Insertar esta estructura como página de inicio del dominio principal o como ruta independiente, no sobreescribir `/v3/`.
- Conservar la aplicación cartográfica existente y enlazarla desde «Explorar».
- En producción, las páginas de Comprender, Investigación y Matrices pueden separarse en rutas propias, pero se recomienda primero una implementación no intrusiva.
- Sustituir los vínculos genéricos de documentación por las rutas reales de metodología, datos y fuentes tras confirmar su ubicación en el repositorio.
- Mantener explícita la distinción entre resultados oficiales y escenarios simulados.
- Verificar antes de publicar: escritorio, móvil, contraste, teclado, rutas, carga de vídeo/mapa, códigos territoriales, estados de datos y licencias.

## Estado de verificación

- No se han modificado los archivos de la web pública ni el repositorio remoto.
- La referencia a `/v3/` procede de la URL comunicada por la usuaria; este paquete no certifica el funcionamiento online del mapa.
- La portada es un prototipo funcional de interfaz, no una copia del código de Murciego.
