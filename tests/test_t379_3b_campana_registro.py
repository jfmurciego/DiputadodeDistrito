"""T-379 PR 3b (diseño T-378 §5-§6, D-147; opción A del Planificador, 19-11): registro en ensayo y re-aplicación en el cierre.

Repositorios git temporales (nunca el remoto real) y almacén local (nunca R2). Cada regla con su control negativo:
- `ensayo`: `origin` pasa a un repositorio local con `main` y la rama del run; un push nunca sale a GitHub.
- `capturar`: el cambio que el registro dejó en el ensayo (delta por claves en JSON, ficheros nuevos tal cual, texto
  versionado con su base para la fusión a tres bandas); rutas ⊆ RUTAS_ROBOT + catalogo_preparacion.yaml (D-147).
- `componer`: el cierre re-aplica, en orden, las capturas de los territorios sanos sobre `main`; lo ajeno se conserva y
  un choque de texto falla cerrado (CIERRE_CONFLICTO).
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT))
import campana_estado as ce  # noqa: E402
import campana_registro as cr  # noqa: E402

CATALOGO = "configuracion/catalogo_preparacion.yaml"
ARCHIVO = "orchestracion/archivo_r2.json"


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


def escribir(root, rel, texto):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(texto, encoding="utf-8")


class Base(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.alm = ce.AlmacenLocal(self.tmp / "alm")
        self.origen = self.tmp / "origen"
        self.origen.mkdir()
        git(self.origen, "init", "-q", "-b", "main")
        escribir(self.origen, ARCHIVO, json.dumps({"artefactos": {"viejo": {"run_id": "1"}}}, indent=1) + "\n")
        escribir(self.origen, CATALOGO, "territories:\n  aut11:\n    estado: viejo\n\n  nac22:\n    estado: viejo\n")
        git(self.origen, "add", "-A")
        git(self.origen, "commit", "-qm", "base")

    def tearDown(self):
        self._td.cleanup()

    def clon(self, nombre):
        d = self.tmp / nombre
        git(self.tmp, "clone", "-q", "--depth", "1", f"file://{self.origen}", str(d))
        return d

    def registrar_en_ensayo(self, territorio, orden, cambios, nombre="registrar"):
        """Un job de registro: ensayo → la herramienta escribe y empuja a `origin` → captura a R2."""
        w = self.clon(f"w-{territorio}-{orden}")
        base = cr.ensayo(w, self.tmp / f"ensayo-{territorio}-{orden}.git", "main", self.alm, "900", territorio, orden)
        for rel, texto in cambios.items():
            escribir(w, rel, texto)
        git(w, "add", "-A")
        git(w, "commit", "-qm", "registro")
        git(w, "push", "-q", "origin", "HEAD:refs/heads/main")
        return cr.capturar(w, base, "main", self.alm, "900", territorio, orden, nombre, 1)


class Ensayo(Base):
    def test_origin_local_y_el_remoto_real_intacto(self):
        w = self.clon("w")
        cr.ensayo(w, self.tmp / "e.git", "main", self.alm, "900", "aut11", 10)
        self.assertTrue(git(w, "remote", "get-url", "origin").startswith("file://"))
        self.assertNotIn(str(self.origen), git(w, "remote", "get-url", "origin"))
        escribir(w, ARCHIVO, "{}\n")
        git(w, "commit", "-qam", "x")
        git(w, "push", "-q", "origin", "HEAD:refs/heads/main")
        self.assertEqual(git(self.origen, "rev-list", "--count", "main"), "1")  # nada llegó al remoto real

    def test_reaplica_lo_anterior_del_mismo_territorio(self):
        self.registrar_en_ensayo("aut11", 10, {"datos/x.json": '{"a": 1}\n'})
        w = self.clon("w2")
        cr.ensayo(w, self.tmp / "e2.git", "main", self.alm, "900", "aut11", 11)
        self.assertEqual(json.loads((w / "datos/x.json").read_text()), {"a": 1})
        # control negativo: otro territorio no hereda lo de aut11, ni un orden anterior lo posterior
        w3 = self.clon("w3")
        cr.ensayo(w3, self.tmp / "e3.git", "main", self.alm, "900", "nac22", 11)
        self.assertFalse((w3 / "datos/x.json").exists())
        w4 = self.clon("w4")
        cr.ensayo(w4, self.tmp / "e4.git", "main", self.alm, "900", "aut11", 10)
        self.assertFalse((w4 / "datos/x.json").exists())


class Captura(Base):
    def test_tipos(self):
        cap = self.registrar_en_ensayo("aut11", 10, {
            ARCHIVO: json.dumps({"artefactos": {"viejo": {"run_id": "1"}, "nuevo": {"run_id": "900"}}}, indent=1) + "\n",
            "datos/resultados/runs/aut11_900.csv": "a,b\n",
            CATALOGO: "territories:\n  aut11:\n    estado: nuevo\n\n  nac22:\n    estado: viejo\n",
            "orchestracion/catalogo_procedencia.json": "{}\n",
        })
        tipos = {e["ruta"]: e["tipo"] for e in cap["entradas"]}
        self.assertEqual(tipos, {ARCHIVO: "json", "datos/resultados/runs/aut11_900.csv": "nuevo", CATALOGO: "texto"})
        self.assertIsNotNone(self.alm.leer("campanas/900/registro/aut11/10-registrar/1.json"))

    def test_ruta_fuera_de_robot_falla_cerrado(self):
        with self.assertRaises(cr.RegistroError) as e:
            self.registrar_en_ensayo("aut11", 10, {"herramientas/intruso.py": "x\n"})
        self.assertIn("CAPTURA_RUTA_NO_ROBOT", str(e.exception))


class Componer(Base):
    def cierre(self, territorios):
        w = self.clon("cierre")
        return w, cr.componer(w, self.alm, "900", territorios)

    def test_dos_territorios_y_lo_ajeno_se_conserva(self):
        self.registrar_en_ensayo("aut11", 10, {
            ARCHIVO: json.dumps({"artefactos": {"viejo": {"run_id": "1"}, "a11": {"run_id": "900"}}}, indent=1) + "\n",
            CATALOGO: "territories:\n  aut11:\n    estado: nuevo\n\n  nac22:\n    estado: viejo\n"})
        self.registrar_en_ensayo("nac22", 10, {
            ARCHIVO: json.dumps({"artefactos": {"viejo": {"run_id": "1"}, "n22": {"run_id": "900"}}}, indent=1) + "\n",
            CATALOGO: "territories:\n  aut11:\n    estado: viejo\n\n  nac22:\n    estado: nuevo\n"})
        # mientras tanto, otro robot escribió en main
        escribir(self.origen, ARCHIVO, json.dumps({"artefactos": {"viejo": {"run_id": "1"}, "ajeno": {"run_id": "7"}}},
                                                  indent=1) + "\n")
        git(self.origen, "commit", "-qam", "ajeno")
        w, rutas = self.cierre(["aut11", "nac22"])
        self.assertEqual(sorted(rutas), [CATALOGO, ARCHIVO])
        self.assertEqual(set(json.loads((w / ARCHIVO).read_text())["artefactos"]), {"viejo", "ajeno", "a11", "n22"})
        self.assertEqual((w / CATALOGO).read_text(),
                         "territories:\n  aut11:\n    estado: nuevo\n\n  nac22:\n    estado: nuevo\n")

    def test_solo_los_sanos(self):
        self.registrar_en_ensayo("aut11", 10, {"datos/a.json": "{}\n"})
        self.registrar_en_ensayo("nac22", 10, {"datos/n.json": "{}\n"})
        w, rutas = self.cierre(["nac22"])
        self.assertEqual(rutas, ["datos/n.json"])
        self.assertFalse((w / "datos/a.json").exists())

    def test_choque_de_texto_falla_cerrado(self):
        self.registrar_en_ensayo("aut11", 10, {CATALOGO: "territories:\n  aut11:\n    estado: A\n\n  nac22:\n    estado: viejo\n"})
        self.registrar_en_ensayo("nac22", 10, {CATALOGO: "territories:\n  aut11:\n    estado: B\n\n  nac22:\n    estado: viejo\n"})
        with self.assertRaises(cr.RegistroError) as e:
            self.cierre(["aut11", "nac22"])
        self.assertIn("CIERRE_CONFLICTO", str(e.exception))

    def test_ultimo_intento_gana(self):
        w = self.clon("w")
        base = cr.ensayo(w, self.tmp / "e.git", "main", self.alm, "900", "aut11", 10)
        escribir(w, "datos/a.json", '{"v": 1}\n')
        git(w, "add", "-A"); git(w, "commit", "-qm", "1"); git(w, "push", "-q", "origin", "HEAD:refs/heads/main")
        cr.capturar(w, base, "main", self.alm, "900", "aut11", 10, "registrar", 1)
        escribir(w, "datos/a.json", '{"v": 2}\n')
        git(w, "commit", "-qam", "2"); git(w, "push", "-q", "origin", "HEAD:refs/heads/main")
        cr.capturar(w, base, "main", self.alm, "900", "aut11", 10, "registrar", 2)
        w2, _ = self.cierre(["aut11"])
        self.assertEqual(json.loads((w2 / "datos/a.json").read_text()), {"v": 2})


class Cerrar(Base):
    """§6: un solo commit con lo de los sanos, idempotente, y el objeto «cierre» solo tras el push."""

    def setUp(self):
        super().setUp()
        self.remoto = self.tmp / "remoto.git"
        git(self.tmp, "clone", "-q", "--bare", str(self.origen), str(self.remoto))
        self.origen_real = self.origen
        self.origen = self.remoto  # los clones de los registros y del cierre parten del remoto «real»
        ce.guardar_semaforo(self.alm, "900", ce.comprobar("aut11, nac22", "vigente"))

    def sanar(self, t):
        for paso in ce.PASOS:
            ce.empezar(self.alm, "900", t, paso, 1)
            ce.registrar(self.alm, "900", t, paso, 1, "ok")

    def cierre(self, ref="refs/heads/main"):
        w = self.tmp / f"cierre-{len(list(self.tmp.iterdir()))}"
        git(self.tmp, "clone", "-q", f"file://{self.remoto}", str(w))
        return cr.cerrar(w, self.alm, "900", ref, "900", backoff=None)

    def test_un_commit_solo_con_los_sanos(self):
        self.registrar_en_ensayo("aut11", 10, {"datos/a.json": "{}\n"})
        self.registrar_en_ensayo("nac22", 10, {"datos/n.json": "{}\n"})
        self.sanar("aut11")
        ce.empezar(self.alm, "900", "nac22", "P10", 1)
        ce.registrar(self.alm, "900", "nac22", "P10", 1, "apartado", "CONTRATO_ROTO")
        antes = int(git(self.remoto, "rev-list", "--count", "main"))
        r = self.cierre()
        self.assertEqual((r["rama"], r["sanos"], r["commit"]), ("main", ["aut11"], True))
        self.assertEqual(int(git(self.remoto, "rev-list", "--count", "main")), antes + 1)
        ficheros = git(self.remoto, "show", "--name-only", "--format=", "main").split()
        self.assertEqual(ficheros, ["datos/a.json"])
        self.assertIsNotNone(self.alm.leer("campanas/900/cierre.json"))
        # idempotente: otro cierre no añade commit
        self.assertEqual(self.cierre()["sha"], r["sha"])
        self.assertEqual(int(git(self.remoto, "rev-list", "--count", "main")), antes + 1)

    def test_validacion_desde_rama_nunca_en_main(self):
        self.registrar_en_ensayo("aut11", 10, {"datos/a.json": "{}\n"})
        self.sanar("aut11")
        git(self.remoto, "branch", "p00-cierre/900", "main")
        antes = git(self.remoto, "rev-parse", "main")
        r = self.cierre("refs/heads/t379-p00")
        self.assertEqual(r["rama"], "p00-cierre/900")
        self.assertEqual(git(self.remoto, "rev-parse", "main"), antes)
        self.assertIn("datos/a.json", git(self.remoto, "show", "--name-only", "--format=", "p00-cierre/900"))

    def test_push_rechazado_deja_el_cierre_pendiente(self):
        self.registrar_en_ensayo("aut11", 10, {"datos/a.json": "{}\n"})
        self.sanar("aut11")
        w = self.tmp / "cierre-roto"
        git(self.tmp, "clone", "-q", f"file://{self.remoto}", str(w))
        git(w, "remote", "set-url", "--push", "origin", str(self.tmp / "no-existe.git"))
        with self.assertRaises(cr.rem.PushRechazado):
            cr.cerrar(w, self.alm, "900", "refs/heads/main", "900", backoff=None)
        self.assertIsNone(self.alm.leer("campanas/900/cierre.json"))  # §6.5: sin objeto cierre si el push no se confirma


class CatalogoEnElCierre(unittest.TestCase):
    """D-147 y §6: el cierre SÍ escribe catalogo_preparacion.yaml (única ruta fuera de RUTAS_ROBOT); cualquier otra, no."""

    def test_excepcion_unica(self):
        with tempfile.TemporaryDirectory() as td:
            alm = ce.AlmacenLocal(Path(td))
            ce.guardar_semaforo(alm, "900", ce.comprobar("nac22", "vigente"))
            plan = ce.plan_cierre(alm, "900", "refs/heads/main", "900", False, [CATALOGO, ARCHIVO])
            self.assertEqual(plan["ficheros"], [CATALOGO, ARCHIVO])
            with self.assertRaises(ce.EstadoError):
                ce.plan_cierre(alm, "900", "refs/heads/main", "900", False, [CATALOGO, "configuracion/otro.yaml"])


if __name__ == "__main__":
    unittest.main()
