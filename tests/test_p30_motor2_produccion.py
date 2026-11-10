"""T-216: P30 del motor 2 en la cadena de producción, detrás del interruptor `motor: m05|motor2` (m05 por defecto).

Solo stdlib + PyYAML (la competición real se prueba en local; ver docs/registro/*t216*)."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import yaml

from ddd_motor2 import produccion as p30
from herramientas import huella_checkpoint_motor as motor
from herramientas import manifest_generacion_territorial as mg
from tests.test_huella_checkpoint_motor import Base

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"


def _canon(d) -> bytes:
    return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


class HuellaModoM05Identica(Base):
    def test_m05_por_defecto_es_la_de_1_0_0(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DDD_MOTOR", None)
            h = motor.build_fingerprint(params=self.params, root_dir=self.root)
        self.assertEqual(set(h), {"schema", "territory_id", "m04", "m05", "fingerprint"})
        self.assertEqual(h["fingerprint"], hashlib.sha256(_canon({"m04": h["m04"]["fingerprint"],
                                                                    "m05": h["m05"]["fingerprint"]})).hexdigest())
        self.assertEqual(h, motor.build_fingerprint(params=self.params, root_dir=self.root, motor="m05"))
        self.assertEqual(h, self.antigua)

    def test_motor_desconocido_falla_cerrado(self):
        with self.assertRaises(ValueError):
            motor.build_fingerprint(params=self.params, root_dir=self.root, motor="motor3")


class HuellaModoMotor2(Base):
    def setUp(self):
        super().setUp()
        f = self.root / "ddd_motor2" / "competicion.py"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("v1\n", encoding="utf-8")
        self.m2 = motor.build_fingerprint(params=self.params, root_dir=self.root, motor="motor2")

    def test_capa_motor2(self):
        self.assertEqual(self.m2["motor"], "motor2")
        self.assertIn("ddd_motor2/competicion.py", self.m2["motor2"]["engine_files"])
        self.assertEqual((self.m2["motor2"]["funcion"], self.m2["motor2"]["cadenas"]), ("D8", 10))
        self.assertNotEqual(self.m2["fingerprint"], self.antigua["fingerprint"])
        self.assertEqual(self.m2["m04"], self.antigua["m04"])
        self.assertEqual(self.m2["m05"], self.antigua["m05"])

    def test_m06_no_se_cruza_entre_modos(self):
        for guardada, actual in ((self.antigua, self.m2), (self.m2, self.antigua)):
            r = motor.comparar(guardada, actual, 6)
            self.assertEqual((r["status"], r["invalidate_from"]), (motor.MISMATCH, "M05"))
        self.assertEqual(motor.comparar(self.m2, self.m2, 6)["status"], motor.MATCH)

    def test_m04_m05_valen_en_los_dos_modos(self):
        for etapa in (4, 5):
            self.assertEqual(motor.comparar(self.antigua, self.m2, etapa)["status"], motor.MATCH)
            self.assertEqual(motor.comparar(self.m2, self.antigua, etapa)["status"], motor.MATCH)

    def test_cambiar_el_motor2_invalida_el_m06(self):
        (self.root / "ddd_motor2" / "competicion.py").write_text("v2\n", encoding="utf-8")
        nueva = motor.build_fingerprint(params=self.params, root_dir=self.root, motor="motor2")
        self.assertEqual(motor.comparar(self.m2, nueva, 6)["status"], motor.MISMATCH)

    def test_ddd_motor_del_entorno(self):
        with mock.patch.dict(os.environ, {"DDD_MOTOR": "motor2"}):
            self.assertEqual(motor.build_fingerprint(params=self.params, root_dir=self.root), self.m2)


class Etiquetas(unittest.TestCase):
    def test_emparejamiento_con_el_canonico(self):
        can = {"a": "1", "b": "1", "c": "2", "d": "2", "e": "3"}
        gan = {"a": "x", "b": "y", "c": "y", "d": "y", "e": "z"}
        pob = dict.fromkeys(can, 10)
        et = p30.etiquetas(gan, can, pob)
        self.assertEqual(sorted(et.values()), [1, 2, 3])
        self.assertEqual((et["y"], et["z"]), (2, 3))
        self.assertEqual(et["x"], 1)

    def test_determinista(self):
        can = {s: str(i % 3 + 1) for i, s in enumerate("abcdefghi")}
        gan = {s: "abc"[(i + 1) % 3] for i, s in enumerate("abcdefghi")}
        pob = dict.fromkeys(can, 1)
        self.assertEqual(p30.etiquetas(gan, can, pob), p30.etiquetas(dict(reversed(gan.items())), can, pob))


class ReescribirEntradaM06(unittest.TestCase):
    def test_solo_cambia_el_distrito(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "x_m05_distritos_optimizados.geojson.zip"
            feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [i, 0]},
                      "properties": {"CUSEC_KEY": f"s{i}", "district_id": 1, "pob": i}} for i in range(4)]
            with zipfile.ZipFile(ruta, "w") as zf:
                zf.writestr("x.geojson", json.dumps({"type": "FeatureCollection", "features": feats}))
            n = p30.reescribir_entrada_m06(ruta, "CUSEC_KEY", "district_id", {"s0": 1, "s1": 1, "s2": 2, "s3": 2})
            self.assertEqual(n, 2)
            with zipfile.ZipFile(ruta) as zf:
                out = json.loads(zf.read("x.geojson"))
            self.assertEqual([f["properties"]["district_id"] for f in out["features"]], [1, 1, 2, 2])
            self.assertEqual([f["geometry"] for f in out["features"]], [f["geometry"] for f in feats])
            with self.assertRaises(ValueError):
                p30.reescribir_entrada_m06(ruta, "CUSEC_KEY", "district_id", {"s0": 1})


class VerificarRestauraM05(unittest.TestCase):
    def test_m06_del_ganador_y_m05_original(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            m05 = d / "x_m05_distritos_optimizados.geojson.zip"
            with zipfile.ZipFile(m05, "w") as zf:
                zf.writestr("x.geojson", json.dumps({"type": "FeatureCollection", "features": []}))
            original = m05.read_bytes()
            runs = d / "run"
            destino = runs / "p30_motor2"
            (destino / p30.RESPALDO).mkdir(parents=True)
            (destino / p30.RESPALDO / m05.name).write_bytes(original)
            m05.write_bytes(b"reescrita")
            comp = d / "x_m06_composicion_distritos.csv"
            comp.write_text("CUSEC_KEY,district_id\ns0,1\ns1,2\n", encoding="utf-8")
            (destino / "PLAN_GANADOR.json").write_text(json.dumps({"s0": 1, "s1": 2}), encoding="utf-8")
            (destino / "P30.json").write_text(json.dumps({"rehacer_m06": True, "m05_salida": {
                "sha256": hashlib.sha256(original).hexdigest()}}), encoding="utf-8")
            contrato = d / "c.yaml"
            contrato.write_text("meta: {}\n", encoding="utf-8")
            rutas = {"in_m06": m05, "composicion": comp, "runs": runs}
            with mock.patch.object(p30, "_rutas", return_value=rutas):
                v = p30.verificar(contrato)
                self.assertEqual(p30.main(["verificar", "--params", str(contrato)]), 0)  # idempotente
                m05.write_bytes(b"otra")  # sin respaldo y con otro contenido: falla cerrado
                self.assertEqual(p30.main(["verificar", "--params", str(contrato)]), 5)
                m05.write_bytes(original)
            self.assertTrue(v["verificacion_m06"]["igual_al_ganador"])
            self.assertTrue(v["m05_restaurada"])
            self.assertEqual(m05.read_bytes(), original)
            self.assertFalse((destino / p30.RESPALDO).exists())


class ManifiestoP30(unittest.TestCase):
    def _estado(self, d, datos):
        f = Path(d) / "run" / "p30_motor2" / "P30.json"
        f.parent.mkdir(parents=True)
        f.write_text(json.dumps(datos), encoding="utf-8")

    def test_sin_p30_no_hay_campo(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(mg._p30(Path(d)))

    def test_con_p30(self):
        with tempfile.TemporaryDirectory() as d:
            self._estado(d, {"valido": True, "estado": "P30_GANA_OTRO_PLAN", "ganador": "ponderado-s1",
                             "huella_resultado": "h", "motor2": {"fingerprint": "f"}, "rehacer_m06": True,
                             "verificacion_m06": {"igual_al_ganador": True}, "m05_restaurada": True,
                             "funcion": "D8", "cadenas": 10})
            r = mg._p30(Path(d))
            self.assertEqual((r["motor"], r["ganador"], r["motor2_fingerprint"]), ("motor2", "ponderado-s1", "f"))

    def test_invalido_o_sin_verificar_no_se_acredita(self):
        for datos in ({"valido": False}, {"valido": True, "rehacer_m06": True},
                      {"valido": True, "rehacer_m06": True, "verificacion_m06": {"igual_al_ganador": True}}):
            with tempfile.TemporaryDirectory() as d:
                self._estado(d, datos)
                with self.assertRaises(mg.GenerationManifestError):
                    mg._p30(Path(d))


class Flujos(unittest.TestCase):
    def _wf(self, nombre):
        return yaml.safe_load((WF / nombre).read_text(encoding="utf-8"))

    def test_entrada_motor_m05_por_defecto(self):
        r = self._wf("_reutilizable-generacion-territorial.yml")[True]["workflow_call"]["inputs"]["motor"]
        self.assertEqual(r["default"], "m05")
        p = self._wf("produccion-distritos.yml")[True]["workflow_call"]["inputs"]["motor"]
        self.assertEqual(p["default"], "m05")
        e = self._wf("ejecucion-completa-proyecto.yml")[True]
        self.assertEqual(e["workflow_call"]["inputs"]["motor"]["default"], "m05")
        boton = e["workflow_dispatch"]["inputs"]["motor"]
        self.assertEqual((boton["default"], boton["options"]), ("m05", ["m05", "motor2"]))

    def test_pasos_p30_solo_con_motor2_en_m06(self):
        jobs = self._wf("_reutilizable-generacion-territorial.yml")["jobs"]
        pasos = [s for s in jobs["m06"]["steps"] if str(s.get("name", "")).startswith("P30")]
        self.assertEqual(len(pasos), 5)
        for s in pasos:
            self.assertIn("env.STAGE == 'M06' && inputs.motor == 'motor2'", s["if"])
        # el ancla es la misma en todos los jobs de módulo: en M04/M05 los pasos existen pero no se cumplen
        self.assertEqual(jobs["m04"]["env"]["STAGE"], "M04")

    def test_la_00_pasa_el_motor_a_la_02_y_a_la_cadena(self):
        texto = (WF / "ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
        gen = self._wf("ejecucion-completa-proyecto.yml")["jobs"]["generar"]["with"]
        self.assertEqual(gen["motor"], "${{ inputs.motor || 'm05' }}")
        self.assertIn('-f "inputs[motor]=$MOTOR"', texto)


if __name__ == "__main__":
    unittest.main()
