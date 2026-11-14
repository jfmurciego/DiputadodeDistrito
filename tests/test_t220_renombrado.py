#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-220: carpetas de territorios con el id nuevo; ni ids viejos vivos ni detección por prefijo `congreso_`."""
from __future__ import annotations

import csv
import hashlib
import io
import os
import re
import tokenize
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core import territorio_ids as ti  # noqa: E402

TABLA = ROOT / "configuracion" / "notacion_territorial.csv"
EQUIV = ROOT / "configuracion" / "equivalencias_territorios.csv"
SHA_TABLA = "13299081885c5d2736af5cbb86251641e962f63b91ad38914c694de1c3e621ee"  # literal: sha256 de la tabla maestra

# config/elecciones: contratos electorales con sha256 anclado en evidencias electorales (no cambian de contenido).
# Rutas donde un id viejo es histórico o trazabilidad (se leen vía ddd_core.territorio_ids.resolver_id).
EXENTOS = (
    "legacy/", "docs/", "tests/fixtures/", "tests/legacy/", "orchestracion/", "datos/", "datos_abiertos/",
    "resultados/", "publicado/", "evals/", "diagnostico/", "fuentes/observatorio_autonomicas/",
    "dashboard/", "infraestructura/ordenes-manuales/",  # generado (estado operativo) e histórico (órdenes manuales)
    "configuracion/notacion_territorial.csv", "configuracion/equivalencias_territorios.csv",
    "configuracion/equivalencia_secciones_congreso_2023.json",  # derivado de datos/ (equivalencia_congreso_2023.py)
    "ddd_core/territorio_ids.py", "tests/test_t220_renombrado.py", "tests/test_resolver_territorio.py",
    "tests/test_notacion_territorial.py", "tests/test_motor2_semilla.py", "tests/generar_equivalencias_5_0_0.py",
    # Regresiones sobre la raíz congelada de aee8215e o sobre evidencias históricas: sus ids son los de entonces.
    "tests/test_f10_asturias_galicia_receipt_candidates.py", "tests/test_f10_preparacion_aislada.py",
    "tests/test_f10_receipt_contract.py", "tests/test_source_preparation_generation_decoupling.py",
    "tests/test_electoral_gap_filler_real_evidence.py", "tests/_raiz_congelada.py",
    # Operan sobre datos derivados, registro del visor, claves R2 o títulos de runs históricos (D-61: no se renombran).
    "tests/test_visor_wgs84.py",
    "tests/test_dashboard_activation_alternative.py",
    "tests/test_homologacion_siglas_autonomicas.py",
    "tests/test_resultados_partidos.py",
    "tests/test_resolver_cadena_publicacion.py",
    "tests/test_archivar_artefactos_r2.py",
    "tests/test_escenarios_fase_c.py",
    "tests/test_materializar_fuentes_nacionales_ine.py",
    "tests/test_t201_vigente_por_eleccion.py",
    "tests/test_t126_registro_sin_mapa_350.py",
    "tests/test_resultados_ligeros.py",
    "tests/test_crosswalk_nacional.py",
    "tests/test_t83a_historico_m07.py",
    "tests/test_congreso_politica_propuesta.py",
    "tests/test_t166_cadena_m08_linaje.py",
    "tests/test_movilidad_em_union.py",
    "tests/test_registro_escenarios.py",
    "tests/test_visor_v2_botones.py",
    "tests/test_metricas_proceso.py",
    "tests/test_archivo_origen.py", "tests/test_desajuste_d17.py", "tests/test_materializacion_contratos_nacionales.py",
    "tests/test_gestor_campana_nacional.py", "tests/test_pre_m04_evidence_pipeline.py",  # métodos sobre la raíz congelada
    "tests/test_m06_product_reuse_integration.py",
    "tests/test_visor_v2_secciones.py",
    "tests/test_publicabilidad_policy.py",
    "tests/test_f10_2025_independent_territorial_receipts.py",
    "tests/test_f10_valencia_2023_universe.py",
    "tests/test_f10_electoral_three_territories.py",
    "tests/test_f10_derived_doors.py",
    "tests/test_f10_valencia_2023_durable_receipt.py",
    "tests/test_f10_interannual_correspondence.py",
    # Visor V3 (T-292): lee datos_abiertos/INDEX.json y las URL públicas, que conservan ids viejos (D-61); convivencia un ciclo.
    "visor/v3/", "tests/test_visor_v3_ui.js", "tests/test_preparar_portada_v3.py",
)
# Ficheros donde la palabra es otra cosa (slug de provincia, clave de un informe de población, zona del mapa).
NO_ES_ID = {
    "herramientas/generar_hemiciclo.py": "slugs de provincia de PROVINCIAS (el id se resuelve con territorio_ids)",
    "herramientas/generar_nombres_comunidades_nacional.py": "slugs de provincia",
    "herramientas/crosswalk_nacional.py": "claves ceuta/melilla del informe de población",
    "herramientas/materializar_fuentes_nacionales_ine.py": "claves ceuta/melilla del informe de población",
    "herramientas/resumir_preflight_nacional.py": "nombre de variable",
    "herramientas/procesar_f10_resultados_aragon_cyl.py": "variables y carpetas de originales F10 (evidencia histórica)",
    "herramientas/preflight_caceres_n08.py": "herramienta N08 con su sha256 anclado en la campaña nacional (histórica)",
    "visor/nacional/nacional.js": "zona del mapa", "visor/nacional/index.html": "zona del mapa",
}
EXENTOS_RE = re.compile(r"^territorios/[^/]+/(evidencia|resultados|inputs|docs|config/elecciones)/|^territorios/[^/]+/[^/]+\.md$"
                        r"|^territorios/congreso350_|^territorios/congreso/")
