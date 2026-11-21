"""T-379 3c-ii (opción A del Planificador, 20-11): P40 publica una campaña de P00, en la que todos los territorios comparten run.

De punta a punta con el código real, cada regla con su control negativo:
- El cierre escribe los manifiestos de dos territorios del MISMO run (campana_registro.manifiestos) → p40_resolver da un par
  `<run>:<espacio>` por territorio → el lote lo acepta (parse-run-ids). Sin filtrar por territorio, el resolutor da
  REGISTRO_00_DUPLICADO; una 00 de siempre sigue dando el run a secas.
- La evaluación con `--territory-id` solo mira ese territorio (sin él: VARIOS_TERRITORIOS_CARGADOS_PARA_LA_MISMA_EJECUCION).
- Los bloques de shell nuevos de P40 (ayudas del lote y descarga de campaña) se ejecutan bajo `bash -eo pipefail` con un `gh`
  de prueba: con el manifiesto en git, .ok y manifest.json; sin él, .fallo (lección #726).
- P40 y P00: entradas ocultas vacías por defecto; P00 llama con «Territorios», los sanos y el sha del cierre.
"""
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
import campana_estado as ce  # noqa: E402
import campana_registro as cr  # noqa: E402
import p40_resolver  # noqa: E402
import resolver_cadena_publicacion as rcp  # noqa: E402
from herramientas.evaluar_publicacion_visor import evaluate_publication  # noqa: E402
from tests.test_t379_3b_campana_registro import SHA, huellas_cadena  # noqa: E402

NS = {t: f"campaign-900-1--01--{t}" for t in ("aut11", "nac22")}


def campana_cerrada(root: Path) -> None:
    """Dos sanos de la campaña 900 con los manifiestos que escribe el cierre real."""
    alm = ce.AlmacenLocal(root / "alm")
    ce.guardar_semaforo(alm, "900", ce.comprobar("aut11, nac22", "vigente"))
    for t in ("aut11", "nac22"):
        h = huellas_cadena(t)
        for paso in ce.PASOS:
            ce.empezar(alm, "900", t, paso, 1)
            ce.registrar(alm, "900", t, paso, 1, "ok", huellas=h[paso])
    cr.manifiestos(root, alm, "900", "900", SHA, ["aut11", "nac22"])


