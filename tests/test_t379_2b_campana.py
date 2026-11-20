"""T-379 PR 2b (D-163, 2b mínima; diseño T-378 §3, §4 y §5): entrada oculta `campana` en P10, P20 y P30.

- Sin campaña, los tres ficheros se comportan como antes: `tests/_t379_2b.deshacer(actual)` es IGUAL a la versión anterior congelada en
  `tests/fixtures/t379_2b_workflows/` (sha256 abajo; si falta o cambia, falla).
- Permisos: ningún job pide más que `contents: read`/`actions: read`. El push a main va con el token de la app de registro, que no
  depende de GITHUB_TOKEN: `contents: read` NO es barrera para ese push. La garantía «la campaña no escribe en main» es:
  (a) los jobs (en P30, los pasos) que registran se saltan con `campana` no vacía; (b) no hay push ni herramienta de registro fuera de
  esa lista cerrada; (c) el entorno `registro` (PR 2a).
- Ruta de campaña: sin los jobs de registro, la cadena de cada fichero es una serie (nunca dos jobs a la vez, §3) y solo usa grupos de
  concurrencia con el territorio (los globales, como `ddd-catalog-promotion`, quedan en jobs de registro saltados, §5).
Cada comprobación lleva su control negativo.
"""
import copy
import hashlib
import re
import unittest
from pathlib import Path

import yaml

from tests._t379_2b import M04_SERIE, PERSIST_CAMPANA, SIN_CAMPANA, deshacer
from tests._t379_3b import deshacer as deshacer_3b
from tests._uses_sin_version import cargar

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t379_2b_workflows"
HUELLAS = {
    "p10-fuentes": "bfffcdb3986093c65d7d6aa80f4f3b9634ec821665dc5940e185f6026bd575c4",
    "p20-distritos": "20234a06c6785a018731b736524e23aef31d796cb7de046f8134266c87a2aaa8",
    "p30-resultados-electorales": "18cd270112b9aa4dd3537456067faa5fdcbd9ff912222975118d5b759119e4b5",
}
REGISTRO = re.compile(r"promover_catalogo_tras_preparacion|promover_catalogo_operacional|registrar_par_fuentes_legislatura|"
                      r"persistir_estado_operativo_compartido|persistir_producto_electoral_operacional|persistir_evidencia_pre_m04_operacional|"
                      r"git push|registrar_en_main|archivo_origen|DDD_REGISTRO_APP")
# Lista cerrada: (fichero, job) que registran en main; en P30, (fichero, job, paso).
JOBS_REGISTRO = {
    ("p10-fuentes", "p11_registrar"), ("p10-fuentes", "p11_generation_pending"), ("p10-fuentes", "p12_registrar"),
    ("p20-distritos", "pre_m04_evidence"), ("p20-distritos", "pre_m04_diagnostic"), ("p20-distritos", "registrar"),
}
PASOS_REGISTRO = {
    ("p30-resultados-electorales", "incorporar", "Credencial de registro"),
    ("p30-resultados-electorales", "incorporar", "Archivo en origen — M08 a R2 y votos por partido a git"),
    ("p30-resultados-electorales", "incorporar", "Registrar disponibilidad del producto electoral"),
}
# Paso que prepara el registro de P30 sin registrar (carga el persistidor de main); también se salta con campaña.
PASOS_PREVIOS = {("p30-resultados-electorales", "incorporar", "Cargar persistidor vigente compatible con main")}
RAMA_P10 = {"p11": "p11_", "p12": "p12_"}


def leer(nombre):
    return yaml.safe_load((WF / f"{nombre}.yml").read_text(encoding="utf-8"))


def needs(job):
    n = job.get("needs") or []
    return {n} if isinstance(n, str) else set(n)


def registro_sin_condicion(docs):
    """Jobs o pasos que registran sin `!inputs.campana`, o que registran sin estar en la lista cerrada."""
    malos = []
    for n, d in docs.items():
        for j, job in d["jobs"].items():
            pasos = [s for s in job.get("steps") or [] if REGISTRO.search(yaml.safe_dump(s))]
            if not pasos:
                continue
            if (n, j) in JOBS_REGISTRO:
                if not str(job.get("if", "")).endswith(SIN_CAMPANA):
                    malos.append((n, j))
                continue
            for s in pasos:
                clave = (n, j, s.get("name"))
                if clave not in PASOS_REGISTRO or not str(s.get("if", "")).endswith(SIN_CAMPANA):
                    malos.append(clave)
    return sorted(malos)


def ruta_de_campana(d, prefijo=None):
    """Jobs que pueden correr con campaña: fuera los que llevan `!inputs.campana` y, en P10, los de la otra rama (tipo)."""
    out = {}
    for j, job in d["jobs"].items():
        if str(job.get("if", "")).endswith(SIN_CAMPANA):
            continue
        if prefijo and (j.startswith("p11_") or j.startswith("p12_")) and not j.startswith(prefijo):
            continue
        out[j] = job
    return out


