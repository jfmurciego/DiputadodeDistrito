"""T-349 · test de FLUJO (criterio de hecho): con TODO el estado registrado de la r3 tal cual (id viejo), la cadena de la r4
no reutiliza nada con id no canónico y prepara todo de nuevo con el id canónico.

Fixture congelada SIN TOCAR: `tests/fixtures/t349_flujo/raiz`, copiada byte a byte con `git show <BASE>:<ruta>` por
`tests/fixtures/t349_flujo/_generar_fixture.py` (configuración, fuentes y territorios aut11, nac01 y aut01). Ningún test lee el
estado vivo de `territorios/`, `orchestracion/` ni del catálogo: el código se enlaza a una copia temporal de la fixture.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from ddd_core import territorio_ids
from herramientas import consumir_par_fuentes_legislatura as consumir
from herramientas import preflight_preparacion_fuente as pf
from herramientas import registrar_par_fuentes_legislatura as registrar
from herramientas import resolver_preparacion_legislatura as rpl
from herramientas.identidad_fuentes_legislatura import territorial_identity
from herramientas.resolver_activos_durables import validate_durable_assets
from herramientas.resolver_ejecucion_completa import build_plan
from herramientas.validar_puerta_ejecucion import _artifact_name_is_consistent

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/t349_flujo/raiz"
# Estado registrado real en el commit base, por territorio: ¿qué objeto lleva el id viejo? (lo verifica el primer test).
# aut11 es el piloto: su M06 y su par ya se regeneraron con id canónico en la r3; su recibo electoral y su M08, no.
ESTADO_R3 = {
    "aut11": {"electoral_source": True, "territorial_product": False, "electoral_product": True, "prepared_source_pair": False},
    **{t: {"electoral_source": True, "territorial_product": True, "electoral_product": True, "prepared_source_pair": True}
       for t in ("nac01", "aut01", "aut02", "aut05", "aut19", "aut08", "aut12")},
}
MUESTRA = tuple(ESTADO_R3)
MODOS = ("reuse", "catalog_source", "from_start")


def _raiz_temporal() -> Path:
    td = Path(tempfile.mkdtemp(prefix="t349_flujo_"))
    raiz = td / "r"
    shutil.copytree(FIX, raiz)
    for d in ("modulos", "herramientas", "ddd_core"):  # solo código; el estado es el de la fixture
        os.symlink(ROOT / d, raiz / d)
    return raiz


def _fila(raiz: Path, tid: str) -> dict:
    cat = yaml.safe_load((raiz / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
    return next(r for r in cat["territories"] if r["territory_id"] == tid)


def _json(raiz: Path, rel: str) -> dict:
    return json.loads((raiz / rel).read_text(encoding="utf-8"))


class FlujoR4SobreEstadoR3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raiz = _raiz_temporal()
        cls.cat = cls.raiz / "configuracion/catalogo_preparacion.yaml"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.raiz.parent, ignore_errors=True)

    def test_la_fixture_trae_el_estado_viejo(self):
        """Precondición: la fixture (sin tocar) es exactamente el estado de ESTADO_R3."""
        for tid, esperado in ESTADO_R3.items():
            ev = _fila(self.raiz, tid)["editions"]["2025"]["evidence"]
            for clave, viejo in esperado.items():
                with self.subTest(tid=tid, objeto=clave):
                    recibo = _json(self.raiz, ev[clave])["territory_id"]
                    self.assertEqual(recibo == territorio_ids.tabla()[tid].id_legacy, viejo, recibo)
                    self.assertEqual(recibo == tid, not viejo, recibo)

    def test_activacion_no_reutiliza_nada_con_id_viejo(self):
        planes = {p["territory_id"]: p for p in rpl.resolve(self.raiz, "Todos")["plans"]}
        for tid in MUESTRA:
            with self.subTest(tid=tid):
                p = planes[tid]
                self.assertEqual(p["electoral_action"], "ACQUIRE")
                if p["territorial_action"].startswith("REUSE"):
                    c = p["territorial_candidate"]
                    self.assertEqual(c["territory_id"], tid)
                    self.assertTrue(c["artifact_name"].startswith(f"ddd-source-package-{tid}-"))
                    recibo = _json(self.raiz, c["receipt_path"])
                    self.assertEqual(recibo["territory_id"], tid)

    def test_preflight_no_registra_el_paquete_electoral_viejo(self):
        for tid in MUESTRA:
            with self.subTest(tid=tid):
                self.assertFalse(pf.preflight(self.raiz, "electoral", tid, "2025")["registered"])

    def test_par_registrado_no_se_consume(self):
        # Con id viejo se rechaza por el id; el de aut11 (canónico) lleva dentro el paquete electoral viejo: también.
        for tid in MUESTRA:
            with self.subTest(tid=tid):
                with self.assertRaises(consumir.PreparedPairExecutionBlock):
                    consumir.resolve_pair(root_dir=self.raiz, territory=tid, edition="2025")

    def test_m06_viejo_no_habilita_reuso_geometrico(self):
        for tid in MUESTRA:
            ev = _fila(self.raiz, tid)["editions"]["2025"]
            recibo_m06 = _json(self.raiz, ev["evidence"]["territorial_product"])
            prep = ev["preparation_evidence"]
            fuente = {k: prep[k] for k in ("run_id", "artifact_name", "artifact_sha256")}
            ident = prep["territorial_identity_sha256"]
            with self.subTest(tid=tid):
                g = consumir.resolve_geometric_reuse(root_dir=self.raiz, territory_id=tid, edition="2025",
                                                    current_identity=ident, current_source=fuente)
                h = registrar._historical_product_reuse(self.raiz, plan={"territory_id": tid, "project_edition": "2025"},
                                                        current_identity=ident)
                self.assertEqual(recibo_m06["territory_id"] != tid, ESTADO_R3[tid]["territorial_product"])
                if ESTADO_R3[tid]["territorial_product"]:
                    self.assertFalse(g["compatible"], g)
                    self.assertFalse(h["geometric_reuse_compatible"], h)
                else:  # M06 canónico: si no se reutiliza, no es por el id
                    self.assertNotEqual(g.get("reason"), "PRODUCT_ID_NO_CANONICO")
                    self.assertNotEqual(h.get("reason"), "PRODUCT_ID_NO_CANONICO")

    def test_m06_viejo_con_linaje_sellado_que_casa_no_habilita_reuso(self):
        """B2: aunque el linaje producto→fuente (sellado) case con la identidad vigente, el recibo M06 con id viejo no entra."""
        tid = "nac01"
        cat_path = self.raiz / "configuracion/catalogo_preparacion.yaml"
        cat_original = cat_path.read_text(encoding="utf-8")
        cat = yaml.safe_load(cat_original)
        fila = next(r for r in cat["territories"] if r["territory_id"] == tid)
        ev = fila["editions"]["2025"]
        ident = ev["preparation_evidence"]["territorial_identity_sha256"]
        rel = f"territorios/{tid}/evidencia/catalogo/linaje_t349_flujo.json"
        for linaje_id in (territorio_ids.tabla()[tid].id_legacy, tid):
            (self.raiz / rel).write_text(json.dumps({
                "schema": "ddd.territorial-product-source-lineage/1.0", "territory_id": linaje_id, "edition": "2025",
                "territorial_source": {"territorial_identity_sha256": ident}}), encoding="utf-8")
            ev["evidence"]["territorial_product_source_lineage"] = rel
            cat_path.write_text(yaml.safe_dump(cat, allow_unicode=True, sort_keys=False), encoding="utf-8")
            try:
                with self.subTest(linaje=linaje_id):
                    g = consumir.resolve_geometric_reuse(root_dir=self.raiz, territory_id=tid, edition="2025",
                                                        current_identity=ident)
                    h = registrar._historical_product_reuse(
                        self.raiz, plan={"territory_id": tid, "project_edition": "2025"}, current_identity=ident)
                    self.assertFalse(g["compatible"], g)
                    self.assertFalse(h["geometric_reuse_compatible"], h)
            finally:
                cat_path.write_text(cat_original, encoding="utf-8")
                (self.raiz / rel).unlink()

    def test_activos_durables_no_devuelven_nada_viejo(self):
        for tid in MUESTRA:
            st = _fila(self.raiz, tid)["editions"]["2025"]
            with self.subTest(tid=tid):
                try:
                    d = validate_durable_assets(root_dir=self.raiz, state=st, territory_id=tid, edition="2025",
                                                territorial_source=st["preparation_evidence"], expected_election_id=None)
                except Exception as exc:  # bloquear también es no reutilizar, salvo que sea por otra causa
                    self.assertIn("ID_NO_CANONICO", str(exc))
                    continue
                for clave in ("territorial_product", "electoral_source", "electoral_product"):
                    if d[clave] is not None:
                        self.assertEqual(d[clave]["territory_id"], tid, clave)

    def test_00_prepara_todo_de_nuevo_en_todos_los_modos(self):
        for tid in MUESTRA:
            nombre = _fila(self.raiz, tid)["name"]
            m06_viejo = ESTADO_R3[tid]["territorial_product"]
            for modo in MODOS:
                with self.subTest(tid=tid, modo=modo):
                    plan = build_plan(territory=nombre, edition="2025", execution_mode=modo, catalog=self.cat,
                                      root_dir=self.raiz)
                    estado = plan["catalog_state"]
                    self.assertFalse(estado["electoral_source_prepared"])
                    self.assertFalse(estado["electoral_product_available"])
                    self.assertTrue(plan["run_prepare_electoral"])
                    self.assertTrue(plan["run_incorporate"])
                    descartados = {d["objeto"] for d in estado["non_canonical_discarded"]}
                    self.assertTrue({"electoral_source", "electoral_product"} <= descartados, descartados)
                    if m06_viejo:
                        self.assertFalse(estado["territorial_product_available"])
                        self.assertIn("territorial_product", descartados)
                        self.assertTrue(plan["run_generate"])
                    else:  # el M06 canónico de aut11 sí se reutiliza en «Reutilizar» (no hay nada que regenerar)
                        self.assertNotIn("territorial_product", descartados)
                        if modo == "reuse":
                            self.assertTrue(estado["territorial_product_available"])
                            self.assertFalse(plan["run_generate"])
                    for clave in ("electoral_source", "electoral_product"):
                        self.assertIsNone(plan["existing"][clave]["decision"], clave)

    def test_puerta_03_04_rechaza_el_nombre_viejo(self):
        for tid in MUESTRA:
            viejo = territorio_ids.tabla()[tid].id_legacy
            with self.subTest(tid=tid):
                self.assertFalse(_artifact_name_is_consistent(
                    "electoral_source", tid, "2025", "1", f"ddd-electoral-package-{viejo}-2025-1"))
                self.assertTrue(_artifact_name_is_consistent(
                    "electoral_source", tid, "2025", "1", f"ddd-electoral-package-{tid}-2025-1"))


class PaquetePrevioDelP12(unittest.TestCase):
    """Defensa en profundidad: `preparar_fuente_electoral.validate_previous` rechaza por sí misma un paquete previo con alias."""

    def _paquete(self, raiz: Path, territorio: str) -> Path:
        import hashlib
        previo = raiz / territorio
        (previo / "data").mkdir(parents=True)
        fuente = previo / "data/votes.csv"
        fuente.write_text("section,votes\n1,10\n", encoding="utf-8")
        (previo / "manifest.json").write_text(json.dumps({
            "schema": "ddd-electoral-package/1.0", "decision": "ACQUIRE", "territory_id": territorio, "edition": "2025",
            "selected_source": {"path": "data/votes.csv", "sha256": hashlib.sha256(fuente.read_bytes()).hexdigest(),
                                "bytes": fuente.stat().st_size, "records": 1}}), encoding="utf-8")
        return previo

    def test_manifiesto_previo_con_id_viejo_no_se_reutiliza(self):
        from herramientas.preparar_fuente_electoral import validate_previous
        with tempfile.TemporaryDirectory() as td:
            raiz = Path(td)
            self.assertIsNone(validate_previous(self._paquete(raiz, territorio_ids.tabla()["aut11"].id_legacy), "aut11", "2025"))
            self.assertIsNotNone(validate_previous(self._paquete(raiz, "aut11"), "aut11", "2025"))


class ReconciliacionReconoceNoHabilita(unittest.TestCase):
    """SOLO_LECTURA_RECONCILIACION: una huella sellada con el id viejo se RECONOCE, pero nunca habilita reuso."""

    @classmethod
    def setUpClass(cls):
        cls.raiz = _raiz_temporal()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.raiz.parent, ignore_errors=True)

    def _sellar_con_id_viejo(self, tid: str) -> tuple[dict, str]:
        st = _fila(self.raiz, tid)["editions"]["2025"]
        prep = st["preparation_evidence"]
        recibo_path = self.raiz / prep["receipt_path"]
        recibo = json.loads(recibo_path.read_text(encoding="utf-8"))
        viejo = territorio_ids.tabla()[tid].id_legacy
        sellada = territorial_identity(
            territory_id=viejo, edition="2025", population_year=recibo["population_year"],
            section_year=recibo["section_year"], package_sha256=recibo["package_sha256"],
            compatibility_identity_sha256=recibo["compatibility_identity_sha256"])["territorial_identity_sha256"]
        return {**recibo, "territorial_identity_sha256": sellada}, sellada

    def test_reconoce_la_huella_vieja(self):
        recibo, sellada = self._sellar_con_id_viejo("aut11")
        r = territorial_identity(territory_id="aut11", edition="2025", population_year=recibo["population_year"],
                                 section_year=recibo["section_year"], package_sha256=recibo["package_sha256"],
                                 compatibility_identity_sha256=recibo["compatibility_identity_sha256"], esperado=sellada)
        self.assertEqual(r["territorial_identity_sha256"], sellada)
        self.assertNotEqual(r["territory_id"], "aut11")

    def test_no_habilita_reuso_de_la_fuente(self):
        tid = "aut11"
        recibo, sellada = self._sellar_con_id_viejo(tid)
        st = _fila(self.raiz, tid)["editions"]["2025"]
        rel = st["preparation_evidence"]["receipt_path"]
        original = (self.raiz / rel).read_text(encoding="utf-8")
        try:
            (self.raiz / rel).write_text(json.dumps(recibo), encoding="utf-8")
            cat = yaml.safe_load((self.raiz / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
            fila = next(r for r in cat["territories"] if r["territory_id"] == tid)
            fila["editions"]["2025"]["preparation_evidence"]["territorial_identity_sha256"] = sellada
            cat_path = self.raiz / "configuracion/catalogo_preparacion.yaml"
            cat_original = cat_path.read_text(encoding="utf-8")
            cat_path.write_text(yaml.safe_dump(cat, allow_unicode=True, sort_keys=False), encoding="utf-8")
            try:
                c = rpl._territorial_candidate(self.raiz, tid, "2025", fila["editions"]["2025"]["preparation_evidence"],
                                               recibo["population_year"], recibo["section_year"])
                self.assertFalse(c.get("reusable"), c)
                with self.assertRaises(consumir.PreparedPairExecutionBlock):
                    consumir.validate_territorial_receipt(root_dir=self.raiz, territory=tid, edition="2025")
            finally:
                cat_path.write_text(cat_original, encoding="utf-8")
        finally:
            (self.raiz / rel).write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