class Resolver(unittest.TestCase):
    def test_un_par_por_territorio_en_el_run_compartido(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            campana_cerrada(root)
            r = p40_resolver.territorios(root, "nac22,aut11")
            self.assertEqual(r["production_run_ids"], f"900:{NS['nac22']} 900:{NS['aut11']}")
            self.assertEqual([t["territory_id"] for t in r["territorios"]], ["aut11", "nac22"])
            # control negativo: sin territorio, el run compartido es un duplicado (lo que hacía la 1.0.0)
            self.assertEqual(rcp.resolver(root, "900")["reasons"], ["REGISTRO_00_DUPLICADO"])
            self.assertEqual(rcp.resolver(root, "900", "aut11")["status"], "READY")
            # y el lote lo acepta tal cual
            from herramientas.registro_publicaciones_visor import parse_run_ids
            self.assertEqual(parse_run_ids(r["production_run_ids"]), [f"900:{NS['nac22']}", f"900:{NS['aut11']}"])

    def test_00_de_siempre_da_el_run_a_secas(self):
        r = {"publish_run_id": "240", "m08_artifact": "ddd-state-240-M08"}
        self.assertEqual(p40_resolver.elemento_lote(r, "aut01"), "240")
        r["m08_artifact"] = "ddd-state-240-M08-otro-sufijo"  # sufijo que no es de campaña: como antes, el run
        self.assertEqual(p40_resolver.elemento_lote(r, "aut01"), "240")

    def test_espacio_de_otro_run_o_territorio_se_rechaza(self):
        for art in (f"ddd-state-900-M08-{NS['nac22']}", "ddd-state-900-M08-campaign-901-1--01--aut11",
                    "ddd-state-900-M08-campaign-900-1--00--aut11"):
            with self.assertRaisesRegex(ValueError, "P40_ESPACIO_DE_CAMPANA_AJENO"):
                p40_resolver.elemento_lote({"publish_run_id": "900", "m08_artifact": art}, "aut11")


class Lote(unittest.TestCase):
    def setUp(self):
        from herramientas.registro_publicaciones_visor import parse_run_ids
        self.parse = parse_run_ids

    def test_admite_el_par_de_campana(self):
        self.assertEqual(self.parse(f"900:{NS['aut11']}, 123"), [f"900:{NS['aut11']}", "123"])

    def test_rechaza_pares_mal_formados(self):
        for malo in ("901:" + NS["aut11"], "900:campaign-900-1--00--aut11", "900:aut11", "900:", f"900:{NS['aut11']}x;"):
            with self.assertRaisesRegex(ValueError, "LOTE_RUN_ID_INVALIDO"):
                self.parse(malo)
        with self.assertRaisesRegex(ValueError, "LOTE_RUN_ID_DUPLICADO"):
            self.parse(f"900:{NS['aut11']} 900:{NS['aut11']}")


class Evaluacion(unittest.TestCase):
    def preparar(self, td):
        root = Path(td) / "prod"
        root.mkdir()
        (root / "production_status.json").write_text(json.dumps({"run_id": "900", "workflow_run_id": "900",
                                                                 "territory_id": "aut11"}), encoding="utf-8")
        reg = Path(td) / "viewer-results.json"
        filas = [{"kind": "canonical_m06", "run_id": "900", "territory_id": t, "viewer_path": f"datos/{t}.geojson"}
                 for t in ("aut11", "nac22")]
        reg.write_text(json.dumps({"results": filas}), encoding="utf-8")
        return root, reg

    def test_filtra_por_territorio(self):
        with tempfile.TemporaryDirectory() as td:
            root, reg = self.preparar(td)
            sin = evaluate_publication(requested_run_id="900", production_root=root, registry_path=reg, phase="prepared")
            self.assertIn("VARIOS_TERRITORIOS_CARGADOS_PARA_LA_MISMA_EJECUCION", sin["reasons"])
            con = evaluate_publication(requested_run_id="900", production_root=root, registry_path=reg, phase="prepared",
                                       territory_id="aut11")
            self.assertEqual((con["status"], con["territory_id"]), ("READY", "aut11"))
            otro = evaluate_publication(requested_run_id="900", production_root=root, registry_path=reg, phase="prepared",
                                        territory_id="nac22")
            self.assertIn("TERRITORIO_GENERADO_NO_ES_EL_SOLICITADO", otro["reasons"])


def pasos(job):
    return {p.get("name"): p for p in leer("p40-publicacion.yml")["jobs"][job]["steps"]}


def leer(nombre):
    return yaml.safe_load((WF / nombre).read_text(encoding="utf-8"))


def heredoc(run, fin="SH"):
    m = re.search(r"<<'SH'\n(.*?)\n" + fin + r"\n", run, re.S)
    return m.group(1)


class Shell(unittest.TestCase):
    """Los bloques nuevos de P40 bajo `bash -eo pipefail` (lección #726)."""

    def lote_sh(self):
        return heredoc(pasos("publicar")["Normalizar lote de ejecuciones solicitadas"]["run"])

    def test_ayudas_del_lote(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / ".ddd-publication"
            d.mkdir()
            (d / "lote.sh").write_text(self.lote_sh(), encoding="utf-8")
            item = f"900:{NS['aut11']}"
            prueba = (f'source .ddd-publication/lote.sh; for i in "${{LOTE[@]}}"; do '
                      f'echo "$(run_de "$i")|$(ns_de "$i")|$(terr_de "$i")|$(raiz_run "$i")|$(evidencia_run "$i")|$(territorio_args "$i")"; done')
            (d / "run-ids.txt").write_text(f"{item}\n123\n", encoding="utf-8")
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", prueba], cwd=td, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.splitlines(), [
                f"900|{NS['aut11']}|aut11|/tmp/production/900--{NS['aut11']}|.ddd-publication/publicacion_visor_900--{NS['aut11']}.json|--territory-id aut11",
                "123|||/tmp/production/123|.ddd-publication/publicacion_visor_123.json|"])  # sin espacio: rutas de siempre
            (d / "run-ids.txt").write_text("123\n", encoding="utf-8")
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", prueba], cwd=td, capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), "123|||/tmp/production|.ddd-publication/publicacion_visor.json|")

    def descarga(self, td, con_manifiesto):
        td = Path(td)
        (td / ".ddd-publication" / "descargas").mkdir(parents=True)
        (td / ".ddd-publication" / "lote.sh").write_text(self.lote_sh().replace("/tmp/production", str(td / "prod")),
                                                       encoding="utf-8")
        item = f"900:{NS['aut11']}"
        (td / ".ddd-publication" / "run-ids.txt").write_text(f"{item}\n", encoding="utf-8")
        if con_manifiesto:
            m = td / "territorios/aut11/evidencia/ejecuciones_completas/900.json"
            m.parent.mkdir(parents=True)
            m.write_text('{"status": "SUCCESS"}', encoding="utf-8")
        bin_ = td / "bin"
        bin_.mkdir()
        gh = bin_ / "gh"
        # gh de prueba: por cada --pattern crea su carpeta con lo que pide lista_completa; registra lo pedido.
        gh.write_text('#!/usr/bin/env bash\nset -eo pipefail\nprintf "%s\\n" "$*" >> "$GH_LOG"\ndir=""; pats=()\n'
                      'while (( $# )); do case "$1" in --dir) dir="$2"; shift 2;; --pattern) pats+=("$2"); shift 2;; *) shift;; esac; done\n'
                      'for p in "${pats[@]}"; do mkdir -p "$dir/$p"; done\n'
                      'touch "$dir/${pats[0]}/production_status.json" "$dir/${pats[2]}/decision.json" '
                      '"$dir/${pats[0]}/x_contiguedad_geometrica.json" "$dir/${pats[3]}/x_m06_distritos.geojson.zip"\n',
                      encoding="utf-8")
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        script = heredoc(pasos("publicar")["Recuperar ejecución solicitada como fuente transitoria"]["run"])
        (td / "descargar_run.sh").write_text(script, encoding="utf-8")
        env = {**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}", "GH_LOG": str(td / "gh.log")}
        r = subprocess.run(["bash", "-eo", "pipefail", "descargar_run.sh", item], cwd=td, env=env, capture_output=True, text=True)
        return td, r

    def test_descarga_de_campana_con_manifiesto(self):
        with tempfile.TemporaryDirectory() as td:
            td, r = self.descarga(td, True)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            k = f"900--{NS['aut11']}"
            self.assertTrue((td / ".ddd-publication/descargas" / f"{k}.ok").is_file())
            man = td / "prod" / f"ddd-full-run-manifest-900-{NS['aut11']}" / "manifest.json"
            self.assertEqual(json.loads(man.read_text(encoding="utf-8")), {"status": "SUCCESS"})
            pedidos = (td / "gh.log").read_text(encoding="utf-8")
            self.assertEqual(pedidos.count("run download"), 1)  # sin descarga completa ni R2
            for p in ("ddd-audit-900-", "ddd-audit-electoral-900-", "ddd-decision-900-", "ddd-state-900-M06-", "ddd-state-900-M08-"):
                self.assertIn(f"--pattern {p}{NS['aut11']}", pedidos)
            self.assertNotIn("nac22", pedidos)
            self.assertNotIn("*", pedidos)  # nada con comodín: solo este territorio

    def test_descarga_de_campana_sin_manifiesto_falla(self):
        with tempfile.TemporaryDirectory() as td:
            td, r = self.descarga(td, False)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("sin manifiesto", (td / ".ddd-publication/descargas" / f"900--{NS['aut11']}.fallo").read_text())


