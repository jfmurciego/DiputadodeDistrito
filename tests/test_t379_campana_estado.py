"""T-379 PR 1: estado de campaña de P00 (herramientas/campana_estado.py).

Controles negativos del diseño 1.1 (§2, §4, §6, §10): parada con 2 frente a 3 apartados, 20 % con mínimo 3,
idempotencia por (campaña, territorio, paso, run_attempt), «sin_resultado», re-ejecución, código inexistente, lista
mixta con elección inexistente → rojo por territorio, cierre (rama, ensayo vacío, RUTAS_ROBOT) y contrato del informe.
Los territorios y elecciones salen del catálogo real; el almacén es un directorio temporal (nunca R2 real).
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import campana_estado as ce  # noqa: E402

CLI = [sys.executable, str(ROOT / "herramientas" / "campana_estado.py")]


class Base(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.alm = ce.AlmacenLocal(Path(self._td.name))

    def tearDown(self):
        self._td.cleanup()

    def campana(self, territorios="nac22, nac42, nac52, aut11, aut13", eleccion="vigente", c="900"):
        ce.guardar_semaforo(self.alm, c, ce.comprobar(territorios, eleccion))
        return c

    def apartar(self, c, t, causa, paso="P10", intento=1):
        ce.empezar(self.alm, c, t, paso, intento)
        return ce.registrar(self.alm, c, t, paso, intento, "apartado", causa)

    def sanar(self, c, t, intento=1):
        for paso in ce.PASOS:
            ce.empezar(self.alm, c, t, paso, intento)
            ce.registrar(self.alm, c, t, paso, intento, "ok", huellas={"m06": "ab" * 32})


class Eleccion(unittest.TestCase):
    def test_tabla_de_traduccion(self):
        self.assertEqual(ce.traducir_eleccion("vigente")["p12"], "vigente")
        e = ce.traducir_eleccion("2026-11")
        self.assertEqual((e["p12"], e["ensayo"]), ("ensayo 2026-11-29", True))
        e = ce.traducir_eleccion("2019-11")
        self.assertEqual((e["p12"], e["soportada"]), (None, False))
        for malo in ("", "2026-13", "ensayo", "2026-11-29"):
            with self.assertRaises(ce.EstadoError):
                ce.traducir_eleccion(malo)

    def test_otro_mes_rojo_por_territorio_y_no_lanzable(self):
        s = ce.comprobar("nac22", "2019-11")
        self.assertEqual(s["territorios"][0]["causas"], ["ELECCION_NO_SOPORTADA"])
        self.assertFalse(s["lanzable"])
        self.assertIn("NINGUN_TERRITORIO_LANZABLE", s["bloqueos"])


class Territorios(unittest.TestCase):
    def test_grupos_del_catalogo(self):
        self.assertEqual(len(ce.resolver_territorios("todos")), 71)
        congreso = ce.resolver_territorios("congreso")
        self.assertEqual((len(congreso), congreso[0], congreso[-1]), (52, "nac01", "nac52"))
        self.assertEqual(len(ce.resolver_territorios("autonómicas")), 19)
        self.assertEqual(ce.resolver_territorios("NAC22, aut11 nac22"), ["nac22", "aut11"])
        for malo in ("", "todos, nac22"):
            with self.assertRaises(ce.EstadoError):
                ce.resolver_territorios(malo)

    def test_lista_mixta_con_ensayo(self):
        s = ce.comprobar("nac22, aut11, xyz99", "2026-11")
        colores = {f["territorio"]: (f["color"], f["causas"]) for f in s["territorios"]}
        self.assertEqual(colores, {"nac22": ("verde", []), "aut11": ("rojo", ["SIN_ELECCION"]),
                                   "xyz99": ("rojo", ["CODIGO_INEXISTENTE"])})
        self.assertTrue(s["lanzable"])
        self.assertEqual(s["lanzados"], ["nac22"])

    def test_ensayo_sin_contrato_y_ids_viejos_o_350(self):
        s = ce.comprobar("nac01, congreso_huesca, congreso350_huesca", "2026-11")
        causas = [f["causas"] for f in s["territorios"]]
        self.assertEqual(causas, [["ENSAYO_SIN_CONTRATO"], ["CODIGO_INEXISTENTE"], ["CONGRESO_350"]])
        self.assertFalse(s["lanzable"])

    def test_vigente_mixto_toma_la_eleccion_de_cada_territorio(self):
        s = ce.comprobar("nac22, aut11", "vigente")
        self.assertEqual([f["color"] for f in s["territorios"]], ["verde", "verde"])
        self.assertEqual(s["territorios"][0]["etiqueta"], "NAC22 · Huesca")
        self.assertNotEqual(s["territorios"][0]["election_id"], s["territorios"][1]["election_id"])

    def test_hechos_ambar_rojo_y_campana(self):
        s = ce.comprobar("nac22, nac42, nac52", "vigente", {
            "territorios": {"nac22": ["PAQUETE_FUENTES_CADUCADO"], "nac42": ["BLOQUEADA_SIN_DATO"]},
            "campana": {"ci_verde": True, "r2_responde": None}})
        self.assertEqual([f["color"] for f in s["territorios"]], ["ámbar", "rojo", "verde"])
        self.assertEqual(s["lanzados"], ["nac22", "nac52"])
        self.assertTrue(s["lanzable"])
        self.assertIn("R2_NO_RESPONDE_SIN_COMPROBAR", s["avisos"])
        self.assertFalse(ce.comprobar("nac22", "vigente", {"campana": {"ci_verde": False}})["lanzable"])
        with self.assertRaises(ce.EstadoError):
            ce.comprobar("nac22", "vigente", {"territorios": {"nac22": ["INVENTADA"]}})
        with self.assertRaises(ce.EstadoError):
            ce.comprobar("nac22", "vigente", {"territorios": {"nac42": ["BLOQUEADA_SIN_DATO"]}})

    def test_ensayo_no_publica(self):
        s = ce.comprobar("nac22", "2026-11", publicar=True)
        self.assertFalse(s["publicar"])
        self.assertIn("ENSAYO_NO_PUBLICA", s["avisos"])


class Parada(Base):
    def test_misma_causa_2_frente_a_3(self):
        c = self.campana("congreso")  # 52 lanzados: el 20 % (11) no interviene
        for t in ("nac01", "nac02"):
            self.apartar(c, t, "ARTIFACT_MISSING")
        self.assertFalse(ce.recuento(self.alm, c)["parada"]["activa"])
        self.assertEqual(ce.empezar(self.alm, c, "nac04", "P10", 1)[0], 0)
        self.apartar(c, "nac03", "ARTIFACT_MISSING")
        r = ce.recuento(self.alm, c)
        self.assertTrue(r["parada"]["activa"])
        self.assertIn("ARTIFACT_MISSING", r["parada"]["motivo"])
        self.assertEqual(ce.empezar(self.alm, c, "nac05", "P10", 1)[0], ce.RC_PARADA)

    def test_veinte_por_ciento_de_71_es_15(self):
        self.assertEqual(ce.umbral_parada(71), 15)
        c = self.campana("todos")
        tids = ce.resolver_territorios("todos")
        for i, t in enumerate(tids[:14]):
            self.apartar(c, t, f"CAUSA_{i:02d}")
        self.assertFalse(ce.recuento(self.alm, c)["parada"]["activa"])
        self.apartar(c, tids[14], "CAUSA_14")
        self.assertTrue(ce.recuento(self.alm, c)["parada"]["activa"])

    def test_minimo_3_con_pocos_lanzados(self):
        self.assertEqual(ce.umbral_parada(5), 3)
        c = self.campana()  # 5 lanzados: el 20 % sería 1
        self.apartar(c, "nac22", "CAUSA_A")
        self.apartar(c, "nac42", "CAUSA_B")
        self.assertFalse(ce.recuento(self.alm, c)["parada"]["activa"])
        self.apartar(c, "nac52", "CAUSA_C")
        self.assertTrue(ce.recuento(self.alm, c)["parada"]["activa"])


class Recuento(Base):
    def test_misma_clave_dos_veces_cuenta_una(self):
        c = self.campana()
        self.assertEqual(self.apartar(c, "nac22", "CANDIDATE_FAILED"), "escrito")
        self.assertEqual(ce.registrar(self.alm, c, "nac22", "P10", 1, "apartado", "CANDIDATE_FAILED"), "sin_cambios")
        self.assertEqual(ce.recuento(self.alm, c)["apartados"], 1)
        with self.assertRaises(ce.EstadoError):  # la historia de un intento no se reescribe
            ce.registrar(self.alm, c, "nac22", "P10", 1, "ok")

    def test_reintento_que_sana_quita_el_apartado(self):
        c = self.campana()
        self.apartar(c, "nac22", "SIN_RESULTADO")
        self.assertEqual(ce.recuento(self.alm, c)["apartados"], 1)
        self.sanar(c, "nac22", intento=2)
        r = ce.recuento(self.alm, c)
        self.assertEqual((r["apartados"], r["territorios"]["nac22"]["estado"]), (0, "sano"))

    def test_sin_resultado_es_apartado_al_final_nunca_verde(self):
        c = self.campana()
        ce.empezar(self.alm, c, "nac22", "P10", 1)
        self.assertEqual(ce.recuento(self.alm, c)["territorios"]["nac22"]["estado"], "en_curso")
        f = ce.recuento(self.alm, c, final=True, jobs={"nac22": {"P10": "cancelled"}})["territorios"]["nac22"]
        self.assertEqual((f["estado"], f["causa"], f["detalle"]), ("apartado", "SIN_RESULTADO", "cancelled"))

    def test_job_verde_sin_salida_es_apartado(self):
        c = self.campana()
        ce.empezar(self.alm, c, "nac22", "P10", 1)
        f = ce.recuento(self.alm, c, jobs={"nac22": {"P10": "success"}})["territorios"]["nac22"]
        self.assertEqual((f["estado"], f["causa"]), ("apartado", "SALIDA_R2_AUSENTE"))

    def test_final_sin_empezar_por_parada_es_detenido(self):
        c = self.campana()
        for t, causa in (("nac22", "X_A"), ("nac42", "X_B"), ("nac52", "X_C")):
            self.apartar(c, t, causa)
        r = ce.recuento(self.alm, c, final=True)
        self.assertEqual(r["territorios"]["aut11"]["estado"], "detenido")
        self.assertEqual(r["apartados"], 3)

    def test_reejecucion_solo_de_transitorios(self):
        c = self.campana()
        self.apartar(c, "nac22", "TERRITORIAL_READY_PAIR_INCOMPATIBLE")
        rc, msg = ce.empezar(self.alm, c, "nac22", "P10", 2)
        self.assertEqual(rc, ce.RC_NO_REEJECUTABLE)
        self.assertIn("NO_REEJECUTABLE", msg)
        ce.empezar(self.alm, c, "nac42", "P10", 1)  # queda en sin_resultado (runner perdido)
        self.assertEqual(ce.empezar(self.alm, c, "nac42", "P10", 2), (0, "marcado"))

    def test_territorio_no_lanzado_o_paso_invalido(self):
        c = self.campana("nac22, aut11", "2026-11")  # aut11 es rojo: no se lanzó
        for args in (("aut11", "P10", 1), ("nac22", "P40", 1), ("nac22", "P10", 0)):
            with self.assertRaises(ce.EstadoError):
                ce.empezar(self.alm, c, *args)


class Cierre(Base):
    def test_rama_de_cierre_y_rutas_robot(self):
        c = self.campana()
        f = ["orchestracion/estado_operativo.json"]
        self.assertEqual(ce.plan_cierre(self.alm, c, "refs/heads/main", "123", False, f)["rama"], "main")
        p = ce.plan_cierre(self.alm, c, "refs/heads/t379-p00", "123", False, f)
        self.assertEqual((p["rama"], p["commit"]), ("p00-cierre/123", True))
        with self.assertRaises(ce.EstadoError):
            ce.plan_cierre(self.alm, c, "refs/heads/main", "123", False, ["configuracion/catalogo_preparacion.yaml"])

    def test_ensayo_sin_ficheros_ni_commit(self):
        c = self.campana("nac22", "2026-11")
        p = ce.plan_cierre(self.alm, c, "refs/heads/main", "123", True, ["configuracion/catalogo_preparacion.yaml"])
        self.assertEqual((p["ficheros"], p["commit"]), ([], False))

    def test_cierre_idempotente_por_huella(self):
        c = self.campana("nac22")
        self.sanar(c, "nac22")
        h = ce.huella_estado(self.alm, c)
        self.assertEqual(ce.registrar_cierre(self.alm, c, h, "main", "abc1234"), "escrito")
        self.assertEqual(ce.registrar_cierre(self.alm, c, h, "main", "abc1234"), "sin_cambios")
        with self.assertRaises(ce.EstadoError):
            ce.registrar_cierre(self.alm, c, "0" * 64, "main", "abc1234")


class Resultado(Base):
    def test_cero_uno_y_pendiente(self):
        c = self.campana("nac22, nac42")
        self.sanar(c, "nac22")
        self.sanar(c, "nac42")
        self.assertEqual(ce.resultado(self.alm, c)[0], ce.RC_ROJO)  # cierre pendiente
        ce.registrar_cierre(self.alm, c, ce.huella_estado(self.alm, c), "main", "abc1234")
        self.assertEqual(ce.resultado(self.alm, c)[0], 0)
        c2 = self.campana("nac22, nac42", c="901")
        self.sanar(c2, "nac22")
        self.apartar(c2, "nac42", "CANDIDATE_FAILED")
        ce.registrar_cierre(self.alm, c2, ce.huella_estado(self.alm, c2), "main", "abc1234")
        rc, r = ce.resultado(self.alm, c2)
        self.assertEqual((rc, r["motivos"]), (ce.RC_ROJO, ["1 apartado(s)"]))


class Informe(Base):
    def test_contrato_del_informe(self):
        ce.guardar_semaforo(self.alm, "902", ce.comprobar("nac22, nac42, aut11", "2026-11"))
        self.sanar("902", "nac22")
        ce.empezar(self.alm, "902", "nac42", "P10", 1)
        ce.registrar(self.alm, "902", "nac42", "P10", 1, "ok")
        self.apartar("902", "nac42", "CANDIDATE_FAILED", paso="P20")
        ce.registrar_cierre(self.alm, "902", ce.huella_estado(self.alm, "902"), "p00-cierre/902", None)
        md = ce.informe(self.alm, "902").splitlines()
        h = ce.huella_estado(self.alm, "902")[:12]
        self.assertEqual(md[:16], [
            "## P00 Campaña · 902", "",
            "- Elección: 2026-11 (ensayo: no persiste, no commitea, no publica)",
            "- Resultado: rojo (1 apartado(s))",
            "- Lanzados: 2 · sanos: 1 · apartados: 1 · umbral de parada: 3",
            "- Parada sistémica: no",
            f"- Cierre: hecho en `p00-cierre/902` (sin commit), huella `{h}`", "",
            "| Territorio | Semáforo | Estado | Paso | Causa |", "|---|---|---|---|---|",
            "| NAC22 · Huesca | verde | sano | — | — |",
            "| NAC42 · Soria | verde | apartado | P20 | CANDIDATE_FAILED |", "",
            "**Apartados por causa**", "", "- `CANDIDATE_FAILED`: 1"])
        self.assertIn("**Rojos de la comprobación previa** (no se lanzaron; no cuentan como apartados)", md)
        self.assertIn("- AUT11 · Extremadura: SIN_ELECCION", md)


class AlmacenR2(unittest.TestCase):
    def test_ausente_es_none_y_otro_fallo_es_error(self):
        class P:
            def __init__(self, rc, err=b"", out=b""):
                self.returncode, self.stderr, self.stdout = rc, err, out
        a = ce.AlmacenR2("b", "c", run=lambda *a, **k: P(1, b"An error occurred (404) when calling HeadObject: Not Found"))
        self.assertIsNone(a.leer("campanas/1/semaforo.json"))
        a = ce.AlmacenR2("b", "c", run=lambda *a, **k: P(1, b"Could not connect to the endpoint URL"))
        with self.assertRaises(ce.EstadoError):
            a.leer("campanas/1/semaforo.json")
        a = ce.AlmacenR2("b", "c", run=lambda *a, **k: P(0, out=b'["campanas/1/x.json"]'))
        self.assertEqual(a.listar("campanas/1/"), ["campanas/1/x.json"])

    def test_sin_credenciales_falla_cerrado(self):
        r = subprocess.run([*CLI, "recuento", "--almacen", "r2", "--campana", "1"], capture_output=True, text=True,
                           env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(r.returncode, ce.RC_ENTRADA)
        self.assertIn("::error::CAMPANA_R2_SIN_CREDENCIALES", r.stderr)


class Cli(unittest.TestCase):
    def test_help_rc_0(self):
        for sub in ([], ["comprobar"], ["empezar"], ["registrar"], ["recuento"], ["resultado"], ["informe"],
                    ["plan-cierre"], ["registrar-cierre"]):
            self.assertEqual(subprocess.run([*CLI, *sub, "--help"], capture_output=True).returncode, 0, sub)

    def test_errores_a_stderr_y_rc(self):
        r = subprocess.run([*CLI, "comprobar", "--territorios", "nac22", "--eleccion", "2026-13"], capture_output=True, text=True)
        self.assertEqual(r.returncode, ce.RC_ENTRADA)
        self.assertTrue(r.stderr.startswith("::error::"))
        r = subprocess.run([*CLI, "comprobar", "--territorios", "xyz99"], capture_output=True, text=True)
        self.assertEqual(r.returncode, ce.RC_NO_LANZABLE)
        self.assertIn("::error::CAMPANA_NO_LANZABLE", r.stderr)

    def test_flujo_por_cli_con_almacen_local(self):
        with tempfile.TemporaryDirectory() as td:
            a = ["--almacen", f"dir:{td}", "--campana", "77"]
            run = lambda *x: subprocess.run([*CLI, *x], capture_output=True, text=True)  # noqa: E731
            self.assertEqual(run("comprobar", "--territorios", "nac22", *a).returncode, 0)
            for paso in ce.PASOS:
                self.assertEqual(run("empezar", *a, "--territorio", "nac22", "--paso", paso, "--intento", "1").returncode, 0)
                self.assertEqual(run("registrar", *a, "--territorio", "nac22", "--paso", paso, "--intento", "1",
                                     "--estado", "ok", "--huellas", '{"m06": "aa"}').returncode, 0)
            plan = json.loads(run("plan-cierre", *a, "--ref", "refs/heads/main", "--run-id", "77").stdout)
            self.assertEqual(run("resultado", *a).returncode, ce.RC_ROJO)
            self.assertEqual(run("registrar-cierre", *a, "--huella", plan["huella"], "--rama", "main").returncode, 0)
            self.assertEqual(run("resultado", *a).returncode, 0)


if __name__ == "__main__":
    unittest.main()
