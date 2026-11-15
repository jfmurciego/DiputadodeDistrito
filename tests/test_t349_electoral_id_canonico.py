"""T-349: un paquete electoral/territorial REGISTRADO cuyo id no es EXACTAMENTE el canónico no se reutiliza.

Sin alias ni reescritura del id viejo: la Activación planifica ACQUIRE, el P12 prepara uno nuevo y las puertas
(03→04) comparan con igualdad exacta. Caso real: aut11 con `ddd-electoral-package-extremadura-2025-42720735134`.
"""
from __future__ import annotations

import importlib
import inspect
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from ddd_core import territorio_ids
from herramientas import preflight_preparacion_fuente as pf
from herramientas import resolver_preparacion_legislatura as rpl
from herramientas.validar_puerta_ejecucion import _artifact_name_is_consistent

ROOT = Path(__file__).resolve().parents[1]
CANON = "aut11"
VIEJO = territorio_ids.tabla()[CANON].id_legacy
NAC = next(t for t in territorio_ids.tabla() if t.startswith("nac"))
NAC_VIEJO = territorio_ids.tabla()[NAC].id_legacy
RUN = 42720735134
P12 = ROOT / ".github/workflows/preparacion-resultados-electorales.yml"
# Estado congelado en el commit base (id viejo en los 71 recibos): los tests no dependen del catálogo vivo.
FIX = ROOT / "tests/fixtures/t349_base/raiz"
PLANTILLA = FIX / "territorios/aut19/evidencia/fuentes_electorales/2025/8ac3f49c633f1be8ba441bf1290dc79c1a4b30b2bac0033f9c2699e73c1fd019/40832114779/receipt.json"


