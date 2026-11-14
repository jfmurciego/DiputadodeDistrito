"""T-298: la batería toma las fuentes nacionales del espejo (sha256 verificado) y nunca de ine.es; la entrada mínima en R2
se indexa por la identidad del contrato, no por el id del territorio."""
import socket
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import contextlib
import hashlib
import io
import json

import yaml

from herramientas import bateria_motor as b
from herramientas import podar_r2

ROOT = Path(__file__).resolve().parents[1]
# Valores independientes: medidos sobre la descarga real del INE (2026-11-14) y de inputs/partes/reconstruir_fuentes.sh.
SHA = {
    "seccionado_2023.zip": "7a15e700a4592d793230441cfcb4b72e40979998aef019ca644389271886bf1f",
    "seccionado_2024.zip": "df931fa0d372808eb81abb2f2645ed5ecccbd6ed397b85db656980748ddd6bf7",
    "seccionado_2025.zip": "55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4",
    "65034.csv.zip": "91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3",
}


class EspejoIne(unittest.TestCase):
    def test_ficha_de_las_cuatro_fuentes(self):
        f = json.loads((ROOT / "orchestracion/fuentes_r2.json").read_text(encoding="utf-8"))["fuentes"]
        f = {k: v for k, v in f.items() if k in SHA}  # T-299 añade el ZIP de Interior al mismo índice
        self.assertEqual({k: v["sha256"] for k, v in f.items()}, SHA)
        for k, v in f.items():
            self.assertEqual(v["clave"], f"arc-e/fuentes/ine/{k.rsplit('.zip', 1)[0]}_{SHA[k][:12]}.zip")
            self.assertTrue(v["origen_url"].startswith("https://www.ine.es/") and v["descargado_en"] and v["bytes"])
        self.assertEqual(f["seccionado_2023.zip"]["bytes"], 64929708)

    def test_la_poda_no_puede_borrar_arc_e(self):
        for k in ("arc-e/fuentes/ine/seccionado_2023_7a15e700a459.zip", "arc-e/entradas-minimas/0123456789abcdef.zip"):
            self.assertIsNone(podar_r2._ESTADO.match(k))

    def _con_ficha(self, td: Path, contenido: bytes):
        import hashlib
        ficha = {"x.zip": {"clave": "arc-e/fuentes/ine/x.zip", "sha256": hashlib.sha256(contenido).hexdigest()}}
        return mock.patch.object(b, "_espejo", lambda: ficha)

    def test_toma_del_espejo_sin_red_y_sin_ine(self):
        def sin_red(*a, **k):
            raise AssertionError("acceso a red")
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "espejo").mkdir()
            (td / "espejo/x.zip").write_bytes(b"datos")
            with self._con_ficha(td, b"datos"), mock.patch.dict("os.environ", {"DDD_ESPEJO_DIR": str(td / "espejo")}), \
                    mock.patch.object(socket, "socket", sin_red), mock.patch.object(b.urllib.request, "urlopen", sin_red), \
                    mock.patch.object(b.urllib.request, "urlretrieve", sin_red):
                p = b.obtener_fuente_nacional("x.zip", td / "nac")
                self.assertEqual(p.read_bytes(), b"datos")
                # segunda vez: ya está con su sha256, tampoco toca red
                self.assertEqual(b.obtener_fuente_nacional("x.zip", td / "nac"), p)

    def test_sha256_distinto_falla_y_no_deja_fichero(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "espejo").mkdir()
            (td / "espejo/x.zip").write_bytes(b"otra cosa")
            with self._con_ficha(td, b"datos"), mock.patch.dict("os.environ", {"DDD_ESPEJO_DIR": str(td / "espejo")}):
                with self.assertRaises(b.FuenteNacionalError):
                    b.obtener_fuente_nacional("x.zip", td / "nac")
            self.assertFalse((td / "nac/x.zip").exists())

    def test_sin_copia_ni_r2_falla_sin_ir_al_ine(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            vistas = []

            def r2_caido(clave, dest):
                vistas.append(clave)
                raise OSError("sin R2")
            with self._con_ficha(td, b"datos"), mock.patch.dict("os.environ", {}, clear=False), \
                    mock.patch.object(b, "_bajar_r2", r2_caido):
                with self.assertRaises(b.FuenteNacionalError):
                    b.obtener_fuente_nacional("x.zip", td / "nac")
            self.assertEqual(vistas, ["arc-e/fuentes/ine/x.zip"])

    def test_nada_de_la_bateria_toca_el_ine(self):
        import inspect
        for f in (b.nacionales, b.obtener_fuente_nacional, b.entradas, b.archivar_p10):
            self.assertNotIn("urlretrieve", inspect.getsource(f))
            self.assertNotIn("urlopen", inspect.getsource(f))

    def test_el_defecto_nunca_llega_al_ine_ni_al_ogc(self):
        import argparse, contextlib, io
        a = argparse.Namespace(territorios=["nac42"], todos=False, out="/nonexistent", desde_fuente=True,
                               seccionado="ogc", permitir_red_ine=False)
        buf = io.StringIO()
        with mock.patch.object(b, "entradas_uno", side_effect=AssertionError("no debe ejecutarse")), contextlib.redirect_stdout(buf):
            self.assertEqual(b.entradas(a), 2)
        self.assertIn("BATERIA_RED_INE_PROHIBIDA", buf.getvalue())
        import inspect
        self.assertEqual(inspect.signature(b.entradas_uno).parameters["seccionado"].default, "shapefile")
        self.assertIn('"--seccionado", default="shapefile"', inspect.getsource(b.main))

    def test_la_poda_no_borra_arc_e_ni_por_la_ruta_de_borrado(self):
        import csv
        borrar = mock.Mock()
        fila = {"clave": "arc-e/entradas-minimas/0123456789abcdef.zip", "sha256": "a", "copia_clave": "x/1/ddd-state-1-M03.zip",
                "copia_sha256": "b", "territorio": "arc-e", "tamano_bytes": "1"}
        with tempfile.TemporaryDirectory() as td:
            lista = Path(td) / "l.csv"
            with open(lista, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(fila))
                w.writeheader()
                w.writerow(fila)
            sha = podar_r2.sha256_fichero(lista)
            with self.assertRaises(ValueError):
                podar_r2.leer_lista(lista, sha)
            man = Path(td) / "m.json"
            man.write_text('{"artefactos": {}}', encoding="utf-8")
            # `verificar` exige una clave ddd-state-*: con arc-e/ falla (AttributeError al leer la etapa) antes de llegar a `borrar`.
            with self.assertRaises(AttributeError):
                podar_r2.podar([fila], man, lambda k: "a", lambda t: True, borrar, True)
        borrar.assert_not_called()

    def test_secretos_de_r2_solo_en_los_pasos_que_los_usan(self):
        wf = yaml.safe_load((ROOT / ".github/workflows/bateria-motor.yml").read_text(encoding="utf-8"))
        esperado = {"archivar_p10": ["Paquete P10 de la fuente y archivado por package_sha256"],
                    "bateria": ["Entradas desde R2 (paquete P10)"],
                    "competicion": ["Entradas (R2, paquete P10)"], "plan": [], "aceptacion": []}
        for job, pasos in esperado.items():
            j = wf["jobs"][job]
            self.assertFalse([k for k in j.get("env", {}) if k.startswith(("AWS_", "R2_"))], job)
            self.assertEqual([s["name"] for s in j["steps"] if any(k.startswith("AWS_") for k in s.get("env", {}))], pasos, job)

    # ---- T-303: paquete P10 de la fuente en R2; M01-M03 se recalculan -------------------------------------------------------
    def _paquete(self, td: Path, contenido: bytes = b"bundle"):
        """Carpeta de paquete P10 sintética: manifest.json + bundle; devuelve (carpeta, sha256 del bundle)."""
        carpeta = td / "pkg"
        carpeta.mkdir()
        (carpeta / "bundle.zip").write_bytes(contenido)
        h = hashlib.sha256(contenido).hexdigest()
        (carpeta / "manifest.json").write_text(json.dumps({"path": "bundle.zip", "sha256": h}), encoding="utf-8")
        return carpeta, h

    def test_clave_del_paquete_por_package_sha256_no_por_territorio(self):
        a = {"package_sha256": "ab" * 32, "contrato_sha256": "1"}
        o = {"package_sha256": "ab" * 32, "contrato_sha256": "2"}
        self.assertEqual(b.clave_paquete(a), b.clave_paquete(o))
        self.assertEqual(b.clave_paquete(a), "arc-e/paquetes-p10/" + "ab" * 32 + ".zip")
        self.assertNotEqual(b.clave_paquete(a), b.clave_paquete({"package_sha256": "cd" * 32}))

    def test_validar_paquete_es_el_del_contrato(self):
        with tempfile.TemporaryDirectory() as td:
            carpeta, h = self._paquete(Path(td))
            with mock.patch.object(b, "_identidad_contrato", lambda t: {"package_sha256": h}), \
                    mock.patch.object(b, "_anios_fuentes", lambda t: ("2025", "2023", "2023")), \
                    mock.patch("herramientas.seleccionar_paquete_fuentes.validate_prepared_package", lambda *a, **k: (True, [])):
                b.validar_paquete_p10("nac42", carpeta)  # no lanza
            with mock.patch.object(b, "_identidad_contrato", lambda t: {"package_sha256": "0" * 64}):
                with self.assertRaises(b.PaqueteP10Corrupto):
                    b.validar_paquete_p10("nac42", carpeta)
            with mock.patch.object(b, "_identidad_contrato", lambda t: {"package_sha256": h}), \
                    mock.patch.object(b, "_anios_fuentes", lambda t: ("2025", "2023", "2023")), \
                    mock.patch("herramientas.seleccionar_paquete_fuentes.validate_prepared_package", lambda *a, **k: (False, ["año distinto"])):
                with self.assertRaisesRegex(b.PaqueteP10Corrupto, "año distinto"):
                    b.validar_paquete_p10("nac42", carpeta)

    def test_paquete_desde_r2_sin_red_ausente_corrupto_y_zip_slip(self):
        import zipfile

        def sin_red(*a, **k):
            raise AssertionError("acceso a red")
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            carpeta, h = self._paquete(td)
            z = td / "p.zip"
            with zipfile.ZipFile(z, "w") as zf:
                for f in sorted(carpeta.iterdir()):
                    zf.write(f, f.name)
            claves = []

            def cp(origen, destino):
                claves.append(origen)
                Path(destino).write_bytes(z.read_bytes())

            def sin_objeto(origen, destino):
                raise OSError("NoSuchKey")
            ident = {"package_sha256": h}
            base = [mock.patch.dict("os.environ", {"R2_BUCKET": "bk"}), mock.patch.object(b, "_identidad_contrato", lambda t: ident),
                    mock.patch.object(socket, "socket", sin_red), mock.patch.object(b.urllib.request, "urlopen", sin_red),
                    mock.patch.object(b, "_anios_fuentes", lambda t: ("2025", "2023", "2023")),
                    mock.patch("herramientas.seleccionar_paquete_fuentes.validate_prepared_package", lambda *a, **k: (True, []))]
            with contextlib.ExitStack() as st:
                for m in base:
                    st.enter_context(m)
                with mock.patch.object(b, "_r2_cp", cp):
                    pkg = b.paquete_p10_desde_r2("nac42", td / "out")
                self.assertEqual(claves, [f"s3://bk/arc-e/paquetes-p10/{h}.zip"])
                self.assertEqual((pkg / "bundle.zip").read_bytes(), b"bundle")
                with mock.patch.object(b, "_r2_cp", sin_objeto):
                    self.assertIsNone(b.paquete_p10_desde_r2("nac42", td / "out2"))
                mal = td / "mal.zip"
                with zipfile.ZipFile(mal, "w") as zf:
                    zf.writestr("../fuera.txt", "x")
                with mock.patch.object(b, "_r2_cp", lambda o, d: Path(d).write_bytes(mal.read_bytes())):
                    with self.assertRaises(b.PaqueteP10Corrupto):
                        b.paquete_p10_desde_r2("nac42", td / "out3")

    def test_entradas_codigos_ausente_y_corrupto(self):
        import argparse
        ident = {"package_sha256": "ab" * 32, "contrato_sha256": "1"}
        a = argparse.Namespace(territorios=["nac42"], todos=False, out="/nonexistent", desde_fuente=False,
                               seccionado="shapefile", permitir_red_ine=False)

        def salida(efecto):
            buf = io.StringIO()
            with mock.patch.object(b, "paquete_p10_desde_r2", efecto), mock.patch.object(b, "_identidad_contrato", lambda t: ident), \
                    contextlib.redirect_stdout(buf):
                self.assertEqual(b.entradas(a), 1)
            return buf.getvalue()
        corrupto = salida(mock.Mock(side_effect=b.PaqueteP10Corrupto("fichero alterado")))
        self.assertIn("BATERIA_PAQUETE_P10_CORRUPTO nac42: fichero alterado", corrupto)
        self.assertNotIn("FALTA_PAQUETE", corrupto)
        ausente = salida(mock.Mock(return_value=None))
        self.assertIn("BATERIA_FALTA_PAQUETE_P10 nac42", ausente)
        self.assertIn(b.clave_paquete(ident), ausente)
        self.assertNotIn("CORRUPTO", ausente)

    def _uno_con_paquete(self, td: Path, reuse: bool, vistos: list, politica: dict | None = None):
        """entradas_uno con un paquete: _run simulado; devuelve el resultado."""
        pkg = td / "pkg"
        pkg.mkdir()
        (pkg / "manifest.json").write_text("{}", encoding="utf-8")
        decl = td / "decl.yaml"
        decl.write_text("x: 1\n", encoding="utf-8")
        cache = td / "cache"

        def run(cmd, log, env):
            vistos.append(list(cmd))
            if "herramientas.ejecutar_fuentes_workflow" in cmd:
                with open(log, "a", encoding="utf-8") as fh:
                    fh.write('{"decision": "REUSE"}\n' if reuse else '{"decision": "ACQUIRE"}\n')
                mat = td / "out" / "_trabajo" / "t" / "ev" / "materialized" / "inputs"
                mat.mkdir(parents=True, exist_ok=True)
                return 0, 1.0
            cache.mkdir(exist_ok=True)
            for suf in b.ENTRADA_MINIMA:
                (cache / f"t_2025{suf}").write_bytes(b"x")
            return 0, 1.0
        decision = {"decision": "REUSE", "reason": "ok"} if politica is None else politica
        with mock.patch.object(b, "_run", run), mock.patch.object(b, "_declaracion_temporal", lambda *a: decl), \
                mock.patch.object(b, "_huellas_contrato", lambda c: {}), mock.patch.object(b, "_cfg", lambda t: {}), \
                mock.patch.object(b, "_cache", lambda t: cache), mock.patch.object(b, "contrato", lambda t: b.ROOT / "c.yaml"), \
                mock.patch.object(b, "_anios_fuentes", lambda t: ("2025", "2023", "2023")), \
                mock.patch("herramientas.politica_reutilizacion_fuentes.resolve_source_action", lambda **k: decision), \
                mock.patch.object(b, "_guardar_minima", lambda *a: None):
            return b.entradas_uno("t", td / "out", {}, "shapefile", paquete=pkg)

    def test_con_paquete_restaura_como_la_00_y_ejecuta_m01_m02_m03_con_el_codigo_vigente(self):
        with tempfile.TemporaryDirectory() as td:
            vistos = []
            r = self._uno_con_paquete(Path(td), True, vistos)
            self.assertEqual(r["estado"], "OK")
            self.assertEqual(r["origen"], "paquete_p10")
            adq = [c for c in vistos if "herramientas.ejecutar_fuentes_workflow" in c][0]
            self.assertIn("--checkpoint-in", adq)          # el paquete entra como checkpoint de fuentes (REUSE), igual que la 00
            self.assertNotIn("-c", adq)                    # ni el OGC ni la copia nacional
            modulos = [Path(c[1]).name for c in vistos if len(c) > 1 and c[1].startswith("modulos/")]
            self.assertEqual(modulos, ["01_preparar_base_territorial.py", "02_construir_adyacencias.py", "03_construir_grafo.py"])

    def test_si_la_politica_de_fuentes_adquiere_en_vez_de_reutilizar_falla(self):
        with tempfile.TemporaryDirectory() as td:
            vistos = []
            r = self._uno_con_paquete(Path(td), False, vistos)
            self.assertEqual(r["estado"], "FALLO_ADQUISICION")
            self.assertEqual([c for c in vistos if len(c) > 1 and str(c[1]).startswith("modulos/")], [])

    def test_no_queda_ningun_m03_archivado_que_usar(self):
        import inspect
        src = inspect.getsource(b)
        for muerto in ("entradas_r2_identidad", "entradas_r2_uno", "estados_r2", "clave_identidad", "def archivar("):
            self.assertNotIn(muerto, src)
        self.assertNotIn("entradas-minimas", src[src.index("def clave_paquete"):])

    def test_paquete_que_la_politica_no_reutilizaria_falla_antes_de_ejecutar_nada(self):
        with tempfile.TemporaryDirectory() as td:
            vistos = []
            r = self._uno_con_paquete(Path(td), True, vistos, {"decision": "BLOCK", "reason": "copia preparada dañada: checksum incorrecto"})
            self.assertEqual(r["estado"], "FALLO_ADQUISICION")
            self.assertEqual(vistos, [])  # ni el ejecutor de fuentes ni M01-M03: nunca se llega a la adquisición
            self.assertIn("BATERIA_PAQUETE_P10_NO_REUTILIZABLE", (Path(td) / "out" / "entradas" / "t" / "log.txt").read_text(encoding="utf-8"))

    def test_la_politica_se_consulta_sin_fuente_oficial_disponible(self):
        import inspect
        self.assertIn("official_available=False", inspect.getsource(b.entradas_uno))

    def test_poda_protege_m01_m03_con_el_paquete_p10_del_contrato(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root / "territorios" / "nac42" / "config"
            cfg.mkdir(parents=True)
            (cfg / "nac42_2025.yaml").write_text("generation_state:\n  package_sha256: " + "ab" * 32 + "\n", encoding="utf-8")
            esperada = "arc-e/paquetes-p10/" + "ab" * 32 + ".zip"
            self.assertEqual(podar_r2.clave_paquete_p10("nac42", root), esperada)
            self.assertEqual(podar_r2.clave_paquete_p10("congreso_soria", root), esperada)  # id viejo
            self.assertIsNone(podar_r2.clave_paquete_p10("nac01", root))  # sin contrato


if __name__ == "__main__":
    unittest.main()
