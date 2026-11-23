#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: P40 promueve a `mapas/` la doble vuelta fijada (T-443, D-198) y el lector la busca primero allí
VERSIÓN: 1.0.0 · FECHA: 2026-11-23 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: R2 simulado en memoria (objetos con metadatos y ETag). Claves esperadas escritas a mano (`mapas/nacionales/congreso-2023/alava/…`,
  `mapas/autonomicas/andalucia-2026/…`). Controles negativos: sha256 de origen distinto (nada se escribe), objeto que no queda con su sha256
  tras subir, put concurrente con otro contenido; idempotencia (segunda pasada sin escrituras); el fijado no se reescribe.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT))
import publicar_doble_vuelta as pdv  # noqa: E402
from tests.test_t419_publicar_doble_vuelta import Montaje, zips_buenos, zip_de, resultados, detalle  # noqa: E402

ZIP_ALAVA = "mapas/nacionales/congreso-2023/alava/doble-vuelta.zip"
ZIP_ALBACETE = "mapas/nacionales/congreso-2023/albacete/doble-vuelta.zip"
INF_NAC = "mapas/nacionales/congreso-2023/informe-doble-vuelta.json"
ZIP_AND = "mapas/autonomicas/andalucia-2026/doble-vuelta.zip"
INF_AUT = "mapas/autonomicas/informe-doble-vuelta.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class R2:
    """Bucket simulado: objetos {clave: bytes}, metadatos {clave: {sha256, run}}, ETag = sha256 del contenido."""

    def __init__(self, objetos: dict):
        self.objetos = objetos
        self.meta: dict = {}
        self.escrituras: list = []
        self.corromper = False

    def cp(self, origen, destino, extra=None):
        clave = origen.split("/", 3)[3]
        if clave not in self.objetos:
            raise OSError("NoSuchKey")
        Path(destino).write_bytes(self.objetos[clave])

    def cab(self, k):
        if k not in self.objetos:
            return None
        m = self.meta.get(k, {})
        return {"sha256": m.get("sha256"), "run": m.get("run"), "bytes": len(self.objetos[k]), "etag": sha(self.objetos[k])}

    def subir(self, k, ruta, h, run=None, condicion=None):
        actual = self.objetos.get(k)
        if (condicion == "*" and actual is not None) or (condicion not in (None, "*") and (actual is None or sha(actual) != condicion)):
            raise RuntimeError(f"R2_ESCRITURA_CONCURRENTE: {k}")
        datos = Path(ruta).read_bytes()
        self.objetos[k] = (datos + b"x") if self.corromper else datos
        self.meta[k] = {"sha256": h, "run": run}
        self.escrituras.append(k)


