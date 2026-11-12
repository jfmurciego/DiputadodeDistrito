# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.1.0
# CAMBIOS 1.1.0: T-215, columna «Nombre visible v5» (el nombre que lleva hoy cada fichero tras el paso 4) y nota de separadores.
# FECHA: 2026-11-10
# ANTERIOR: legacy/tests/generar_equivalencias_5_0_0_v1.0.0_20261110.py
"""T-198: genera docs/ARQUITECTURA/EQUIVALENCIAS_5_0_0.md (viejo -> nuevo) de la tabla maestra.

Reproducible: `python tests/generar_equivalencias_5_0_0.py` reescribe el documento;
`--comprobar` falla si el fichero difiere de lo generado. Ids de territorio: de
configuracion/notacion_territorial.csv y del catalogo; fases, flujos y productos: de las
tablas literales de abajo (copia de docs/ARQUITECTURA/CORTE_5_0_0.md, §a-c).
"""
import csv
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TABLA = ROOT / "configuracion" / "notacion_territorial.csv"
CATALOGO = ROOT / "configuracion" / "catalogo_territorios_espana_2025.yaml"
SALIDA = ROOT / "docs" / "ARQUITECTURA" / "EQUIVALENCIAS_5_0_0.md"

FASES = [  # (viejo, nuevo)
    ("M01 `01_preparar_base_territorial.py`", "P21 población y secciones + P22 geometría"),
    ("M02 `02_construir_adyacencias.py`", "P23 grafo de vecindad"),
    ("M03 `03_construir_grafo.py`", "P23 grafo de vecindad"),
    ("M04 `04_generar_semillas.py`", "P32 generación (punto de partida)"),
    ("M05 `05_optimizar_distritos.py`", "P32 generación (competidor canónico)"),
    ("M06 `06_consolidar_distritos.py`", "P34 certificación"),
    ("M07 `07_agregar_resultados_electorales.py`", "P41 votos a secciones + P42 agregación"),
    ("M08 `08_integrar_resultados.py`", "P42 agregación + P43 validación"),
]
# (fichero, nombre anterior al corte, flujo v5, nombre visible v5 — T-215)
FLUJOS = [
    ("gestor-campanas.yml", "0 Gestor de Campañas", "P00 Campaña", "P00 Campaña — Gestor"),
    ("ejecucion-completa-proyecto.yml", "00 Ejecución Completa del Proyecto", "P00 Campaña", "P00 Campaña"),
    ("activacion-por-eleccion.yml", "Auxiliar — Activación por Elección", "P00 Campaña", "P00 Campaña — Elección"),
    ("preparacion-legislatura-vigente.yml", "Auxiliar — Activación de Legislatura Vigente", "P00 Campaña", "P00 Campaña — Legislatura"),
    ("preparacion-fuentes.yml", "01 Preparación de Datos Territoriales", "P10 Fuentes", "P10 Fuentes — P11 Territoriales"),
    ("preparacion-resultados-electorales.yml", "03 Preparación de Resultados Electorales", "P10 Fuentes", "P10 Fuentes — P12 Electorales"),
    ("produccion-distritos.yml", "02 Generación de Distritos Autonómicos", "P20 Base territorial + P30 Distritos", "P20 Base territorial — P30 Distritos"),
    ("generar-alternativas-territoriales.yml", "06 Escenarios y Ensembles", "P30 Distritos (P33)", "P30 Distritos — P33 Alternativas"),
    ("incorporacion-resultados-electorales.yml", "04 Incorporación de Resultados Electorales", "P40 Resultados electorales", "P40 Resultados electorales"),
    ("desplegar-visor-publico.yml", "05 Publicación del Visor", "P50 Publicación", "P50 Publicación"),
    ("cadena-publicacion.yml", "05 Cadena de Publicación", "P50 Publicación", "P50 Publicación — Cadena"),
    ("publicar-version-mapa.yml", "Publicar versión de mapa", "P60 Publicación académica", "P60 Publicación académica"),
    ("podar-r2.yml", "Auxiliar — Poda de R2", "ARC Archivo", "ARC Archivo — Poda de R2"),
    ("recuperar-producto-electoral-durable.yml", "Recuperar producto electoral durable", "ARC Archivo", "ARC Archivo — Recuperar producto electoral"),
]
PRODUCTOS = [
    ("M06, `kind=canonical_m06`", "Mapa certificado, `kind=mapa_certificado`"),
    ("M08, `kind=canonical_m08`", "Resultados por distrito, `kind=resultados_distrito`"),
    ("`kind=static`", "`kind=estatico`"),
    ("`kind=ensemble`", "`kind=alternativas`"),
    ("id `m06-<id>-<run>`", "`mapa-<id5>-<run>`"),
    ("id `m08-<id>-<run>`", "`resultados-<id5>-<run>`"),
    ("id `static-<id>`", "`estatico-<id5>`"),
]


