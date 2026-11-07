---
name: publicar-visor
description: Procedimiento para publicar territorios o escenarios en el visor público (05 Publicación del Visor, desplegar-visor-publico.yml). Úsala solo en el chat operador y con permiso explícito del propietario en ese mensaje.
---

# Publicar en el visor

1. Permiso explícito del propietario en este chat, con la lista de territorios o escenarios.
2. Comprueba que cada territorio tiene una 00 completa (M06 + 04 en success) y anota su `production_run_id`.
   El visor solo muestra lo que está en `orchestracion/publicaciones_visor.json`.
3. Lanza por REST un dispatch por territorio nuevo, con `production_run_id=<run 00 completo>`; con el campo vacío solo
   entra `latest_validated`. Inputs vigentes: `pagina_publicar`, `production_run_id`, `scenario_id`, `scenario_strategy`.
   Escenarios (ensembles): `scenario_id` y `scenario_strategy`; un escenario se añade, no sustituye al canónico.
   ```
   gh api -X POST repos/jfmurciego/DiputadodeDistrito/actions/workflows/desplegar-visor-publico.yml/dispatches \
     -f ref=main -f "inputs[pagina_publicar]=<opción>" -f "inputs[production_run_id]=<run>"
   ```
3b. El dispatch (05 y 06) espera la aprobación del propietario en GitHub (entorno `produccion`); el operador solo
   prepara y da el enlace del run. La 05 llamada desde la 00 no pide un segundo clic.
4. Ensembles: el zip lleva `ensemble_sha256` y la copia web una feature por distrito (K), no por sección (#418 #424).
5. Una línea al planificador por publicación: territorio · run publicado · resultado. Sin vigilar el despliegue.
