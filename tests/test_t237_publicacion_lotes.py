# -*- coding: utf-8 -*-
"""T-237: publicación por lotes en la P50 (`production_run_id` con varios runs 00, todo o nada).

PROYECTO: Diputado de Distrito · VERSIÓN: 1.1.0 · FECHA: 2026-11-11 · ESTADO: candidato
CAMBIOS 1.1.0 (T-239): descarga selectiva y en paralelo; el `gh` falso simula los artefactos de una 00 y respeta --pattern.
ANTERIOR: legacy/tests/test_t237_publicacion_lotes_v1.0.0_20261111.py
Repetidos: se RECHAZAN (no se deduplican). Lista vacía: «solo sitio» (como T-125).
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from herramientas import registro_publicaciones_visor as rpv  # noqa: E402

PUBLISHER = ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml"
P50 = ROOT / ".github/workflows/desplegar-visor-publico.yml"
TOOL = ROOT / "herramientas/registro_publicaciones_visor.py"


def _steps():
    data = yaml.safe_load(PUBLISHER.read_text(encoding="utf-8"))
    return data["jobs"]["publicar"]["steps"]


def _step(name):
    for step in _steps():
        if step.get("name") == name:
            return step["run"]
    raise AssertionError(f"falta el paso {name}")


def _desc(territory, run, stage="M08"):
    return {"id": f"{stage.lower()}-{territory}-{run}", "territory_id": territory, "run_id": run, "stage": stage}


class ListaDeRuns(unittest.TestCase):
    def test_id_unico_identico(self):
        self.assertEqual(rpv.parse_run_ids("42531122768"), ["42531122768"])
        self.assertEqual(rpv.parse_run_ids(" 42531122768 "), ["42531122768"])

    def test_separadores_espacios_y_comas(self):
        esperado = ["101", "202", "303"]
        for texto in ("101 202 303", "101,202,303", "101, 202 ,303", "101,,202  303,", "101\t202\n303"):
            self.assertEqual(rpv.parse_run_ids(texto), esperado, texto)

    def test_lista_vacia_es_solo_sitio(self):
        self.assertEqual(rpv.parse_run_ids(""), [])
        self.assertEqual(rpv.parse_run_ids(None), [])
        self.assertEqual(rpv.parse_run_ids(" , "), [])

    def test_id_no_numerico_rechaza_el_lote_y_lo_nombra(self):
        with self.assertRaisesRegex(ValueError, "LOTE_RUN_ID_INVALIDO: abc"):
            rpv.parse_run_ids("101 abc 303")

    def test_duplicado_se_rechaza_no_se_deduplica(self):
        with self.assertRaisesRegex(ValueError, "LOTE_RUN_ID_DUPLICADO: 101$|LOTE_RUN_ID_DUPLICADO: 101 "):
            rpv.parse_run_ids("101,202,101")

    def test_escenario_solo_con_un_id(self):
        self.assertEqual(rpv.parse_run_ids("101", "gerrychain-50-101"), ["101"])
        with self.assertRaisesRegex(ValueError, "LOTE_CON_ESCENARIO"):
            rpv.parse_run_ids("101 202", "gerrychain-50-101")

    def test_cli_imprime_lista_normalizada(self):
        out = subprocess.run([sys.executable, str(TOOL), "parse-run-ids", "--value", "101,202 303"],
                             capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT)})
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "101 202 303")


class DescriptoresDelLote(unittest.TestCase):
    def test_un_run_salida_identica(self):
        uno = [_desc("aragon", "101", "M06"), _desc("aragon", "101")]
        self.assertEqual(rpv.merge_batch_descriptors([uno]), uno)

    def test_lote_valido_une_todos(self):
        a, b = [_desc("aragon", "101")], [_desc("murcia", "202", "M06"), _desc("murcia", "202")]
        self.assertEqual([d["id"] for d in rpv.merge_batch_descriptors([a, b])],
                         ["m08-aragon-101", "m06-murcia-202", "m08-murcia-202"])

    def test_territorio_repetido_en_el_lote_se_rechaza(self):
        with self.assertRaisesRegex(ValueError, "LOTE_TERRITORIO_REPETIDO: aragon en los runs 101 y 202"):
            rpv.merge_batch_descriptors([[_desc("aragon", "101")], [_desc("aragon", "202")]])

    def test_mapa_350_en_el_lote_se_rechaza(self):
        with self.assertRaisesRegex(ValueError, "mapa 350"):
            rpv.merge_batch_descriptors([[_desc("aragon", "101")], [_desc("congreso350_soria", "202")]])

    def test_cli_con_un_run_invalido_no_escribe_nada(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "a.json").write_text(json.dumps([_desc("aragon", "101")]), encoding="utf-8")
        (tmp / "b.json").write_text(json.dumps([_desc("congreso350_soria", "202")]), encoding="utf-8")
        out = subprocess.run([sys.executable, str(TOOL), "merge-descriptors", "--inputs", str(tmp / "a.json"),
                              str(tmp / "b.json"), "--output", str(tmp / "todo.json")],
                             capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT)})
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("congreso350_soria", out.stderr)
        self.assertFalse((tmp / "todo.json").exists())


class _Entorno(unittest.TestCase):
    """Directorio temporal con `gh` falso para ejecutar los pasos reales del workflow."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / "herramientas").symlink_to(ROOT / "herramientas")
        (self.tmp / ".ddd-publication").mkdir()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.descargas = self.tmp / "descargas.log"
        gh = self.bin / "gh"
        # gh run download RUN --pattern P... --dir D con los artefactos de una 00 (respeta los patrones).
        # 999: falla siempre. 555: su producto M06 está en un artefacto fuera de la selección (fuerza la completa).
        gh.write_text(f"""#!/usr/bin/env bash
run="$3"; shift 3; pats=(); dir=""
while (( $# )); do case "$1" in --pattern) pats+=("$2"); shift 2;; --dir) dir="$2"; shift 2;; *) shift;; esac; done
echo "$run ${{pats[*]}}" >> {self.descargas}
[[ "$run" == 999 ]] && {{ echo "HTTP 404" >&2; exit 1; }}
declare -A arts=(
  [ddd-audit-$run]=production_status.json [ddd-decision-$run]=decision.json
  [ddd-full-run-manifest-$run]=manifest.json [ddd-state-$run-M01]=cache/m01.bin
  [ddd-source-package-$run]=fuentes.zip [ddd-estado-operativo-$run]=estado.json)
if [[ "$run" == 555 ]]; then arts[ddd-state-$run-M07]=cache/t_m06_distritos.geojson.zip
else arts[ddd-state-$run-M06]=cache/t_m06_distritos.geojson.zip; fi
for name in "${{!arts[@]}}"; do
  for p in "${{pats[@]}}"; do
    if [[ "$name" == $p ]]; then mkdir -p "$(dirname "$dir/$name/${{arts[$name]}}")"; echo x > "$dir/$name/${{arts[$name]}}"; break; fi
  done
done
""", encoding="utf-8")
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        self.prod = self.tmp / "production"

    def _bash(self, script, run_ids):
        script = script.replace("/tmp/production", str(self.prod))
        env = {**os.environ, "PRODUCTION_RUN_ID": run_ids, "SCENARIO_ID": "", "PYTHONPATH": str(ROOT),
               "PATH": f"{self.bin}:{os.environ['PATH']}"}
        return subprocess.run(["bash", "-c", script], cwd=self.tmp, env=env, capture_output=True, text=True)

    def _normalizar_y_descargar(self, run_ids):
        norm = self._bash(_step("Normalizar lote de ejecuciones solicitadas"), run_ids)
        if norm.returncode:
            return norm
        return self._bash(_step("Recuperar ejecución solicitada como fuente transitoria"), run_ids)

    def _rutas(self, run_ids):
        r = self._bash("source .ddd-publication/lote.sh; for r in \"${LOTE[@]}\"; do echo \"$r $(raiz_run $r) $(evidencia_run $r)\"; done", run_ids)
        return r.stdout.split("\n")[:-1]


