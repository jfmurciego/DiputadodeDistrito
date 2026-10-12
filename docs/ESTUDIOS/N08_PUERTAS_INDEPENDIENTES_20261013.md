# N08 Congreso — Puertas independientes, sin Plan Maestro histórico

Versión 1.0 — diagnóstico aislado. Basado en fuentes oficiales INE 2025/2025,
N06 K=407 y producto topológico N08 nacional ya integrados.

## Responsabilidad de cada puerta

| Puerta | Qué certifica | Qué no certifica |
| --- | --- | --- |
| `PROVINCIAL_PREFLIGHT` | Identidad CPRO/CUSEC, integridad SHA-256 del producto N08, cuota provincial N06 y invariantes del grafo seccional para la unidad consultada | Reejecución M01–M03, factibilidad M04, partición real, acreditación de excepciones |
| `NATIONAL_READINESS` | Resultado actual de `production_blockers()`, incluida cobertura 52/52 y decisiones institucionales | Autorización de ejecución |
| `EXECUTION_AUTHORIZATION` | Negación explícita y bloqueos restantes | **No emite ni consume** una orden de ejecución; se mantiene `generation_authorized=false` |

Esta herramienta **no permite ensayos, generación ni publicación**. La primera
puerta puede dar `PASS_INPUTS_ONLY` mientras la segunda está `BLOCKED` y la
tercera permanece `DENIED`. No son resultados contradictorios.

La topología de secciones no demuestra contigüidad de todas las partes físicas
de una sección multipartes. El límite de componentes es una condición
**necesaria, no suficiente**. Tampoco se infiere población por partes.

## Ejecución de solo lectura

```shell
python herramientas/diagnosticar_puertas_congreso.py --province 10
python herramientas/diagnosticar_puertas_congreso.py --province 01
python -m unittest tests.test_congreso_readiness
```

Usa el producto comprometido en
`docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto`.
No requiere recrear el ZIP Shapefile ni descargar datos.
La cobertura de los consumidores **reales** M01–M03 de Cáceres sigue
acreditada únicamente por el expediente y las pruebas de PR #256.

## Invariantes de seguridad

- El contrato original `territorios/congreso/contrato_congreso_2026.json`
  **no se modifica**.
- `production_blockers()` y `validate_production_admission()` **no se relajan**.
- Nunca se convierte un diagnóstico provincial en admisión nacional.
- Nunca se infiere autorización de ejecución del resultado de otra puerta.
- K=407 nacional, K=3 para Cáceres y K provincial derivado por N06.
- Se rechaza cualquier alteración de hashes, cuotas, límites de provincia
  o `generation_authorized`.
- No se importa el Plan Maestro externo, ramas N07 heredadas ni estados
  `PENDING` obsoletos.

## Progresión posterior

Una vez revisada esta PR, el propietario decidirá si desea crear una **vía de
ensayo provincial** separada de readiness nacional, con políticas completas,
fuentes acreditadas y orden expresa. Eso queda **fuera** de este incremento.
