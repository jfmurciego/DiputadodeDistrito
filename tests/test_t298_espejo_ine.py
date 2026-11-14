"""T-298: la batería toma las fuentes nacionales del espejo (sha256 verificado) y nunca de ine.es; la entrada mínima en R2
se indexa por la identidad del contrato, no por el id del territorio."""
import socket
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_entradas_solo_desde_r2_sin_red_y_sin_paquete_falla_claro(self):
        import argparse, contextlib, io

        def sin_red(*a, **k):
            raise AssertionError("acceso a red")
        ident = {"contrato": "c", "contrato_sha256": "1", "package_sha256": "p", "compatibility_identity_sha256": "c"}
        a = argparse.Namespace(territorios=["nac42"], todos=False, out="/nonexistent", desde_fuente=False, seccionado="ogc")
        buf = io.StringIO()
        with mock.patch.object(socket, "socket", sin_red), mock.patch.object(b.urllib.request, "urlopen", sin_red), \
                mock.patch.object(b, "entradas_r2_identidad", lambda t, out: None), \
                mock.patch.object(b, "_identidad_contrato", lambda t: ident), contextlib.redirect_stdout(buf):
            rc = b.entradas(a)
        self.assertEqual(rc, 1)
        self.assertIn("BATERIA_FALTA_PAQUETE_P10 nac42", buf.getvalue())
        self.assertIn(b.clave_identidad(ident), buf.getvalue())

    def test_entradas_desde_r2_restaura_y_verifica_sha256(self):
        import argparse, hashlib, json, zipfile
        ident = {"contrato": "c", "contrato_sha256": "1", "package_sha256": "p", "compatibility_identity_sha256": "c"}
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            datos = {"nac42_2025_m01_secciones_poblacion.geojson.zip": b"m01", "nac42_2025_m03_grafo.json": b"m03"}
            meta = {"identidad_contrato": ident, "entrada_minima": {k: hashlib.sha256(v).hexdigest() for k, v in datos.items()}}
            z = td / "p.zip"
            with zipfile.ZipFile(z, "w") as zf:
                zf.writestr("ENTRADAS.json", json.dumps(meta))
                for k, v in datos.items():
                    zf.writestr(k, v)

            def cp(origen, destino):
                self.assertEqual(origen, f"s3://bk/{b.clave_identidad(ident)}")
                Path(destino).write_bytes(z.read_bytes())
            cache = td / "cache"
            with mock.patch.dict("os.environ", {"R2_BUCKET": "bk"}), mock.patch.object(b, "_r2_cp", cp), \
                    mock.patch.object(b, "_identidad_contrato", lambda t: ident), mock.patch.object(b, "_cache", lambda t: cache):
                r = b.entradas_r2_identidad("nac42", td / "out")
                self.assertEqual(r["estado"], "OK")
                self.assertEqual((cache / "nac42_2025_m03_grafo.json").read_bytes(), b"m03")
            # fichero alterado: sha256 distinto → rechazado
            with zipfile.ZipFile(z, "w") as zf:
                zf.writestr("ENTRADAS.json", json.dumps(meta))
                zf.writestr("nac42_2025_m01_secciones_poblacion.geojson.zip", b"alterado")
                zf.writestr("nac42_2025_m03_grafo.json", b"m03")
            with mock.patch.dict("os.environ", {"R2_BUCKET": "bk"}), mock.patch.object(b, "_r2_cp", cp), \
                    mock.patch.object(b, "_identidad_contrato", lambda t: ident), mock.patch.object(b, "_cache", lambda t: cache):
                with self.assertRaises(b.PaqueteP10Corrupto):
                    b.entradas_r2_identidad("nac42", td / "out")

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

    def test_paquete_corrupto_y_ausente_tienen_codigos_distintos(self):
        import argparse, contextlib, io
        ident = {"contrato": "c", "contrato_sha256": "1", "package_sha256": "p", "compatibility_identity_sha256": "c"}
        a = argparse.Namespace(territorios=["nac42"], todos=False, out="/nonexistent", desde_fuente=False,
                               seccionado="shapefile", permitir_red_ine=False)

        def salida(efecto):
            buf = io.StringIO()
            with mock.patch.object(b, "entradas_r2_identidad", efecto), mock.patch.object(b, "_identidad_contrato", lambda t: ident), \
                    contextlib.redirect_stdout(buf):
                self.assertEqual(b.entradas(a), 1)
            return buf.getvalue()
        corrupto = salida(mock.Mock(side_effect=b.PaqueteP10Corrupto("fichero alterado")))
        self.assertIn("BATERIA_PAQUETE_P10_CORRUPTO nac42: fichero alterado", corrupto)
        self.assertNotIn("FALTA_PAQUETE", corrupto)
        ausente = salida(mock.Mock(return_value=None))
        self.assertIn("BATERIA_FALTA_PAQUETE_P10 nac42", ausente)
        self.assertNotIn("CORRUPTO", ausente)

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
        esperado = {"archivar_p10": ["Estado M03 de la 00 y archivado por identidad del contrato"],
                    "bateria": ["Entradas desde R2 (paquete P10)", "Archivar entradas en R2"],
                    "competicion": ["Entradas (R2, paquete P10)"], "plan": [], "aceptacion": []}
        for job, pasos in esperado.items():
            j = wf["jobs"][job]
            self.assertFalse([k for k in j.get("env", {}) if k.startswith(("AWS_", "R2_"))], job)
            self.assertEqual([s["name"] for s in j["steps"] if any(k.startswith("AWS_") for k in s.get("env", {}))], pasos, job)

    def test_clave_r2_por_identidad_no_por_territorio(self):
        a = {"contrato": "territorios/aut01/config/aut01_2025.yaml", "contrato_sha256": "1", "package_sha256": "p", "compatibility_identity_sha256": "c"}
        o = {**a, "contrato": "territorios/otro/config/otro_2025.yaml", "contrato_sha256": "2"}
        self.assertEqual(b.clave_identidad(a), b.clave_identidad(o))
        self.assertNotEqual(b.clave_identidad(a), b.clave_identidad({**a, "package_sha256": "q"}))
        self.assertRegex(b.clave_identidad(a), r"^arc-e/entradas-minimas/[0-9a-f]{16}\.zip$")


if __name__ == "__main__":
    unittest.main()
