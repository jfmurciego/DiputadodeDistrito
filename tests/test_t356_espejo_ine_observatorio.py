"""T-356: índice de ARC-E con los 17 seccionados INE y las 625 piezas del Observatorio, y script PowerShell del propietario."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDX = json.loads((ROOT / "orchestracion/fuentes_r2.json").read_text(encoding="utf-8"))["fuentes"]
PS1 = (ROOT / "herramientas/espejo_ine_observatorio_r2.ps1").read_text(encoding="utf-8")
# Literales independientes: sha256 de T-85 (docs/ESTUDIOS/T306_HISTORICO/INVENTARIO.md §3) y huella T-89 de una pieza del Observatorio.
SHA_INE = {2012: "772ad76b84e1b3bb9293a5595d2ccafa06f21a3a58ccc96a9ec5dadd99e46c4a", 2015: "50dda58ed4afb57c7f1f38e6b6b8150768efaa225bfc3a523b9c210a2a218c03",
           2016: "3410af763bfe58d1b0f9c0d0038cbdd6417e0f3f6d0fce6a3e70bef64c84b3e1", 2019: "656119dadadb57ef3fa9d20a8ba33399fe606e553c9fef3fc338786e52fae967",
           2020: "07544bb49256e9e9f290b6f459a0a833e69c97900eb840c3f5bbe863914ede6e", 2024: "df931fa0d372808eb81abb2f2645ed5ecccbd6ed397b85db656980748ddd6bf7"}


class Indice(unittest.TestCase):
    def test_17_seccionados_2010_2026(self):
        ine = {k: v for k, v in IDX.items() if re.fullmatch(r"seccionado_\d{4}\.zip", k)}
        self.assertEqual(sorted(ine), [f"seccionado_{y}.zip" for y in range(2010, 2027)])
        for k, v in ine.items():
            self.assertEqual(v["origen_url"], f"https://www.ine.es/prodyser/cartografia/{k}")

    def test_sha_conocidos_y_clave_con_sha12(self):
        for y, s in SHA_INE.items():
            e = IDX[f"seccionado_{y}.zip"]
            self.assertEqual(e["sha256"], s)
            self.assertEqual(e["clave"], f"arc-e/fuentes/ine/seccionado_{y}_{s[:12]}.zip")

    def test_sha_null_es_fail_closed_sin_clave(self):
        pend = [k for k, v in IDX.items() if k.startswith("seccionado_") and v["sha256"] is None]
        self.assertTrue(pend)
        for k in pend:
            self.assertIsNone(IDX[k]["clave"])

    def test_625_piezas_del_observatorio_con_las_huellas_del_manifiesto(self):
        man = json.loads((ROOT / "orchestracion/fuente_nazioenbehatokia.json").read_text(encoding="utf-8"))["ficheros"]
        obs = {k: v for k, v in IDX.items() if k.startswith("nazioenbehatokia/")}
        self.assertEqual(len(obs), 625)
        self.assertEqual(obs["nazioenbehatokia/data/201111/sekzioa/01.json"]["sha256"], "d4cd5dfba24c516bb1223bc6516ee795c5ffdb295bd9d82349f22dc5b36e9e28")
        for r, m in man.items():
            e = obs[f"nazioenbehatokia/{r}"]
            self.assertEqual((e["sha256"], e["bytes"]), (m["sha256"], m["bytes"]))
            self.assertEqual(e["clave"], f"arc-e/fuentes/nazioenbehatokia/{r[:-5]}_{m['sha256'][:12]}.json")
            self.assertEqual(e["origen_url"], f"https://nazioenbehatokia.eus/{r}")

    def test_negativo_clave_sin_sha12_no_pasa(self):
        e = IDX["seccionado_2012.zip"]
        self.assertNotEqual(e["clave"], "arc-e/fuentes/ine/seccionado_2012.zip")
        self.assertIn(e["sha256"][:12], e["clave"])

    def test_fuentes_previas_intactas(self):
        self.assertEqual(IDX["seccionado_2023.zip"]["bytes"], 64929708)
        self.assertEqual(IDX["02202307_MESA.zip"]["sha256"], "e78fc231326a03cf67bbec87b7100ea0c8c46859daa1b2a631c06daaaf1717f8")


class Script(unittest.TestCase):
    def test_requisitos(self):
        for frag in ("-SoloBajar", "[switch]$Forzar", "Read-Host", "exit 1", "PK", "Retry-After", "429", "C:\\ddd",
                     "arc-e/fuentes/ine/", "arc-e/fuentes/nazioenbehatokia/", "raw.githubusercontent.com", "head-object",
                     "UTF8Encoding($false)", "descargado_en", "origen_url"):
            self.assertIn(frag, PS1)

    def test_no_imprime_ni_guarda_credenciales(self):
        # ninguna línea que lea $env:AWS_*/R2_* (salvo la subida y los comentarios) imprime o escribe
        for linea in PS1.splitlines():
            if re.search(r"\$env:(AWS_|R2_)|Env:\$v", linea) and not linea.lstrip().startswith("#"):
                self.assertNotRegex(linea, r"Write-(Host|Warning|Output|Error|Verbose|Debug)|Set-Content|Out-File|WriteAllText|Escribir-Sin-Bom|ConvertTo-Json|echo")
        self.assertNotRegex(PS1, r"Write-(Host|Warning)[^\n]*\$env:")

    def test_ruta_completa_absolutas_y_relativas(self):
        # Sin pwsh en CI no se ejecuta el .ps1: se comprueba que la función usa IsPathRooted y no concatena a ciegas,
        # y se prueba una función espejo (ntpath = semántica de Windows) con el mismo algoritmo. Limitación: no es el .ps1 real.
        m = re.search(r"function Ruta-Completa\(\$ruta\) \{(.*?)\n\}", PS1, re.S)
        self.assertIsNotNone(m)
        self.assertIn("IsPathRooted", m.group(1))
        self.assertIn("(Get-Location).ProviderPath", m.group(1))
        self.assertNotIn("Join-Path (Get-Location) $ruta", PS1)
        self.assertIn("Ruta-Completa $ruta", PS1.split("function Escribir-Sin-Bom")[1].splitlines()[0])
        import ntpath

        def espejo(ruta, cwd="C:\\Users\\x"):
            return ntpath.normpath(ruta if ntpath.isabs(ruta) else ntpath.join(cwd, ruta))
        self.assertEqual(espejo("C:\\ddd\\ine\\seccionado_2012.zip.ok"), "C:\\ddd\\ine\\seccionado_2012.zip.ok")
        self.assertEqual(espejo("salida.json"), "C:\\Users\\x\\salida.json")
        self.assertNotEqual(ntpath.join("C:\\Users\\x", "C:\\ddd\\a"), "C:\\Users\\x\\C:\\ddd\\a")  # el bug de 1.0.0 no se reproduce

    def test_reanudacion_recalcula_sha_y_cancelar_no_es_exito(self):
        self.assertIn("(Sha256Hex $ruta) -eq $m.sha256", PS1)
        self.assertRegex(PS1, r"Cancelado[^\n]*exit 2")

    def test_solo_ascii(self):
        # PowerShell 5.1 lee un .ps1 sin BOM como ANSI: cualquier byte > 127 sale roto
        datos = (ROOT / "herramientas/espejo_ine_observatorio_r2.ps1").read_bytes()
        self.assertEqual([i for i, b in enumerate(datos) if b > 127][:5], [])

    def test_indice_de_la_rama_documentado_y_error_claro(self):
        self.assertIn("-Indice https://raw.githubusercontent.com/jfmurciego/DiputadodeDistrito/t356-espejo-ine-observatorio-r2/", PS1)
        self.assertRegex(PS1, r"solo \$\(\$piezas\.Count\)[^\n]*Pasa -Indice")

    def test_limite_y_error_completo_por_pieza(self):
        # Sin pwsh no se ejecuta el .ps1: se comprueba el texto y una funcion espejo del formato de error en una linea.
        self.assertIn("[int]$Limite = 0", PS1)
        self.assertIn("Select-Object -First $Limite", PS1)
        self.assertIn("-Limite 1 -SoloBajar", PS1)
        self.assertIn("function Detalle($e)", PS1)
        for frag in ("GetType().FullName", "InnerException", "ScriptLineNumber", "ScriptStackTrace", "FullyQualifiedErrorId"):
            self.assertIn(frag, PS1)
        self.assertIn("$resultado[$p.nombre] = [ordered]@{ origen_url = $f.origen_url; subido = $false; error = $detalle }", PS1)
        self.assertNotIn("$($_.Exception.Message)\"\n        $fallos", PS1)  # el catch ya no imprime solo el mensaje
        import re as _re

        def espejo(tipo, msg, linea):
            return f"{tipo}: {_re.sub(chr(92) + 's+', ' ', msg).strip()} | linea {linea}"
        d = espejo("System.Exception", "\r\n  HTTP 0 \n  cortado", "146: $http = Bajar")
        self.assertNotIn("\n", d)
        self.assertIn("System.Exception: HTTP 0 cortado", d)
        self.assertTrue(espejo("System.IO.IOException", "", "9").startswith("System.IO.IOException:"))  # mensaje vacio: queda el tipo

    def test_cabecera_y_sin_ids_viejos(self):
        self.assertIn("VERSION 1.0.0", PS1.splitlines()[1])
        self.assertIn("ANTERIOR: ninguna (fichero nuevo)", PS1)
        self.assertNotRegex(PS1, r"territorios/(?!aut|nac)[a-z_]+/")


if __name__ == "__main__":
    unittest.main()
