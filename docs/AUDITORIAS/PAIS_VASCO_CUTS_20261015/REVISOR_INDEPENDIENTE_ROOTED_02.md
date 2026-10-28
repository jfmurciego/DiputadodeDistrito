# Revisión independiente — PV-CUT-02

**Dictamen: `PASS_ACOTADO` para la formulación de cortes enraizados y los controles inspeccionados.** El resultado de búsqueda es `NEGATIVE_BOUNDED`; no se encontró asignación conectada y no hay prueba de infactibilidad global.

El revisor inspeccionó en solo lectura el script, helper, tests, resultado y supervisor. Confirmó que hay una variable raíz binaria por cada variable de asignación, que se elige exactamente una raíz por distrito y que una raíz solo puede estar en una unidad asignada. Para una componente S que no contiene la raíz, el helper implementa `x(S)-x(N(S))-|S|r(S) <= |S|-1`. En una asignación conectada futura, si todo S está asignado y la raíz queda fuera, conectividad exige asignar al menos un vecino elegible del borde; si la raíz cae dentro de S, el término de raíz relaja el corte. Si S no está completamente asignado, `x(S) <= |S|-1` basta. El borde se limita a unidades con variable de asignación elegible y provincia coincidente.

También verificó que las unidades congeladas quedan fijadas individualmente al distrito de origen, incluidas las de distritos mixtos, y que pueden seleccionarse como raíz. Las tres pruebas helper cubren: corte del componente desconectado no raíz; admisión del distrito conectado igual a S; y admisión cuando el componente tiene frontera asignada.

La telemetría confirma `candidate=false`, ausencia de archivo de asignación, nueve resoluciones óptimas con incumbents desconectados y una décima resolución con límite de tiempo e incumbent aún desconectado. Total: 42 cortes, 49 nodos. Conclusión limitada al presupuesto y modelo inspeccionados.

**Limitaciones observadas:** el proceso total excedió los 120 s agregados en 0,244 s durante retorno/postprocesado (el supervisor de 130 s terminó normalmente); el script presupone consistencia intragrupo de provincia, distrito y congelación. El material inspeccionado no demuestra que haya inconsistencia efectiva de esos atributos.

El revisor no ejecutó el solver, no modificó archivos y no examinó otros territorios, las validaciones M06 ni el código productivo.