def paralelos(jobs):
    """Pares de jobs de la ruta que no dependen uno del otro (podrían correr a la vez)."""
    anc = {}

    def a(j):
        if j not in anc:
            anc[j] = set()
            for n in needs(jobs[j]) & set(jobs):
                anc[j] |= {n} | a(n)
        return anc[j]

    js = sorted(jobs)
    return [(x, y) for i, x in enumerate(js) for y in js[i + 1:] if x not in a(y) and y not in a(x)]


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Capa 2b: los ficheros reales con la 3b deshecha (la 3b hace correr los registros en ensayo con campaña; sus reglas
        # sobre el fichero real las fija tests/test_t379_3b_workflows.py).
        cls.docs = {n: deshacer_3b(n, leer(n)) for n in HUELLAS}


class Equivalencia(Base):
    def test_copias_congeladas_con_su_huella(self):
        for n, sha in HUELLAS.items():
            f = FIX / f"{n}_1.0.0.yml"
            self.assertTrue(f.is_file(), f)
            self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(), sha, f)

    def test_sin_campana_igual_que_antes(self):
        for n in HUELLAS:
            with self.subTest(workflow=n):
                antes = cargar((FIX / f"{n}_1.0.0.yml").read_text(encoding="utf-8"))
                ahora = cargar((WF / f"{n}.yml").read_text(encoding="utf-8"))
                self.assertEqual(deshacer(n, ahora), antes)

    def test_control_negativo_equivalencia(self):
        casos = {
            "p10-fuentes": lambda d: d["jobs"]["p11_registrar"].__setitem__("if", "${{ !inputs.campana }}"),
            "p20-distritos": lambda d: d["jobs"]["m04"].__setitem__("needs", ["entrada"]),
            "p30-resultados-electorales": lambda d: next(s for s in d["jobs"]["incorporar"]["steps"]  # por nombre: el último es la captura de la 3b
                                                         if s.get("name") == "Registrar disponibilidad del producto electoral").__setitem__("if", "${{ always() }}"),
        }
        for n, mutar in casos.items():
            with self.subTest(workflow=n):
                antes = cargar((FIX / f"{n}_1.0.0.yml").read_text(encoding="utf-8"))
                ahora = cargar((WF / f"{n}.yml").read_text(encoding="utf-8"))
                mutar(ahora)
                self.assertNotEqual(deshacer(n, ahora), antes)

    def test_campana_solo_por_workflow_call_y_vacia_por_defecto(self):
        for n, d in self.docs.items():
            on = d.get("on") or d.get(True)
            self.assertEqual(on["workflow_call"]["inputs"]["campana"], {"required": False, "type": "string", "default": ""}, n)
            self.assertNotIn("campana", (on.get("workflow_dispatch") or {}).get("inputs") or {}, n)


class Permisos(Base):
    @staticmethod
    def escrituras(docs):
        out = []
        for n, d in docs.items():
            for donde, p in [("<workflow>", d.get("permissions"))] + [(j, job.get("permissions")) for j, job in d["jobs"].items()]:
                for k, v in (p or {}).items():
                    if v != "read":
                        out.append((n, donde, k, v))
        return out

    def test_nadie_pide_mas_que_lectura(self):
        self.assertEqual(self.escrituras(self.docs), [])
        for n, d in self.docs.items():
            self.assertEqual(d["permissions"], {"contents": "read", "actions": "read"}, n)

    def test_control_negativo_permisos(self):
        docs = copy.deepcopy(self.docs)
        docs["p20-distritos"]["jobs"]["resolver_interfaz"]["permissions"]["issues"] = "write"
        self.assertEqual(self.escrituras(docs), [("p20-distritos", "resolver_interfaz", "issues", "write")])

    def test_la_credencial_no_cae_en_github_token(self):
        for n, d in self.docs.items():
            for j, job in d["jobs"].items():
                for s in job.get("steps") or []:
                    if s.get("name") == "Credencial de registro":
                        self.assertNotIn("Registro con github.token", s["run"], (n, j))
                        self.assertIn("exit 1", s["run"].split("\n")[1], (n, j))


class Persistencia(Base):
    """Con campaña, P10 fuerza `persist_state=false`: sin él, `p11_resultado`/`p12_resultado` darían FAILURE REGISTRATION_SKIPPED (exit 56)."""

    def resueltos(self, d):
        out = []
        for j in ("p11_resolver", "p12_resolver"):
            for s in d["jobs"][j]["steps"]:
                if "PERSIST_INPUT" in (s.get("env") or {}):
                    out.append((j, s["env"]["PERSIST_INPUT"]))
        return out

    def test_campana_fuerza_sin_persistencia(self):
        self.assertEqual(self.resueltos(self.docs["p10-fuentes"]), [("p11_resolver", PERSIST_CAMPANA), ("p12_resolver", PERSIST_CAMPANA)])

    def test_terminal_con_registro_saltado(self):
        import subprocess
        import sys
        import json
        def terminal(persist):
            r = subprocess.run([sys.executable, "herramientas/evaluar_persistencia_preparacion.py", "terminal", "--preparation-result", "success",
                                "--registration-result", "skipped", "--persist-state", persist], cwd=ROOT, capture_output=True, text=True)
            return r.returncode, r.stdout
        rc, out = terminal("false")
        self.assertEqual(rc, 0, out)
        self.assertIn("PERSISTENCE_NOT_REQUIRED", out)
        rc, out = terminal("true")  # control negativo: lo que pasaría sin forzar
        self.assertNotEqual(rc, 0)
        self.assertIn("REGISTRATION_SKIPPED", out)

    def test_control_negativo_persistencia(self):
        d = copy.deepcopy(self.docs["p10-fuentes"])
        for s in d["jobs"]["p12_resolver"]["steps"]:
            if "PERSIST_INPUT" in (s.get("env") or {}):
                s["env"]["PERSIST_INPUT"] = "${{ toJSON(inputs.persist_state) }}"
        self.assertNotEqual(self.resueltos(d), self.resueltos(self.docs["p10-fuentes"]))


