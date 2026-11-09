"""T-105: Gestor de Campañas 2.0 (D-22), entradas en español → plan en seco; lo no disponible falla al planificar.

VERSIÓN: 1.0.0 · FECHA: 2026-11-08
ANTERIOR: ninguna (fichero nuevo)
Valores esperados de fuentes independientes: provincias por comunidad del INE (Aragón 22, 44, 50) y los 49 gemelos
del mapa de 350 de T-102 (sin Baleares, Las Palmas ni Santa Cruz de Tenerife).
"""
import json
import subprocess
import sys
import unittest

import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import gestor_campanas_2 as g  # noqa: E402
import legislatura_vigente as lv  # noqa: E402

BASE = {"eleccion": "legislatura vigente", "tipo": "nacional", "territorios": "todos",
        "inicio": "reutilizar progreso", "publicar": "no", "ensemble": "ninguno", "mapa": "407"}


def ids(**kw):
    return g.resolve({**BASE, **kw}, ROOT)["ids"]


class Seleccion(unittest.TestCase):
    def test_todo_el_congreso(self):
        self.assertEqual(len(ids()), 52)

    def test_una_comunidad_da_sus_provincias(self):
        self.assertEqual(ids(territorios="Aragón"), ["congreso_huesca", "congreso_teruel", "congreso_zaragoza"])

    def test_lista_por_nombre_codigo_y_matricula(self):
        self.assertEqual(ids(territorios="HU, 42, Vizcaya"), ["congreso_huesca", "congreso_soria", "congreso_vizcaya"])

    def test_autonomico_por_nombre_y_codigo(self):
        self.assertEqual(ids(tipo="autonómico", territorios="Galicia,13"), ["galicia", "madrid"])
        self.assertEqual(len(ids(tipo="autonómico")), 19)

    def test_mapa_350(self):
        self.assertEqual(len(ids(mapa="350")), 49)
        self.assertEqual(ids(mapa="350", territorios="Soria"), ["congreso350_soria"])
        with self.assertRaisesRegex(g.NoDisponible, "islas"):
            ids(mapa="350", territorios="Canarias")

    def test_relevo_con_ids_exactos_y_auto(self):
        r = g.resolve({**BASE, "mapa": "350", "inicio": "desde el principio",
                       "territorios": "congreso350_soria@auto,congreso350_teruel"}, ROOT)
        self.assertEqual(r["inicio"], {"congreso350_soria": "auto", "congreso350_teruel": "desde_el_principio"})

    def test_parte_desconocida(self):
        with self.assertRaisesRegex(g.lv.GestorError, "Narnia"):
            ids(territorios="Narnia")


class NoDisponible(unittest.TestCase):
    def test_historico_ensemble_25_y_350(self):
        casos = [({"eleccion": "histórico: generales 2016", "tipo": "autonómico"}, "nacional"), ({"ensemble": "25"}, "no está validado"),
                 ({"mapa": "350", "publicar": "sí"}, "D-18"), ({"mapa": "350", "tipo": "autonómico"}, "nacional"),
                 ({"ensemble": "10"}, "congreso_soria")]
        for kw, msg in casos:
            with self.subTest(kw=kw), self.assertRaisesRegex(g.NoDisponible, msg):
                g.resolve({**BASE, **kw}, ROOT)

    def test_ensemble_10_con_configuracion(self):
        r = g.resolve({**BASE, "ensemble": "10", "territorios": "Salamanca"}, ROOT)
        self.assertEqual(r["ensemble"], {"congreso_salamanca": "congreso_salamanca"})

    def test_cli_falla_sin_lanzar(self):
        p = subprocess.run([sys.executable, "herramientas/gestor_campanas_2.py", "plan", "--sin-api",
                            *[f"--{k}={v}" for k, v in {**BASE, "ensemble": "25"}.items()],
                            "--salida", "/dev/null"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("::error::El ensemble de 25", p.stderr)


class Workflow(unittest.TestCase):
    def test_sin_claves_duplicadas(self):
        """PyYAML se queda con la última clave repetida; GitHub rechaza el fichero (run sin jobs)."""
        import yaml

        class Estricto(yaml.SafeLoader):
            pass

        def mapping(loader, node):
            keys = [loader.construct_object(k) for k, _ in node.value]
            dup = {k for k in keys if keys.count(k) > 1}
            if dup:
                raise AssertionError(f"claves duplicadas en línea {node.start_mark.line + 1}: {dup}")
            return loader.construct_mapping(node)

        Estricto.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
        yaml.load((ROOT / ".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8"), Loader=Estricto)


class Plan(unittest.TestCase):
    def test_plan_en_seco_muestra_entradas_y_cadena(self):
        plan = g.build({**BASE, "territorios": "Huesca", "inicio": "desde el principio", "publicar": "sí"}, {}, ROOT)
        self.assertEqual([(r["territory_id"], r["accion"], r["publicar"]) for r in plan["territorios"]],
                         [("congreso_huesca", "desde_el_principio", True)])
        md = g.markdown(plan, True)
        self.assertIn("SOLO PLAN (no se lanza nada)", md)
        self.assertIn("5) Publicar: sí", md)
        json.dumps(plan)  # el plan viaja como JSON al paso de lanzamiento


class CampanaCompleta(unittest.TestCase):
    """T-130: una orden = vigente (nacional y/o autonómica) + histórico de las cinco generales, en seco."""
    C = {**BASE, "eleccion": "campaña completa", "tipo": "nacional y autonómico", "territorios": "todos"}

    def test_una_orden_planifica_todo(self):
        plan = g.build(self.C, {}, ROOT)
        # 52 provincias + 19 comunidades (INE/Constitución) y 5 elecciones × 52 provincias.
        self.assertEqual(len(plan["territorios"]), 52 + 19)
        h = plan["historico"]
        self.assertEqual(len(h["include"]) + len(h["omitidos"]), 5 * 52)
        self.assertEqual({r["clave"] for r in h["include"]}, {"201111", "201512", "201606", "201904", "201911"})
        self.assertTrue(any("T-131" in t for t in plan["pendiente"]))
        self.assertIn("Pendiente", g.markdown(plan, True))

    def test_solo_nacional_no_deja_pendiente_y_solo_autonomico_no_trae_historico(self):
        self.assertEqual(g.build({**self.C, "tipo": "nacional"}, {}, ROOT)["pendiente"], [])
        self.assertNotIn("historico", g.build({**self.C, "tipo": "autonómico"}, {}, ROOT))

    def test_rechazos(self):
        casos = [({"ensemble": "25"}, "no está validado"), ({"mapa": "350"}, "407"),
                 ({"territorios": "Aragón"}, "todos"),
                 ({"eleccion": "legislatura vigente"}, "campaña completa")]
        for kw, msg in casos:
            with self.subTest(kw=kw), self.assertRaisesRegex(g.NoDisponible if msg != "todos" else lv.GestorError, msg):
                g.resolve({**self.C, **kw}, ROOT)

    def test_workflow_matriz_con_clave_y_tope_de_256(self):
        wf = yaml.safe_load((ROOT / ".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8"))
        for job in ("historico_prueba", "historico", "historico_2"):
            self.assertIn("matrix.clave", json.dumps(wf["jobs"][job]["steps"]), job)
        self.assertIn("1:251", json.dumps(wf["jobs"]["legislatura"]["steps"], ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
