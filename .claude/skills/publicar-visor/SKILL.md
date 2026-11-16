---
name: publicar-visor
description: Procedimiento para publicar territorios o escenarios en el visor público («P40 Publicación», p40-publicacion.yml, desde T-372). Úsala solo en el chat operador y con permiso explícito del propietario en ese mensaje.
---

# Publicar en el visor

1. Permiso explícito del propietario en este chat, con la lista de territorios o escenarios; o autorización de campaña
   vigente (D-52, `docs/autorizaciones/`) cuya ficha diga «publica: sí» y nombre esos territorios. Sin ese «sí», no se publica.
2. Comprueba que cada territorio tiene una 00 completa (M06 + 04 en success) y anota su `production_run_id`.
   El visor solo muestra lo que está en `orchestracion/publicaciones_visor.json`.
3. Lanza por REST un dispatch (todo o nada para varios territorios): `que_publicar=Territorios`, `territorios=aut01,nac42` (el código toma del
   registro la última 00 completa con la 04 en verde de cada uno) y `simular=false`; `que_publicar=Solo el sitio` no toca el registro.
   Con `simular=true` (por defecto) solo resuelve y comprueba. Escenarios (ensembles): `scenario_id`/`scenario_strategy` solo por `workflow_call`.
   ```
   gh api -X POST repos/jfmurciego/DiputadodeDistrito/actions/workflows/p40-publicacion.yml/dispatches \
     -f ref=main -f "inputs[que_publicar]=Territorios" -f "inputs[territorios]=<códigos>" -F "inputs[simular]=false"
   ```
3b. El dispatch (05 y 06) ya no espera aprobación en `produccion` (D-127): solo se lanza con la frase del propietario en este chat (D-52);
   da el enlace del run. La 05 llamada desde la 00 no pide un segundo clic.
4. Ensembles: el zip lleva `ensemble_sha256` y la copia web una feature por distrito (K), no por sección (#418 #424).
5. Una línea al planificador por publicación: territorio · run publicado · resultado. Sin vigilar el despliegue.