class Llamadas(unittest.TestCase):
    def test_p40_entradas_ocultas_vacias_y_ref_del_resolver(self):
        doc = leer("p40-publicacion.yml")
        call = doc[True]["workflow_call"]["inputs"]
        for k in ("que_publicar", "territorios", "ref"):
            self.assertEqual(call[k], {"required": False, "type": "string", "default": ""}, k)
        co = doc["jobs"]["resolver"]["steps"][0]
        self.assertEqual(co["with"], {"ref": "${{ inputs.ref }}"})

    def test_p00_publica_los_sanos_con_el_sha_del_cierre(self):
        jobs = leer("p00-campana.yml")["jobs"]
        w = jobs["publicar"]["with"]
        self.assertEqual(w, {"pagina_publicar": "Sitio completo", "que_publicar": "Territorios",
                             "territorios": "${{ needs.cierre_main.outputs.sanos }}", "ref": "${{ needs.cierre_main.outputs.sha }}"})
        self.assertNotIn("production_run_id", w)
        cond = jobs["publicar"]["if"]
        for c in ("needs.comprobar.outputs.publicar == 'true'", "needs.cierre_main.outputs.commit == 'true'",
                  "needs.cierre_main.outputs.sanos != ''", "!cancelled()"):
            self.assertIn(c, cond)
        self.assertEqual(jobs["cierre_main"]["outputs"]["sanos"], "${{ steps.cerrar.outputs.sanos }}")
        self.assertEqual(jobs["cierre_main"]["outputs"]["sha"], "${{ steps.cerrar.outputs.sha }}")
        # «publicar» por defecto «no» (D-177)
        self.assertEqual(leer("p00-campana.yml")[True]["workflow_dispatch"]["inputs"]["publicar"]["default"], "no")

    def test_salida_sanos_bajo_pipefail(self):
        run = next(p for p in leer("p00-campana.yml")["jobs"]["cierre_main"]["steps"] if p.get("id") == "cerrar")["run"]
        linea = next(l for l in run.splitlines() if "sanos=" in l).strip()
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / ".ddd-p00"
            d.mkdir()
            for sanos, esperado in ((["aut11", "nac22"], "sanos=aut11,nac22"), ([], "sanos=")):
                (d / "cierre.json").write_text(json.dumps({"sanos": sanos}), encoding="utf-8")
                r = subprocess.run(["bash", "-eo", "pipefail", "-c", linea], cwd=td, capture_output=True, text=True)
                self.assertEqual((r.returncode, r.stdout.strip()), (0, esperado), r.stderr)


if __name__ == "__main__":
    unittest.main()
