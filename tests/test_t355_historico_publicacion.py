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
    """Sin `election_date` la P50 hace lo mismo que antes: se EJECUTA el bash de las líneas tocadas, con el entorno heredado,
    y se comparan los argumentos con los del workflow legacy (3.16.0). Control negativo: con valor aparecen los nuevos."""

    NUEVO = (ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text("utf-8")
    LEGACY = (ROOT / "legacy/workflows/_reutilizable-publicar-sitio_v3.16.0_20261114.yml").read_text("utf-8")
    PRELUDIO = ('python() { printf "%s\\n" "$@"; }\n'
                'raiz_run() { echo "$RAIZ"; }\nevidencia_run() { echo evid.json; }\n'
                'fallos=(); SCENARIO_ID=""; SCENARIO_STRATEGY=""; PAGE_URL=u; DEPLOYMENT_OUTCOME=ok; run=7\n')

    def ejecutar(self, texto_workflow, marca, fin=None, **env):
        """Líneas del workflow desde la que contiene `marca` hasta la que contiene `fin` (o solo esa), ejecutadas en bash."""
        import os
        lineas = texto_workflow.splitlines()
        a = next(i for i, l in enumerate(lineas) if marca in l and not l.lstrip().startswith("#"))
        while a > 0 and lineas[a - 1].rstrip().endswith("\\"):  # la orden empieza donde empieza su continuación
            a -= 1
        b = a if fin is None else next(i for i in range(a, len(lineas)) if fin in lineas[i])
        while lineas[b].rstrip().endswith("\\") and b + 1 < len(lineas):
            b += 1
        guion = "\n".join(l.strip() for l in lineas[a:b + 1])
        with tempfile.TemporaryDirectory() as raiz:
            e = {**os.environ, "RAIZ": raiz, **env}
            e.pop("ELECTION_DATE", None) if "ELECTION_DATE" not in env else None
            r = subprocess.run(["bash", "-c", self.PRELUDIO + guion], capture_output=True, text=True, env=e, cwd=raiz)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.replace(raiz, "<RAIZ>")

    def test_acreditacion_source_igual_sin_fecha_y_con_historico_con_ella(self):
        marca = "--phase source --output"
        vacio = self.ejecutar(self.NUEVO, marca, ELECTION_DATE="")
        self.assertEqual(vacio, self.ejecutar(self.LEGACY, marca))
        self.assertNotIn("--historico", vacio)
        self.assertIn("--historico", self.ejecutar(self.NUEVO, marca, ELECTION_DATE="2019-11-10"))

    def test_describe_production_igual_sin_fecha_y_con_fecha_con_ella(self):
        marca = "registro_publicaciones_visor.py describe-production"
        vacio = self.ejecutar(self.NUEVO, marca, ELECTION_DATE="")
        self.assertEqual(vacio, self.ejecutar(self.LEGACY, marca))
        self.assertNotIn("--election-date", vacio)
        con = self.ejecutar(self.NUEVO, marca, ELECTION_DATE="2019-11-10").splitlines()
        self.assertEqual(con[con.index("--election-date") + 1], "2019-11-10")

    def test_fase_prepared_igual_sin_fecha(self):
        marca = "--phase prepared --output \"$(evidencia_run"
        vacio = self.ejecutar(self.NUEVO, marca, ELECTION_DATE="")
        self.assertEqual(vacio, self.ejecutar(self.LEGACY, marca))
        self.assertIn("--historico", self.ejecutar(self.NUEVO, marca, ELECTION_DATE="2019-11-10"))

    def test_fase_final_igual_sin_fecha(self):
        marca, fin = "args=(--requested-run-id \"$run\" --registry", "python herramientas/evaluar_publicacion_visor.py"
        def bloque(texto, **env):
            return self.ejecutar(texto, marca, fin, **env)
        # el bloque «final»: args=(…) + production-root + (nuevo) historico, y la llamada a evaluar con "${args[@]}"
        nuevo_vacio = bloque(self.NUEVO, ELECTION_DATE="")
        self.assertEqual(nuevo_vacio, bloque(self.LEGACY))
        self.assertNotIn("--historico", nuevo_vacio)
        self.assertIn("--historico", bloque(self.NUEVO, ELECTION_DATE="2019-11-10"))

    def test_la_descarga_historica_solo_con_fecha(self):
        lineas = self.NUEVO.splitlines()
        a = next(i for i, l in enumerate(lineas) if 'if [[ -n "${ELECTION_DATE:-}" ]]; then' in l)
        sangria = len(lineas[a]) - len(lineas[a].lstrip())
        b = next(i for i in range(a + 1, len(lineas)) if lineas[i].strip() == "fi" and len(lineas[i]) - len(lineas[i].lstrip()) == sangria)
        bloque = "\n".join(l.strip() for l in lineas[a:b + 1])
        pre = 'gh() { echo "gh $*"; }\nrun=7; mkdir -p .ddd-publication/descargas "$root"\n'
        import os
        for fecha, esperado in (("", False), ("2019-11-10", True)):
            with tempfile.TemporaryDirectory() as raiz:
                r = subprocess.run(["bash", "-c", pre + bloque + '\necho SIGUE'], capture_output=True, text=True, cwd=raiz,
                                   env={**os.environ, "root": raiz + "/r", "ELECTION_DATE": fecha})
            self.assertEqual("ddd-historico-" in r.stdout, esperado, r.stdout + r.stderr)
            self.assertEqual("SIGUE" in r.stdout, not esperado)  # con fecha sale (éxito o fallo); sin fecha el flujo sigue

    def test_p50_solo_anade_el_input_opcional_vacio(self):
        import yaml
        nuevo = yaml.safe_load((ROOT / ".github/workflows/desplegar-visor-publico.yml").read_text("utf-8"))
        viejo = yaml.safe_load((ROOT / "legacy/workflows/desplegar-visor-publico_v3.6.0_20261114.yml").read_text("utf-8"))
        for ev in ("workflow_call", "workflow_dispatch"):
            n, v = nuevo[True][ev]["inputs"], viejo[True][ev]["inputs"]
            self.assertEqual(set(n) - set(v), {"election_date"})
            self.assertEqual(n["election_date"]["default"], "")
            self.assertTrue(all(n[k] == v[k] for k in v))

    def test_cli_sin_fecha_no_cambia_en_una_raiz_de_run_00(self):
        # Una raíz sin PUERTA sigue por el camino de producción (falla por falta de manifiesto, como antes).
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(Exception) as c:
                rpv.production_descriptors(Path(tmp), "1")
            self.assertNotIn("PUERTA", str(c.exception))


class UnaEleccionPorRun(unittest.TestCase):
    def test_cero_puertas_no_publica_nada(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "ninguna PUERTA"):
                rpv.historico_descriptors(Path(tmp), "1")
            with self.assertRaises(Exception) as c:  # raíz sin PUERTA ni production_status: camino de producción, falla
                rpv.production_descriptors(Path(tmp), "1", None, None, "2019-11-10", None)
            self.assertNotIn("PUERTA_NO_PASS", str(c.exception))

    def test_dos_claves_del_mismo_territorio_en_un_run_se_rechazan(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = raiz_historica(Path(tmp), "201911")
            raiz_historica(raiz, "201904")
            with self.assertRaisesRegex(ValueError, "CLAVE_REPETIDA"):
                rpv.production_descriptors(raiz, "1")

    def test_dos_runs_de_distinta_eleccion_no_caben_en_un_lote(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            d1 = rpv.production_descriptors(raiz_historica(Path(a), "201911"), "1")
            d2 = rpv.production_descriptors(raiz_historica(Path(b), "201904"), "2")
        with self.assertRaisesRegex(ValueError, "LOTE_TERRITORIO_REPETIDO"):
            rpv.merge_batch_descriptors([d1, d2])
