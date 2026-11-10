# Ecuador (Asamblea Nacional) · nota de preparación (T-158)

Fecha de consulta: 2026-11-10. **Ninguna fuente de Ecuador es alcanzable desde la sesión cloud** (CNE, INEC, Asamblea Nacional, Registro Civil: `connect_rejected`). No hay ficheros ni sha256. Todo lo siguiente es conocimiento general **NO VERIFICADO**: sirve para planificar la adquisición, no para ningún contrato.

## 1. Sistema vigente y norma (NO VERIFICADO)
- Norma: Constitución de 2008 (arts. 118-120, Función Legislativa) y Ley Orgánica Electoral y de Organizaciones Políticas de la República del Ecuador, «Código de la Democracia» (reformas de 2020 y 2023-2024). Texto y reformas vigentes: pedir a Registro Oficial/CNE.
- Estructura de la Asamblea (de memoria): asambleístas nacionales (circunscripción nacional), provinciales (2 por provincia más uno por cada 200.000 habitantes o fracción mayor de 150.000), del exterior (circunscripciones de Europa/Oceanía/Asia/África, Canadá/EE. UU. y Latinoamérica/Caribe) y distritos en provincias grandes (Guayas, Pichincha, Manabí). Total aprox. 151 en 2023. Todas las cifras a confirmar.
- Reparto: listas plurinominales con método proporcional (Webster/Sainte-Laguë tras la reforma de 2020; antes D'Hondt). A confirmar con el texto vigente.

## 2. Qué sería un «distrito uninominal»
- Por provincia o circunscripción: K = escaños provinciales; la unidad dura es la provincia/circunscripción (ya lo es).
- Los escaños nacionales (15) y del exterior (6) no tienen territorio dentro del país: quedarían fuera o se trazarían como un distrito nacional adicional (decisión del propietario).
- Calcado de lo que hace el módulo español: partición dura = provincia (24 provincias, 221 cantones, ~1.000 parroquias; cifras a confirmar).

## 3. Unidades mínimas y cartografía (NO VERIFICADO)
- Unidades: parroquia (menor unidad administrativa) y, para el voto, zona/recinto electoral; las secciones censales españolas no existen. El INEC tiene sectores y zonas censales (censo 2022).
- Cartografía candidata: INEC (límites político-administrativos y sectores censales del Censo 2022), IGM (Instituto Geográfico Militar). Formato y licencia sin confirmar.
- Hueco: cruce recinto/junta receptora de votos → parroquia/zona.

## 4. Población oficial
Censo de Población y Vivienda 2022 (INEC) y proyecciones oficiales de población. Cifras y fecha por confirmar en origen. Hay que decidir si se reparte por población o por votantes (el censo electoral difiere).

## 5. Resultados y licencia
El CNE publica resultados por junta receptora del voto (JRV) y por recinto, previsiblemente en portal de datos abiertos; formato, histórico (2021, 2023 anticipadas) y licencia sin confirmar. No alcanzable desde la nube: haría falta que el propietario descargue y suba los ficheros a un release (mecanismo ya usado con Infoelectoral).

## 6. Reglas del núcleo a parametrizar
- **Partición dura**: provincia (24) o circunscripción especial; el motor admite hoy 52 territorios españoles con CPRO: habría que generalizar el identificador y la notación (T-148 fija AUTnn/NACnn solo para España).
- **K**: dada por la fórmula de la ley (2 + 1 por cada 200.000), no por el motor.
- **Techo/suelo**: sin comparación con los límites españoles; tamaños provinciales de unos pocos cientos de miles a unos 4 millones de habitantes: dispersión mucho mayor.
- **Atomicidad**: parroquia (tamaño muy variable, rural pequeñísima y urbana enorme); zonas censales como unidad menor.
- Contigüidad: Galápagos (insular) y la Amazonía (conectividad por ríos/carreteras) requieren aristas virtuales.
- CRS y geografía: cambia el huso/proyección (UTM 17S/18S, EPSG:32717 o 32718 a confirmar); el contrato usa EPSG:25830 (España).
- Nombres en español: ya cumplen la regla (Quito, Guayaquil…).

## 7. Huecos y riesgos
1. Todo sin verificar y no alcanzable.
2. Sin partición de menor nivel homogénea ni equivalente a la sección censal.
3. Normativa electoral cambiante (reformas 2020 y 2023): K y método pueden variar.
4. Circunscripciones del exterior y nacional sin territorio.
5. Licencias de datos y acceso desde la red restringida.

## 8. Esfuerzo (estimación)
ALTO. Antes de cualquier tarea de código: 1 tarea de adquisición manual (propietario descarga CNE/INEC/IGM), 1 de verificación normativa. Después 8-12 tareas: nueva fuente, notación, CRS, contrato, política, tests, prueba local con una provincia piloto (p. ej. una pequeña como Galápagos o Carchi, a elegir). Sin acceso a red hoy no se puede empezar.