CODIGO = ("herramientas/", "ddd_core/", "ddd_motor2/", "ddd_ensemble/", "modulos/", ".github/", "procedimiento.sh",
          "visor/")


def _ls_files() -> list[str]:
    """Ficheros versionados; sin .git (contenedor de la CI) recorre el árbol sin carpetas ocultas ni cachés."""
    if (ROOT / ".git").exists():
        r = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 0:
            return [f for f in r.stdout.splitlines() if (ROOT / f).is_file()]
    omitir = {".git", "__pycache__", "node_modules", ".venv"}
    res = []
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in omitir]
        res += [(Path(d) / f).relative_to(ROOT).as_posix() for f in files]
    return res


def _equivalencias() -> list[dict]:
    filas = [l for l in EQUIV.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    return list(csv.DictReader(io.StringIO("\n".join(filas))))


def _viejos() -> list[str]:
    return [r["antiguo"] for r in _equivalencias()]


class TablaDeEquivalencias(unittest.TestCase):
    def test_fuente_con_sha256_de_la_tabla_maestra(self):
        self.assertEqual(hashlib.sha256(TABLA.read_bytes()).hexdigest(), SHA_TABLA)
        self.assertIn(f"sha256 {SHA_TABLA}", EQUIV.read_text(encoding="utf-8"))

    def test_se_regenera_de_la_tabla_maestra(self):
        esperado = [{"antiguo": t.id_legacy, "nuevo": t.id, "etiqueta": t.etiqueta}
                    for t in sorted(ti.tabla().values(), key=lambda t: t.codigo)]
        self.assertEqual(_equivalencias(), esperado)
        self.assertEqual(len(esperado), 71)

    def test_madrid_ceuta_y_melilla_por_id_exacto(self):
        self.assertEqual(ti.resolver_id("madrid"), "aut13")
        self.assertEqual(ti.resolver_id("congreso_madrid"), "nac28")
        self.assertEqual(ti.resolver_id("ceuta"), "aut18")
        self.assertEqual(ti.resolver_id("congreso_ceuta"), "nac51")
        self.assertEqual(ti.resolver_id("melilla"), "aut19")
        self.assertEqual(ti.resolver_id("congreso_melilla"), "nac52")


class Ambito(unittest.TestCase):
    def test_ambito_por_resolutor(self):
        self.assertEqual(ti.ambito("nac01"), "NAC")
        self.assertEqual(ti.ambito("congreso_alava"), "NAC")
        self.assertEqual(ti.ambito("aut13"), "AUT")
        self.assertEqual(ti.ambito("congreso350_alava"), "NAC350")
        self.assertEqual(ti.ambito("congreso"), "CONGRESO")
        with self.assertRaises(ti.IdTerritorioDesconocido):
            ti.ambito("congreso_inexistente")
        self.assertFalse(ti.es_nacional("congreso_inexistente"))

    def test_cli_para_workflows(self):
        r = subprocess.run([sys.executable, "-m", "ddd_core.territorio_ids", "ambito", "nac35"], cwd=ROOT,
                           capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "NAC"))
        r = subprocess.run([sys.executable, "-m", "ddd_core.territorio_ids", "ambito", "nac99"], cwd=ROOT,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


class CarpetasRenombradas(unittest.TestCase):
    def test_carpetas_igual_a_tabla_mas_350_y_congreso(self):
        carpetas = {p.name for p in (ROOT / "territorios").iterdir() if p.is_dir()}
        nuevos = {r["nuevo"] for r in _equivalencias()}
        resto = carpetas - nuevos
        self.assertTrue(nuevos <= carpetas, sorted(nuevos - carpetas))
        self.assertEqual({c for c in resto if not c.startswith(ti.PREFIJO_350_LEGACY)}, {"congreso"})
        self.assertEqual(len([c for c in resto if c.startswith(ti.PREFIJO_350_LEGACY)]), 49)

    def test_contratos_con_id_nuevo(self):
        for r in _equivalencias():
            cfg = ROOT / "territorios" / r["nuevo"] / "config" / f"{r['nuevo']}_2025.yaml"
            self.assertTrue(cfg.exists(), cfg)
            self.assertRegex(cfg.read_text(encoding="utf-8"), rf"(?m)^  territory_id: {r['nuevo']}$")


def _exento(f: str) -> bool:
    return f.startswith(EXENTOS) or f in NO_ES_ID or bool(EXENTOS_RE.search(f))


def _lineas_con_datos(f: str, texto: str):
    """Líneas donde un id es un dato. En Python, solo los literales de texto (un nombre de variable como `aragon` no
    es un id); en el resto (YAML, JSON, workflows, shell), la línea entera."""
    if not f.endswith(".py"):
        yield from enumerate(texto.splitlines(), 1)
        return
    try:
        for tok in tokenize.generate_tokens(io.StringIO(texto).readline):
            if tok.type == tokenize.STRING or getattr(tokenize, "FSTRING_MIDDLE", -1) == tok.type:
                for k, parte in enumerate(tok.string.splitlines()):
                    yield tok.start[0] + k, parte
    except (tokenize.TokenError, SyntaxError, IndentationError):
        yield from enumerate(texto.splitlines(), 1)


class SinIdsViejos(unittest.TestCase):
    def test_sin_ids_viejos_vivos(self):
        alt = "|".join(sorted(map(re.escape, _viejos()), key=len, reverse=True))
        token = re.compile(rf"(?<![A-Za-z0-9_.\-])({alt})(?![A-Za-z0-9_\-])")
        # URL, rutas públicas o de datos derivados (no se renombran, D-61) y claves R2 `<id>/<run>/…`.
        # y nombres de fichero de datos derivados (`congreso_soria.csv`, `<id>.zip` de un M06 publicado).
        url = re.compile(r"\w+://\S+|(site/data|resultados/finales|diagnostico/auto)/\w+|\bdatos(_abiertos)?/[\w/.\-]+"
                         r"|(?<![\w/])(docs|resultados|data)/[\w/.\-]+|\b\w+\.(csv|zip)\b|(?<![\w/])\w+/\d+(?=[/\"'])")
        alias = re.compile(r"\b(aut|nac)\d\d\b")  # una línea que nombra el id viejo y el nuevo documenta el alias
        malos = []
        for f in _ls_files():
            if token.search(f) and not _exento(f):
                malos.append(f"{f} (ruta)")
            if _exento(f):
                continue
            try:
                texto = (ROOT / f).read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            fuente = texto.splitlines()
            for n, linea in _lineas_con_datos(f, texto):
                original = fuente[n - 1] if 0 < n <= len(fuente) else linea
                if (token.search(url.sub("", linea)) and not alias.search(original)
                        and "t220: no es id" not in original):
                    malos.append(f"{f}:{n}: {linea.strip()[:100]}")
        self.assertEqual(malos, [], f"{len(malos)} ids viejos vivos:\n" + "\n".join(malos[:5000]))


class SinDeteccionPorPrefijo(unittest.TestCase):
    # `congreso_` suelto (sin provincia detrás) = detección por prefijo; con ids `nacNN` falla en silencio.
    PREFIJO = re.compile(r"(?<![A-Za-z0-9_])congreso_(?![a-z0-9])")

    def test_codigo_y_workflows_usan_el_ambito_del_resolutor(self):
        malos = []
        for f in _ls_files():
            if (not f.startswith(CODIGO) or f.endswith(".md") or f == "ddd_core/territorio_ids.py"
                    or f == "herramientas/preflight_caceres_n08.py"):  # N08 histórica: sha256 anclado en la campaña
                continue
            try:
                texto = (ROOT / f).read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            malos += [f"{f}:{n}: {l.strip()[:100]}" for n, l in enumerate(texto.splitlines(), 1)
                      if self.PREFIJO.search(l)]
        self.assertEqual(malos, [], "\n".join(malos))

    def test_el_vigilante_detecta_el_prefijo(self):
        for caso in ('t.startswith("congreso_")', "case territorios/congreso_*)", 'f"congreso_{slug}"'):
            self.assertRegex(caso, self.PREFIJO)
        self.assertNotRegex("congreso350_alava equivalencia_secciones_congreso_2023 congreso_alava", self.PREFIJO)


if __name__ == "__main__":
    unittest.main()