class Registro(Base):
    def test_lista_cerrada_y_condicion_de_campana(self):
        self.assertEqual(registro_sin_condicion(self.docs), [])
        for n, j in JOBS_REGISTRO:
            self.assertTrue(self.docs[n]["jobs"][j]["if"].endswith(SIN_CAMPANA), (n, j))
        for n, j, p in PASOS_REGISTRO | PASOS_PREVIOS:
            paso = next(s for s in self.docs[n]["jobs"][j]["steps"] if s.get("name") == p)
            self.assertTrue(paso["if"].endswith(SIN_CAMPANA), (n, j, p))

    def test_control_negativo_registro(self):
        docs = copy.deepcopy(self.docs)
        docs["p20-distritos"]["jobs"]["registrar"]["if"] = "${{ always() }}"
        m05 = docs["p20-distritos"]["jobs"]["m05"]
        m05["steps"] = m05["steps"] + [{"name": "intruso", "run": "git push origin HEAD:main"}]  # lista nueva: P20 comparte pasos por anclas YAML
        self.assertEqual(registro_sin_condicion(docs), [("p20-distritos", "m05", "intruso"), ("p20-distritos", "registrar")])


class RutaDeCampana(Base):
    def test_cada_cadena_es_una_serie(self):
        self.assertEqual(paralelos(ruta_de_campana(self.docs["p20-distritos"])), [])
        self.assertEqual(paralelos(ruta_de_campana(self.docs["p30-resultados-electorales"])), [])
        for rama, prefijo in RAMA_P10.items():
            with self.subTest(rama=rama):
                self.assertEqual(paralelos(ruta_de_campana(self.docs["p10-fuentes"], prefijo)), [])

    def test_m04_detras_de_pre_m04_evidence(self):
        m04 = self.docs["p20-distritos"]["jobs"]["m04"]
        self.assertIn("pre_m04_evidence", m04["needs"])
        self.assertTrue(m04["if"].endswith(M04_SERIE))  # en éxito o saltado (hoy, sin campaña, siempre saltado cuando m04 corre)
        self.assertIn("!(needs.entrada.outputs.preflight_only == 'true')", m04["if"])
        self.assertIn("(needs.entrada.outputs.preflight_only == 'true')", self.docs["p20-distritos"]["jobs"]["pre_m04_evidence"]["if"])

    def test_control_negativo_serie(self):
        d = copy.deepcopy(self.docs["p20-distritos"])
        d["jobs"]["pre_m04_evidence"]["if"] = "${{ always() }}"  # deja de saltarse con campaña
        d["jobs"]["m04"]["needs"] = ["entrada", "resolve", "internal_units"]  # y m04 ya no espera
        self.assertIn(("m04", "pre_m04_evidence"), paralelos(ruta_de_campana(d)))

    @staticmethod
    def grupos_sin_territorio(docs):
        out = []
        for n, d in docs.items():
            prefijos = list(RAMA_P10.values()) if n == "p10-fuentes" else [None]
            for prefijo in prefijos:
                for j, job in ruta_de_campana(d, prefijo).items():
                    g = str((job.get("concurrency") or {}).get("group", "")) if isinstance(job.get("concurrency"), dict) else str(job.get("concurrency") or "")
                    if g and not re.search(r"territor", g):
                        out.append((n, j, g))
        return sorted(set(out))

    def test_ruta_de_campana_sin_grupos_globales(self):
        self.assertEqual(self.grupos_sin_territorio(self.docs), [])
        # los globales siguen donde estaban, en jobs de registro (saltados con campaña)
        grupos = {(n, j) for n, d in self.docs.items() for j, job in d["jobs"].items()
                  if isinstance(job.get("concurrency"), dict) and job["concurrency"].get("group") == "ddd-catalog-promotion"}
        self.assertTrue(grupos)
        self.assertLessEqual(grupos, JOBS_REGISTRO)

    def test_control_negativo_grupos(self):
        docs = copy.deepcopy(self.docs)
        docs["p20-distritos"]["jobs"]["m05"]["concurrency"] = {"group": "ddd-catalog-promotion", "cancel-in-progress": False}
        self.assertEqual(self.grupos_sin_territorio(docs), [("p20-distritos", "m05", "ddd-catalog-promotion")])


if __name__ == "__main__":
    unittest.main()
