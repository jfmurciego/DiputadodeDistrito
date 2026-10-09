# Preinscripción OSF — Mapa de Aragón v1.0

> Plantilla para **OSF Registries → "OSF Preregistration"**. Copiar cada sección
> en el campo del mismo nombre. Una vez registrada es inmutable y lleva marca de
> tiempo: todo lo que aquí se fije ya no puede ajustarse después de ver el mapa.
>
> **Registrar solo después** de restaurar los controles que falla hoy
> `tests/test_controles_obligatorios.py`. Preinscribir un método con la
> contigüidad geométrica desactivada congelaría ese defecto.

## 1. Información del estudio

**Título.** Distritos uninominales para las Cortes de Aragón a partir de secciones censales: método preinscrito.

**Pregunta.** ¿Puede dividirse Aragón en 67 distritos uninominales contiguos, de población equilibrada y forma compacta, mediante un procedimiento determinista declarado de antemano y sin datos electorales?

**Lo que este registro NO afirma.** No afirma neutralidad partidista del resultado ni lo propone como mapa oficial. Afirma únicamente que el procedimiento quedó fijado antes de conocer el mapa y antes de cruzarlo con votos.

## 2. Diseño

**Unidad.** Sección censal del INE, seccionado y padrón 2025, verificados por SHA-256 contra `inputs/partes/reconstruir_fuentes.sh`.

**Número de distritos.** K = 67, igual al número de escaños de las Cortes de Aragón. *Decisión política declarada.*

**Reparto provincial.** Proporcional a población por el método de Hamilton: Huesca 11, Teruel 7, Zaragoza 49. *Decisión política declarada:* difiere deliberadamente del reparto por circunscripción de las Cortes (Huesca 18, Teruel 14, Zaragoza 35), que sobrerrepresenta a las provincias menos pobladas.

**Restricciones duras** (un mapa que incumpla cualquiera se descarta): las doce de `configuracion/controles_obligatorios.yaml` en el commit registrado, incluida `geometric_contiguity`.

**Límites de población.** Tolerancia objetivo ±12 % sobre la media (20.367 hab.); suelo 0,80; techo 1,75.

**Adyacencia.** Dos secciones son adyacentes si comparten al menos 1,0 m de frontera (`min_shared_border_m: 1.0`). Contactos puntuales excluidos.

## 3. Procedimiento de generación

- Partición inicial: salida de M04 del commit registrado, validada contra el contrato.
- Motor: GerryChain 1.0.0, propuesta ReCom, `proposal_epsilon` = ________ (fijar antes de registrar).
- Sobrecargo comarcal: `region_surcharge = {"comarca": ______}` (fijar tras el barrido 0,3–0,8, antes de registrar).
- Semillas: 20260921, 20260922, 20260923, 20260924 (base 20260920, cuatro cadenas).
- Pasos: 3.000 por cadena. `PYTHONHASHSEED=0`.

## 4. Regla de selección

El mapa publicado es el mínimo de `candidate_rank` en el commit registrado, entre todos los estados visitados de las cuatro cadenas. Texto de la función: pegar aquí literalmente.

```
(pegar candidate_rank)
```

No se admite ninguna otra selección, manual ni automática. Si el revisor humano rechaza el resultado, se publica igualmente junto con el motivo del rechazo.

## 5. Plan de análisis

Se publicarán, para **todos** los estados visitados (≈12.000) y no solo para el seleccionado:

1. Distribución de desviación máxima de población.
2. Distribución de Polsby-Popper mínimo y mediano, y número de distritos bajo 0,15.
3. Número de distritos geométricamente discontinuos.
4. Comarcas divididas y retención de población comarcal.
5. Posición del mapa seleccionado dentro de cada distribución.

## 6. Datos electorales

El cruce con votos se hará **después** de publicar el hash de asignación del mapa seleccionado, en un commit posterior a este registro.

- Fuente: ________ (convocatoria, fecha, URL, SHA-256 del fichero).
- Clasificación de partidos en bloques: fichero `________`, SHA-256 `________`, justificación: ________.
- Se publicará el reparto simulado de escaños sea cual sea el resultado.

## 7. Reglas de parada y desviación

- Si ningún estado cumple todas las restricciones duras, se publica el fracaso y no se relaja ningún umbral en esta versión.
- Cualquier cambio de parámetros después del registro genera una **versión nueva** con registro nuevo; la anterior se conserva.

## 8. Artefactos que se enlazarán

Commit: ________ · DOI Zenodo del mapa: ________ · Atestación: `gh attestation verify ddd-aragon-v1.0.0.tar.gz --repo jfmurciego/DiputadodeDistrito`
