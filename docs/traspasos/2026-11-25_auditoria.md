# Traspaso del chat de la auditoría (25-11, 23:05 UTC)

Quien lea esto continúa el trabajo de la auditoría y del plan de mejora. Responder corto y en español. El contexto de este
chat ha llegado al 70 % del umbral: el estado queda aquí, en ficheros. **No se crea chat sucesor**: el plan lo escribe el
Planificador vivo (acuerdo de abajo), que es quien releva la función de planificación de este chat.

## 1. Sesiones
| Quién | session_id | Papel |
|---|---|---|
| Chat de la auditoría | session_01KQDtFrtDBQe7ZUMhVHCH58 | Autor de la auditoría y del plan de mejora; referencia del contenido |
| Planificador vivo | session_01KQDtFtbjHrVwhhgHnNE6nU | Único escritor de `docs/PLAN.md`; integra lo que apruebe el propietario |

## 2. Qué hay y dónde
Rama `claude/dreamy-maxwell-mezgob`, **sin PR** (el propietario no la ha pedido):
- `docs/AUDITORIAS/AUDITORIA_INTEGRAL_2026-11-24.md` 1.0.1: veredicto, benchmark, web y dirección.
- `docs/AUDITORIAS/PLAN_MEJORA_2026-11-25.md` 2.0.0: informe para decidir, 13 bloques (A a M), 35 tareas T-463 a T-498
  (T-464 reservada para la actualización del plan). El propietario tiene además el PDF (25 páginas).
- `docs/registro/2026-11-24_claude-dreamy-maxwell-mezgob.md`: entrada de registro de la rama.

**Cierre (26-11, 20:20 UTC):** el propietario ordenó, vía Planificador, abrir la PR de esta rama (solo documentación, `no-automerge`).
La fusiona el Coordinador con la orden del propietario y después archiva este chat. El contenido aprobado está en el plan 1.0.78 (D-213 y D-214).

## 3. Estado de aprobaciones al entregar el informe (25-11): ninguna
El propietario rechazó la primera tabla por falta de porqués y dijo que nada queda autorizado hasta leer un informe
detallado. Se le entregó el 2.0.0 a las 13:35 UTC del 25-11. **No ha contestado ningún bloque.** T-463 a T-498 son propuesta.

Lo que sí dijo en este chat el 25-11 (lo registra el Planificador):
1. La desigualdad de población de los distritos «se acepta»: sin tareas para corregirla.
2. Coste: dentro de su plan semanal, sin gasto adicional; «lo que se puede hacer se hará y lo que no, esperará».
3. No quiere olas hasta marzo: orden por dependencias, sin fechas.
4. Meta: el resto de ámbitos, a nivel de los mejores.

**Actualización del 26-11 (17:06 UTC), según mensaje del Planificador; este chat no lo ha visto directamente:** el propietario
dijo en el chat del Planificador «Sí al paquete de 2 días». Según él, eso aprueba: A (T-463), B solo el piloto (T-465 y T-466,
5 territorios), F solo la licencia (T-473), G (T-476), H solo los indicadores (T-478), I solo el diseño de T-482 y K (T-491).
El resto sigue como propuesta. La fuente de verdad es el plan 1.0.78 (T-464), que escribe el Planificador. Avisos de contenido
enviados ese día: regla de «seguir o no» del piloto escrita antes de ejecutar; T-482 con la equivalencia de secciones 2026→2023;
T-478 sin el tablero antiguo y rehaciendo el 10,7 % → 1,9 % desde ficheros con fuente; T-476 detrás de T-460; T-463 detrás de T-473.

## 4. Acuerdo con el Planificador vivo (25-11, 22:57 a 23:00 UTC; pendiente de lo que apruebe el propietario)
- Un solo escritor del plan: el Planificador. Pasa a este chat solo el fragmento que salga del informe, para confirmarlo.
- Números: T-463 a T-498, este plan; T-459 a T-462 y T-499/T-500, del Planificador; decisiones nuevas desde D-211, las numera él.
- Orden: antes del 29-11 solo documentos (T-463, T-473, T-465); después, empezando por T-491. T-463 necesita además una
  publicación «solo el sitio» con frase del propietario.
- Banco (T-466): primero un piloto de 5 territorios (propuestos: Burgos, Valladolid, La Rioja, Sevilla y Madrid) con GerryChain
  puro y el exacto; decisión de seguir o no antes de los bloques C, D y E. `redist`, solo si se sigue.
- Aprobación por bloque, un diseño por bloque como mucho. La página de licencia (T-473) va sola y antes.
- Web: las tareas de web van detrás de T-459 y T-500, que tocan `explorar.js`.

## 5. Qué hacer cuando el propietario conteste
Pasar al Planificador, literal y al momento, cada bloque con su «sí», «no» o «más adelante», y las cuatro decisiones de la
hoja (licencia, informe técnico, ritmo, quién escribe el plan). No abrir tareas desde este chat.

## 6. Lecciones (para el Coordinador)
- El propietario no aprueba una tabla de tareas: necesita, por cada una, qué problema hay hoy, por qué importa, qué recibe y
  qué pasa si no se hace, en un documento que pueda descargar (PDF) y leer con calma.
- El coste no se expresa en dólares: se trabaja dentro del plan semanal y se dan tallas comparadas con tareas ya cerradas.
- Las decisiones recién tomadas pueden estar solo en el chat del Planificador: se leen con `list_events` antes de numerar.
- Desde la sesión de la nube no se abre la web en vivo: se juzga por el código y las capturas versionadas.
- Dos chats planificando a la vez confunden al propietario: un solo escritor del plan y aviso con `send_message` desde el principio.
