# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: test T-11 de generar_estado_operativo 2.3.5
VERSIÓN: 1.0.0
FECHA: 2026-11-01
FUNCIÓN: un fallo solo en la 05 no marca «parada» si la cadena está completa y publicada.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("estado", ROOT / "herramientas/generar_estado_operativo.py")
estado = importlib.util.module_from_spec(spec)
spec.loader.exec_module(estado)

FALLO_05 = {"run_id": 1, "status": "FAILED", "stopped_at": "05 · Publicación del Visor", "reason": "ver log del run"}


class ParadaSoloPublicacion(unittest.TestCase):
    def test_completa_y_publicada_no_queda_parada(self):
        r = estado._clear_publication_only_stop(FALLO_05, True, True)
        self.assertIsNone(r["stopped_at"])
        self.assertIsNone(r["reason"])
        self.assertEqual(r["superseded_failure"]["stopped_at"], FALLO_05["stopped_at"])
        self.assertEqual(r["status"], "FAILED")

    def test_sin_publicar_o_incompleta_sigue_parada(self):
        self.assertEqual(estado._clear_publication_only_stop(FALLO_05, True, False), FALLO_05)
        self.assertEqual(estado._clear_publication_only_stop(FALLO_05, False, True), FALLO_05)

    def test_fallo_en_otra_fase_no_se_toca(self):
        fallo_02 = dict(FALLO_05, stopped_at="02 · Generación de Distritos Autonómicos")
        self.assertEqual(estado._clear_publication_only_stop(fallo_02, True, True), fallo_02)

    def test_registro_de_publicaciones(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(estado._published_territories(root), set())
            (root / "orchestracion").mkdir()
            (root / "orchestracion/publicaciones_visor.json").write_text(
                json.dumps({"products": [{"territory_id": "congreso_lugo"}, {"id": "sin-territorio"}]}),
                encoding="utf-8",
            )
            self.assertEqual(estado._published_territories(root), {"congreso_lugo"})


if __name__ == "__main__":
    unittest.main()
