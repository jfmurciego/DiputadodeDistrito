# Inventario de workflows retirados en la migración (T-397c, solo lectura)

Fecha: 2026-11-17. Fuente: API REST de Actions (`workflows/<fichero>` y `runs?per_page=1`, `total_count`). **No se ha borrado nada**:
borrar ejecuciones es efecto externo y lo hace el Operador con permiso del propietario (borrar run: `DELETE actions/runs/<id>`).
Los ficheros salen de los «renamed → legacy/workflows/» de las PR indicadas. #861, #877 y #882 no borran ficheros de workflow
(#877 y #882 solo modifican `auto-merge.yml`, `revisor-pr.yml` y `p90-automatico.yml`).

| PR | Fichero retirado | id workflow | estado API | ejecuciones |
|---|---|---|---|---|
| #845 | forense-00.yml | 410497511 | deleted | 386 |
| #845 | pruebas-plataforma.yml | 359810096 | **active** (¡sigue en la lista!) | 7506 |
| #851 | mantenimiento-programado.yml | 413104058 | deleted | 7 |
| #851 | podar-r2.yml | 412746329 | deleted | 3 |
| #851 | recuperar-producto-electoral-durable.yml | — (404 en la API) | — | sin workflow registrado |
| #853 | bateria-motor.yml | 412883281 | deleted | 234 |
| #855 | publicar-version-mapa.yml | 363223973 | deleted | 1 |
| #862 | _reutilizable-publicar-sitio.yml | 362674370 | deleted | 29 |
| #862 | cadena-publicacion.yml | 411036110 | deleted | 1 |
| #862 | desplegar-visor-publico.yml | 356955597 | deleted | 147 |
| #866 | _reutilizable-incorporacion-electoral.yml | 362736771 | deleted | 28 |
| #866 | incorporacion-resultados-electorales.yml | 362351353 | deleted | 24 |
| #874 | preparacion-fuentes.yml | 361271157 | deleted | 198 |
| #874 | preparacion-resultados-electorales.yml | 362318583 | deleted | 124 |
| #880 | _reutilizable-generacion-territorial.yml | 362736770 | deleted | 30 |
| #880 | generar-alternativas-territoriales.yml | 358237796 | deleted | 63 |
| #880 | produccion-distritos.yml | 359809506 | deleted | 61 |

Total: 16 workflows con id, 8 862 ejecuciones (7506 de «Pruebas de la Plataforma»).

## Observaciones
- Solo `pruebas-plataforma.yml` figura `active` en la lista de Actions (aparece como «Pruebas de la Plataforma»): el resto ya sale como `deleted`
  y la UI los oculta salvo con ejecuciones. Para limpiar la lista hay que borrar sus ejecuciones (y las de `forense-00`, etc. si se quiere
  que desaparezcan del historial).
- Su fichero ya no está en `main` (#845); que siga `active` indica ejecuciones recientes o una referencia en otra rama: comprobarlo antes de borrar.
- «Dependabot Updates», «Dependency Graph» y `pages-build-deployment` son dinámicos y no se tocan.
