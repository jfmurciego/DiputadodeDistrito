#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba del catálogo de procedencia (T-74)
VERSIÓN: 1.2.2 · FECHA: 2026-11-14 · ESTADO: candidato
CAMBIOS: 1.2.2 (T-203): sin literal de id viejo (guardián T-220): id_legacy('aut01').
  1.2.1 (T-203): en el repositorio, 0 fuentes vacías con ids nuevos y «eleccion» en todos los productos.
  1.2.0 (T-203): «eleccion» por producto y fuente hallada por id nuevo (aut/nac).
  1.1.0 (T-203): aviso ORIGEN_M06_NO_PUBLICADO por (territorio, elección).
ANTERIOR: legacy/tests/test_catalogo_procedencia_v1.2.1_20261114.py
FUNCIÓN: registros sintéticos: producto completo, M08 publicado sin sha256 (ERROR), composición de un M06 no
  publicado (AVISO), determinismo; y en el repositorio, catálogo versionado igual al regenerado y sin errores.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import catalogo_procedencia as cp  # noqa: E402
from ddd_core.territorio_ids import id_legacy  # noqa: E402

H = "a" * 64


def escribir(raiz: Path, rel: str, datos) -> None:
    p = raiz / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(datos) if rel.endswith(".json") else datos, encoding="utf-8")


def repo_sintetico(raiz: Path, sha_m08=H) -> None:
    prod = {"repository": "r", "territory_id": "t1", "territory_label": "T1", "publication_status": "PUBLICABLE"}
    escribir(raiz, "orchestracion/publicaciones_visor.json", {"products": [
        dict(prod, id="m06-t1-10", kind="canonical_m06", run_id="10", blob_sha="b6", sha256=H),
        dict(prod, id="m08-t1-10", kind="canonical_m08", run_id="10", blob_sha="b8", sha256=sha_m08),
    ], "ensembles": []})
    escribir(raiz, "orchestracion/archivo_r2.json", {"artefactos": {"t1/10/ddd-state-10-M06.zip": {
        "territorio": "t1", "run_id": "10", "url": "r2://x/t1/10/ddd-state-10-M06.zip", "sha256": "c" * 64}}})
    escribir(raiz, "datos/composicion/MANIFEST.json", {"territorios": {"t1": {
        "run_id": "9", "sha256_m06": "f" * 64, "sha256_csv": "d" * 64}}})
    escribir(raiz, "configuracion/catalogo_preparacion.yaml", (
        "default_edition: '2025'\nterritories:\n- territory_id: t1\n  editions:\n    '2025':\n"
        "      preparation_evidence: {run_id: 5, package_sha256: " + "e" * 64 + "}\n"
        "      evidence: {electoral_source: territorios/t1/evidencia/fuentes_electorales/2025/" + H + "/7/receipt.json}\n"))


class CatalogoSintetico(unittest.TestCase):
    def test_producto_completo_y_avisos(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            repo_sintetico(raiz)
            cat = cp.generar(raiz)
            t = cat["territorios"]["t1"]
            self.assertEqual(t["fuente_territorial"]["package_sha256"], "e" * 64)
            self.assertEqual(t["fuente_electoral"]["identity_sha256"], H)
            m06 = next(p for p in t["productos"] if p["producto"] == "M06")
            self.assertEqual(m06["copias_r2"][0]["url"], "r2://x/t1/10/ddd-state-10-M06.zip")
            self.assertEqual(m06["copia_git"]["blob_sha"], "b6")
            self.assertEqual(cat["resumen"]["errores"], 0)
            codigos = {(i["codigo"], i["producto"]) for i in cat["incoherencias"]}
            self.assertIn(("ORIGEN_M06_NO_PUBLICADO", "composicion"), codigos)
            self.assertIn(("SIN_COPIA_R2", "M08"), codigos)
            self.assertEqual(cp.serializar(cat), cp.serializar(cp.generar(raiz)))

    def test_origen_m06_por_eleccion(self):
        # El sha256_m06 es el del M06 de 2023: vale para 2023 (sin election_date) y no para una composición de 2026.
        for extra, avisa in (({}, False), ({"election_date": "2026-11-29"}, True)):
            with tempfile.TemporaryDirectory() as d:
                raiz = Path(d)
                repo_sintetico(raiz)
                escribir(raiz, "datos/composicion/MANIFEST.json", {"territorios": {"t1": dict(
                    {"run_id": "9", "sha256_m06": H, "sha256_csv": "d" * 64}, **extra)}})
                cat = cp.generar(raiz)
                codigos = {(i["codigo"], i["producto"]) for i in cat["incoherencias"]}
                self.assertEqual(("ORIGEN_M06_NO_PUBLICADO", "composicion") in codigos, avisa, extra)

    def test_publicado_sin_sha256_es_error_y_comprobar_falla(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            repo_sintetico(raiz, sha_m08=None)
            self.assertEqual(cp.main(["--raiz", d]), 0)
            self.assertEqual(cp.generar(raiz)["resumen"]["errores"], 1)
            self.assertEqual(cp.main(["--raiz", d, "--comprobar"]), 1)

    def test_comprobar_detecta_catalogo_desfasado(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            repo_sintetico(raiz)
            cp.main(["--raiz", d])
            self.assertEqual(cp.main(["--raiz", d, "--comprobar"]), 0)
            escribir(raiz, "orchestracion/archivo_r2.json", {"artefactos": {}})
            self.assertEqual(cp.main(["--raiz", d, "--comprobar"]), 1)


class CatalogoVersionado(unittest.TestCase):
    def test_versionado_coincide_y_sin_errores(self):
        cat = cp.generar(ROOT)
        versionado = (ROOT / cp.SALIDA).read_text(encoding="utf-8")
        self.assertEqual(versionado, cp.serializar(cat),
                         "Regenera con: python herramientas/catalogo_procedencia.py")
        self.assertEqual(cat["resumen"]["errores"], 0, cp.informe(cat))


class ProcedenciaPorEleccion(unittest.TestCase):
    def test_eleccion_en_cada_producto_y_fuente_por_id_nuevo(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            viejo = id_legacy("aut01")  # el visor aún publica con ids viejos
            repo_sintetico(raiz)
            v = json.loads((raiz / "orchestracion/publicaciones_visor.json").read_text(encoding="utf-8"))
            v["products"][0]["territory_id"] = v["products"][1]["territory_id"] = viejo
            v["products"][1]["election_date"] = "2019-11-10"
            escribir(raiz, "orchestracion/publicaciones_visor.json", v)
            escribir(raiz, "configuracion/catalogo_preparacion.yaml",
                     "default_edition: '2025'\nterritories:\n- territory_id: aut01\n  editions:\n    '2025':\n"
                     "      preparation_evidence: {run_id: 7, package_sha256: " + H + "}\n")
            t = cp.generar(raiz)["territorios"][viejo]
            self.assertEqual({p["producto"]: p["eleccion"] for p in t["productos"]},
                             {"M06": "2023-07-23", "M08": "2019-11-10"})
            self.assertEqual(t["fuente_territorial"]["run_id"], "7")


    def test_repositorio_fuentes_y_eleccion_completas(self):
        cat = cp.generar(ROOT)
        vacias = [t for t, x in cat["territorios"].items()
                  if any(p["publicacion"] == "PUBLICABLE" for p in x["productos"]) and not x["fuente_territorial"]]
        self.assertEqual(vacias, [])
        self.assertTrue(all(p.get("eleccion") for x in cat["territorios"].values() for p in x["productos"]))


if __name__ == "__main__":
    unittest.main()
