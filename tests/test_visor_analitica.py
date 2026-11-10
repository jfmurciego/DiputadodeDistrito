# -*- coding: utf-8 -*-
"""T-174: la analítica opcional (Cloudflare Web Analytics) no se inyecta sin token y, con token, solo carga el beacon de Cloudflare.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-10 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
Ejecuta el bloque real de cada página en Node con un DOM mínimo; valores esperados literales.
"""
import json, re, shutil, subprocess, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINAS = ["visor/index.html", "visor/nacional/index.html", "visor/v2/index.html"]
BLOQUE = re.compile(r"<!-- ANALITICA:INICIO.*?-->\s*<script>(.*?)</script>\s*<!-- ANALITICA:FIN -->", re.S)
HARNESS = """
const els=[];const mk=t=>({t,attrs:{},style:{},children:[],setAttribute(k,v){this.attrs[k]=v},appendChild(c){this.children.push(c);return c}});
const doc={createElement:mk,createTextNode:s=>({text:s}),body:mk('body'),head:mk('head')};
global.document=doc;
global.window={};
// cualquier acceso a almacenamiento o cookies es un fallo
Object.defineProperty(doc,'cookie',{set(){throw new Error('cookie')},get(){throw new Error('cookie')}});
global.localStorage=new Proxy({},{get(){throw new Error('storage')}});
global.sessionStorage=global.localStorage;
%s
console.log(JSON.stringify({body:doc.body.children.length,head:doc.head.children.map(s=>({src:s.src,cfg:s.attrs['data-cf-beacon']}))}));
"""


def ejecutar(codigo):
    r = subprocess.run(["node", "-e", HARNESS % codigo], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@unittest.skipUnless(shutil.which("node"), "node no disponible")
class Analitica(unittest.TestCase):
    def codigo(self, pagina):
        m = BLOQUE.search((RAIZ / pagina).read_text(encoding="utf-8"))
        self.assertIsNotNone(m, pagina)
        return m.group(1)

    def test_bloques_identicos_y_token_vacio_en_el_repo(self):
        codigos = {self.codigo(p) for p in PAGINAS}
        self.assertEqual(len(codigos), 1)
        self.assertIn('TOKEN=""', codigos.pop())

    def test_sin_token_no_inyecta_nada(self):
        for p in PAGINAS:
            self.assertEqual(ejecutar(self.codigo(p)), {"body": 0, "head": []}, p)

    def test_con_token_solo_el_beacon_de_cloudflare(self):
        for p in PAGINAS:
            c = self.codigo(p).replace('TOKEN=""', 'TOKEN="abc123"')
            r = ejecutar(c)
            self.assertEqual(r["body"], 1, p)  # solo el aviso
            self.assertEqual(r["head"], [{"src": "https://static.cloudflareinsights.com/beacon.min.js",
                                          "cfg": '{"token":"abc123"}'}], p)

    def test_el_resto_de_hosts_no_cambia(self):
        for p in PAGINAS:
            hosts = set(re.findall(r"https?://([^/\"' ]+)", self.codigo(p)))
            self.assertEqual(hosts, {"static.cloudflareinsights.com", "developers.cloudflare.com"}, p)


if __name__ == "__main__":
    unittest.main()
