"""T-09: huella de puentes heredados antes de M02, con puentes rotos sintéticos."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from herramientas.verificar_puentes_congreso import check_contract, classify, main, sections_from_geojson

SECTIONS = {"4713401001", "4718301001", "4718301002", "2200101001", "2200101002"}
BASE = {"admin_scope": "province:47", "edge_type": "administrative_exclave", "reason": "r", "source": "s"}


def bridge(u, v, **kw):
    return {**BASE, "u": u, "v": v, **kw}


class VerificarPuentes(unittest.TestCase):
    def test_clasificacion(self):
        cases = {
            "VALIDO": bridge("4713401001", "4718301001"),
            "MUNICIPIO_INEXISTENTE": bridge("4717501001", "4718301001"),
            "CODIGO_SECCION_CAMBIADO": bridge("4713401009", "4718301001"),
            "EXTREMOS_IGUALES": bridge("4713401001", "4713401001"),
            "FUERA_DE_AMBITO": bridge("4718301001", "4718301002", admin_scope="municipality:47134"),
            "FUERA_DE_PROVINCIA": bridge("2200101001", "2200101002", admin_scope="province:22"),
            "CAMPOS_INCOMPLETOS": {"u": "4713401001", "v": "4718301001"},
        }
        for expected, b in cases.items():
            with self.subTest(expected=expected):
                self.assertEqual(classify(b, SECTIONS, {"47"}), expected)

    def test_contrato_con_puente_roto_bloquea_y_m01_como_inventario(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            contract = tmp / "c.yaml"
            contract.write_text(yaml.safe_dump({
                "territory_contract": {"province_codes": ["47"]},
                "modulos": {"modulo_02_construir_adyacencias": {"topology_bridges": [
                    bridge("4713401001", "4718301001"), bridge("4717501001", "4718301001")]}},
            }), encoding="utf-8")
            geo = tmp / "m01.geojson.zip"
            with zipfile.ZipFile(geo, "w") as z:
                z.writestr("m01.geojson", json.dumps({"features": [
                    {"properties": {"CUSEC_KEY": s}} for s in sorted(SECTIONS)]}))
            self.assertEqual(sections_from_geojson(geo), SECTIONS)
            report = check_contract(contract, SECTIONS)
            self.assertEqual((report["status"], report["broken"]), ("BLOCK", 1))
            self.assertEqual(main(["--params", str(contract), "--sections-geojson", str(geo)]), 1)

    def test_contratos_nacionales_declaran_puentes_bien_formados(self):
        root = Path(__file__).resolve().parents[1]
        contracts = sorted(root.glob("territorios/congreso_*/config/congreso_*_2025.yaml"))
        self.assertEqual(len(contracts), 52)
        for path in contracts:
            for b in (yaml.safe_load(path.read_text(encoding="utf-8"))["modulos"]
                      ["modulo_02_construir_adyacencias"].get("topology_bridges") or []):
                with self.subTest(contract=path.name, u=b.get("u")):
                    self.assertNotEqual(classify(b, {str(b["u"]), str(b["v"])}, set()), "CAMPOS_INCOMPLETOS")

    def test_paso_del_workflow_solo_en_m02_y_ambitos_nacionales(self):
        root = Path(__file__).resolve().parents[1]
        wf = yaml.safe_load((root / ".github/workflows/_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8"))
        steps = wf["jobs"]["m02"]["steps"]
        names = [s.get("name") for s in steps]
        i = names.index("Huella de puentes antes de M02")
        self.assertEqual(names[i + 1], "Ejecutar módulo")
        step = steps[i]
        self.assertEqual(step["if"], "${{ env.STAGE == 'M02' }}")
        self.assertIn("territorios/congreso_*) ;;", step["run"])  # las autonómicas salen sin comprobar
        self.assertIn("--sections-geojson", step["run"])
        # Si M02 se reutiliza por checkpoint, el job m02 no corre y el paso tampoco.
        self.assertIn("needs.m01.result == 'success'", wf["jobs"]["m02"]["if"])


if __name__ == "__main__":
    unittest.main()
