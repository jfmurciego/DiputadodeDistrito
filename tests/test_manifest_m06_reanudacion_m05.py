# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: test de manifest_generacion_territorial 1.0.1
VERSIÓN: 1.0.0
FECHA: 2026-11-01
FUNCIÓN: al reanudar desde M05, el índice trae el mismo artefacto M04 como «checkpoint» y como «m04»;
artifact_ref debe aceptarlo (Congreso Álava, run 41335088773) y seguir rechazando ids distintos.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herramientas.manifest_generacion_territorial import GenerationManifestError, artifact_ref  # noqa: E402

RUN = 41324180872
NAME = f"ddd-state-{RUN}-M04"
M04 = {
    "id": 13091186122, "name": NAME, "workflow_run_id": RUN, "expired": False,
    "digest": "sha256:" + "a" * 64, "size_in_bytes": 84409803,
}


class ReanudacionDesdeM05(unittest.TestCase):
    def test_mismo_artefacto_como_checkpoint_y_m04(self):
        ref = artifact_ref({"artifacts": [dict(M04), dict(M04)]}, run_id=RUN, name=NAME)
        self.assertEqual(ref["artifact_id"], 13091186122)
        self.assertEqual(ref["artifact_sha256"], "a" * 64)

    def test_ids_distintos_siguen_siendo_ambiguos(self):
        otro = dict(M04, id=13091186999)
        with self.assertRaises(GenerationManifestError):
            artifact_ref({"artifacts": [dict(M04), otro]}, run_id=RUN, name=NAME)

    def test_mismo_id_con_datos_distintos_falla(self):
        otro = dict(M04, digest="sha256:" + "b" * 64)
        with self.assertRaises(GenerationManifestError):
            artifact_ref({"artifacts": [dict(M04), otro]}, run_id=RUN, name=NAME)


if __name__ == "__main__":
    unittest.main()
