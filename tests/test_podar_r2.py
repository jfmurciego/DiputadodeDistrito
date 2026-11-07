"""
PROYECTO: Diputado de Distrito
PRUEBA: poda de R2 (T-76): política, simulación, lista estable, borrado con lista aprobada y límite de 9 GB
VERSIÓN: 1.0.0
FECHA: 2026-11-07
ANTERIOR: ninguna (fichero nuevo)
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("podar", ROOT / "herramientas/podar_r2.py")
pod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pod)

MB = 10**6


def entrada(terr, run, nombre, mb):
    return f"{terr}/{run}/{nombre}.zip", {"artefacto": nombre, "territorio": terr, "run_id": run, "tamano_bytes": mb * MB}


def manifiesto(*runs):
    ent = {}
    for terr, run, etapas, extra in runs:
        for n in etapas:
            k, e = entrada(terr, run, f"ddd-state-{run}-M0{n}", 100 + n)
            ent[k] = e
        k, e = entrada(terr, run, f"ddd-audit-{run}", 0)
        ent[k] = e
        for nom, mb in extra:
            k, e = entrada(terr, run, nom, mb)
            ent[k] = e
    return {"artefactos": ent}


def visor(*prods):
    return {"products": [{"kind": k, "territory_id": t, "run_id": r} for k, t, r in prods]}


class Politica(unittest.TestCase):
    def setUp(self):
        self.m = manifiesto(("a", "100", range(1, 9), []), ("a", "200", range(1, 7), []), ("b", "300", range(1, 9), []))
        self.v = visor(("canonical_m08", "a", "100"))

    def test_conserva_run_publicado_y_producto_final(self):
        p = pod.calcular(self.m, self.v)
        self.assertIn("a/100/ddd-state-100-M08.zip", p["conservar"])
        self.assertNotIn("a/100/ddd-state-100-M06.zip", p["conservar"])
        self.assertIn("a/100/ddd-audit-100.zip", p["conservar"])  # auditoría pequeña
        self.assertIn("a/200/ddd-state-200-M06.zip", p["borrar"])  # el run 200 es más nuevo pero menos completo
        self.assertEqual(p["bytes_total"], p["bytes_borrar"] + p["bytes_final"])

    def test_sin_publicar_toma_el_mas_completo_y_nuevo(self):
        p = pod.calcular(self.m, {})
        self.assertEqual(p["vigentes"], {"a": "100", "b": "300"})

    def test_run_mas_nuevo_y_completo_sin_publicar_tambien_se_conserva(self):
        m = manifiesto(("a", "100", range(1, 7), []), ("a", "200", range(1, 9), []))
        p = pod.calcular(m, visor(("canonical_m06", "a", "100")))
        self.assertIn("a/100/ddd-state-100-M06.zip", p["conservar"])
        self.assertIn("a/200/ddd-state-200-M08.zip", p["conservar"])
        self.assertTrue(p["avisos"])

    def test_conservar_m06_y_auditoria_grande(self):
        m = manifiesto(("a", "100", range(1, 9), [("ddd-audit-electoral-100", 5)]))
        p = pod.calcular(m, {}, conservar_m06=True)
        self.assertIn("a/100/ddd-state-100-M06.zip", p["conservar"])
        self.assertIn("a/100/ddd-audit-electoral-100.zip", p["borrar"])

    def test_m03u_no_cuenta_como_etapa(self):
        self.assertEqual(pod.etapa("ddd-state-1-M03U"), 0)
        self.assertEqual(pod.etapa("ddd-state-1-M07"), 7)

    def test_real_final_bajo_9gb(self):
        man = json.loads((ROOT / "orchestracion/archivo_r2.json").read_text(encoding="utf-8"))
        vis = json.loads((ROOT / "orchestracion/publicaciones_visor.json").read_text(encoding="utf-8"))
        for m06 in (False, True):
            p = pod.calcular(man, vis, m06)
            self.assertLess(p["bytes_final"], pod.LIMITE_BYTES)


class Lista(unittest.TestCase):
    def setUp(self):
        self.m = manifiesto(("a", "100", range(1, 9), []))
        self.p = pod.calcular(self.m, {})

    def test_lista_estable(self):
        a = pod.lista_json(self.p)
        b = pod.lista_json(pod.calcular(json.loads(json.dumps(self.m)), {}))
        self.assertEqual(a, b)
        self.assertEqual(a["sha256"], pod.huella_lista(reversed(a["claves"])))

    def test_verificacion(self):
        lista = pod.lista_json(self.p)
        self.assertEqual(pod.verificar_lista(lista, lista["sha256"], self.p, self.m), [])
        self.assertTrue(pod.verificar_lista(lista, "0" * 64, self.p, self.m))
        mala = {**lista, "claves": lista["claves"] + ["a/100/ddd-state-100-M08.zip"]}
        mala["sha256"] = pod.huella_lista(mala["claves"])
        self.assertTrue(any("conserva" in e for e in pod.verificar_lista(mala, mala["sha256"], self.p, self.m)))
        ajena = {**lista, "claves": ["x/1/y.zip"]}
        ajena["sha256"] = pod.huella_lista(ajena["claves"])
        self.assertTrue(any("manifiesto" in e for e in pod.verificar_lista(ajena, ajena["sha256"], self.p, self.m)))

    def test_borrado_retira_solo_lo_borrado(self):
        borradas = []

        def rm(k):
            if k.endswith("M01.zip"):
                raise RuntimeError("fallo")
            borradas.append(k)

        res = pod.borrar(self.p["borrar"], self.m, rm)
        self.assertEqual(len(res["errores"]), 1)
        self.assertIn("a/100/ddd-state-100-M01.zip", self.m["artefactos"])
        self.assertNotIn("a/100/ddd-state-100-M02.zip", self.m["artefactos"])

    def test_borrar_sin_lista_falla(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "orchestracion").mkdir()
            (Path(td) / pod.MANIFIESTO).write_text(json.dumps(self.m), encoding="utf-8")
            self.assertEqual(pod.main(["--root-dir", td, "--borrar"]), 1)


class Limite(unittest.TestCase):
    def test_rojo_y_verde(self):
        gran = {"artefactos": {"k": {"tamano_bytes": 9 * 10**9 + 1}}}
        peq = {"artefactos": {"k": {"tamano_bytes": 9 * 10**9}}}
        self.assertTrue(pod.superar_limite(gran)[0])
        self.assertFalse(pod.superar_limite(peq)[0])
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "orchestracion").mkdir()
            for man, rc in ((gran, 1), (peq, 0)):
                (Path(td) / pod.MANIFIESTO).write_text(json.dumps(man), encoding="utf-8")
                self.assertEqual(pod.main(["--root-dir", td, "--comprobar-limite"]), rc)


if __name__ == "__main__":
    unittest.main()
