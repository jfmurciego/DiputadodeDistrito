"""T-379 PR 2a (D-147, opción a; diseño T-378 §10 y §16.3): los secretos de la app de registro (`DDD_REGISTRO_APP_ID`/`KEY`) solo los usan
jobs con `environment: registro` (entorno sin revisores con ramas de despliegue = main). Desde una rama o una PR esos jobs no reciben los
secretos (un job con entorno desde una ref no permitida falla), así que «la rama no escribe en main» deja de ser solo norma del código.

Equivalencia: `tests/_t379_2a.deshacer(actual)` es IGUAL a la versión anterior congelada en `tests/fixtures/t379_2a_workflows/` (sha256
abajo; si falta o cambia, el test falla). Cada comprobación lleva su control negativo.
"""
import copy
import hashlib
import unittest
from pathlib import Path

import yaml

from tests._t379_2a import APP, REGISTRO_PR, deshacer, es_registro
from tests._uses_sin_version import cargar

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t379_2a_workflows"
HUELLAS = {
    "auto-merge": ("1.3.1", "9b50b3c95b76d2fd2c6f988c0b8989124331750856224805e88179761bb83507"),
    "ejecucion-completa-proyecto": ("1.11.5", "0020929dad33a797344e5465afa579496b03a2facd959ef4e47ee1d4bf37cac8"),
    "p10-fuentes": ("1.0.0", "bfffcdb3986093c65d7d6aa80f4f3b9634ec821665dc5940e185f6026bd575c4"),
    "p20-distritos": ("1.0.0", "20234a06c6785a018731b736524e23aef31d796cb7de046f8134266c87a2aaa8"),
    "p30-resultados-electorales": ("1.0.0", "18cd270112b9aa4dd3537456067faa5fdcbd9ff912222975118d5b759119e4b5"),
    "p40-publicacion": ("1.1.0", "83ff6b15487ab4cb2e1fcb49a630f9e54363e2637300859fce1979bfa5bbf741"),
    "p70-archivo": ("1.0.0", "ddb3166791def05e71d60cbc48e48dab3a98ca3dc07ce0417d4c3688af2651f3"),
    "p90-automatico": ("1.1.0", "473b6bc87f97383fdd412236e7ff3e801ccd3e7e752e65472aa56caf8e7d9a3a"),
    "preparacion-legislatura-vigente": ("1.0.12", "b96beddd60487e4937e40e2ca5d5652efe4a739ed91e13f8ba7bce6e79cc8245"),
}
# Inventario de §10 tras la 2a: 25 usos. En P40 `publicar` cede el registro a `registrar`; en P70 `podar` a `registrar_poda`.
INVENTARIO = {
    ("auto-merge.yml", "fusionar"),
    ("ejecucion-completa-proyecto.yml", "detectar_recuperacion_electoral"), ("ejecucion-completa-proyecto.yml", "actualizar_estado"),
    ("ejecucion-completa-proyecto.yml", "manifestar"),
    ("p10-fuentes.yml", "p11_registrar"), ("p10-fuentes.yml", "p11_generation_pending"), ("p10-fuentes.yml", "p12_registrar"),
    ("p20-distritos.yml", "pre_m04_evidence"), ("p20-distritos.yml", "pre_m04_diagnostic"), ("p20-distritos.yml", "registrar"),
    ("p30-resultados-electorales.yml", "incorporar"),
    ("p40-publicacion.yml", "preparar"), ("p40-publicacion.yml", "registrar"),
    *(("p70-archivo.yml", j) for j in ("archivar_r2", "resolver_producto", "acreditar", "registrar", "acreditar_registro", "extraer_m06",
                                       "registrar_poda")),
    *(("p90-automatico.yml", j) for j in ("catalogo", "resultados", "numeracion", "metricas")),
    ("preparacion-legislatura-vigente.yml", "registrar_par"),
}
# Jobs con la app en workflows con `pull_request` cuyo `if` no nombra el evento: no corren en PR porque dependen de un job que lo excluye.
SIN_PR_POR_DEPENDENCIA = {("ejecucion-completa-proyecto.yml", "actualizar_estado"): "puerta_01"}


def usos_app(docs):
    return {(f, j) for f, d in docs.items() for j, job in (d.get("jobs") or {}).items() if APP in yaml.safe_dump(job)}


def sin_entorno(docs):
    return sorted((f, j) for f, j in usos_app(docs) if not es_registro(docs[f]["jobs"][j].get("environment")))


def on(d):
    return d.get("on") or d.get(True)


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = {p.name: yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(WF.glob("*.yml"))}