class PasosDelPublicador(_Entorno):
    def test_id_unico_mismas_rutas_que_antes(self):
        r = self._normalizar_y_descargar("42531122768")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._rutas(""), [f"42531122768 {self.prod} .ddd-publication/publicacion_visor.json"])
        self.assertTrue((self.prod / "ddd-audit-42531122768/production_status.json").is_file())
        self.assertTrue((self.prod / "ddd-state-42531122768-M06/cache/t_m06_distritos.geojson.zip").is_file())

    def test_solo_baja_lo_que_lee_la_publicacion(self):
        r = self._normalizar_y_descargar("101 202")
        self.assertEqual(r.returncode, 0, r.stderr)
        for run in ("101", "202"):
            bajados = sorted(p.name for p in (self.prod / run).iterdir())
            self.assertEqual(bajados, [f"ddd-audit-{run}", f"ddd-decision-{run}", f"ddd-full-run-manifest-{run}",
                                       f"ddd-state-{run}-M06"])
        self.assertNotIn("ddd-*", self.descargas.read_text(encoding="utf-8"))
        self.assertIn("DESCARGA run=101 modo=selectiva", r.stdout)

    def test_sin_producto_en_la_seleccion_baja_todo_ese_run(self):
        r = self._normalizar_y_descargar("101 555")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("DESCARGA run=555 modo=completa", r.stdout)
        self.assertTrue((self.prod / "555/ddd-state-555-M07/cache/t_m06_distritos.geojson.zip").is_file())
        self.assertFalse((self.prod / "101/ddd-state-101-M01").exists())

    def test_paralelo_con_limite(self):
        # Seis runs a la vez por defecto; el límite se lee del entorno (DDD_DESCARGAS_PARALELAS).
        texto = _step("Recuperar ejecución solicitada como fuente transitoria")
        self.assertIn('xargs -P "${DDD_DESCARGAS_PARALELAS:-6}" -n 1', texto)

    def test_lote_con_comas_y_espacios_una_raiz_por_run(self):
        r = self._normalizar_y_descargar("101, 202 303")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._rutas(""), [f"{i} {self.prod}/{i} .ddd-publication/publicacion_visor_{i}.json"
                                           for i in ("101", "202", "303")])

    def test_run_que_no_descarga_para_el_lote_y_lo_nombra(self):
        r = self._normalizar_y_descargar("101 999 303")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("LOTE_RECHAZADO: el run 999 no se pudo descargar", r.stdout)
        self.assertNotIn("LOTE_RECHAZADO: el run 303", r.stdout)

    def test_lista_invalida_o_duplicada_no_descarga_nada(self):
        for ids in ("101 abc", "101,101"):
            r = self._normalizar_y_descargar(ids)
            self.assertNotEqual(r.returncode, 0, ids)
            self.assertFalse(self.descargas.exists(), ids)

    def test_solo_separadores_es_error_explicito(self):
        r = self._normalizar_y_descargar(" , ")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("LOTE_VACIO", r.stdout)


