#!/usr/bin/env python3
"""Contrato estático del lanzador local reproducible."""
from __future__ import annotations
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"ddd-local.sh"

class LocalLauncherContract(unittest.TestCase):
    def test_shell_es_valido(self):
        result=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_no_instala_ni_descarga_entorno(self):
        text=SCRIPT.read_text(encoding="utf-8").lower()
        for forbidden in ("miniforge","conda install","brew install","curl ","wget "):
            self.assertNotIn(forbidden,text)

    def test_ofrece_operacion_separada_y_autorizacion(self):
        text=SCRIPT.read_text(encoding="utf-8")
        for token in ("comprobar)","construir)","admitir)","probar)","ejecutar)","--autorizar","M01","M08"):
            self.assertIn(token,text)
        self.assertIn('docker build --pull -t "$IMAGE" .',text)
        self.assertIn("resolver_ejecucion_territorial.py",text)

if __name__=="__main__":unittest.main()
