# VERSIÓN: 1.0.0 · FECHA: 2026-11-11 · CAMBIOS: T-230b, idempotencia del registro del par ante campos derivados.
# ANTERIOR: ninguna (fichero nuevo)
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from herramientas import registrar_par_fuentes_legislatura as rp

SHA = "29577f2efcc4d643fc6a1b7c5c88313ecdc936fe32bee397f971f1b5dfd49d0b"


def _pair(reuse: dict, *, artifact: str = "a" * 64, pair_sha: str = SHA) -> dict:
    return {
        "schema": "x",
        "territory_id": "congreso_alava",
        "edition": "2023",
        "territorial_source": {"run_id": 1, "artifact_sha256": artifact},
        "electoral_source": {"run_id": 2, "artifact_sha256": "b" * 64},
        "territorial_product_reuse": reuse,
        "pair_sha256": pair_sha,
    }


OLD = {"available": False, "geometric_reuse_compatible": False, "reason": "NO_TERRITORIAL_PRODUCT"}
NEW = {"available": True, "geometric_reuse_compatible": True, "reason": "SOURCE_IDENTITY_MATCH"}


class RegistroParIdempotente(unittest.TestCase):
    def _run(self, stored: dict | None, rebuilt: dict, *, verify_only: bool = False):
        tmp = Path(tempfile.mkdtemp())
        path = tmp / "territorios/congreso_alava/evidencia/pares_fuentes/2023" / f"{SHA}.json"
        if stored is not None:
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(stored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before = path.read_bytes() if stored is not None else None
        (tmp / "rv.json").write_text("{}", encoding="utf-8")
        with mock.patch.object(rp, "build_pair", return_value=rebuilt), mock.patch.object(
            rp, "_set_pair_pointer"
        ) as pointer:
            result = rp.register_pair(
                root_dir=tmp, territory="Congreso Álava",
                remote_verification_path=tmp / "rv.json", verify_only=verify_only,
            )
        return result, path, before, pointer

    def test_alava_solo_cambia_campo_derivado_acepta_sin_reescribir(self):
        for verify_only in (False, True):
            result, path, before, _ = self._run(_pair(OLD), _pair(NEW), verify_only=verify_only)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(result["territorial_product_reuse"], OLD)
            self.assertEqual(result["pair_sha256"], SHA)

    def test_receipt_real_de_alava(self):
        root = Path(__file__).resolve().parents[1]
        real = root / "territorios/congreso_alava/evidencia/pares_fuentes/2025" / f"{SHA}.json"
        if not real.is_file():
            self.skipTest("receipt de Álava no presente")
        stored = json.loads(real.read_text(encoding="utf-8"))
        self.assertEqual(stored["territorial_product_reuse"]["reason"], "NO_TERRITORIAL_PRODUCT")
        rebuilt = {**stored, "territorial_product_reuse": NEW}
        result, path, before, _ = self._run(stored, rebuilt)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(result["territorial_product_reuse"]["reason"], "NO_TERRITORIAL_PRODUCT")
        otro = {**rebuilt, "electoral_source": {**stored["electoral_source"], "run_id": 1}}
        with self.assertRaisesRegex(rp.PreparedSourcePairBlock, "contradictorio"):
            self._run(stored, otro)

    def test_contradiccion_real_sigue_bloqueando(self):
        with self.assertRaisesRegex(rp.PreparedSourcePairBlock, "contradictorio"):
            self._run(_pair(OLD), _pair(NEW, artifact="c" * 64))
        with self.assertRaisesRegex(rp.PreparedSourcePairBlock, "contradictorio"):
            self._run(_pair(OLD), _pair(OLD, artifact="c" * 64), verify_only=True)

    def test_identico_y_nuevo(self):
        result, path, before, pointer = self._run(_pair(NEW), _pair(NEW))
        self.assertEqual(path.read_bytes(), before)
        pointer.assert_called_once()
        result, path, before, _ = self._run(None, _pair(NEW))
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), _pair(NEW))
        with self.assertRaisesRegex(rp.PreparedSourcePairBlock, "ausente"):
            self._run(None, _pair(NEW), verify_only=True)


if __name__ == "__main__":
    unittest.main()
