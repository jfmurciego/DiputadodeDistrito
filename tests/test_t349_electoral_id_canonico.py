"""T-349: un paquete electoral/territorial REGISTRADO cuyo id no es EXACTAMENTE el canónico no se reutiliza.

Sin alias ni reescritura del id viejo: la Activación planifica ACQUIRE, el P12 prepara uno nuevo y las puertas
(03→04) comparan con igualdad exacta. Caso real: aut11 con `ddd-electoral-package-extremadura-2025-42720735134`.
"""
from __future__ import annotations

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
PLANTILLA = ROOT / "territorios/aut19/evidencia/fuentes_electorales/2025/8ac3f49c633f1be8ba441bf1290dc79c1a4b30b2bac0033f9c2699e73c1fd019/40832114779/receipt.json"


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


class ActivacionConCatalogoVivo(unittest.TestCase):
    def test_aut11_vivo_planifica_acquire_no_reuse(self):
        plan = rpl.resolve(ROOT, "Extremadura")["plans"][0]
        self.assertEqual(plan["territory_id"], CANON)
        self.assertEqual(plan["electoral_action"], "ACQUIRE")
        self.assertEqual(plan["electoral_candidate"]["reason"], "ELECTORAL_ID_NO_CANONICO")

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

    def test_aut11_vivo_por_cli(self):
        r = subprocess.run(["python", "-m", "herramientas.preflight_preparacion_fuente", "--root-dir", ".",
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
    """Un test por rama estricta con objetos reales del repo; la tabla committed se regenera idéntica."""

    @classmethod
    def setUpClass(cls):
        from herramientas import inventario_ids_no_canonicos as inv
        cls.inv = inv
        cls.tabla = inv.construir(ROOT)

    def test_rama_electoral_los_71_registros_reales_con_id_viejo_se_rechazan(self):
        no_canonicos = {f["territorio"] for f in self.tabla["filas"] if f["rama"] == "electoral_fuente" and not f["canonico"]}
        self.assertEqual(len(no_canonicos), 71)
        for a in self.tabla["activacion"]:
            with self.subTest(territorio=a["territorio"]):
                self.assertEqual(a["electoral_action"], "ACQUIRE")

    def test_rama_fuentes_territoriales_objeto_real_con_nombre_viejo_se_rechaza(self):
        catalogo = yaml.safe_load((ROOT / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
        st = next(r for r in catalogo["territories"] if r["territory_id"] == CANON)["editions"]["2025"]
        prep = st["preparation_evidence"]
        viejo = dict(st, preparation_evidence=dict(prep, artifact_name=f"ddd-source-package-{VIEJO}-2025-{prep['run_id']}"))
        c = rpl._territorial_candidate(ROOT, CANON, "2025", viejo, 2025, 2025)
        self.assertFalse(c["reusable"])
        self.assertIn(c["reason"], {"TERRITORIAL_ID_NO_CANONICO", "TERRITORIAL_RECEIPT_CONTRADICTORY"})
        self.assertEqual(rpl._territorial_admissibility("ACQUIRE", c) in {"NOT_ACCREDITED", "INCOMPATIBLE"}, True)

    def test_rama_poblacion_va_con_el_paquete_de_fuentes(self):
        self.assertEqual(self.tabla["ramas"]["poblacion"]["politica"], "ESTRICTA")

    def test_tabla_committed_es_reproducible(self):
        committed = json.loads((ROOT / "docs/diagnostico/inventario_ids_no_canonicos.json").read_text(encoding="utf-8"))
        regenerada = json.loads(json.dumps(self.tabla, ensure_ascii=False))
        regenerada["base_commit"] = committed["base_commit"]  # la base cambia con cada rebase; el resto es determinista
        self.assertEqual(regenerada, committed)

    def test_ramas_con_alias_quedan_listadas(self):
        alias = {k for k, v in self.tabla["ramas"].items() if v["politica"] == "ALIAS"}
        self.assertEqual(alias, {"par_fuentes", "producto_M06", "producto_M08", "composicion_datos", "registro_visor"})


if __name__ == "__main__":
    unittest.main()
