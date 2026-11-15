#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba del seguimiento de T-329: manifiesto neutro, puerta con m07/perdidos y tabla verificada (T-334)
VERSIÓN: 1.0.0 · FECHA: 2026-11-15 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: (1) `MANIFEST_M07` usa la clave `seccionado` con `mapa` y `tabla`, y las entradas ya escritas (`seccionado_2025`) se siguen
  leyendo; (2) la PUERTA vuelca el estado de M07 tal cual y los votos sin asignar; (3) `registro_tabla` falla cerrado si el sha256 de la
  tabla no es el de su JSON (T-328); (4) el Gestor llama sin `--mapa` y el valor por defecto es 2023.
"""
import inspect
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT))
try:
    import historico_campana as hc
    import historico_m07m08 as hm
except ImportError:  # pragma: no cover
    hc = hm = None


@unittest.skipIf(hc is None, "dependencias no instaladas")
class Seguimiento(unittest.TestCase):
    def test_manifiesto_clave_neutra_y_lectura_retrocompatible(self):
        antiguo = json.loads((ROOT / "datos/resultados/historico/MANIFEST_M07.json").read_text("utf-8"))["territorios"]
        entrada = next(iter(antiguo.values()))
        self.assertIn("seccionado_2025", entrada)  # lo histórico no se reescribe
        self.assertEqual(hm.huella_seccionado(entrada), entrada["seccionado_2025"])
        self.assertEqual(hm.huella_seccionado({"seccionado": "a" * 64}), "a" * 64)
        with tempfile.TemporaryDirectory() as t:
            z = Path(t) / "s.zip"
            z.write_bytes(b"x")
            comp = ROOT / "datos/composicion/MANIFEST.json"
            informe = {"201111": {"m07": "PASS", "tabla": "b" * 64}, "201512": {"m07": "PASS", "tabla": None}}
            e = hm.entrada_manifiesto({"sha256_origen": "c" * 64, "run_id": "1"}, comp, z, "2023", {}, informe)
        self.assertNotIn("seccionado_2025", e)
        self.assertEqual((e["mapa"], e["tabla"]), ("2023", {"201111": "b" * 64, "201512": None}))
        self.assertEqual(e["seccionado"], "2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881")  # sha256 de b"x"
        self.assertTrue(all("tabla" not in v for v in e["elecciones"].values()))
        self.assertEqual(informe["201111"]["tabla"], "b" * 64)  # el informe de entrada no se muta

    def test_puerta_vuelca_m07_y_perdidos(self):
        with tempfile.TemporaryDirectory() as t:
            salida, raiz = Path(t) / "salida", Path(t) / "raiz"
            (salida / "201111" / "nac01").mkdir(parents=True)
            (raiz / "configuracion").mkdir(parents=True)
            (raiz / "configuracion/resultados_oficiales_congreso_2011_11.csv").write_text(
                "codigo,provincia,escanos_circunscripcion,partido,votos,escanos\n01,X,4,AAA,600000,2\n01,X,4,BBB,400000,2\n", encoding="utf-8")
            esp = Path(t) / "espejo.json"
            esp.write_text(json.dumps({"s": ["AAA", "BBB"], "r": {"0100100001": [1500000, 1000000, 980000, [[0, 590000], [1, 390000]]]}}),
                           encoding="utf-8")
            (salida / "201111" / "nac01" / "reconciliacion.json").write_text(
                json.dumps({"status": "PASS_WITH_DECLARED_EXCEPTIONS", "ddd_unassigned_votes": 37, "source_votes": 980000}), encoding="utf-8")
            p = hc.puerta_json("nac01", "201111", "2023", 0, None, salida, None, "01", raiz, esp)  # 37/980000 = 0,004 % ≤ 0,1 % y BOE dentro de tolerancia
            self.assertEqual((p["m07"], p["perdidos"], p["estado"]), ("PASS_WITH_DECLARED_EXCEPTIONS", 37, "PASS"))
            self.assertEqual(hc.puerta_json("nac01", "201111", "2023", 1, None, salida, None, "01", raiz, esp)["estado"], "FAIL")
            # sin la comprobación de la ficha (provincia y espejo) la puerta ya no pasa en silencio
            self.assertEqual(hc.puerta_json("nac01", "201111", "2023", 0, None, salida)["estado"], "FAIL")

    def test_registro_tabla_falla_cerrado(self):
        origen = hc.tabla_2023("201111")
        self.assertEqual(hc.registro_tabla(origen)["sha256"],
                         json.loads(origen.with_suffix(".json").read_text("utf-8"))["csv"]["sha256"])
        with tempfile.TemporaryDirectory() as t:
            raiz = Path(t)
            (raiz / "configuracion").mkdir()
            tabla = raiz / "configuracion" / origen.name
            shutil.copy(origen, tabla)
            shutil.copy(origen.with_suffix(".json"), tabla.with_suffix(".json"))
            tabla.write_text(tabla.read_text("utf-8") + "0,0,1:1,1,1\n", encoding="utf-8")  # solo coincide consigo misma
            with self.assertRaises(SystemExit) as c:
                hc.registro_tabla(tabla, raiz)
            self.assertIn("TABLA_SHA256_DISTINTO", str(c.exception))
            tabla.with_suffix(".json").unlink()  # sin ficha: tampoco se acepta
            with self.assertRaises(SystemExit):
                hc.registro_tabla(tabla, raiz)

    def test_el_m06_se_busca_con_id_nuevo_aunque_el_indice_tenga_el_viejo(self):
        from ddd_core.territorio_ids import en_mapa
        idx = json.loads((ROOT / "datos_abiertos/INDEX.json").read_text("utf-8"))["territorios"]
        self.assertNotIn("nac01", idx)  # el INDEX conserva el id viejo
        self.assertIsNotNone(en_mapa(idx, "nac01"))
        with self.assertRaises(SystemExit):
            hc._m06("nac999", Path("/nonexistent/x.zip"))

    def test_el_gestor_llama_sin_mapa_y_el_defecto_es_2023(self):
        wf = (ROOT / ".github/workflows/gestor-campanas.yml").read_text("utf-8")
        llamadas = re.findall(r"historico_campana\.py ejecutar[^\n]*(?:\\\n[^\n]*)*", wf)
        self.assertGreaterEqual(len(llamadas), 3)
        self.assertTrue(all("--mapa" not in l for l in llamadas))
        self.assertEqual(inspect.signature(hc.ejecutar).parameters["mapa"].default, "2023")


if __name__ == "__main__":
    unittest.main()
