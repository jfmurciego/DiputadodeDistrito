"""T-332: la 03 elige la elección de ENSAYO 2026-11-29 por entrada, sin cambiar la vigente ni persistir."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.evaluar_persistencia_preparacion import resolve_persist_state, terminal_decision
from herramientas.resolver_contrato_minsait_provisional import resolve as resolve_contract
from herramientas.resolver_ensayo_electoral import resolve as resolve_ensayo
from herramientas.resolver_eleccion_vigente import resolve_for_preparation

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "preparacion-resultados-electorales.yml"
# Votos: literales del ZIP oficial Infoelectoral 2023 (configuracion/contratos_infoelectoral.yaml, sha e78fc231…), que el reparto
# a claves de sección 2026 conserva. Secciones y mesas: recuentos del fixture de ensayo (MANIFEST de #801, T-333).
ESPERADO = {
    "nac22": ("congreso_huesca", "02", 285, 401, 117735, "Congreso Huesca"),
    "nac42": ("congreso_soria", "08", 219, 265, 49823, "Congreso Soria"),
    "nac52": ("congreso_melilla", "19", 44, 90, 26925, "Congreso Melilla"),
}


def _resolve_step_script() -> str:
    wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    step = next(s for s in wf["jobs"]["resolver"]["steps"] if s.get("id") == "resolve")
    return step["run"]


class ResolutorEnsayo(unittest.TestCase):
    def test_tres_territorios_dan_la_eleccion_2026_con_contrato_de_ensayo(self):
        for tid, (slug, *_rest) in ESPERADO.items():
            got = resolve_ensayo(tid, ROOT)
            self.assertEqual(got["election_id"], f"{slug}_2026-11-29")
            self.assertEqual(got["election_date"], "2026-11-29")
            self.assertTrue(got["rehearsal"])
            self.assertFalse(got["persist_state"])

    def test_sin_contrato_de_ensayo_o_territorio_desconocido_falla_cerrado(self):
        with self.assertRaises(SystemExit) as c1:
            resolve_ensayo("nac01", ROOT)  # existe en las generales 2026 pero no tiene contrato de ensayo
        self.assertIn("ENSAYO_SIN_CONTRATO", str(c1.exception))
        with self.assertRaises(SystemExit):
            resolve_ensayo("nac99", ROOT)

    def test_la_eleccion_vigente_no_cambia(self):
        for tid, (_s, _c, _se, _p, _v, nombre) in ESPERADO.items():
            row = resolve_for_preparation(nombre, root_dir=ROOT)
            self.assertEqual(row["election_date"], "2023-07-23", tid)
            self.assertTrue(row["election_id"].endswith("_2023-07-23"))


class ContratosDeEnsayo(unittest.TestCase):
    def test_contratos_no_promocionables_y_con_totales_del_zip_oficial(self):
        for tid, (slug, ccaa, secciones, mesas, votos, _n) in ESPERADO.items():
            row = resolve_contract(election_id=f"{slug}_2026-11-29", territory_id=tid, election_date="2026-11-29", root_dir=ROOT)
            self.assertTrue(row["rehearsal"])
            self.assertEqual(row["source_status"], "PROVISIONAL")
            self.assertFalse(row["production_eligible"])
            self.assertFalse(row["promotion_allowed"])
            self.assertNotIn("owner_production_exception", row)
            self.assertEqual(
                (row["expected"]["ccaa"], row["expected"]["provinces"], row["expected"]["sections"],
                 row["expected"]["polling_stations"], row["expected"]["candidate_votes"]),
                (ccaa, 1, secciones, mesas, votos),
            )
            self.assertEqual(row["reconciliation"]["delta_definitive_minus_provisional"], 0)
            self.assertIn("ENSAYO", row["publisher"])

    def test_sha256_es_huella_real_o_pendiente_que_falla_cerrado(self):
        # Mientras no exista el fichero de ensayo (T-333) la huella es PENDIENTE_T333: la 03 sale con exit 53 al compararla.
        for slug in (v[0] for v in ESPERADO.values()):
            raw = yaml.safe_load((ROOT / "configuracion/contratos_minsait_provisionales.yaml").read_text(encoding="utf-8"))
            sha = raw["contracts"][f"{slug}_2026-11-29"]["source_sha256"]
            self.assertTrue(sha == "PENDIENTE_T333" or re.fullmatch(r"[0-9a-f]{64}", sha), sha)

    def test_los_contratos_existentes_no_son_ensayo(self):
        row = resolve_contract(election_id="andalucia_parlamento_2026", territory_id="aut01", election_date="2026-05-17", root_dir=ROOT)
        self.assertFalse(row["rehearsal"])

    def test_un_contrato_de_ensayo_con_excepcion_o_estado_distinto_se_rechaza(self):
        raw = yaml.safe_load((ROOT / "configuracion/contratos_minsait_provisionales.yaml").read_text(encoding="utf-8"))
        base = raw["contracts"]["congreso_huesca_2026-11-29"]
        casos = {
            "estado": {**base, "source_status": "DEFINITIVE"},
            "excepcion": {**base, "owner_production_exception": {"decided_at": "x", "rationale": "x", "evidence": "x", "max_delta_ratio": 1}},
            "elegible": {**base, "production_eligible": True},
        }
        for nombre, row in casos.items():
            with tempfile.TemporaryDirectory() as tmp:
                tmpdir = Path(tmp)
                (tmpdir / "c.yaml").write_text(
                    yaml.safe_dump({"schema": "ddd-minsait-provisional-contracts/1.0", "contracts": {"congreso_huesca_2026-11-29": row}}),
                    encoding="utf-8")
                with self.assertRaises(ValueError, msg=nombre):
                    resolve_contract(election_id="congreso_huesca_2026-11-29", territory_id="nac22", election_date="2026-11-29",
                                     root_dir=tmpdir, contract_path=Path("c.yaml"))


class ResolverSha256(unittest.TestCase):
    def _con_sha(self, sha):
        raw = yaml.safe_load((ROOT / "configuracion/contratos_minsait_provisionales.yaml").read_text(encoding="utf-8"))
        row = {**raw["contracts"]["congreso_huesca_2026-11-29"], "source_sha256": sha}
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        (Path(tmp.name) / "c.yaml").write_text(yaml.safe_dump(
            {"schema": "ddd-minsait-provisional-contracts/1.0", "contracts": {"congreso_huesca_2026-11-29": row}}), encoding="utf-8")
        return resolve_contract(election_id="congreso_huesca_2026-11-29", territory_id="nac22", election_date="2026-11-29",
                                root_dir=Path(tmp.name), contract_path=Path("c.yaml"))

    def test_acepta_64_hex_y_la_marca_pendiente(self):
        self.assertTrue(self._con_sha("a" * 64)["rehearsal"])
        self.assertTrue(self._con_sha("PENDIENTE_T333")["rehearsal"])

    def test_rechaza_cualquier_otra_cadena(self):
        for malo in ("", "abc", "A" * 64, "PENDIENTE", "g" * 64):
            with self.assertRaises(ValueError, msg=malo):
                self._con_sha(malo)


class PersistStateFalse(unittest.TestCase):
    def test_persist_false_no_registra_y_termina_en_exito(self):
        self.assertFalse(resolve_persist_state(False))
        self.assertFalse(resolve_persist_state("false"))
        self.assertEqual(terminal_decision(preparation_result="success", registration_result="skipped", persist_state=False),
                         {"status": "SUCCESS", "reason": "PERSISTENCE_NOT_REQUIRED"})
        self.assertEqual(terminal_decision(preparation_result="failure", registration_result="skipped", persist_state=False)["status"], "FAILURE")
        # Con persistencia obligatoria (por defecto) la ausencia de registro es un fallo.
        self.assertTrue(resolve_persist_state(None))
        self.assertEqual(terminal_decision(preparation_result="success", registration_result="skipped", persist_state=True)["status"], "FAILURE")

    def test_registrar_exige_persistencia_y_elegibilidad(self):
        wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        cond = wf["jobs"]["registrar"]["if"]
        self.assertIn("persist_state == 'true'", cond)
        self.assertIn("production_eligible == 'true'", cond)

    def test_workflow_declara_entrada_y_version(self):
        wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        on = wf.get("on") or wf.get(True)
        self.assertEqual(on["workflow_dispatch"]["inputs"]["eleccion"]["default"], "vigente")
        self.assertIn("ensayo 2026-11-29", on["workflow_dispatch"]["inputs"]["eleccion"]["options"])
        self.assertEqual(on["workflow_call"]["inputs"]["eleccion"]["default"], "vigente")
        self.assertRegex(WORKFLOW.read_text(encoding="utf-8"), r"# VERSIÓN: 1\.0\.15")


@unittest.skipUnless(os.system("command -v jq >/dev/null 2>&1") == 0, "jq no disponible")
class PasoResolverBajoBash(unittest.TestCase):
    """Ejecuta el paso real «resolve» de la 03 bajo `bash -eo pipefail` (lección T-267)."""

    def _run(self, eleccion: str, persist: str = "null") -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            out.touch()
            env = {**os.environ, "TERRITORY": "Congreso Huesca", "EDITION": "2025", "PERSIST_INPUT": persist,
                   "ELECCION": eleccion, "GITHUB_OUTPUT": str(out)}
            proc = subprocess.run(["bash", "-eo", "pipefail", "-c", _resolve_step_script()], cwd=ROOT, env=env,
                                  capture_output=True, text=True)
            pairs = dict(l.split("=", 1) for l in out.read_text(encoding="utf-8").splitlines() if "=" in l)
            return proc.returncode, pairs

    def test_vigente_no_cambia(self):
        rc, out = self._run("vigente")
        self.assertEqual(rc, 0)
        self.assertEqual((out["ensayo"], out["persist_state"], out["election_id"], out["election_date"]),
                         ("false", "true", "congreso_huesca_2023-07-23", "2023-07-23"))

    def test_ensayo_elige_2026_sin_persistir_ni_reutilizar(self):
        rc, out = self._run("ensayo 2026-11-29")
        self.assertEqual(rc, 0)
        self.assertEqual((out["ensayo"], out["persist_state"], out["election_id"], out["election_date"]),
                         ("true", "false", "congreso_huesca_2026-11-29", "2026-11-29"))
        self.assertEqual(out["registered_run_id"], "")
        self.assertEqual(out["registered_artifact_sha256"], "")

    def test_ensayo_fuerza_persistencia_falsa_aunque_se_pida_true(self):
        rc, out = self._run("ensayo 2026-11-29", persist="true")
        self.assertEqual(rc, 0)
        self.assertEqual(out["persist_state"], "false")

    def test_valor_desconocido_falla(self):
        rc, _ = self._run("ensayo 2027")
        self.assertEqual(rc, 42)


@unittest.skipUnless(os.system("command -v jq >/dev/null 2>&1") == 0, "jq no disponible")
class AdaptadorYEntradaVacia(unittest.TestCase):
    def _modo(self, election_id: str, territory_id: str, election_date: str, ensayo: str) -> tuple[int, str, str]:
        wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        script = next(s for s in wf["jobs"]["electorales"]["steps"] if s.get("id") == "mode")["run"]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            out.touch()
            proc = subprocess.run(["bash", "-eo", "pipefail", "-c", script], cwd=ROOT, capture_output=True, text=True,
                                  env={**os.environ, "ELECTION_ID": election_id, "TERRITORY_ID": territory_id,
                                       "ELECTION_DATE": election_date, "ENSAYO": ensayo, "GITHUB_OUTPUT": str(out)})
            try:
                return proc.returncode, out.read_text(encoding="utf-8"), proc.stdout + proc.stderr
            finally:
                for f in (".ddd-special-acquisition.json", ".ddd-infoelectoral-contract.json", ".ddd-minsait-contract.json"):
                    (ROOT / f).unlink(missing_ok=True)

    def test_ensayo_con_adaptador_distinto_de_minsait_sale_con_57(self):
        # La elección de 2023 de Huesca resuelve a infoelectoral_mesas: en ensayo es un error (exit 57).
        rc, _out, log = self._modo("congreso_huesca_2023-07-23", "nac22", "2023-07-23", "true")
        self.assertEqual(rc, 57, log)
        # Sin ensayo, el mismo caso sigue resolviendo infoelectoral_mesas (producción no cambia).
        rc, out, _ = self._modo("congreso_huesca_2023-07-23", "nac22", "2023-07-23", "false")
        self.assertEqual(rc, 0)
        self.assertIn("adapter=infoelectoral_mesas", out)

    def test_ensayo_con_la_eleccion_2026_resuelve_minsait_provisional(self):
        rc, out, log = self._modo("congreso_huesca_2026-11-29", "nac22", "2026-11-29", "true")
        self.assertEqual(rc, 0, log)
        self.assertIn("adapter=minsait_provisional", out)

    def test_eleccion_vacia_en_workflow_call_sigue_el_flujo_de_produccion(self):
        script = _resolve_step_script()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            out.touch()
            proc = subprocess.run(["bash", "-eo", "pipefail", "-c", script], cwd=ROOT, capture_output=True, text=True,
                                  env={**os.environ, "TERRITORY": "Congreso Huesca", "EDITION": "2025", "PERSIST_INPUT": "null",
                                       "ELECCION": "", "GITHUB_OUTPUT": str(out)})
            pares = dict(l.split("=", 1) for l in out.read_text(encoding="utf-8").splitlines() if "=" in l)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((pares["ensayo"], pares["persist_state"], pares["election_id"]), ("false", "true", "congreso_huesca_2023-07-23"))


@unittest.skipUnless(os.system("command -v jq >/dev/null 2>&1") == 0, "jq no disponible")
class TerminalDelEnsayo(unittest.TestCase):
    """El paso «Aplicar decisión electoral» real, bajo `bash -eo pipefail`: un ensayo válido sale en verde; producción no cambia."""

    def _run(self, *, ensayo: str, eligible: str, status: str, validation: str = "READY_PACKAGE", decision: str = "ACQUIRE",
             allow_gap: str = "false", source_class: str = "rehearsal") -> tuple[int, dict, str]:
        wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        script = next(s for s in wf["jobs"]["electorales"]["steps"] if s.get("id") == "outcome")["run"]
        for expr, value in (("steps.policy.outputs.production_eligible", eligible), ("steps.policy.outputs.source_status", status),
                            ("inputs.allow_source_gap_success", allow_gap)):
            script = script.replace("${{ %s }}" % expr, value)
        self.assertNotIn("${{", script)
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / ".ddd-electoral-package"
            (pkg / "evidence").mkdir(parents=True)
            (pkg / "manifest.json").write_text(json.dumps({"decision": decision, "selected_source": {"source_class": source_class}}), encoding="utf-8")
            (pkg / "evidence" / "validacion_preparacion.json").write_text(json.dumps({"decision": validation}), encoding="utf-8")
            out = Path(tmp) / "out"
            out.touch()
            proc = subprocess.run(["bash", "-eo", "pipefail", "-c", script], cwd=tmp, capture_output=True, text=True,
                                  env={**os.environ, "ENSAYO": ensayo, "GITHUB_OUTPUT": str(out)})
            text = out.read_text(encoding="utf-8")
            return proc.returncode, dict(l.split("=", 1) for l in text.splitlines() if "=" in l and "<<" not in l), proc.stdout

    def test_ensayo_correcto_sale_en_verde_y_no_es_ready(self):
        rc, out, stdout = self._run(ensayo="true", eligible="false", status="PROVISIONAL")
        self.assertEqual(rc, 0)
        self.assertEqual(out["electoral_outcome"], "ENSAYO_OK")
        self.assertIn("ENSAYO correcto", stdout)

    def test_ensayo_con_paquete_no_valido_sigue_fallando(self):
        self.assertEqual(self._run(ensayo="true", eligible="false", status="PROVISIONAL", validation="BLOCK")[0], 42)
        self.assertEqual(self._run(ensayo="true", eligible="false", status="PROVISIONAL", decision="BLOCK")[0], 42)
        self.assertEqual(self._run(ensayo="true", eligible="false", status="DEFINITIVE")[0], 42)

    def test_ensayo_sin_source_class_rehearsal_en_el_manifiesto_falla(self):
        self.assertEqual(self._run(ensayo="true", eligible="false", status="PROVISIONAL", source_class="provisional_mirror")[0], 42)
        self.assertEqual(self._run(ensayo="true", eligible="false", status="PROVISIONAL", source_class="")[0], 42)

    def test_produccion_no_cambia(self):
        # No ensayo y no elegible: sigue siendo bloqueo (exit 42), igual que antes.
        self.assertEqual(self._run(ensayo="false", eligible="false", status="PROVISIONAL")[0], 42)
        rc, out, _ = self._run(ensayo="false", eligible="true", status="PROVISIONAL")
        self.assertEqual((rc, out["electoral_outcome"]), (0, "READY"))


if __name__ == "__main__":
    unittest.main()