class Huellas(Base):
    def test_copias_congeladas_con_su_huella(self):
        for n, (v, sha) in HUELLAS.items():
            f = FIX / f"{n}_{v}.yml"
            self.assertTrue(f.is_file(), f)
            self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(), sha, f)

    def test_deshacer_la_2a_da_la_version_anterior(self):
        for n, (v, _) in HUELLAS.items():
            with self.subTest(workflow=n):
                antes = cargar((FIX / f"{n}_{v}.yml").read_text(encoding="utf-8"))
                ahora = cargar((WF / f"{n}.yml").read_text(encoding="utf-8"))
                self.assertEqual(deshacer(n, ahora), antes)

    def test_control_negativo_equivalencia(self):
        casos = {
            "p40-publicacion": lambda d: d["jobs"]["registrar"]["steps"][-1].__setitem__("run", d["jobs"]["registrar"]["steps"][-1]["run"].replace("exit 48", "exit 0")),
            "p70-archivo": lambda d: d["jobs"]["registrar_poda"].__setitem__("if", "${{ always() }}") or d["jobs"]["podar"]["steps"][0].__setitem__("with", {"ref": "otra"}),
            "p10-fuentes": lambda d: d["jobs"]["p11_registrar"].__setitem__("environment", "produccion"),
            "auto-merge": lambda d: d["jobs"]["fusionar"].__setitem__("runs-on", "ubuntu-latest"),
        }
        for n, mutar in casos.items():
            with self.subTest(workflow=n):
                v = HUELLAS[n][0]
                antes = cargar((FIX / f"{n}_{v}.yml").read_text(encoding="utf-8"))
                ahora = cargar((WF / f"{n}.yml").read_text(encoding="utf-8"))
                mutar(ahora)
                self.assertNotEqual(deshacer(n, ahora), antes)


class Entorno(Base):
    def test_todo_job_con_la_app_declara_registro(self):
        self.assertEqual(sin_entorno(self.docs), [])

    def test_control_negativo_job_sin_entorno(self):
        docs = copy.deepcopy(self.docs)
        docs["p20-distritos.yml"]["jobs"]["registrar"].pop("environment")
        docs["p40-publicacion.yml"]["jobs"]["registrar"]["environment"] = "produccion"
        self.assertEqual(sin_entorno(docs), [("p20-distritos.yml", "registrar"), ("p40-publicacion.yml", "registrar")])

    def test_inventario_de_usos(self):
        self.assertEqual(usos_app(self.docs), INVENTARIO)
        self.assertEqual(len(INVENTARIO), 25)

    def test_en_las_pr_ningun_job_con_entorno_registro(self):
        """En workflows con `pull_request`, un job con la app o lleva el entorno condicional, o su `if` excluye el evento, o depende de un job
        que lo excluye. Si no, el humo de cada PR fallaría con el despliegue rechazado."""
        def malos(docs):
            out = []
            for f, j in sorted(usos_app(docs)):
                d = docs[f]
                if "pull_request" not in on(d):
                    continue
                job = d["jobs"][j]
                cond = str(job.get("if", ""))
                if job.get("environment") == REGISTRO_PR or "github.event_name == 'push'" in cond or "github.event_name == 'schedule'" in cond \
                        or "github.event_name != 'pull_request'" in cond:
                    continue
                previo = SIN_PR_POR_DEPENDENCIA.get((f, j))
                if previo and f"needs.{previo}.result == 'success'" in cond and "github.event_name != 'pull_request'" in str(d["jobs"][previo]["if"]):
                    continue
                out.append((f, j))
            return out
        self.assertEqual(malos(self.docs), [])
        docs = copy.deepcopy(self.docs)
        docs["ejecucion-completa-proyecto.yml"]["jobs"]["manifestar"]["environment"] = "registro"
        docs["ejecucion-completa-proyecto.yml"]["jobs"]["puerta_01"]["if"] = "${{ always() }}"
        self.assertEqual(malos(docs), [("ejecucion-completa-proyecto.yml", "actualizar_estado"), ("ejecucion-completa-proyecto.yml", "manifestar")])

    def test_entorno_condicional_solo_donde_hay_pr(self):
        for f, d in self.docs.items():
            for j, job in d["jobs"].items():
                if job.get("environment") == REGISTRO_PR:
                    self.assertIn("pull_request", on(d), (f, j))


