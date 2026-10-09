# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 2.0.0
**Fecha de corte:** 2026-09-11
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.13.0.md`

## 1. Estado arbitral

La referencia territorial vigente sigue siendo **GitHub Run #9 `34599224954` / R016**, ejecutado sobre `f9ca44ff005043f630fce39334d34726d8bf55c5`. Resultado: 67 distritos, 1.463 secciones, 1.364.621 habitantes, Huesca 11 / Teruel 7 / Zaragoza 49, 0 cruces provinciales, 0 desconectados, 0 infracciones municipales, 0 bajo suelo, 0 sobre techo, `fuera_12=0` y máximo desvío `0.099299365905`.

R018 **no modifica el algoritmo territorial ni sustituye Run #9**. Cambia la arquitectura del repositorio para soportar múltiples territorios con un único motor.

## 2. Arquitectura vigente

- Motor común: `ddd_core/`, `modulos/`, `herramientas/`.
- Paquetes territoriales: `territorios/<territorio>/`.
- Aragón: `territorios/aragon/`.
- Castilla y León: `territorios/castilla_y_leon/` preparado como siguiente implantación.
- Tests globales: `tests/`.
- Gobernanza global: `docs/`.
- Versiones históricas: `legacy/`.
- Rama permanente: únicamente `main`.

No se crean repositorios ni ramas permanentes por comunidad autónoma. Las ramas temporales, si son imprescindibles, se integran y eliminan.

## 3. Estado de Aragón

Aragón es la **implantación de referencia madura** del motor, aunque queda pendiente R017 de auditoría de calidad territorial fina. M05 v7.4.0 / Run #9 es el baseline protegido. La regresión automática debe seguir garantizando sus invariantes.

La estructura canónica de Aragón pasa a `territorios/aragon/`. Por seguridad de transición se conservan temporalmente rutas históricas en raíz usadas por el workflow validado. Es compatibilidad, no arquitectura objetivo.

## 4. Estado del motor general

El motor DDD se considera **beta funcional**: existe un flujo completo reproducible y validado, pero su generalidad todavía no está demostrada fuera de Aragón. Castilla y León es el segundo caso y la prueba de generalización.

Éxito de generalización: incorporar un nuevo territorio principalmente mediante fuentes, YAML, reglas declarativas y tests. Cualquier `if aragon`, `if castilla_y_leon` o copia del motor es deuda arquitectónica.

## 5. R018 — multi-territorio

Objetivos:
1. convertir Aragón de “proyecto implícito” a paquete territorial explícito;
2. mantener un único motor común;
3. crear el contrato estándar de territorio;
4. preparar el paquete Castilla y León;
5. crear continuidad autosuficiente para abrir un nuevo chat;
6. retirar documentación activa redundante sin borrar historia útil;
7. generalizar `procedimiento.sh` para derivar `run_name` desde el YAML.

## 6. Compatibilidad temporal

Mientras el workflow GitHub territorial siga especializado en Aragón, se mantienen `configuracion/`, `inputs/` y `resultados/ejecuciones/` como rutas compatibles. Los nuevos desarrollos deben usar `territorios/`. La generalización del workflow es trabajo inicial del hilo Castilla y León y debe conservar la capacidad de reproducir Run #9.

## 7. Próximos frentes

- **Aragón / este hilo:** R017, auditoría de calidad territorial fina, cuando se retome.
- **Castilla y León / nuevo hilo:** inventariar fuentes, poblar el contrato territorial, generalizar workflow y ejecutar M01–M03 antes de cualquier optimización.
- **Después:** Extremadura como prueba de que la generalización realmente reduce trabajo de ingeniería.

## 8. Documentación obligatoria

Leer en orden: `README.md`, este Estado Maestro, `docs/CONTINUIDAD_NUEVO_CHAT.md`, `docs/ARQUITECTURA_MULTI_TERRITORIO.md`, `docs/CONTRATO_TERRITORIO.md` y, para Castilla y León, `docs/CONTINUIDAD_CASTILLA_Y_LEON.md`.
