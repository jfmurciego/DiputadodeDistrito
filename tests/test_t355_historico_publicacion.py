# -*- coding: utf-8 -*-
"""T-355: publicación del histórico (paso A) como M08 vigente de SU elección, sin pisar la de 2023.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-15 · ESTADO: candidato · ANTERIOR: ninguno (fichero nuevo)
Valores esperados: fechas de las generales (BOE) escritas a mano; ningún id viejo literal (se deriva con id_legacy).
"""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
from herramientas import registro_publicaciones_visor as rpv  # noqa: E402
from herramientas import evaluar_publicacion_visor as epv  # noqa: E402
from herramientas import historico_m07m08 as hm  # noqa: E402

T = "nac22"
FECHAS = {"201911": "2019-11-10", "201904": "2019-04-28", "201606": "2016-06-26", "201512": "2015-12-20", "201111": "2011-11-20"}


def raiz_historica(raiz: Path, clave="201911", estado="PASS", territorio=T, con_zip=True, distritos=3) -> Path:
    """Forma de `salida_historico` del paso A: PUERTA en la raíz y <clave>/<t>/ con CSV y M08."""
    d = raiz / clave / territorio
    d.mkdir(parents=True, exist_ok=True)
    (raiz / f"PUERTA_{territorio}_{clave}.json").write_text(json.dumps(
        {"territorio": territorio, "clave": clave, "mapa": "2023", "m07": "PASS", "estado": estado}), encoding="utf-8")
    with (d / "resumen_electoral.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["district_id", "winner_party"])
        for i in range(distritos):
            w.writerow([f"D{i + 1}", "X"])
    if con_zip:
        (d / hm.M08_ZIP).write_bytes(b"zip-m08-" + clave.encode())
    return raiz


class CopiaM08(unittest.TestCase):
    def test_copia_el_m08_junto_a_los_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr, dest = Path(tmp) / "tr", Path(tmp) / "dest"
            tr.mkdir(); dest.mkdir()
            (tr / hm.M08_ZIP).write_bytes(b"abc")
            self.assertEqual(hm.copiar_m08(tr, dest).read_bytes(), b"abc")

    def test_sin_m08_falla(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                hm.copiar_m08(Path(tmp), Path(tmp))


class DescriptoresHistoricos(unittest.TestCase):
    def describir(self, raiz, **kw):
        return rpv.production_descriptors(raiz, "123", None, None, kw.get("election_date"), kw.get("election_id"))

    def test_cada_clave_lleva_su_fecha_y_es_m08_canonico(self):
        for clave, fecha in FECHAS.items():
            with tempfile.TemporaryDirectory() as tmp:
                d = self.describir(raiz_historica(Path(tmp), clave))
                self.assertEqual(len(d), 1)
                self.assertEqual((d[0]["kind"], d[0]["stage"], d[0]["election_date"]), ("canonical_m08", "M08", fecha))
                self.assertTrue(d[0]["election_id"].endswith(fecha))
                self.assertEqual((d[0]["territory_id"], d[0]["run_id"], d[0]["expected_districts"]), (T, "123", 3))
                self.assertTrue(d[0]["local_source"].endswith(hm.M08_ZIP))
                rpv._validate_eleccion(d[0])

    def test_puerta_que_no_es_pass_no_se_publica_nunca(self):
        for estado in ("FAIL", "", None, "pass", "PASS_WITH_DECLARED_EXCEPTIONS"):
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaisesRegex(ValueError, "PUERTA_NO_PASS"):
                    self.describir(raiz_historica(Path(tmp), estado=estado))

    def test_un_territorio_en_rojo_rechaza_todo_el_lote(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = raiz_historica(Path(tmp))
            raiz_historica(raiz, territorio="nac33", estado="FAIL")
            with self.assertRaisesRegex(ValueError, "PUERTA_NO_PASS nac33"):
                self.describir(raiz)

    def test_sin_m08_zip_o_sin_distritos_se_rechaza(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "SIN_M08"):
                self.describir(raiz_historica(Path(tmp), con_zip=False))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "SIN_DISTRITOS"):
                self.describir(raiz_historica(Path(tmp), distritos=0))

    def test_fecha_declarada_distinta_de_la_clave_se_rechaza(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "no corresponde"):
                self.describir(raiz_historica(Path(tmp)), election_date="2023-07-23")
            self.assertEqual(self.describir(raiz_historica(Path(tmp)), election_date="2019-11-10")[0]["election_date"], "2019-11-10")

    def test_clave_2023_o_desconocida_no_entra(self):
        for clave in ("202307", "199999"):
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaisesRegex(ValueError, "CLAVE_HISTORICA"):
                    self.describir(raiz_historica(Path(tmp), clave=clave))

    def test_alias_de_id_viejo(self):
        from ddd_core.territorio_ids import id_legacy
        with tempfile.TemporaryDirectory() as tmp:
            d = self.describir(raiz_historica(Path(tmp)))
            self.assertEqual(d[0].get("alias_de"), id_legacy(T))

    def test_el_registro_acepta_historico_y_2023_a_la_vez(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self.describir(raiz_historica(Path(tmp)))[0]
        base = {k: d[k] for k in ("asset_type", "kind", "territory_id", "election_date", "election_id")}
        h = {**base, "id": "m08-h", "source_type": "repository_blob", "repository": "o/r", "blob_sha": "a" * 40,
             "immutable_location": "github-git-blob://o/r/" + "a" * 40, "sha256": "a" * 64, "run_id": "1", "canonical": True}
        v = {**h, "id": "m08-v", "blob_sha": "b" * 40, "immutable_location": "github-git-blob://o/r/" + "b" * 40,
             "sha256": "b" * 64, "run_id": "2"}
        del v["election_date"], v["election_id"]
        rpv.validate_registry({"schema": rpv.SCHEMA, "products": [h, v], "ensembles": []})
        self.assertEqual((rpv.eleccion_de(h), rpv.eleccion_de(v)), ("2019-11-10", "2023-07-23"))


class AcreditacionHistorica(unittest.TestCase):
    def test_raiz_historica_acredita_la_ejecucion_solicitada(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = raiz_historica(Path(tmp))
            raiz_historica(raiz, territorio="nac33")
            r = epv.evaluate_publication(requested_run_id="123", production_root=raiz, phase="source", historico=True)
            self.assertEqual((r["status"], r["generated_run_id"], r["reasons"]), ("READY", "123", []))

    def test_sin_puerta_pass_no_acredita(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = epv.evaluate_publication(requested_run_id="123", production_root=raiz_historica(Path(tmp), estado="FAIL"),
                                         phase="source", historico=True)
            self.assertEqual(r["status"], "BLOCK")

    def test_sin_historico_el_comportamiento_es_el_de_siempre(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = raiz_historica(Path(tmp))
            r = epv.evaluate_publication(requested_run_id="123", production_root=raiz, phase="source")
            self.assertEqual(r["status"], "BLOCK")
            self.assertIn("EXECUCION_SOLICITADA_SIN_EVIDENCIA_GENERADA", r["reasons"])


class SinEleccionNadaCambia(unittest.TestCase):
    """Sin input de elección la P50 se comporta como hoy: los argumentos nuevos solo se pasan si hay valor."""

    def test_workflows_solo_pasan_los_argumentos_con_valor(self):
        txt = (ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text("utf-8")
        self.assertIn('${ELECTION_DATE:+--election-date "$ELECTION_DATE"}', txt)
        self.assertIn('${ELECTION_DATE:+--historico}', txt)
        P50 = (ROOT / ".github/workflows/desplegar-visor-publico.yml").read_text("utf-8")
        self.assertEqual(P50.count("election_date:"), 3)  # workflow_call, workflow_dispatch y paso a la reutilizable

    def test_cli_sin_fecha_no_cambia_en_una_raiz_de_run_00(self):
        # Una raíz sin PUERTA sigue por el camino de producción (falla por falta de manifiesto, como antes).
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(Exception) as c:
                rpv.production_descriptors(Path(tmp), "1")
            self.assertNotIn("PUERTA", str(c.exception))


if __name__ == "__main__":
    unittest.main()
