# -*- coding: utf-8 -*-
"""T-443 (2/5): las entradas de índice admiten `clave_anterior` (ruta vieja) durante la transición al árbol nuevo de R2 (D-188).

Regla: se lee la clave de la entrada (nueva); solo si el objeto falta se prueba la anterior; un sha256 distinto falla cerrado
(fuente_r2, restaurar_estado_r2, publicar_doble_vuelta). localizar_artefacto_durable ya descartaba cualquier fuente con SHA-256
distinto y probaba la siguiente: la anterior entra como primer respaldo, antes de Actions y la release.
"""
import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
import fuente_r2  # noqa: E402
import publicar_doble_vuelta as pdv  # noqa: E402
import restaurar_estado_r2 as rr  # noqa: E402
from herramientas.localizar_artefacto_durable import fetch, locate  # noqa: E402

NUEVA = "fuentes/interior/2023/02202307_MESA.zip"
VIEJA = "arc-e/fuentes/interior/02202307_MESA_e78fc231326a.zip"
DATOS = b"mesas"
SHA = hashlib.sha256(DATOS).hexdigest()
ENV = {"R2_BUCKET": "cubo", "R2_ACCOUNT_ID": "cta"}


def _r2(objetos: dict[str, bytes], vistas: list):
    def cp(origen, destino):
        vistas.append(origen)
        k = origen.split("/", 3)[3]
        if k not in objetos:
            raise OSError("NoSuchKey")
        Path(destino).write_bytes(objetos[k])
    return cp