class AcreditarYDescribirTodoONada(_Entorno):
    """Pasos Acreditar y Validar descriptores con un `python` falso que rechaza el run 202."""

    def setUp(self):
        super().setUp()
        self.llamadas = self.tmp / "python.log"
        fake = self.bin / "python"
        fake.write_text(f"""#!/usr/bin/env bash
echo "$*" >> {self.llamadas}
args=" $* "
if [[ "$args" == *" merge-descriptors "* ]]; then exec {sys.executable} "$@"; fi
run=""; out=""; prev=""
for a in "$@"; do
  [[ "$prev" == --requested-run-id || "$prev" == --run-id ]] && run="$a"
  [[ "$prev" == --output ]] && out="$a"
  prev="$a"
done
[[ "$run" == 202 ]] && {{ echo "Publicación bloqueada: run $run sin M06 certificado" >&2; exit 1; }}
if [[ "$args" == *" describe-production "* ]]; then
  printf '[{{"id": "m08-t%s-%s", "territory_id": "t%s", "run_id": "%s"}}]' "$run" "$run" "$run" "$run" > "$out"
fi
""", encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.descriptores = self.tmp / "product-descriptors.json"

    def _paso(self, nombre, ids):
        self.assertEqual(self._bash(_step("Normalizar lote de ejecuciones solicitadas").replace(
            "python herramientas", f"{sys.executable} herramientas"), ids).returncode, 0)
        script = _step(nombre).replace("/tmp/product-descriptors", str(self.tmp / "product-descriptors"))
        return self._bash(script, ids)

    def test_acreditar_evalua_todos_y_nombra_el_que_falla(self):
        r = self._paso("Acreditar identidad de la ejecución descargada", "101 202 303")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("LOTE_RECHAZADO: no acreditan 202", r.stdout)
        self.assertIn("run 202 sin M06", r.stderr)
        self.assertIn("--requested-run-id 303", self.llamadas.read_text(encoding="utf-8"))

    def test_descriptor_fallido_no_deja_lista_para_promover(self):
        r = self._paso("Validar descriptores de todo el lote antes de escribir", "101 202 303")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("sin producto publicable en 202", r.stdout)
        self.assertFalse(self.descriptores.exists())

    def test_lote_valido_une_descriptores(self):
        r = self._paso("Validar descriptores de todo el lote antes de escribir", "101 303")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([d["run_id"] for d in json.loads(self.descriptores.read_text(encoding="utf-8"))], ["101", "303"])

    def test_un_id_mismos_argumentos_que_antes(self):
        r = self._paso("Acreditar identidad de la ejecución descargada", "101")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.llamadas.read_text(encoding="utf-8").split("\n")[-2],
                         f"herramientas/evaluar_publicacion_visor.py --requested-run-id 101 --production-root {self.prod} "
                         "--phase source --output .ddd-publication/publicacion_visor.json --strict-request")


class Estructura(unittest.TestCase):
    def test_todo_se_valida_antes_del_primer_blob_y_un_solo_commit(self):
        names = [s.get("name", "") for s in _steps()]
        idx = {n: i for i, n in enumerate(names)}
        self.assertLess(idx["Normalizar lote de ejecuciones solicitadas"], idx["Recuperar ejecución solicitada como fuente transitoria"])
        self.assertLess(idx["Acreditar identidad de la ejecución descargada"], idx["Validar descriptores de todo el lote antes de escribir"])
        self.assertLess(idx["Validar descriptores de todo el lote antes de escribir"], idx["Promover productos a blob persistente verificable"])
        promover = _step("Promover productos a blob persistente verificable")
        self.assertNotIn("describe-production", promover)
        text = PUBLISHER.read_text(encoding="utf-8")
        self.assertEqual(text.count("git commit"), 1)
        self.assertEqual(text.count("actions/deploy-pages@"), 1)

    def test_puerta_produccion_intacta(self):
        job = yaml.safe_load(P50.read_text(encoding="utf-8"))["jobs"]["preparar_publicacion"]
        self.assertEqual(job["environment"], "${{ (github.event_name == 'workflow_dispatch' && github.actor != 'github-actions[bot]' && github.actor != 'ddd-registro[bot]' && github.workflow == 'P50 Publicación') && 'produccion' || '' }}")


if __name__ == "__main__":
    unittest.main()