def _tabla():
    lineas = [l for l in TABLA.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    return list(csv.DictReader(lineas))


def territorios():
    """[(codigo, nombre_es, id_viejo, id_nuevo)] de la tabla maestra (id nuevo en minúsculas)."""
    return [(r["codigo"], r["nombre_es"], r["id_interno"], r["codigo"].lower()) for r in _tabla()]


def variantes_350():
    """[(id_viejo, codigo_padre, id_nuevo)] del catálogo (parent_territory_id -> NACnn)."""
    cat = yaml.safe_load(CATALOGO.read_text(encoding="utf-8"))
    por_id = {r["id_interno"]: r["codigo"] for r in _tabla()}
    out = []
    for t in cat["pilot_territories"]:
        if t.get("scope") == "congreso_350":
            cod = por_id.get(t["parent_territory_id"]) or t["parent_territory_id"].upper()  # T-220: el padre ya es nacNN
            out.append((t["territory_id"], cod, cod.lower() + "-350"))
    return sorted(out, key=lambda x: x[1])


def _tab(cab, filas):
    out = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    out += ["| " + " | ".join(f) + " |" for f in filas]
    return out


def generar():
    t, v = territorios(), variantes_350()
    L = [
        "# Equivalencias viejo → nuevo del corte 5.0.0 (T-198)",
        "",
        "GENERADO por `python tests/generar_equivalencias_5_0_0.py`; no editar a mano (lo comprueba",
        "`tests/test_corte_5_0_0_equivalencias.py`). Fuente de los ids: `configuracion/notacion_territorial.csv` y el",
        "catálogo; el resto, `docs/ARQUITECTURA/CORTE_5_0_0.md` §a-c. Ids nuevos en minúsculas (DECISIÓN 5, pendiente).",
        "",
        "Nota: el test de entorno `produccion` (`tests/test_corte_5_0_0_equivalencias.py`) cubre solo la 05 y la 06.",
        "",
        "Separadores (T-215, aceptado por el Planificador): « — » en los nombres de flujo con botón manual (lo exige",
        "`test_all_manually_dispatchable_workflow_names_are_free_of_middle_dot`); «·» solo en territorios (`NAC01 · Álava`),",
        "en «Interno ·» y en los run-name. Desviación declarada: el job `archivar_r2` sigue en «Automático — Mantenimiento»;",
        "su traslado a ARC, después del corte.",
        "",
        "## Módulos → fases", "",
    ]
    L += _tab(["Viejo", "Nuevo"], FASES)
    L += ["", "## Flujos de trabajo → flujo v5", ""]
    L += _tab(["Fichero", "Nombre anterior", "Flujo v5", "Nombre visible v5"], [(f"`{a}`", b, c, d) for a, b, c, d in FLUJOS])
    L += ["", "## Productos", ""] + _tab(["Hoy", "v5"], PRODUCTOS)
    L += ["", f"## Territorios ({len(t)} ids AUT/NAC)", ""]
    L += _tab(["Código", "Nombre", "id viejo", "id nuevo"], [(a, b, f"`{c}`", f"`{d}`") for a, b, c, d in t])
    L += ["", f"## Variante de 350 ({len(v)} ids, sufijo `-350`)", ""]
    L += _tab(["id viejo", "padre", "id nuevo"], [(f"`{a}`", b, f"`{c}`") for a, b, c in v])
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    txt = generar()
    if "--comprobar" in sys.argv:
        sys.exit(0 if SALIDA.read_text(encoding="utf-8") == txt else 1)
    SALIDA.write_text(txt, encoding="utf-8")