class Promover(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(pdv, "ESPERADOS", 2)
        p.start()
        self.addCleanup(p.stop)
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.m = Montaje(Path(self.td.name), zips_buenos())
        self.r2 = R2(self.m.objetos)

    def promover(self):
        return pdv.promover(self.m.td, self.r2.cp, self.r2.cab, self.r2.subir, "b", fecha="2026-11-23")

    def test_copia_tal_cual_a_mapas_con_manifiestos_y_sin_tocar_el_fijado(self):
        fijado = (self.m.td / "configuracion/doble_vuelta_publicada.json").read_bytes()
        origen = {t: self.m.objetos[f"carpeta_{t}/{r}/ddd-doble-vuelta-{r}-p75-77-1.zip"] for t, r in (("nac01", "1001"), ("nac02", "1002"))}
        out = self.promover()
        self.assertEqual(self.m.objetos[ZIP_ALAVA], origen["nac01"])
        self.assertEqual(self.m.objetos[ZIP_ALBACETE], origen["nac02"])
        self.assertEqual(self.m.objetos[INF_NAC], self.m.informe)
        self.assertEqual(self.r2.meta[ZIP_ALAVA], {"sha256": sha(origen["nac01"]), "run": "77-1"})
        man = json.loads(self.m.objetos["mapas/nacionales/congreso-2023/alava/manifiesto.json"])
        self.assertEqual(man["ficheros"]["doble-vuelta.zip"]["sha256"], sha(origen["nac01"]))
        self.assertEqual(man["ficheros"]["doble-vuelta.zip"]["run_m08"], "1001")
        man_inf = json.loads(self.m.objetos["mapas/nacionales/congreso-2023/manifiesto.json"])
        self.assertEqual(man_inf["ficheros"]["informe-doble-vuelta.json"]["sha256"], self.m.pin["informe_sha256"])
        self.assertEqual(out["ambitos"][0]["copiados"], [ZIP_ALAVA, ZIP_ALBACETE, INF_NAC])
        self.assertEqual((self.m.td / "configuracion/doble_vuelta_publicada.json").read_bytes(), fijado)

    def test_segunda_pasada_no_escribe_nada(self):
        self.promover()
        self.r2.escrituras.clear()
        out = self.promover()
        self.assertEqual(self.r2.escrituras, [])
        self.assertEqual(out["manifiestos"], [])

    def test_sustituye_en_mapas_un_objeto_con_otro_sha(self):
        self.m.objetos[ZIP_ALAVA] = b"viejo"
        self.r2.meta[ZIP_ALAVA] = {"sha256": sha(b"viejo")}
        self.promover()
        self.assertEqual(sha(self.m.objetos[ZIP_ALAVA]), json.loads(self.m.informe)["territorios"][0]["sha256_salida"])

    def test_conserva_las_otras_entradas_del_manifiesto(self):
        carpeta = "mapas/nacionales/congreso-2023/alava"
        self.m.objetos[f"{carpeta}/manifiesto.json"] = json.dumps({"ficheros": {"mapa.geojson": {"sha256": "c" * 64, "bytes": 7}}}).encode()
        self.promover()
        man = json.loads(self.m.objetos[f"{carpeta}/manifiesto.json"])
        self.assertEqual(sorted(man["ficheros"]), ["doble-vuelta.zip", "mapa.geojson"])

    def test_origen_con_otro_sha_no_escribe_nada(self):
        clave = "carpeta_nac02/1002/ddd-doble-vuelta-1002-p75-77-1.zip"
        self.m.objetos[clave] = b"otro"
        with self.assertRaisesRegex(pdv.DobleVueltaError, "ZIP_SHA256_DISTINTO"):
            self.promover()
        self.assertEqual(self.r2.escrituras, [])

    def test_lo_que_no_queda_con_su_sha_en_r2_falla(self):
        self.r2.corromper = True
        with self.assertRaisesRegex(pdv.DobleVueltaError, "PROMOCION_SHA256_DISTINTO"):
            self.promover()

    def test_put_concurrente_con_otro_contenido_falla(self):
        real = self.r2.subir

        def otro_escribe_antes(k, ruta, h, run=None, condicion=None):
            if k == ZIP_ALAVA and k not in self.m.objetos:
                self.m.objetos[k] = b"de otro"
            return real(k, ruta, h, run, condicion)
        self.r2.subir = otro_escribe_antes
        with self.assertRaisesRegex(pdv.DobleVueltaError, "PROMOCION_CONCURRENTE"):
            self.promover()

    def test_sin_fijado_no_hace_nada(self):
        (self.m.td / "configuracion/doble_vuelta_publicada.json").unlink()
        self.assertIsNone(self.promover())
        self.assertEqual(self.r2.escrituras, [])

    def test_autonomicas_solo_las_ok_a_su_carpeta(self):
        z = zip_de(resultados(), detalle())
        self.m.objetos["interno/doble-vuelta/autonomicas/andalucia-2026/doble-vuelta.zip"] = z
        inf = {"eleccion": "autonomicas", "run_p75": "88-1", "entradas": {"bloques": {"sha256": "b" * 64}, "alias": {"sha256": "a" * 64}}, "total": 2,
               "territorios": [{"territorio": "aut01", "run": "2001", "estado": "OK", "eleccion": "2026-06", "sha256_salida": sha(z),
                                "clave_r2": "interno/doble-vuelta/autonomicas/andalucia-2026/doble-vuelta.zip"},
                               {"territorio": "aut02", "run": "2002", "estado": "NO_APLICA", "motivo": "sin bloques"}]}
        ib = json.dumps(inf).encode()
        self.m.objetos["interno/doble-vuelta/autonomicas/informe-doble-vuelta.json"] = ib
        self.m.pin["autonomicas"] = {"run_p75": "88-1", "informe_clave": "interno/doble-vuelta/autonomicas/informe-doble-vuelta.json", "informe_sha256": sha(ib)}
        self.m.escribir_pin()
        self.promover()
        self.assertEqual(self.m.objetos[ZIP_AND], z)
        self.assertEqual(self.m.objetos[INF_AUT], ib)
        aut = sorted(k for k in self.m.objetos if k.startswith("mapas/autonomicas/"))
        self.assertEqual(aut, [ZIP_AND, "mapas/autonomicas/andalucia-2026/manifiesto.json", INF_AUT,
                               "mapas/autonomicas/manifiesto.json"])  # la fila NO_APLICA no se promueve


class Lector(unittest.TestCase):
    """El lector prueba `mapas/` primero; si falta o es de otro fijado, la clave fijada."""

    def setUp(self):
        p = mock.patch.object(pdv, "ESPERADOS", 2)
        p.start()
        self.addCleanup(p.stop)
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.m = Montaje(Path(self.td.name), zips_buenos())
        self.r2 = R2(self.m.objetos)

    def publicar(self):
        with tempfile.TemporaryDirectory() as d:
            return pdv.publicar(self.m.td, Path(d), self.r2.cp, "b", "2026-11-23", sitio=self.m.td / "sitio")

    def test_tras_promover_basta_mapas(self):
        pdv.promover(self.m.td, self.r2.cp, self.r2.cab, self.r2.subir, "b")
        for k in [k for k in self.m.objetos if not k.startswith("mapas/")]:
            del self.m.objetos[k]  # sin la clave fijada de interno/: lee de mapas/
        self.assertEqual(len(self.publicar()["territorios"]), 2)

    def test_mapas_de_otro_fijado_cae_a_la_clave_fijada(self):
        for k in (ZIP_ALAVA, ZIP_ALBACETE, INF_NAC):
            self.m.objetos[k] = b"de la publicacion anterior"
        self.assertEqual(len(self.publicar()["territorios"]), 2)

    def test_clave_fijada_con_otro_sha_sigue_rechazando(self):
        self.m.objetos["carpeta_nac01/1001/ddd-doble-vuelta-1001-p75-77-1.zip"] = b"otro"
        with self.assertRaisesRegex(pdv.DobleVueltaError, "ZIP_SHA256_DISTINTO"):
            self.publicar()


class WorkflowP40(unittest.TestCase):
    """El paso de P40: después del despliegue en success, solo main y sin simulación, secretos R2 solo en su env, fallo = job rojo."""

    @classmethod
    def setUpClass(cls):
        import yaml
        cls.wf = yaml.safe_load((ROOT / ".github/workflows/p40-publicacion.yml").read_text(encoding="utf-8"))
        cls.pasos = cls.wf["jobs"]["publicar"]["steps"]
        cls.paso = next(s for s in cls.pasos if s.get("name") == "Promover la doble vuelta a mapas/ (T-443)")

    def test_despues_del_despliegue_y_solo_main_sin_simular(self):
        n = [s.get("name") or s.get("id") for s in self.pasos]
        self.assertLess(n.index("deployment"), n.index(self.paso["name"]))
        self.assertLess(n.index("Persistir registro sólo después del despliegue"), n.index(self.paso["name"]))
        self.assertEqual(self.paso["if"], "${{ github.ref == 'refs/heads/main' && steps.deployment.outcome == 'success' && inputs.simular != true }}")
        self.assertNotIn("continue-on-error", self.paso)  # un fallo pone el job en rojo

    def test_secretos_r2_solo_en_el_paso(self):
        self.assertEqual(sorted(self.paso["env"]), ["AWS_ACCESS_KEY_ID", "AWS_DEFAULT_REGION", "AWS_SECRET_ACCESS_KEY", "R2_ACCOUNT_ID", "R2_BUCKET"])
        job_env = json.dumps(self.wf["jobs"]["publicar"].get("env") or {})
        self.assertNotIn("R2_ACCESS_KEY_ID", job_env)

    def test_orden_y_comando(self):
        self.assertIn("python3 herramientas/publicar_doble_vuelta.py promover", self.paso["run"])
        for prohibido in ("git push", "git add", "doble_vuelta_publicada.json"):
            self.assertNotIn(prohibido, self.paso["run"])


if __name__ == "__main__":
    unittest.main()
