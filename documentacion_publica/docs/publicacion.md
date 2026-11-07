# Publicación del portal

## Primera PR: construir y revisar

El workflow `validar-documentacion-publica.yml` instala dependencias documentales separadas, construye con modo estricto y adjunta el HTML como artefacto de revisión. No solicita permisos de Pages, no ejecuta territorios y no modifica publicaciones.

## Opción recomendada: integrar en el publicador único

El visor ya construye un árbol candidato y lo despliega como sitio completo. Una segunda publicación de Pages para el mismo repositorio podría sustituir ese árbol y eliminar el visor.

La siguiente PR debe construir esta documentación e incorporarla en `/tmp/site-candidate/documentacion/` dentro del publicador único, antes de sus validaciones y despliegue. La propuesta de URL es `/DiputadodeDistrito/documentacion/`; todavía no se ha publicado.

Se debe verificar que la raíz, datos y recursos del visor anterior siguen presentes, que los enlaces relativos y la búsqueda funcionan bajo esa ruta y que la documentación se preserva en publicaciones posteriores del visor. Coordinar el cambio del workflow compartido con las sesiones activas.

## Alternativa: repositorio documental separado

Otro repositorio tendría su propio sitio Pages y su propio workflow de publicación. Evita compartir despliegue, a cambio de gestionar dos repositorios y la relación entre versiones. No se ha creado ese repositorio durante esta revisión.

## Aceptación para abrir al público

Revisar contenido y procedencia, construir sin advertencias, comprobar navegación en navegador y verificar ausencia de regresiones en el visor. Publicar requiere una acción explícita del propietario. Un artefacto de revisión no es una URL pública estable.

[Publicador revisado](https://github.com/jfmurciego/DiputadodeDistrito/blob/11f0ba2b775a889f2316e31ebdbd859cbc50ab13/.github/workflows/_reutilizable-publicar-sitio.yml) · [Guía Zensical](https://zensical.org/docs/publish-your-site/)

*Versión 1.0.0 · 2026-11-03 · Archivo nuevo.*