class JobsPartidos(Base):
    def test_p40_puerta_humana_en_aprobar_y_registro_aparte(self):
        j = self.docs["p40-publicacion.yml"]["jobs"]
        antes = yaml.safe_load((FIX / "p40-publicacion_1.1.0.yml").read_text(encoding="utf-8"))["jobs"]["preparar"]["environment"]
        cond = antes.removeprefix("${{ ").removesuffix(" && 'produccion' || '' }}")
        self.assertEqual(j["aprobar"]["environment"], "produccion")
        self.assertEqual(j["aprobar"]["if"], "${{ needs.resolver.outputs.publicar == 'true' && " + cond + " }}")
        self.assertNotIn(APP, yaml.safe_dump(j["aprobar"]))
        self.assertEqual(j["preparar"]["needs"], ["resolver", "aprobar"])
        self.assertIn("!cancelled()", j["preparar"]["if"])
        self.assertIn("needs.aprobar.result == 'skipped'", j["preparar"]["if"])
        self.assertEqual(j["preparar"]["concurrency"]["group"], "ddd-shared-operational-state")  # §16.4
        self.assertNotIn(APP, yaml.safe_dump(j["publicar"]))
        self.assertEqual(j["publicar"]["environment"]["name"], "github-pages")
        self.assertEqual(j["registrar"]["needs"], "publicar")
        self.assertNotIn("concurrency", j["registrar"])  # jobs de registro sin grupo (T-360)
        self.assertIn("needs.publicar.outputs.registro_pendiente == 'true'", j["registrar"]["if"])
        self.assertEqual(j["registrar"]["steps"][0]["with"]["ref"], "${{ needs.publicar.outputs.base_sha }}")

    def test_p40_el_parche_se_sube_y_se_aplica_con_el_mismo_nombre(self):
        j = self.docs["p40-publicacion.yml"]["jobs"]
        sube = next(s for s in j["publicar"]["steps"] if s.get("name") == "Conservar el parche del registro")
        baja = next(s for s in j["registrar"]["steps"] if str(s.get("uses", "")).startswith("actions/download-artifact"))
        self.assertEqual(sube["with"]["name"], baja["with"]["name"])
        self.assertEqual(sube["with"]["path"], baja["with"]["path"])
        self.assertEqual(sube["with"]["retention-days"], 1)
        # el commit del parche sigue después del despliegue y solo desde main
        per = next(s for s in j["publicar"]["steps"] if s.get("name") == "Persistir registro sólo después del despliegue")["run"]
        self.assertLess(per.index("exit 45"), per.index("git format-patch"))
        self.assertNotIn("git push", per)

    def test_p70_borrado_tras_produccion_y_registro_despues(self):
        j = self.docs["p70-archivo.yml"]["jobs"]
        self.assertEqual(j["podar"]["environment"], "${{ !inputs.simular && 'produccion' || '' }}")
        self.assertEqual(j["podar"]["permissions"], {"contents": "read"})
        self.assertNotIn(APP, yaml.safe_dump(j["podar"]))
        self.assertNotIn("git push", yaml.safe_dump(j["podar"]))
        r = j["registrar_poda"]
        self.assertEqual(r["needs"], "podar")
        self.assertTrue(r["if"].startswith("${{ always() && inputs.accion == 'P73 Podar' && !inputs.simular"))
        self.assertNotIn("R2_SECRET_ACCESS_KEY", yaml.safe_dump(r))  # el registro solo recibe salidas, no los secretos de R2
        sube = next(s for s in j["podar"]["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact"))
        baja = next(s for s in r["steps"] if str(s.get("uses", "")).startswith("actions/download-artifact"))
        self.assertEqual(sube["with"]["name"], baja["with"]["name"])

    def test_control_negativo_partidos(self):
        docs = copy.deepcopy(self.docs)
        docs["p40-publicacion.yml"]["jobs"]["aprobar"]["environment"] = "registro"
        with self.assertRaises(AssertionError):
            JobsPartidos.test_p40_puerta_humana_en_aprobar_y_registro_aparte(type("X", (JobsPartidos,), {"docs": docs})("test_p40_puerta_humana_en_aprobar_y_registro_aparte"))
        docs = copy.deepcopy(self.docs)
        docs["p70-archivo.yml"]["jobs"]["podar"]["env"]["APP_ID"] = "${{ " + APP + " }}"
        with self.assertRaises(AssertionError):
            JobsPartidos.test_p70_borrado_tras_produccion_y_registro_despues(type("X", (JobsPartidos,), {"docs": docs})("test_p70_borrado_tras_produccion_y_registro_despues"))


if __name__ == "__main__":
    unittest.main()