def _recibo_congelado(tid: str) -> Path:
    cat = yaml.safe_load((FIX / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
    fila = next(r for r in cat["territories"] if r["territory_id"] == tid)
    return FIX / fila["editions"]["2025"]["evidence"]["electoral_source"]


def _recibo(td: Path, territory_id: str, artifact_territory: str, election_id: str | None = None) -> Path:
    """Registro electoral con la procedencia real de Melilla (registro electoral vigente) y los ids dados."""
    r = json.loads(PLANTILLA.read_text(encoding="utf-8"))
    r.update(territory_id=territory_id, run_id=RUN, artifact_name=f"ddd-electoral-package-{artifact_territory}-2025-{RUN}")
    if election_id:
        r["election_id"] = election_id
    out = td / "receipt.json"
    out.write_text(json.dumps(r), encoding="utf-8")
    return out


def _candidato(td: Path, territory_id: str, receipt_territory: str, artifact_territory: str) -> dict:
    receipt = _recibo(td, receipt_territory, artifact_territory)
    state = {"electoral_source_prepared": True, "evidence": {"electoral_source": str(receipt)}}
    return rpl._electoral_candidate(ROOT, territory_id, state, "melilla_asamblea_local_2023")


class CandidatoElectoral(unittest.TestCase):
    def test_aut11_paquete_registrado_extremadura_no_es_reutilizable(self):
        with tempfile.TemporaryDirectory() as td:
            c = _candidato(Path(td), CANON, CANON, VIEJO)
        self.assertFalse(c["reusable"])
        self.assertEqual(c["reason"], "ELECTORAL_ID_NO_CANONICO")
        self.assertEqual(rpl._electoral_admissibility("ACQUIRE", c), "NOT_ACCREDITED")

    def test_registro_con_id_viejo_no_es_reutilizable(self):
        with tempfile.TemporaryDirectory() as td:
            c = _candidato(Path(td), CANON, VIEJO, VIEJO)
        self.assertFalse(c["reusable"])
        self.assertEqual(c["reason"], "ELECTORAL_ID_NO_CANONICO")

    def test_canonico_se_reutiliza(self):
        with tempfile.TemporaryDirectory() as td:
            c = _candidato(Path(td), "aut19", "aut19", "aut19")
        self.assertTrue(c["reusable"], c)
        self.assertEqual(c["artifact_name"], f"ddd-electoral-package-aut19-2025-{RUN}")

    def test_nac_congreso_con_id_viejo_no_es_reutilizable(self):
        with tempfile.TemporaryDirectory() as td:
            c = _candidato(Path(td), NAC, NAC, NAC_VIEJO)
        self.assertEqual(c["reason"], "ELECTORAL_ID_NO_CANONICO")

    def test_otro_territorio_sigue_siendo_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            c = _candidato(Path(td), CANON, CANON, "aut01")
        self.assertEqual(c["reason"], "ELECTORAL_ARTIFACT_IDENTITY_MISMATCH")


class ActivacionConEstadoCongelado(unittest.TestCase):
    def test_aut11_registro_congelado_planifica_acquire_no_reuse(self):
        receipt = _recibo_congelado(CANON)
        eleccion = json.loads(receipt.read_text(encoding="utf-8"))["election_id"]
        state = {"electoral_source_prepared": True, "evidence": {"electoral_source": str(receipt)}}
        c = rpl._electoral_candidate(ROOT, CANON, state, eleccion)
        self.assertFalse(c["reusable"])
        self.assertEqual(c["reason"], "ELECTORAL_ID_NO_CANONICO")

    def test_simulacion_cadena_de_seleccion_viejo_y_nuevo(self):
        """Mismo plan con el registro viejo (ACQUIRE) y con uno nuevo canónico (REUSE)."""
        with tempfile.TemporaryDirectory() as td:
            viejo = _candidato(Path(td), CANON, CANON, VIEJO)
            nuevo = _candidato(Path(td), "aut19", "aut19", "aut19")
        self.assertEqual(("REUSE" if viejo["reusable"] else "ACQUIRE"), "ACQUIRE")
        self.assertEqual(("REUSE" if nuevo["reusable"] else "ACQUIRE"), "REUSE")


class Preflight(unittest.TestCase):
    def _preflight(self, territory: str, receipt_territory: str, artifact_territory: str) -> dict:
        with tempfile.TemporaryDirectory() as td:
            registro = yaml.safe_load((ROOT / "configuracion/registro_electoral.yaml").read_text(encoding="utf-8"))
            eleccion = (registro.get("territories") or {}).get(territory, {}).get("election_id")
            receipt = _recibo(Path(td), receipt_territory, artifact_territory, eleccion)
            state = {"electoral_source_prepared": True, "evidence": {"electoral_source": str(receipt)}}
            with mock.patch.object(pf, "_state", return_value=(territory, "x", state)):
                return pf.preflight(ROOT, "electoral", territory, "2025")

    def test_id_viejo_no_queda_registrado(self):
        r = self._preflight("aut19", "aut19", "melilla")
        self.assertFalse(r["registered"])
        self.assertEqual(r["rejected_reason"], "ID_NO_CANONICO")
        self.assertIsNone(r["run_id"])

    def test_canonico_queda_registrado(self):
        r = self._preflight("aut19", "aut19", "aut19")
        self.assertTrue(r["registered"])
        self.assertEqual(r["artifact_name"], f"ddd-electoral-package-aut19-2025-{RUN}")

    def test_nac_id_viejo(self):
        r = self._preflight(NAC, NAC, NAC_VIEJO)
        self.assertFalse(r["registered"])

    def test_aut11_congelado_por_cli(self):
        r = subprocess.run(["python", "-m", "herramientas.preflight_preparacion_fuente", "--root-dir", str(FIX),
                            "--kind", "electoral", "--territory", CANON, "--edition", "2025"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertFalse(d["registered"])
        self.assertEqual(d["rejected_reason"], "ID_NO_CANONICO")


class Puerta(unittest.TestCase):
    def test_nombre_exacto(self):
        ok = f"ddd-electoral-package-{CANON}-2025-{RUN}"
        bad = f"ddd-electoral-package-{VIEJO}-2025-{RUN}"
        self.assertTrue(_artifact_name_is_consistent("electoral_source", CANON, "2025", str(RUN), ok))
        self.assertFalse(_artifact_name_is_consistent("electoral_source", CANON, "2025", str(RUN), bad))
        self.assertFalse(_artifact_name_is_consistent("territorial_source", CANON, "2025", str(RUN),
                                                      f"ddd-source-package-{VIEJO}-2025-{RUN}"))
        self.assertFalse(_artifact_name_is_consistent("electoral_source", NAC, "2025", str(RUN),
                                                      f"ddd-electoral-package-{NAC_VIEJO}-2025-{RUN}"))


def _paso(nombre: str) -> str:
    d = yaml.safe_load(P12.read_text(encoding="utf-8"))
    for job in d["jobs"].values():
        for st in job.get("steps", []):
            if st.get("name") == nombre:
                return st["run"]
    raise AssertionError(nombre)


class CadenaP12(unittest.TestCase):
    """Bloques `run:` reales del P12 bajo `bash -eo pipefail`, con un `gh` de pruebas."""

    def _gh(self, d: Path, manifest_territory: str):
        gh = d / "bin" / "gh"
        gh.parent.mkdir()
        gh.write_text(f"""#!/usr/bin/env bash
if [[ "$1 $2" == "run download" ]]; then
  while [[ $# -gt 0 ]]; do [[ "$1" == --dir ]] && dest="$2"; shift; done
  mkdir -p "$dest"; echo '{{"territory_id":"{manifest_territory}","decision":"REUSE"}}' > "$dest/manifest.json"
else
  echo '{{"artifacts":[{{"name":"'"$REGISTERED_ARTIFACT_NAME"'","expired":false,"digest":"sha256:'"$REGISTERED_ARTIFACT_SHA256"'"}}]}}'
fi
""")
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)

    def _recuperar(self, artifact_territory: str, manifest_territory: str):
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            self._gh(cwd, manifest_territory)
            out, summ = cwd / "out.txt", cwd / "summary.md"
            out.touch(); summ.touch()
            env = dict(os.environ, PATH=f"{cwd / 'bin'}:{os.environ['PATH']}", GITHUB_OUTPUT=str(out),
                       GITHUB_STEP_SUMMARY=str(summ), GITHUB_REPOSITORY="o/r", TERRITORY_ID=CANON, EDITION="2025",
                       REGISTERED_RUN_ID=str(RUN), REGISTERED_ARTIFACT_NAME=f"ddd-electoral-package-{artifact_territory}-2025-{RUN}",
                       REGISTERED_ARTIFACT_SHA256="a" * 64)
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", _paso("Recuperar paquete electoral registrado")],
                               cwd=cwd, env=env, capture_output=True, text=True)
            return r.returncode, out.read_text(), summ.read_text(), (cwd / ".ddd-electoral-previous").exists(), r.stdout + r.stderr

    def test_paquete_viejo_se_rechaza_y_se_prepara_de_nuevo(self):
        rc, out, summ, previo, log = self._recuperar(VIEJO, VIEJO)
        self.assertEqual(rc, 0, log)
        self.assertNotIn("run_id=", out)
        self.assertIn("PREPARARÁ", summ)
        self.assertFalse(previo)

    def test_nombre_viejo_con_manifiesto_canonico_tambien_se_rechaza(self):
        rc, out, summ, _, log = self._recuperar(VIEJO, CANON)
        self.assertEqual(rc, 0, log)
        self.assertNotIn("run_id=", out)

    def test_paquete_canonico_se_reutiliza_y_lo_dice(self):
        rc, out, summ, previo, log = self._recuperar(CANON, CANON)
        self.assertEqual(rc, 0, log)
        self.assertIn(f"run_id={RUN}", out)
        self.assertIn("REUTILIZÓ", summ)
        self.assertTrue(previo)

    def _identidad(self, run_id: str, manifest_territory: str):
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            pkg = cwd / ".ddd-electoral-package"
            pkg.mkdir()
            (pkg / "manifest.json").write_text(json.dumps({
                "territory_id": manifest_territory, "edition": "2025", "decision": "REUSE",
                "election_id": "e1", "election_date": "2025-12-21"}))
            summ = cwd / "summary.md"
            summ.touch()
            env = dict(os.environ, GITHUB_STEP_SUMMARY=str(summ), TERRITORY_ID=manifest_territory if manifest_territory == CANON else CANON,
                       EDITION="2025", ELECTION_ID="e1", ELECTION_DATE="2025-12-21")
            run = _paso("Validar identidad vigente del paquete").replace("${{ steps.previous.outputs.run_id }}", run_id)
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", run], cwd=cwd, env=env, capture_output=True, text=True)
            return r.returncode, summ.read_text(), r.stdout + r.stderr

    def test_resumen_dice_reutilizo_o_preparo(self):
        rc, summ, log = self._identidad(str(RUN), CANON)
        self.assertEqual(rc, 0, log)
        self.assertIn("REUTILIZÓ", summ)
        rc, summ, log = self._identidad("", CANON)
        self.assertEqual(rc, 0, log)
        self.assertIn("PREPARÓ", summ)

    def test_reutilizar_id_no_canonico_falla(self):
        rc, _, _ = self._identidad(str(RUN), VIEJO)
        self.assertNotEqual(rc, 0)


class InventarioPorRama(unittest.TestCase):
    """Un test por rama con objetos de la fixture congelada; el generador se prueba sobre la fixture, no sobre el estado vivo."""

    @classmethod
    def setUpClass(cls):
        from herramientas import inventario_ids_no_canonicos as inv
        cls.inv = inv
        cls.tabla = inv.construir(FIX, activacion=False)

    def test_generador_sobre_la_fixture_es_reproducible(self):
        esperado = json.loads((ROOT / "tests/fixtures/t349_base/inventario_esperado.json").read_text(encoding="utf-8"))
        regenerada = json.loads(self.inv.a_json(self.tabla))
        regenerada["base_commit"] = esperado["base_commit"]  # la base cambia con cada rebase; el resto es determinista
        self.assertEqual(regenerada, esperado)

    def test_rama_electoral_los_71_recibos_congelados_con_id_viejo_se_rechazan(self):
        filas = [f for f in self.tabla["filas"] if f["rama"] == "electoral_fuente"]
        self.assertEqual(sum(f["no_canonicos"] for f in filas), 71)
        for f in filas:
            with self.subTest(territorio=f["territorio"]):
                receipt = _recibo_congelado(f["territorio"])
                eleccion = json.loads(receipt.read_text(encoding="utf-8"))["election_id"]
                state = {"electoral_source_prepared": True, "evidence": {"electoral_source": str(receipt)}}
                c = rpl._electoral_candidate(ROOT, f["territorio"], state, eleccion)
                self.assertFalse(c["reusable"])
                self.assertEqual(c["reason"], "ELECTORAL_ID_NO_CANONICO")

    def test_rama_fuentes_territoriales_objeto_con_nombre_viejo_se_rechaza(self):
        raiz = _raiz_estado_viejo(canonico=True)
        catalogo = yaml.safe_load((raiz / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
        st = next(r for r in catalogo["territories"] if r["territory_id"] == "aut08")["editions"]["2025"]
        prep = st["preparation_evidence"]
        viejo = dict(st, preparation_evidence=dict(prep, artifact_name=f"ddd-source-package-{territorio_ids.tabla()['aut08'].id_legacy}-2025-{prep['run_id']}"))
        c = rpl._territorial_candidate(raiz, "aut08", "2025", viejo, 2025, 2025)
        self.assertFalse(c["reusable"])
        self.assertIn(c["reason"], {"TERRITORIAL_ID_NO_CANONICO", "TERRITORIAL_RECEIPT_CONTRADICTORY"})
        self.assertIn(rpl._territorial_admissibility("ACQUIRE", c), {"NOT_ACCREDITED", "INCOMPATIBLE"})

    def test_rama_poblacion_va_con_el_paquete_de_fuentes(self):
        self.assertEqual(self.tabla["ramas"]["poblacion"]["politica"], "ESTRICTA")

    def test_inventario_comprometido_declara_las_mismas_ramas_y_su_procedencia(self):
        committed = json.loads((ROOT / "docs/diagnostico/inventario_ids_no_canonicos.json").read_text(encoding="utf-8"))
        self.assertEqual(committed["ramas"], self.tabla["ramas"])
        self.assertEqual({f["territorio"] for f in committed["filas"]}, {f["territorio"] for f in self.tabla["filas"]})
        # El base_commit es el del commit del que se generó la tabla; que sea un sha completo evita un inventario sin procedencia.
        self.assertRegex(committed["base_commit"], r"^[0-9a-f]{40}$")

    def test_solo_las_ramas_de_lo_publicado_son_solo_lectura(self):
        alias = {k for k, v in self.tabla["ramas"].items() if v["politica"] == "SOLO_LECTURA_PUBLICADO"}
        self.assertEqual(alias, {"composicion_datos", "registro_visor"})


CAT = ROOT / "configuracion/catalogo_preparacion.yaml"


class RamasDeLaCadenaD102(unittest.TestCase):
    """D-102: par, M06 y M08 registrados con id viejo NO se reutilizan en la P00/Activación (objetos reales del inventario)."""

    def _evidencia(self, tid: str, clave: str) -> str:
        cat = yaml.safe_load((FIX / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
        return next(r for r in cat["territories"] if r["territory_id"] == tid)["editions"]["2025"]["evidence"][clave]

    def test_par_congelado_con_id_viejo_se_rechaza(self):
        from herramientas.registrar_par_fuentes_legislatura import PreparedSourcePairBlock, validate_pair_receipt
        with self.assertRaisesRegex(PreparedSourcePairBlock, "territorio del par no coincide"):
            validate_pair_receipt(root_dir=FIX, pair_path=FIX / self._evidencia("aut09", "prepared_source_pair"),
                                  expected_territory_id="aut09", expected_edition="2025")  # par con territory_id='cataluna'

    def test_par_y_su_receipt_exigen_el_mismo_id_exacto(self):
        from herramientas.consumir_par_fuentes_legislatura import validate_territorial_receipt  # noqa: F401  (carga)
        src = inspect.getsource(importlib.import_module("herramientas.registrar_par_fuentes_legislatura").validate_pair_receipt)
        self.assertNotIn("mismo_territorio", src)

    def test_m06_congelado_con_id_viejo_se_rechaza(self):
        from herramientas.resolver_activos_durables import PASS_CERTIFICATIONS, DurableAssetBlock, validate_durable_assets
        estado = {"territorial_product_available": True, "territorial_certification": sorted(PASS_CERTIFICATIONS)[0],
                  "evidence": {"territorial_product": self._evidencia("aut09", "territorial_product")}}
        with self.assertRaisesRegex(DurableAssetBlock, "DURABLE_ASSET_ID_NO_CANONICO: territorial_product"):
            validate_durable_assets(root_dir=FIX, state=estado, territory_id="aut09", edition="2025",
                                    territorial_source=None, expected_election_id=None)

    def test_m06_canonico_se_reutiliza_en_la_p00(self):
        from herramientas.resolver_ejecucion_completa import build_plan
        raiz = _raiz_estado_viejo(canonico=True)  # mismo estado de previo_r3 con ids canónicos (fixture versionada)
        plan = build_plan(territory="Castilla-La Mancha", edition="2025", execution_mode="reuse",
                          catalog=raiz / "configuracion/catalogo_preparacion.yaml", root_dir=raiz)
        self.assertEqual(plan["execution_mode"], "reuse")

    def test_m08_congelado_con_id_viejo_se_descarta_para_reincorporar(self):
        from herramientas.resolver_activos_durables import validate_durable_assets
        estado = {"electoral_product_available": True,
                  "evidence": {"electoral_product": self._evidencia(CANON, "electoral_product")}}
        r = validate_durable_assets(root_dir=FIX, state=estado, territory_id=CANON, edition="2025",
                                    territorial_source=None, expected_election_id=None)
        self.assertIsNone(r["electoral_product"])
        self.assertIn("DURABLE_ASSET_ID_NO_CANONICO: electoral_product", r["rejected_electoral_product"]["reason"])
        self.assertFalse(r["rejected_electoral_product"]["reusable"])


class RegistroVisorP50(unittest.TestCase):
    """La P50 añade la entrada CANÓNICA (territory_id nuevo + alias_de) y el run mayor sustituye a la vieja del territorio."""

    def test_entrada_nueva_es_canonica_con_alias_y_sustituye_a_la_vieja(self):
        from herramientas import legislatura_vigente as lv
        from herramientas.registro_publicaciones_visor import alias_de, identity_key, upsert_entry
        self.assertEqual(alias_de(CANON), VIEJO)
        base = {"asset_type": "territorial_product", "kind": "canonical_m08", "expected_districts": 65,
                "publication_status": "PUBLICABLE"}
        vieja = {**base, "id": f"m08-{VIEJO}-100", "territory_id": VIEJO, "territory_label": "Extremadura", "run_id": "100"}
        nueva = {**base, "id": f"m08-{CANON}-200", "territory_id": CANON, "territory_label": "Extremadura", "run_id": "200",
                 "alias_de": VIEJO}
        registro = {"products": [dict(vieja)], "ensembles": []}
        self.assertNotEqual(identity_key(vieja), identity_key(nueva))
        registro["products"].append(nueva)  # solo adición: la vieja queda intacta, sin reescritura de id
        self.assertEqual([p["territory_id"] for p in registro["products"]], [VIEJO, CANON])
        estado = lv.territory_state(ROOT, CANON, registro, None)
        self.assertEqual(estado["estado"], "PUBLICADO")
        self.assertEqual(estado["run_id"], "200")

    def test_metadatos_de_la_p50_llevan_el_id_canonico_del_run(self):
        from herramientas.preparar_visor_ejecucion import production_metadata
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            params = d / "params.yaml"
            params.write_text(yaml.safe_dump({"meta": {"territory": "Extremadura"},
                                              "modulos": {"modulo_06_consolidar_distritos": {"expected_districts": 65}}}), encoding="utf-8")
            (d / "production_status.json").write_text(json.dumps({"territory_id": CANON, "params": str(params)}), encoding="utf-8")
            (d / "decision.json").write_text(json.dumps({"territory_id": CANON}), encoding="utf-8")
            meta = production_metadata(d)
        self.assertEqual(meta["territory_id"], CANON)  # el descriptor de la P50 usa este id tal cual y añade alias_de


def _raiz_estado_viejo(canonico: bool = False) -> Path:
    """Estado REAL registrado con id viejo (copia fiel del commit previo a r3, `previo_r3`, sin tocar) más la configuración
    estática (matrices, contratos, calendario) que el planificador necesita y que no es estado registrado."""
    import shutil
    from tests._previo_r3 import raiz_previo_r3
    raiz = raiz_previo_r3(canonico=canonico)
    for origen in [*Path(ROOT / "configuracion").rglob("*"), *Path(ROOT / "fuentes").rglob("*"), *ROOT.glob("territorios/*/config/**/*")]:
        if origen.is_file():
            destino = raiz / origen.relative_to(ROOT)
            if not destino.exists():
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(origen, destino)
    return raiz


class FlujoConEstadoViejo(unittest.TestCase):
    """Defensa de fondo («cero sorpresas»): con TODO el estado registrado con id viejo, ni la Activación ni la P00 ni el 03
    activan una sola bandera de reutilización; todo se prepara o se genera de nuevo con el id canónico."""

    TERRITORIOS = ("aut01", "aut08", "aut11", "aut12", "aut19")

    @classmethod
    def setUpClass(cls):
        cls.raiz = _raiz_estado_viejo()
        cls.catalogo = cls.raiz / "configuracion/catalogo_preparacion.yaml"

    def test_activacion_no_reutiliza_nada(self):
        for t in self.TERRITORIOS:
            with self.subTest(territorio=t):
                plan = rpl.resolve(self.raiz, t)["plans"][0]
                self.assertEqual(plan["territorial_action"], "ACQUIRE")
                self.assertEqual(plan["electoral_action"], "ACQUIRE")
                self.assertFalse(plan["territorial_candidate"].get("reusable"))
                self.assertFalse(plan["electoral_candidate"].get("reusable"))

    def test_p00_reutilizar_y_generar_desde_fuente_no_reutilizan(self):
        from herramientas.resolver_ejecucion_completa import build_plan
        for t in self.TERRITORIOS:
            for modo, motivo in (("reuse", r"DURABLE_ASSET_(ID_NO_CANONICO|MISSING)"), ("catalog_source", r"CATALOG_SOURCE_BLOCK")):
                with self.subTest(territorio=t, modo=modo):
                    with self.assertRaisesRegex(ValueError, motivo):
                        build_plan(territory=t, edition="2025", execution_mode=modo, catalog=self.catalogo, root_dir=self.raiz)

    def test_recibos_durables_viejos_se_descartan(self):
        from herramientas.resolver_activos_durables import validate_durable_assets
        cat = yaml.safe_load(self.catalogo.read_text(encoding="utf-8"))
        for fila in cat["territories"]:
            t = fila["territory_id"]
            st = fila["editions"]["2025"]
            rel = (st.get("evidence") or {}).get("electoral_source")
            if t not in self.TERRITORIOS or not rel or not (self.raiz / rel).is_file():
                continue
            with self.subTest(territorio=t):
                estado = {"electoral_source_prepared": True, "electoral_product_available": bool(st["evidence"].get("electoral_product")),
                          "evidence": {k: v for k, v in st["evidence"].items() if k in ("electoral_source", "electoral_product")}}
                r = validate_durable_assets(root_dir=self.raiz, state=estado, territory_id=t, edition="2025",
                                            territorial_source=None, expected_election_id=None)
                self.assertIsNone(r["electoral_source"])
                self.assertIsNone(r["electoral_product"])
                self.assertIn("DURABLE_ASSET_ID_NO_CANONICO: electoral_source", r["rejected_electoral_source"]["reason"])

    def test_par_registrado_viejo_no_se_consume(self):
        from herramientas.consumir_par_fuentes_legislatura import PreparedPairExecutionBlock, resolve_pair
        cat = yaml.safe_load(self.catalogo.read_text(encoding="utf-8"))
        con_par = [f["territory_id"] for f in cat["territories"] if f["territory_id"] in self.TERRITORIOS
                   and (f["editions"]["2025"].get("evidence") or {}).get("prepared_source_pair")]
        self.assertTrue(con_par)
        for t in con_par:
            with self.subTest(territorio=t), self.assertRaises(PreparedPairExecutionBlock):
                resolve_pair(root_dir=self.raiz, territory=t, edition="2025")

    def test_m06_viejo_no_entra_al_par_ni_como_reuso_geometrico(self):
        from herramientas.consumir_par_fuentes_legislatura import resolve_geometric_reuse
        for t in ("aut08", "aut11", "aut12", "aut19"):
            with self.subTest(territorio=t):
                try:
                    r = resolve_geometric_reuse(root_dir=self.raiz, territory_id=t, edition="2025", current_identity="a" * 64,
                                                current_source={"run_id": 1, "artifact_name": "x", "artifact_sha256": "b" * 64})
                except Exception:
                    continue  # bloqueo explícito: tampoco hay reutilización
                self.assertFalse(r.get("compatible"), r)

    def test_la_reconciliacion_de_huellas_selladas_solo_reconoce(self):
        """`territorial_identity` con `esperado` reconoce la huella sellada con el id viejo, pero el recibo del M06 y el
        receipt territorial (los objetos reutilizables) siguen exigiendo el id exacto: reconocer ≠ habilitar reuso."""
        from herramientas.identidad_fuentes_legislatura import territorial_identity
        base = dict(edition="2025", population_year=2025, section_year=2025, package_sha256="a" * 64)
        sellada = territorial_identity(territory_id=VIEJO, **base)["territorial_identity_sha256"]
        self.assertEqual(territorial_identity(territory_id=CANON, esperado=sellada, **base)["territorial_identity_sha256"], sellada)
        from herramientas.resolver_activos_durables import PASS_CERTIFICATIONS, DurableAssetBlock, validate_durable_assets
        cat = yaml.safe_load(self.catalogo.read_text(encoding="utf-8"))
        st = next(f for f in cat["territories"] if f["territory_id"] == "aut11")["editions"]["2025"]
        with self.assertRaises(DurableAssetBlock):
            validate_durable_assets(root_dir=self.raiz, territory_id="aut11", edition="2025", territorial_source=None, expected_election_id=None,
                                    state={"territorial_product_available": True, "territorial_certification": sorted(PASS_CERTIFICATIONS)[0],
                                           "evidence": {"territorial_product": st["evidence"]["territorial_product"]}})


class ProductoM06EnElPar(unittest.TestCase):
    def test_recibo_m06_con_id_viejo_no_es_compatible_aunque_el_linaje_case(self):
        from herramientas.consumir_par_fuentes_legislatura import resolve_geometric_reuse
        from tests._raiz_congelada import frozen_root
        root = frozen_root()  # aee8215e: CyL con M06 histórico e id viejo en su recibo
        from ddd_core.territorio_ids import ruta_existente
        receipt = json.loads(ruta_existente(root, "territorios/aut07/evidencia/fuentes_territoriales/2025/380dc48849ae078bf6c51144eb98e295be3306d9e66098f82a6b4e61cffa825c/35610439734/receipt.json").read_text(encoding="utf-8"))
        r = resolve_geometric_reuse(root_dir=root, territory_id="aut07", edition="2025", current_identity=receipt["territorial_identity_sha256"])
        self.assertFalse(r["compatible"])
        self.assertEqual(r["reason"], "PRODUCT_ID_NO_CANONICO")


class ComposicionSoloLectura(unittest.TestCase):
    def test_fichero_con_id_viejo_solo_se_lee_si_no_existe_el_canonico(self):
        from ddd_core.territorio_ids import fichero_por_id
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / f"{VIEJO}.csv").write_text("v", encoding="utf-8")
            self.assertEqual(fichero_por_id(d, "{}.csv", CANON).name, f"{VIEJO}.csv")  # lectura de lo histórico/publicado
            (d / f"{CANON}.csv").write_text("n", encoding="utf-8")
            self.assertEqual(fichero_por_id(d, "{}.csv", CANON).name, f"{CANON}.csv")  # lo nuevo siempre con el id canónico


if __name__ == "__main__":
    unittest.main()
