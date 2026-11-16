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

    def test_d126_tabla_30832_y_censo_2011(self):
        # literales de T-357 (#831, SHA256SUMS.txt, medidos en otra sesion): el script los verifica al bajar
        casos = {"30832.csv": ("37716cba8cda50a492f52e2bae91a1c543bafb4263110e5aa5da18107ef68311", 445592835, "https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/30832.csv", "csv"),
                 "indicadores_seccion_censal_csv.zip": ("305a19f11b87d4e13d2ea4267774b9b0e3a69a3b7b1ff8e483aad90867628fe7", 4575186, "https://www.ine.es/censos2011_datos/indicadores_seccion_censal_csv.zip", "zip")}
        for k, (sha, n, url, ext) in casos.items():
            e = IDX[k]
            self.assertEqual((e["sha256"], e["bytes"], e["origen_url"]), (sha, n, url))
            self.assertEqual(e["clave"], f"arc-e/fuentes/ine/{k.rsplit('.', 1)[0]}_{sha[:12]}.{ext}")
        self.assertEqual(sum(1 for k in IDX if k.startswith("nazioenbehatokia/")), 625)

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
        self.assertIn("$resultado[$p.nombre] = [ordered]@{ origen_url = $f.origen_url; subido = $false; estado_r2 = 'fallido'; error = $detalle }", PS1)
        self.assertNotIn("$($_.Exception.Message)\"\n        $fallos", PS1)  # el catch ya no imprime solo el mensaje
        import re as _re

        def espejo(tipo, msg, linea):
            return f"{tipo}: {_re.sub(chr(92) + 's+', ' ', msg).strip()} | linea {linea}"
        d = espejo("System.Exception", "\r\n  HTTP 0 \n  cortado", "146: $http = Bajar")
        self.assertNotIn("\n", d)
        self.assertIn("System.Exception: HTTP 0 cortado", d)
        self.assertTrue(espejo("System.IO.IOException", "", "9").startswith("System.IO.IOException:"))  # mensaje vacio: queda el tipo

    def test_aws_solo_por_invocar_aws(self):
        # PS 5.1 + ErrorActionPreference=Stop: el stderr de aws (head-object 404) lanza NativeCommandError aunque se redirija 2>$null
        m = re.search(r"function Invocar-Aws\(.*?\n\}\n", PS1, re.S)
        self.assertIsNotNone(m)
        cuerpo = m.group(0)
        for frag in ("$ErrorActionPreference = 'Continue'", "finally { $ErrorActionPreference = $previo }", "2>&1", "$LASTEXITCODE", "ForEach-Object"):
            self.assertIn(frag, cuerpo)
        resto = PS1.replace(cuerpo, "")
        self.assertEqual([l for l in resto.splitlines() if re.search(r"&\s*aws\b", l) and not l.lstrip().startswith("#")], [])
        self.assertNotIn("2>$null", resto)
        sub = re.search(r"function Estado-R2\(.*?\n\}\n", PS1, re.S).group(0)
        self.assertRegex(sub, r"404.*not.*NoSuchKey")
        self.assertIn("throw \"head-object fallo", sub)
        self.assertRegex(PS1, r"la subida a R2 fallo \(codigo \$\(\$cp\.Codigo\)\): \$\(\$cp\.Salida\)")

    def test_reanudar_explicito_saltar_subir_fallar(self):
        for frag in ("[switch]$Reanudar", "Reanudando: $yaEnR2 piezas ya en R2", "ContentLength", "Metadata.sha256",
                     "$saltados++", "$subidos++", "saltados = $saltados; subidos = $subidos", "fallidas = @($fallidas)",
                     "tras subir, R2 no tiene la clave", "estado_r2"):
            self.assertIn(frag, PS1)
        cuenta = PS1.split('Write-Host "Reanudando:')[0].rsplit("if (-not $SoloBajar) {", 1)[1]
        self.assertIn("Estado-R2", cuenta)  # cuenta previa con head-object, solo si no es -SoloBajar

        # espejo del criterio de Estado-R2/decision (sin pwsh): igual -> saltar; falta/distinto -> subir; otro error -> fallar
        def decide(head, sha, n):
            if head is None:
                return "falta"
            return "igual" if (head.get("sha256") == sha and head.get("len") == n) else "distinto"
        def accion(estado):
            return "saltado" if estado == "igual" else "subir"
        self.assertEqual(accion(decide({"sha256": "a", "len": 5}, "a", 5)), "saltado")
        self.assertEqual(accion(decide({"sha256": "a", "len": 4}, "a", 5)), "subir")   # objeto parcial o distinto: se resube
        self.assertEqual(accion(decide({"sha256": "b", "len": 5}, "a", 5)), "subir")
        self.assertEqual(accion(decide(None, "a", 5)), "subir")

    def test_tabla_igual_distinto_falta_416_casos_de_borde(self):
        # espejo en Python del criterio del .ps1 (sin pwsh). Nota: -eq de PowerShell ignora mayusculas, por eso lower().
        def estado(head, sha, n):
            if head is None:
                return "falta"
            m = head.get("Metadata")
            sha_r2 = (m or {}).get("sha256", "")
            return "igual" if sha_r2.lower() == sha.lower() and head.get("ContentLength") == n else "distinto"

        def descarga(ya, http):
            if http == 416 and ya > 0:
                return "completo"
            return "append" if http == 206 and ya > 0 else "crear"
        sha = "a" * 64
        self.assertEqual(estado({"Metadata": {"sha256": sha}, "ContentLength": 10}, sha, 10), "igual")
        self.assertEqual(estado({"Metadata": {"sha256": sha.upper()}, "ContentLength": 10}, sha, 10), "igual")
        self.assertEqual(estado({"ContentLength": 10}, sha, 10), "distinto")                      # sin metadato
        self.assertEqual(estado({"Metadata": {}, "ContentLength": 10}, sha, 10), "distinto")
        self.assertEqual(estado({"Metadata": {"sha256": sha}, "ContentLength": 9}, sha, 10), "distinto")  # tamano distinto (parcial)
        self.assertEqual(estado({"Metadata": {"sha256": "b" * 64}, "ContentLength": 10}, sha, 10), "distinto")
        self.assertEqual(estado(None, sha, 10), "falta")
        self.assertEqual(descarga(100, 416), "completo")
        self.assertEqual(descarga(0, 416), "crear")
        self.assertEqual(descarga(100, 206), "append")
        self.assertEqual(descarga(100, 200), "crear")   # el servidor ignoro Range: se rehace
        # el texto del .ps1 implementa esos mismos casos
        for frag in ("[string]$j.Metadata.sha256", "if ($j.Metadata)", "[long]$j.ContentLength -eq [long]$bytes", "-eq 416 -and $ya -gt 0", "$http -eq 206 -and $ya -gt 0"):
            self.assertIn(frag, PS1)

    def test_filtro_del_script_ignora_interior_galicia_y_65034(self):
        # el filtro de origen_url del .ps1, aplicado al indice real: solo 642 + padron (2); lo demas (Interior, Galicia, 65034) fuera
        ine = re.search(r"\$esIne = \$u -match '([^']+)'", PS1).group(1)
        obs = re.search(r"\$esObs = \$u -match '([^']+)'", PS1).group(1)
        pad = set(re.findall(r"-eq '(https://www\.ine\.es/[^']+)'", PS1))
        sel = [k for k, v in IDX.items() if re.search(ine, v.get("origen_url", "")) or re.search(obs, v.get("origen_url", "")) or v.get("origen_url") in pad]
        self.assertEqual(len(sel), 644)
        for k in ("02202307_MESA.zip", "65034.csv.zip", "galicia_parlamento_2024_lugo_mesas.csv"):
            self.assertIn(k, IDX)
            self.assertNotIn(k, sel)
        self.assertEqual(len(IDX), len(set(IDX)))

    def test_ok_corrupto_y_cache_de_cuenta_previa(self):
        self.assertIn("try { $m = Get-Content -LiteralPath $ok -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $m = $null }", PS1)
        self.assertIn("        $m = $null\n        if ((Test-Path -LiteralPath $ruta) -and (Test-Path -LiteralPath $ok)) {", PS1)  # sin $m heredado de otra pieza
        self.assertIn("$cacheR2[$q.ficha.clave] = $e0", PS1)
        self.assertIn("$cacheR2.ContainsKey($clave)", PS1)

    def test_subido_clasifica_errores_funcion_espejo(self):
        # espejo del criterio de Subido (sin pwsh): 404/NotFound = no existe; 403/credenciales/red = error
        patron = re.compile(r"(?i)\b404\b|not\s*found|NoSuchKey")
        for salida in ("An error occurred (404) when calling the HeadObject operation: Not Found",
                       "An error occurred (NoSuchKey) when calling the HeadObject operation"):
            self.assertTrue(patron.search(salida))
        for salida in ("An error occurred (403) when calling the HeadObject operation: Forbidden",
                       "Unable to locate credentials", "Could not connect to the endpoint URL"):
            self.assertFalse(patron.search(salida))

    def test_grupo_padron_644_y_descarga_reanudable(self):
        self.assertIn("'padron'", PS1)
        self.assertIn("todo = 644; ine = 17; observatorio = 625; padron = 2", PS1)
        self.assertNotIn("642", PS1)
        self.assertIn("function Bajar-Reanudable", PS1)
        cuerpo = re.search(r"function Bajar-Reanudable.*?\n\}\n", PS1, re.S).group(0)
        for frag in ("AddRange", "FileMode]::Append", "416", "IO.FileStream", "1048576"):
            self.assertIn(frag, cuerpo)
        for malo in ("ReadAllBytes", "Get-Content", "ReadAllText", "DownloadString"):
            self.assertNotIn(malo, cuerpo)
        self.assertIn("Bajar-Reanudable $f.origen_url $parte", PS1)
        self.assertIn("https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/30832.csv", PS1)
        # el CSV grande no se carga en memoria en el resto del flujo: Validar solo lee 512 bytes
        self.assertIn("[Math]::Min(512, $n)", PS1)

    def test_cabecera_y_sin_ids_viejos(self):
        self.assertIn("VERSION 1.0.0", PS1.splitlines()[1])
        self.assertIn("ANTERIOR: ninguna (fichero nuevo)", PS1)
        self.assertNotRegex(PS1, r"territorios/(?!aut|nac)[a-z_]+/")


if __name__ == "__main__":
    unittest.main()
