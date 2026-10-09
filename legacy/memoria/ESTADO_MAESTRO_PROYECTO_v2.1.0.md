# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 2.1.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v2.0.0.md`

## 1. Estado arbitral

El proyecto tiene ya **dos implantaciones territoriales funcionales sobre un único motor**.

### Aragón — baseline protegido
La referencia territorial protegida sigue siendo **GitHub Run #9 `34599224954` / R016**, sobre `f9ca44ff005043f630fce39334d34726d8bf55c5`:
- 67 distritos;
- 1.463 secciones;
- 1.364.621 habitantes;
- Huesca 11 / Teruel 7 / Zaragoza 49;
- 0 cruces provinciales;
- 0 desconectados;
- 0 infracciones municipales;
- 0 bajo suelo;
- 0 sobre techo;
- `fuera_12=0`;
- máximo desvío `0.099299365905`.

Aragón sigue siendo la regresión de referencia y no puede degradarse por cambios necesarios para otros territorios.

### Castilla y León — CYL-04 cerrado
Referencia: commit `1549011cc56c56f3403e11902437228731e7d8ee`, workflow `Optimización DDD — territorio`, run `34619174991`.
Resultado: **SUCCESS**.

Contrato validado hasta M05:
- 3.506 secciones;
- población 2.401.221;
- K=82;
- reparto Hamilton: Ávila 6, Burgos 12, León 15, Palencia 6, Salamanca 11, Segovia 5, Soria 3, Valladolid 18, Zamora 6;
- contigüidad 82/82;
- 0 cruces provinciales;
- 0 violaciones duras;
- `fuera_12=0`;
- máxima desviación relativa 0,1198;
- núcleos urbanos cerrados preservados;
- disciplina municipal preservada.

Esto demuestra que la arquitectura multi-territorio ya no es solo preparatoria: el mismo motor ha producido una solución territorial válida fuera de Aragón.

## 2. Arquitectura vigente

- Motor común: `ddd_core/`, `modulos/`, `herramientas/`.
- Paquetes territoriales: `territorios/<territorio>/`.
- Aragón: `territorios/aragon/`.
- Castilla y León: `territorios/castilla_y_leon/`.
- Configuración territorial declarativa en YAML.
- Workflows GitHub Actions por puerta funcional.
- Tests globales: `tests/`.
- Gobernanza y continuidad: `docs/`.
- Históricos obligatorios: `legacy/`.
- Rama permanente: únicamente `main`.

La regla arquitectónica se mantiene: no crear copias del motor por territorio ni introducir `if aragon`, `if castilla_y_leon` o lógica territorial hardcodeada cuando la diferencia pueda expresarse mediante configuración, datos o reglas generales.

## 3. Modelo operativo

GitHub es la **fuente de verdad y plano de ejecución**:
- código;
- configuración;
- legacy;
- documentación;
- workflows;
- artefactos de ejecución;
- logs y bitácora técnica.

ChatGPT actúa como **plano de decisión y arquitectura**: diagnóstico, diseño de reglas, interpretación de resultados y cambios del motor. El procesamiento pesado, GIS, reconstrucción de fuentes, recocido y validaciones masivas deben delegarse preferentemente en GitHub Actions para reducir carga local y mantener reproducibilidad.

## 4. Lecciones generalizadas de Castilla y León

### 4.1 Factibilidad provincial tras cierres urbanos
Un núcleo urbano cerrado no puede validarse solo por su población individual. El cierre debe preservar que la población provincial restante pueda repartirse entre los distritos abiertos dentro de la banda objetivo.

M04 v7.4.7 convirtió esta condición en una invariante mínima y dirigida.

### 4.2 Residuo abierto no equivale a residuo móvil
Un residuo municipal puede estar marcado como abierto y, sin embargo, quedar inmóvil si constituye una única `ddd_unit_id` que ocupa por sí sola un distrito. M04 v7.4.8 introduce micro-unidades residuales fronterizas únicamente cuando esa atomicidad bloquea la factibilidad posterior.

En Castilla y León se creó exactamente una micro-unidad flexible; M05 v7.4.0 pudo entonces cerrar `fuera_12=0` sin cambiar su algoritmo.

### 4.3 Responsabilidades de módulo
- M04 decide granularidad y factibilidad estructural.
- M05 optimiza la asignación sin romper las unidades M04.
- M06 consolida, mide y publica sin alterar `district_id`.

Los bloqueos deben corregirse en el módulo que crea la restricción, no mediante excepciones posteriores.

## 5. Estado de módulos

- **M01** — base territorial: operativo multi-territorio.
- **M02** — adyacencias: operativo; admite pasarelas topológicas declarativas.
- **M03** — grafo territorial: operativo; audita provincias y municipios.
- **M04** — solución inicial: v7.4.8; factibilidad provincial y granularidad residual flexible.
- **M05** — optimización: v7.4.0; validado en Aragón y Castilla y León.
- **M06** — consolidación: v7.1.0 candidato CYL-05; amplía el antiguo resumen a catálogo territorial auditable y composición exacta.
- **M07** — agregación electoral: funcional en Aragón; todavía no portado a Castilla y León.
- **M08** — producto final: funcional en Aragón; pendiente de segunda implantación.

## 6. CYL-05 — trabajo en curso

M06 v7.0.1 estaba por debajo de su contrato documental: solo generaba resumen poblacional y geometría disuelta. La v7.1.0 corrige esa brecha.

Productos esperados:
- resumen poblacional;
- catálogo distrital de 82 filas;
- composición territorial de 3.506 filas;
- GeoJSON de secciones;
- GeoJSON de distritos disueltos;
- área, perímetro, Polsby–Popper, centroide y bounding box en CRS métrico;
- municipio y provincia por distrito;
- conservación exacta de población, filas, K y asignación M05.

Puerta CI: `.github/workflows/consolidar-territorio.yml`.
Registro detallado: `docs/EJECUCIONES/2026-09-11_CYL04_CYL05.md`.

## 7. Próximos frentes

1. Cerrar CYL-05 y convertir M06 v7.1.0 en baseline aceptado si supera la puerta.
2. Ejecutar regresión de Aragón con M06 v7.1.0 y confirmar compatibilidad hacia atrás.
3. Actualizar `docs/CONTINUIDAD_CASTILLA_Y_LEON.md` tras CYL-05.
4. Decidir la fuente electoral para una futura CYL-06/M07; no inventar ni reutilizar datos de Aragón.
5. Mantener R017 de auditoría territorial fina de Aragón como frente independiente.
6. Usar un tercer territorio, previsiblemente Extremadura, como prueba de que la incorporación ya es mayoritariamente declarativa.

## 8. Documentación obligatoria

Leer en orden:
1. `README.md`;
2. este Estado Maestro;
3. `docs/CONTINUIDAD_NUEVO_CHAT.md`;
4. `docs/ARQUITECTURA_MULTI_TERRITORIO.md`;
5. `docs/CONTRATO_TERRITORIO.md`;
6. `docs/CONTINUIDAD_CASTILLA_Y_LEON.md` para Castilla y León;
7. el último documento de `docs/EJECUCIONES/` asociado al territorio en curso.
