"""T-379 PR 2a (D-147, opción a; D-162, opción A; diseño T-378 §10 y §16.3): los secretos de la app de registro (`DDD_REGISTRO_APP_ID`/`KEY`)
viven solo en entornos limitados a `main`: `registro` (sin revisores), `github-pages` y `produccion`. Todo job que usa la app declara uno de
ellos; desde una rama o una PR no recibe los secretos (un job con entorno desde una ref no permitida falla). Los jobs que ya tenían entorno
(P40 `publicar`, P70 `podar`) NO se parten (D-162: despliegue/borrado y registro siguen en el mismo job y el mismo grupo de concurrencia).

Equivalencia: `tests/_t379_2a.deshacer(actual)` es IGUAL a la versión anterior congelada en `tests/fixtures/t379_2a_workflows/` (sha256
abajo; si falta o cambia, el test falla). Cada comprobación lleva su control negativo.
"""
import copy
import hashlib
import unittest
from pathlib import Path

import yaml

from tests._t379_2a import APP, P40_PREPARAR, REGISTRO_PR, deshacer, es_registro
from tests._uses_sin_version import cargar

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t379_2a_workflows"
HUELLAS = {
    "auto-merge": ("1.3.2", "893d08a77c02ad5fedd30c68d6c2b934567d0f3f21f383dc6f768d312f8228b1"),
    "ejecucion-completa-proyecto": ("1.11.5", "0020929dad33a797344e5465afa579496b03a2facd959ef4e47ee1d4bf37cac8"),
    "p10-fuentes": ("1.0.1", "67ae63df4b96cabe5ecd27ab0e368974c9ff8663806a1a9bfa5dc889b13e6e1c"),
    "p20-distritos": ("1.0.1", "c787e3bcdced5d22f12194fc59feb9b3d75bb3dcf838e67b6862a0a0896a1732"),
    "p30-resultados-electorales": ("1.0.3", "0bb36d8cd475d38dd755474e80e8a2de863a7afeca8e2caac0899c568a8bc77b"),
    "p40-publicacion": ("1.5.0", "86f7487cc8fbe750b56d712929713c4e8b893492aa3f4c14990bf53657b8e64c"),
    "p70-archivo": ("1.1.5", "1dd7b7dbf3ed6911017bab1c85906fa249412f2e7408262e67268c6711943d91"),
    "p90-automatico": ("1.3.0", "708697af1a13c988dce81c7b39e954029c343bfb5a02e6065c82552f0b6abe7e"),
    "preparacion-legislatura-vigente": ("1.0.12", "b96beddd60487e4937e40e2ca5d5652efe4a739ed91e13f8ba7bce6e79cc8245"),
}
# Inventario de §10 (25 usos), rehecho sobre main el 23-11 (mismo conjunto que en e7747ea).
INVENTARIO = {
    ("auto-merge.yml", "fusionar"),
    ("ejecucion-completa-proyecto.yml", "detectar_recuperacion_electoral"), ("ejecucion-completa-proyecto.yml", "actualizar_estado"),
    ("ejecucion-completa-proyecto.yml", "manifestar"),
    ("p10-fuentes.yml", "p11_registrar"), ("p10-fuentes.yml", "p11_generation_pending"), ("p10-fuentes.yml", "p12_registrar"),
    ("p20-distritos.yml", "pre_m04_evidence"), ("p20-distritos.yml", "pre_m04_diagnostic"), ("p20-distritos.yml", "registrar"),
    ("p30-resultados-electorales.yml", "incorporar"),
    ("p40-publicacion.yml", "preparar"), ("p40-publicacion.yml", "publicar"),
    *(("p70-archivo.yml", j) for j in ("archivar_r2", "resolver_producto", "acreditar", "registrar", "acreditar_registro", "extraer_m06", "podar")),
    *(("p90-automatico.yml", j) for j in ("catalogo", "resultados", "numeracion", "metricas")),
    ("preparacion-legislatura-vigente.yml", "registrar_par"),
}
# Entornos con los secretos que no son `registro` (D-162). Cada uno: (fichero, job) -> entorno exacto.
OTROS_ENTORNOS = {
    ("p40-publicacion.yml", "preparar"): P40_PREPARAR,  # personas: produccion (T-41); robots: registro
    ("p40-publicacion.yml", "publicar"): {"name": "github-pages", "url": "${{ steps.deployment.outputs.page_url }}"},
    # en simulación no hay entorno ni secretos: la credencial cae en github.token y `podar` no registra (`!inputs.simular`)
    ("p70-archivo.yml", "podar"): "${{ !inputs.simular && 'produccion' || '' }}",
}
# Jobs con la app en workflows con `pull_request` cuyo `if` no nombra el evento: no corren en PR porque dependen de un job que lo excluye.
SIN_PR_POR_DEPENDENCIA = {("ejecucion-completa-proyecto.yml", "actualizar_estado"): "puerta_01"}


def usos_app(docs):
    return {(f, j) for f, d in docs.items() for j, job in (d.get("jobs") or {}).items() if APP in yaml.safe_dump(job)}


def sin_entorno(docs):
    return sorted((f, j) for f, j in usos_app(docs)
                  if not es_registro(docs[f]["jobs"][j].get("environment"))
                  and ((f, j) not in OTROS_ENTORNOS or docs[f]["jobs"][j].get("environment") != OTROS_ENTORNOS[(f, j)]))


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
            "p40-publicacion": lambda d: d["jobs"]["preparar"].__setitem__("environment", P40_PREPARAR.replace("'registro'", "'otro'")),
            "p70-archivo": lambda d: d["jobs"]["podar"]["steps"][0].__setitem__("with", {"ref": "otra"}),
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
        docs["p40-publicacion.yml"]["jobs"]["publicar"]["environment"] = "produccion"
        docs["p70-archivo.yml"]["jobs"]["podar"]["environment"] = "produccion"
        self.assertEqual(sin_entorno(docs), [("p20-distritos.yml", "registrar"), ("p40-publicacion.yml", "publicar"), ("p70-archivo.yml", "podar")])

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


class SinPartir(Base):
    """D-162: P40 `publicar` y P70 `podar` siguen en un solo job con su grupo (despliegue/borrado y registro juntos)."""

    def test_p40_y_p70_sin_jobs_nuevos(self):
        antes = {n: yaml.safe_load((FIX / f"{n}_{HUELLAS[n][0]}.yml").read_text(encoding="utf-8")) for n in ("p40-publicacion", "p70-archivo")}
        for n, d in antes.items():
            self.assertEqual(set(self.docs[f"{n}.yml"]["jobs"]), set(d["jobs"]), n)
        j = self.docs["p40-publicacion.yml"]["jobs"]
        self.assertEqual(j["publicar"]["concurrency"]["group"], "ddd-pages-prod")
        self.assertIn("git push origin HEAD:main", yaml.safe_dump(j["publicar"]))
        self.assertEqual(self.docs["p70-archivo.yml"]["jobs"]["podar"]["concurrency"]["group"], "archivar-artefactos-r2")

    def test_puerta_humana_de_preparar_intacta(self):
        antes = yaml.safe_load((FIX / f"p40-publicacion_{HUELLAS['p40-publicacion'][0]}.yml").read_text(encoding="utf-8"))["jobs"]["preparar"]["environment"]
        self.assertEqual(self.docs["p40-publicacion.yml"]["jobs"]["preparar"]["environment"], antes.replace("|| ''", "|| 'registro'"))


if __name__ == "__main__":
    unittest.main()
