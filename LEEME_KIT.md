# Kit de linaje, publicación y seguridad — Diputado de Distrito

Todos los ficheros están probados contra el repositorio en `a2a15b3`.

## Contenido

| Fichero | Destino en el repo | Qué hace |
|---|---|---|
| `configuracion/controles_obligatorios.yaml` | igual | Registro cerrado de controles del motor M05 |
| `tests/test_controles_obligatorios.py` | igual | Falla si el motor pierde un control registrado |
| `herramientas/fijar_acciones_por_sha.sh` | igual | Fija las 156 referencias de acciones a SHA inmutable |
| `.github/CODEOWNERS` | igual | Exige revisión en núcleo, módulos y configuración |
| `.github/dependabot.yml` | igual | Mantiene al día SHA y dependencias |
| `.github/workflows/publicar-version-mapa.yml` | igual | Mapa → manifiesto → atestación firmada → Release → DOI |
| `CITATION.cff` | raíz | Botón «Cite this repository» y metadatos para Zenodo |
| `.zenodo.json` | raíz | Metadatos de Zenodo (prevalece sobre CITATION.cff) |
| `docs/PREINSCRIPCION_OSF.md` | igual | Plantilla OSF con los parámetros reales de Aragón |

## Resultados de las pruebas

- `test_controles_obligatorios.py` contra `a2a15b3`: **3 fallos, 1 acierto**. Los fallos son exactamente los tres hallazgos de la auditoría del 20-09: `geometric_contiguity` ausente, `region_surcharge=None`, forma fuera del objetivo. Contra una copia con esos tres puntos corregidos: **4 aciertos**.
- `fijar_acciones_por_sha.sh` sobre copia del repo: 22 workflows modificados, 156 referencias fijadas, 0 restantes, los 23 YAML siguen siendo válidos.
- `CITATION.cff` validado con `cffconvert` contra el esquema 1.2.0.
- Empaquetado del workflow de publicación: dos ejecuciones producen el mismo SHA-256.

**Limitación honesta del test de controles:** comprueba *presencia*, no *corrección*. Impide que un refactor borre un control; no impide que alguien lo implemente mal. La primera versión, además, dio un falso positivo porque un comentario decía «forma determinista»; ahora analiza solo identificadores del código.

## Orden de implantación

### Día 1 — lo que solo puedes hacer tú (≈1 hora)

1. **Licencia.** El repositorio no tiene `LICENSE`: legalmente nadie puede reutilizar nada. En GitHub: *Add file → Create new file → `LICENSE` → Choose a license template*. Recomendación: **Apache-2.0** para el código. Alternativa europea: **EUPL-1.2**. Si eliges otra, cambia `license` en `CITATION.cff` y `.zenodo.json`.
2. **ORCID.** Crea la cuenta en orcid.org y rellena `APELLIDOS`, `NOMBRE` y el iD en `CITATION.cff` y `.zenodo.json`.
3. **Zenodo.** zenodo.org → *Log in with GitHub* → *Account → GitHub* → activa `DiputadodeDistrito`.
4. **Entorno protegido.** *Settings → Environments → New environment* `publicacion` → *Required reviewers*: tú.
5. **Rama protegida.** *Settings → Branches → Add rule* para `main`: requerir PR, requerir *Code Owners*, requerir que pase la CI.
6. **Escaneo de secretos.** *Settings → Code security* → activar *Secret scanning* y *Push protection*.
7. **Borrar `prueba-openai.yml`** y revocar esa clave en OpenAI si ya no se usa.

### Día 2 — commit del kit (≈30 min)

```bash
cp -r kit/{configuracion,tests,herramientas,docs} DiputadodeDistrito/
cp -r kit/.github/* DiputadodeDistrito/.github/
cp kit/CITATION.cff kit/.zenodo.json DiputadodeDistrito/
cd DiputadodeDistrito
bash herramientas/fijar_acciones_por_sha.sh
```

El test de controles **fallará**, por diseño. Dos opciones: commitearlo junto con la corrección del motor (recomendado), o provisionalmente quitar del registro los tres controles con un comentario que diga por qué y cuándo vuelven.

### Días 3–5 — restaurar el motor

Portar `geometric_contiguity` desde `m05_gerrychain_engine.py`; restaurar `region_surcharge` y barrerlo 0,3 → 0,8; meter forma en `candidate_rank`. Cuando el test pase: listo.

### Día 6 — preinscribir

Rellenar los huecos de `docs/PREINSCRIPCION_OSF.md` y registrarlo en osf.io → *Registries → OSF Preregistration*. **Nada del procedimiento puede cambiar después.**

### Día 7 — primera versión con DOI

Ejecutar el mapa según lo registrado. Luego *Actions → Publicar versión de mapa* con el run y el artefacto M06. Aprobar en el entorno `publicacion`. Zenodo asigna DOI a la Release en unos minutos. Comprobar desde cualquier máquina:

```bash
gh attestation verify ddd-aragon-v1.0.0.tar.gz --repo jfmurciego/DiputadodeDistrito
```

Enlazar el DOI en el registro OSF y en el README.

## Lo que queda fuera a propósito

Snakemake, Quarto, RO-Crate y JOSS. Son buenas ideas y ninguna resuelve un riesgo urgente. Después de la primera versión con DOI.
