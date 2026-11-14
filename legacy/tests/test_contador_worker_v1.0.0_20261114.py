#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: contrato del contador de visitas sin datos personales (T-294, opción A)
VERSIÓN: 1.0.0
FECHA: 2026-11-14
ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: el Worker solo guarda (día, ruta, n); sin logs, cookies ni almacenamiento; los visores solo envían location.pathname.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W = ROOT / "herramientas" / "contador_worker"
PROHIBIDO = re.compile(r"console\.|cookie|localStorage|sessionStorage|credentials|CF-Connecting-IP|User-Agent|Referer|X-Forwarded", re.I)


def sin_comentarios(js: str) -> str:
    return re.sub(r"(?m)^\s*//.*$", "", js)


class ContadorWorker(unittest.TestCase):
    def test_worker_sin_logs_ni_datos_personales(self):
        codigo = sin_comentarios((W / "worker.js").read_text(encoding="utf-8"))
        self.assertIsNone(PROHIBIDO.search(codigo), PROHIBIDO.search(codigo))

    def test_esquema_solo_dia_ruta_n(self):
        sql = (W / "schema.sql").read_text(encoding="utf-8")
        cols = re.findall(r"(?m)^\s+(\w+)\s+(?:TEXT|INTEGER)", sql)
        self.assertEqual(cols, ["dia", "ruta", "n"])

    def test_observabilidad_apagada(self):
        t = (W / "wrangler.toml").read_text(encoding="utf-8")
        self.assertRegex(t, r"(?s)\[observability\]\s*enabled\s*=\s*false")
        self.assertNotIn("logpush", t)

    @unittest.skipUnless(shutil.which("node"), "node no disponible")
    def test_pruebas_node_del_worker(self):
        r = subprocess.run(["node", "--test", "prueba.mjs"], cwd=W, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_visores_solo_envian_la_ruta(self):
        # Cada <script> en línea que mencione el contador debe ser exactamente un sendBeacon de location.pathname.
        patron = re.compile(r'^navigator\.sendBeacon&&navigator\.sendBeacon\("https://contador\.diputadodedistrito\.es/v",location\.pathname\)$')
        for rel in ("visor/index.html", "visor/v2/index.html", "visor/v3/index.html"):
            html = (ROOT / rel).read_text(encoding="utf-8")
            for cuerpo in re.findall(r"(?s)<script>(.*?)</script>", html):
                if "contador." in cuerpo:
                    self.assertRegex(cuerpo.strip(), patron, rel)


if __name__ == "__main__":
    unittest.main()