class FuenteR2(unittest.TestCase):
    def _indice(self, td: Path, **extra) -> Path:
        p = td / "fuentes_r2.json"
        p.write_text(json.dumps({"fuentes": {"m.zip": {"clave": NUEVA, "sha256": SHA, **extra}}}), encoding="utf-8")
        return p

    def test_claves(self):
        self.assertEqual(fuente_r2.claves({"clave": NUEVA, "clave_anterior": VIEJA}), [NUEVA, VIEJA])
        self.assertEqual(fuente_r2.claves({"clave": VIEJA}), [VIEJA])
        self.assertEqual(fuente_r2.claves({"clave": VIEJA, "clave_anterior": VIEJA}), [VIEJA])
        self.assertEqual(fuente_r2.claves({"clave_r2": NUEVA, "clave_r2_anterior": VIEJA}, "clave_r2"), [NUEVA, VIEJA])

    def test_nueva_ausente_cae_a_la_vieja(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.dict("os.environ", ENV):
            td = Path(td)
            vistas = []
            rc = fuente_r2.bajar("m.zip", td / "o", _r2({VIEJA: DATOS}, vistas), self._indice(td, clave_anterior=VIEJA))
            self.assertEqual(rc, 0)
            self.assertEqual(vistas, [f"s3://cubo/{NUEVA}", f"s3://cubo/{VIEJA}"])
            self.assertEqual((td / "o").read_bytes(), DATOS)

    def test_nueva_presente_no_toca_la_vieja(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.dict("os.environ", ENV):
            td = Path(td)
            vistas = []
            self.assertEqual(fuente_r2.bajar("m.zip", td / "o", _r2({NUEVA: DATOS, VIEJA: b"x"}, vistas),
                                             self._indice(td, clave_anterior=VIEJA)), 0)
            self.assertEqual(vistas, [f"s3://cubo/{NUEVA}"])

    def test_sha_distinto_en_la_nueva_falla_cerrado(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.dict("os.environ", ENV):
            td = Path(td)
            vistas = []
            self.assertEqual(fuente_r2.bajar("m.zip", td / "o", _r2({NUEVA: b"otro", VIEJA: DATOS}, vistas),
                                             self._indice(td, clave_anterior=VIEJA)), 53)
            self.assertEqual(vistas, [f"s3://cubo/{NUEVA}"])
            self.assertFalse((td / "o").exists())

    def test_sin_clave_anterior_igual_que_antes(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.dict("os.environ", ENV):
            td = Path(td)
            vistas = []
            self.assertEqual(fuente_r2.bajar("m.zip", td / "o", _r2({VIEJA: DATOS}, vistas), self._indice(td)), 3)
            self.assertEqual(vistas, [f"s3://cubo/{NUEVA}"])


class Restaurar(unittest.TestCase):
    RUN = "43204696160"

    def test_clave_anterior_de_archivo_r2(self):
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("estado/production_status.json", "{}")
        datos = b.getvalue()
        nueva, vieja = "interno/estados/autonomicas/andalucia/minimo-m08.zip", f"aut01/{self.RUN}/ddd-minimo-{self.RUN}-M08.zip"
        with tempfile.TemporaryDirectory() as td, mock.patch.dict("os.environ", ENV):
            td = Path(td)
            man = td / "archivo_r2.json"
            man.write_text(json.dumps({"artefactos": {nueva: {"run_id": self.RUN, "artefacto": f"ddd-minimo-{self.RUN}-M08",
                                                              "sha256": hashlib.sha256(datos).hexdigest(), "clave_anterior": vieja}}}))
            vistas = []
            self.assertEqual(rr.restaurar(self.RUN, td / "d", manifiesto=man, cp=_r2({vieja: datos}, vistas)), 0)
            self.assertEqual(vistas, [f"s3://cubo/{nueva}", f"s3://cubo/{vieja}"])
            self.assertTrue((td / "d" / f"ddd-state-{self.RUN}-M08" / "production_status.json").is_file())
            vistas.clear()
            self.assertEqual(rr.restaurar(self.RUN, td / "e", manifiesto=man, cp=_r2({}, vistas)), 3)


class PublicarDobleVuelta(unittest.TestCase):
    def test_bajar_con_respaldo_y_fallo_cerrado(self):
        vistas = []
        self.assertEqual(pdv._bajar(_r2({VIEJA: DATOS}, vistas), "cubo", [NUEVA, VIEJA], SHA, "X"), DATOS)
        self.assertEqual(vistas, [f"s3://cubo/{NUEVA}", f"s3://cubo/{VIEJA}"])
        with self.assertRaisesRegex(pdv.DobleVueltaError, "^X:"):
            pdv._bajar(_r2({NUEVA: b"otro", VIEJA: DATOS}, []), "cubo", [NUEVA, VIEJA], SHA, "X")
        with self.assertRaisesRegex(pdv.DobleVueltaError, "CLAVE_AUSENTE"):
            pdv._bajar(_r2({}, []), "cubo", [NUEVA, VIEJA], SHA, "X")
        self.assertEqual(pdv._bajar(_r2({VIEJA: DATOS}, []), "cubo", VIEJA, SHA, "X"), DATOS)  # una sola clave, como antes


class Localizar(unittest.TestCase):
    def test_clave_anterior_es_el_primer_respaldo(self):
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, "w") as z:
            z.writestr("run/CHAIN_STATE.json", "{}")
        payload = payload.getvalue()
        sha = hashlib.sha256(payload).hexdigest()
        nueva, vieja = "interno/almacen-m06/ddd-state-1-M06.zip", f"arc-p/m06/ddd-state-1-M06_{sha[:12]}.zip"
        indice = {nueva: {"run_id": "1", "artifact_name": "ddd-state-1-M06", "artifact_id": 9, "sha256": sha, "clave_anterior": vieja}}

        def api(path):
            raise AssertionError(f"sin red: {path}")
        with mock.patch("herramientas.localizar_artefacto_durable._locate", side_effect=__import__(
                "herramientas.localizar_artefacto_durable", fromlist=["LocationError"]).LocationError(4, "sin Actions")):
            loc = locate("o/r", 1, "ddd-state-1-M06", sha, api=api, r2_index=indice)
        self.assertEqual((loc["r2_key"], loc["fallback"]["r2_key"], loc["fallback"]["fallback"]), (nueva, vieja, None))
        with tempfile.TemporaryDirectory() as td:
            vistas = []

            def r2(k, t):
                vistas.append(k)
                if k != vieja:
                    raise OSError("NoSuchKey")
                t.write_bytes(payload)
            res = fetch(loc, Path(td) / "in", extract=True, download=lambda *a: (_ for _ in ()).throw(AssertionError("release")), r2=r2)
            self.assertEqual(vistas, [nueva, vieja])
            self.assertEqual(res["r2_key"], vieja)


if __name__ == "__main__":
    unittest.main()
