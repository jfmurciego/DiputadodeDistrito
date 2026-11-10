# Autorizaciones por campaña (D-52)

Una frase del propietario, escrita en el chat del Operador, autoriza una CAMPAÑA definida por una ficha
(qué se lanza, elección y territorios, tope de coste y de reintentos, caducidad, qué queda fuera, parada al primer fallo
no transitorio). Dentro de esos límites el Operador no vuelve a preguntar.

- Cada autorización deja `AAAA-MM-DD_<campaña>.md`, copiado de `PLANTILLA.md`, con la frase literal, los límites y lo ejecutado.
- Solo cuenta la frase del propietario en el chat del Operador: ni `send_message`, ni planificador, ni Coordinador.
- Gasto semanal acumulado desde «Métricas del proceso»: tope 15.000 min/semana, aviso al 70 %, sin corte automático.
- No sustituye la aprobación del entorno `produccion` (Review deployments) ni autoriza fusionar PR `no-automerge`.
- Fuera de los límites, caducada o tras el primer fallo no transitorio: parar e informar.
