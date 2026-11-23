#!/usr/bin/env python3
"""Paquete para el Registro de la Propiedad Intelectual de Deslinde: ZIP, copia identificativa en PDF y manifiesto.

PROYECTO: Diputado de Distrito
VERSIÓN: 2.0.0
NOMBRE DE VERSIÓN: Paquete PI de Deslinde · paquete independiente, PDF y manifiesto
FECHA: 2026-11-23
ESTADO: candidato
CAMBIOS: 2.0.0 (T-281, D-196) — la instantánea es el paquete independiente `paquetes/deslinde/**`, la definición
  formal `docs/ARQUITECTURA/DESLINDE_1_0.md` y SOLO los estudios que esa definición cita (antes: `ddd_motor2/`, los
  módulos 05/06 y todo `docs/ESTUDIOS/`). Nuevos: COPIA_IDENTIFICATIVA.pdf (portada, descripción en lenguaje llano,
  índice con sha256 y código fuente impreso; `--extremos N` deja solo las N primeras y N últimas páginas de código),
  NOTA_AUTORIA.pdf (desde `docs/registro_pi/NOTA_AUTORIA.md`) y MANIFIESTO.txt (sha256 del ZIP y de los PDF). El autor es
  `--autor` (por defecto el marcador «[AUTOR]»: ningún dato personal se versiona). PDF sin dependencias (escritor
  propio, Courier, WinAnsi) y determinista. 1.0.1 — (T-257) entra paquetes/deslinde/**. 1.0.0 — fichero nuevo (T-281).
MOTIVO: D-196: el repositorio sigue público y Deslinde se protege con licencia propietaria y registro de la propiedad
  intelectual; el registro pide una copia identificativa del programa y la declaración de la autoría humana.
ANTERIOR: legacy/herramientas/preparar_paquete_pi_v1.0.1_20261123.py
QUÉ HACE: lee SOLO del objeto git del commit (no del árbol de trabajo):
  - paquetes/deslinde/** (el programa) y el cierre de imports `ddd_core` si lo hubiera (AST, transitivo);
  - docs/ARQUITECTURA/DESLINDE_1_0.md y los estudios que cita: rutas `docs/ESTUDIOS/...` y referencias `T-nnn`/`Tnnn`
    que coinciden con una entrada `docs/ESTUDIOS/Tnnn_*` (carpeta o fichero);
  - docs/registro_pi/DESCRIPCION.md y NOTA_AUTORIA.md (textos del PDF; no entran en el ZIP).
  Excluye por ruta CLAUDE.md, .claude/, secretos y cachés; FALLA (código 2) ante tokens, claves privadas o correos.
  Escribe en la salida (por defecto propiedad_intelectual/, ignorada por git salvo su README): paquete_deslinde.zip
  (orden por ruta, fecha 1980-01-01, 0644, sin compresión), COPIA_IDENTIFICATIVA.pdf, NOTA_AUTORIA.pdf, MANIFEST.json
  (ruta, tamaño y sha256 por fichero), MANIFIESTO.txt y SHA256SUMS. Determinista: misma salida para el mismo commit,
  autor y `--extremos` (la fecha es la del commit salvo `--fecha`).
Uso: python herramientas/preparar_paquete_pi.py [--commit HEAD] [--salida DIR] [--autor "[AUTOR]"] [--fecha AAAA-MM-DD]
     [--extremos N] [--sin-zip] [--excluir RUTA ...] [--raiz RUTA]
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import subprocess
import textwrap
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "2.0.0"
ROOT = Path(__file__).resolve().parents[1]
NOMBRE_ZIP = "paquete_deslinde.zip"
NOMBRE_PDF = "COPIA_IDENTIFICATIVA.pdf"
NOMBRE_NOTA = "NOTA_AUTORIA.pdf"
DOC_DESLINDE = "docs/ARQUITECTURA/DESLINDE_1_0.md"
DOC_DESCRIPCION = "docs/registro_pi/DESCRIPCION.md"
DOC_NOTA = "docs/registro_pi/NOTA_AUTORIA.md"
PREFIJO_PAQUETE = "paquetes/deslinde/"
PREFIJO_ESTUDIOS = "docs/ESTUDIOS/"
INIT_PAQUETE = "paquetes/deslinde/src/deslinde/__init__.py"
PAQUETES_SEGUIDOS = ("ddd_core",)
FECHA_ZIP = (1980, 1, 1, 0, 0, 0)
AUTOR_MARCADOR = "[AUTOR]"
RE_REF_ESTUDIO = re.compile(r"(?<![A-Za-z0-9])T-?(\d{2,4})(?!\d)")

# Rutas que nunca entran (se registran como excluidas por política).
RUTAS_PROHIBIDAS = [
    re.compile(r"(^|/)CLAUDE\.md$"),
    re.compile(r"(^|/)\.claude/"),
    re.compile(r"(^|/)\.env(\.|$)"),
    re.compile(r"\.(pem|key|p12|pfx|keystore)$", re.I),
    re.compile(r"(^|/)id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$"),
    re.compile(r"(^|/)(credentials|secrets?)(\.[a-z]+)?$", re.I),
    re.compile(r"(^|/)__pycache__/|\.pyc$"),
]
# Contenido que hace fallar: (nombre, patrón). El nombre va al informe; el texto encontrado, nunca.
PATRONES_SECRETO = [
    ("token_github", re.compile(rb"\b(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})")),
    ("clave_aws", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("clave_privada", re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("token_slack", re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("clave_api", re.compile(rb"\bsk-(ant-)?[A-Za-z0-9_-]{20,}")),
    ("correo", re.compile(rb"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")),
]
# En binarios (PNG, gz) el patrón de correo da falsos positivos con bytes al azar: solo se busca en texto.
SOLO_TEXTO = {"correo"}
# Rutas de máquina: se avisan en el manifiesto, no paran (el paquete PI es privado; sanear solo importa al público).
PATRONES_AVISO = [
    ("ruta_home", re.compile(rb"/home/[A-Za-z0-9_.-]+")),
    ("ruta_users", re.compile(rb"/Users/[A-Za-z0-9_.-]+")),
]


class PaqueteError(Exception):
    """Fallo que para el paquete (código 2)."""


def _git(raiz: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(raiz), *args], check=True, capture_output=True).stdout


class Arbol:
    """Vista de solo lectura de un commit: rutas y contenido de los blobs."""

    def __init__(self, raiz: Path, commit: str):
        self.raiz = raiz
        self.sha = _git(raiz, "rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip()
        salida = _git(raiz, "ls-tree", "-r", "-z", self.sha)
        self.blobs: dict[str, str] = {}
        for linea in salida.split(b"\0"):
            if not linea:
                continue
            meta, ruta = linea.split(b"\t", 1)
            _modo, tipo, obj = meta.decode().split()
            if tipo == "blob":
                self.blobs[ruta.decode("utf-8")] = obj
        self._cache: dict[str, bytes] = {}

    def leer(self, ruta: str) -> bytes:
        if ruta not in self._cache:
            self._cache[ruta] = _git(self.raiz, "cat-file", "blob", self.blobs[ruta])
        return self._cache[ruta]

    def fecha_utc(self) -> str:
        ts = int(_git(self.raiz, "show", "-s", "--format=%ct", self.sha).decode().strip())
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _modulo_a_ruta(arbol: Arbol, modulo: str) -> str | None:
    base = modulo.replace(".", "/")
    for cand in (f"{base}.py", f"{base}/__init__.py"):
        if cand in arbol.blobs:
            return cand
    return None


def _imports(arbol: Arbol, ruta: str) -> tuple[set[str], set[str]]:
    """(rutas de ddd_core/ddd_motor2 importadas, otros paquetes del repo importados)."""
    try:
        tree = ast.parse(arbol.leer(ruta), filename=ruta)
    except SyntaxError:
        return set(), set()
    paquete = ruta.rsplit("/", 1)[0].replace("/", ".") if "/" in ruta else ""
    modulos: set[str] = set()
    for nodo in ast.walk(tree):
        if isinstance(nodo, ast.Import):
            modulos.update(a.name for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level:
                partes = paquete.split(".")
                base = ".".join(partes[: len(partes) - nodo.level + 1])
                mod = f"{base}.{nodo.module}" if nodo.module else base
            else:
                mod = nodo.module or ""
            modulos.add(mod)
            modulos.update(f"{mod}.{a.name}" for a in nodo.names)
    dentro, fuera = set(), set()
    for mod in modulos:
        top = mod.split(".")[0]
        if top in PAQUETES_SEGUIDOS:
            r = _modulo_a_ruta(arbol, mod)
            if r:
                dentro.add(r)
            ini = _modulo_a_ruta(arbol, top)
            if ini:
                dentro.add(ini)
        elif _modulo_a_ruta(arbol, top):
            fuera.add(top)
    return dentro, fuera



def estudios_citados(arbol: Arbol) -> dict[str, list[str]]:
    """{entrada de docs/ESTUDIOS/ (carpeta o fichero): referencias que la citan} según DESLINDE_1_0.md."""
    texto = arbol.leer(DOC_DESLINDE).decode("utf-8", "replace")
    numeros = sorted({int(n) for n in RE_REF_ESTUDIO.findall(texto)})
    entradas = {r[len(PREFIJO_ESTUDIOS):].split("/", 1)[0] for r in arbol.blobs if r.startswith(PREFIJO_ESTUDIOS)}
    citados: dict[str, list[str]] = {}
    for e in sorted(entradas):
        m = re.match(r"T(\d+)(?:[_.]|$)", e)
        if m and int(m.group(1)) in numeros:
            citados[e] = [f"T{int(m.group(1))}"]
    return citados


def seleccionar(arbol: Arbol, excluir: list[str]) -> dict:
    for doc in (DOC_DESLINDE, DOC_DESCRIPCION, DOC_NOTA, INIT_PAQUETE):
        if doc not in arbol.blobs:
            raise PaqueteError(f"falta {doc} en el commit")
    estudios = estudios_citados(arbol)
    prefijos = tuple([PREFIJO_PAQUETE] + [f"{PREFIJO_ESTUDIOS}{e}" for e in estudios])
    base = {r for r in arbol.blobs if r.startswith(prefijos)} | {DOC_DESLINDE}
    base = {r for r in base if r.startswith(PREFIJO_PAQUETE) or r == DOC_DESLINDE
            or r[len(PREFIJO_ESTUDIOS):].split("/", 1)[0] in estudios}
    pendientes = sorted(r for r in base if r.endswith(".py") and r.startswith(PREFIJO_PAQUETE))
    vistos, externos = set(pendientes), set()
    while pendientes:
        dentro, fuera = _imports(arbol, pendientes.pop())
        externos |= fuera
        for r in dentro - vistos:
            vistos.add(r)
            pendientes.append(r)
    candidatos = base | vistos
    politica = sorted(r for r in candidatos if any(p.search(r) for p in RUTAS_PROHIBIDAS))
    manuales = sorted(r for r in candidatos if r in set(excluir))
    desconocidas = sorted(set(excluir) - candidatos)
    if desconocidas:
        raise PaqueteError(f"--excluir no está en la lista blanca: {', '.join(desconocidas)}")
    incluidos = sorted(candidatos - set(politica) - set(manuales))
    return {"incluidos": incluidos, "excluidos_por_politica": politica, "excluidos_explicitos": manuales,
            "estudios": estudios,
            "paquetes_del_repo_importados_no_incluidos": sorted(externos - set(PAQUETES_SEGUIDOS) - {"deslinde"})}


def detectar_avisos(arbol: Arbol, rutas: list[str]) -> list[dict]:
    return [{"ruta": r, "tipo": nombre} for r in rutas for nombre, patron in PATRONES_AVISO
            if patron.search(arbol.leer(r))]


def detectar_secretos(arbol: Arbol, rutas: list[str]) -> list[tuple[str, str]]:
    hallazgos = []
    for r in rutas:
        datos = arbol.leer(r)
        binario = b"\0" in datos[:8192]
        for nombre, patron in PATRONES_SECRETO:
            if binario and nombre in SOLO_TEXTO:
                continue
            if patron.search(datos):
                hallazgos.append((r, nombre))
    return hallazgos


def version_deslinde(arbol: Arbol) -> str:
    m = re.search(r"(?m)^__version__\s*=\s*[\"']([^\"']+)", arbol.leer(INIT_PAQUETE).decode("utf-8", "replace"))
    if not m:
        raise PaqueteError(f"{INIT_PAQUETE} no declara __version__")
    return m.group(1)


def version_definicion(arbol: Arbol) -> str:
    m = re.search(r"(?m)^VERSIÓN:\s*(\S+)", arbol.leer(DOC_DESLINDE).decode("utf-8", "replace"))
    if not m:
        raise PaqueteError(f"{DOC_DESLINDE} no declara VERSIÓN")
    return m.group(1)


def zip_determinista(arbol: Arbol, rutas: list[str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as z:
        for r in rutas:
            info = zipfile.ZipInfo(r, date_time=FECHA_ZIP)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            z.writestr(info, arbol.leer(r))
    return buf.getvalue()


# ---------------------------------------------------------------- PDF mínimo (sin dependencias, determinista)
PAG_ANCHO, PAG_ALTO, MARGEN = 595, 842, 42  # A4 en puntos
CUERPO, INTERLINEA = 8, 10
COLUMNAS = int((PAG_ANCHO - 2 * MARGEN) / (CUERPO * 0.6))  # Courier: 0,6 em por carácter
FILAS = int((PAG_ALTO - 2 * MARGEN - 2 * INTERLINEA) / INTERLINEA)
SUSTITUCIONES = {"≤": "<=", "≥": ">=", "→": "->", "←": "<-", "≠": "!=", "≈": "~", "×": "x", "−": "-", "✓": "v",
                 "\t": "    "}


def _pdf_texto(s: str) -> bytes:
    for a, b in SUSTITUCIONES.items():
        s = s.replace(a, b)
    datos = s.encode("cp1252", "replace")
    return datos.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _partir(linea: str, ancho: int, sangria: str = "") -> list[str]:
    if len(linea) <= ancho:
        return [linea]
    trozos = [linea[:ancho]]
    resto = linea[ancho:]
    paso = ancho - len(sangria)
    while resto:
        trozos.append(sangria + resto[:paso])
        resto = resto[paso:]
    return trozos


class Pagina:
    """Una página: lista de (tamaño, texto) en filas; tamaño > CUERPO ocupa más de una fila."""

    def __init__(self, seccion: str):
        self.seccion = seccion
        self.lineas: list[tuple[int, str]] = []

    def filas(self) -> int:
        return sum(max(1, round(t * 1.25 / INTERLINEA)) for t, _ in self.lineas)


class Documento:
    def __init__(self):
        self.paginas: list[Pagina] = []

    def nueva(self, seccion: str) -> Pagina:
        self.paginas.append(Pagina(seccion))
        return self.paginas[-1]

    def escribir(self, seccion: str, lineas: list[str], sangria: str = "", tam: int = CUERPO,
                 pagina_nueva: bool = True) -> None:
        pag = self.nueva(seccion) if pagina_nueva or not self.paginas else self.paginas[-1]
        ancho = int((PAG_ANCHO - 2 * MARGEN) / (tam * 0.6))
        alto = max(1, round(tam * 1.25 / INTERLINEA))
        for linea in lineas:
            for trozo in _partir(linea, ancho, sangria):
                if pag.filas() + alto > FILAS:
                    pag = self.nueva(seccion)
                pag.lineas.append((tam, trozo))

    def pdf(self, pie: str, titulo: str) -> bytes:
        objetos: list[bytes] = []
        n = len(self.paginas)
        # 1 catálogo, 2 páginas, 3 fuente, 4 info; luego (contenido, página) por cada página.
        kids = " ".join(f"{6 + 2 * i} 0 R" for i in range(n))
        objetos.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        objetos.append(f"<< /Type /Pages /Count {n} /Kids [{kids}] >>".encode())
        objetos.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>")
        objetos.append(b"<< /Title (" + _pdf_texto(titulo) + b") /Producer (preparar_paquete_pi.py "
                       + VERSION.encode() + b") >>")
        for i, pag in enumerate(self.paginas, start=1):
            flujo = [b"BT"]
            y = PAG_ALTO - MARGEN
            for tam, texto in pag.lineas:
                y -= max(1, round(tam * 1.25 / INTERLINEA)) * INTERLINEA
                flujo.append(f"/F1 {tam} Tf 1 0 0 1 {MARGEN} {y} Tm".encode() + b" (" + _pdf_texto(texto) + b") Tj")
            texto_pie = f"{pie} · {pag.seccion} · página {i} de {n}"
            flujo.append(f"/F1 7 Tf 1 0 0 1 {MARGEN} {MARGEN - 18} Tm".encode() + b" (" + _pdf_texto(texto_pie)
                         + b") Tj")
            flujo.append(b"ET")
            cuerpo = b"\n".join(flujo)
            objetos.append(b"<< /Length " + str(len(cuerpo)).encode() + b" >>\nstream\n" + cuerpo + b"\nendstream")
            objetos.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAG_ANCHO} {PAG_ALTO}] "
                           f"/Resources << /Font << /F1 3 0 R >> >> /Contents {5 + 2 * (i - 1)} 0 R >>".encode())
        salida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        desplazamientos = []
        for k, obj in enumerate(objetos, start=1):
            desplazamientos.append(len(salida))
            salida += f"{k} 0 obj\n".encode() + obj + b"\nendobj\n"
        xref = len(salida)
        salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
        for d in desplazamientos:
            salida += f"{d:010d} 00000 n \n".encode()
        salida += (f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R /Info 4 0 R >>\nstartxref\n{xref}\n%%EOF\n"
                   .encode())
        return bytes(salida)


def _texto_md(arbol: Arbol, ruta: str, autor: str, fecha: str) -> list[str]:
    """Markdown del commit sin la cabecera de gobernanza (comentario HTML inicial), con marcadores resueltos."""
    texto = arbol.leer(ruta).decode("utf-8")
    texto = re.sub(r"^\s*<!--.*?-->\s*", "", texto, count=1, flags=re.S)
    texto = texto.replace(AUTOR_MARCADOR, autor).replace("[FECHA]", fecha).replace("**", "").replace("`", "")
    # Reflujo: une las líneas de cada párrafo o punto de lista y lo parte por palabras al ancho de la página.
    bloques: list[tuple[str, str]] = []  # (prefijo de continuación, texto)
    for linea in texto.splitlines():
        lista = re.match(r"^(\s*(?:[-*]|\d+\.)\s+)", linea)
        if not linea.strip():
            bloques.append(("", ""))
        elif linea.startswith("#"):
            titulo = linea.lstrip("#").strip()
            bloques += [("", titulo.upper() if linea.startswith("# ") else titulo), ("", "")]
        elif lista:
            bloques.append((" " * len(lista.group(1)), linea))
        elif bloques and bloques[-1][1] and not bloques[-1][1].isupper():
            pref, previo = bloques[-1]
            bloques[-1] = (pref, f"{previo} {linea.strip()}")
        else:
            bloques.append(("", linea))
    salida: list[str] = []
    for pref, b in bloques:
        if salida and not b and not salida[-1]:
            continue
        salida += textwrap.wrap(b, COLUMNAS, subsequent_indent=pref, break_on_hyphens=False) or [""]
    return salida


def ficheros_codigo(rutas: list[str]) -> list[str]:
    return [r for r in rutas if r.startswith(PREFIJO_PAQUETE) and r.endswith((".py", ".toml"))]


def copia_identificativa(arbol: Arbol, ficheros: list[dict], autor: str, fecha: str, extremos: int,
                         version: str) -> tuple[bytes, dict]:
    sha7 = arbol.sha[:7]
    doc = Documento()
    portada = ["", "", "", ""]
    doc.escribir("portada", portada)
    doc.escribir("portada", ["Deslinde 1.0"], tam=24, pagina_nueva=False)
    doc.escribir("portada", ["", "Delimitación reproducible de distritos uninominales", "",
                             "Copia identificativa del programa de ordenador", "", ""], tam=12, pagina_nueva=False)
    doc.escribir("portada", [f"Autor: {autor}", f"Fecha: {fecha}", "",
                             f"Versión del código: {version} (paquete «deslinde»)",
                             f"Commit de la instantánea: {arbol.sha}", f"Fecha del commit (UTC): {arbol.fecha_utc()}",
                             f"Ficheros en el paquete ZIP: {len(ficheros)}"], tam=10, pagina_nueva=False)
    doc.escribir("descripción", _texto_md(arbol, DOC_DESCRIPCION, autor, fecha))
    indice = ["Índice de ficheros del paquete ZIP (ruta; sha256 y bytes)", ""]
    for f in ficheros:
        indice += [f["ruta"], f"    {f['sha256']}  {f['bytes']} bytes"]
    doc.escribir("índice", indice, sangria="    ")
    inicio_codigo = len(doc.paginas)
    for r in ficheros_codigo([f["ruta"] for f in ficheros]):
        lineas = arbol.leer(r).decode("utf-8", "replace").splitlines()
        cab = [f"==== {r}  ({len(lineas)} líneas, sha256 {hashlib.sha256(arbol.leer(r)).hexdigest()})", ""]
        doc.escribir("código fuente", cab + [f"{k:5d}  {t}" for k, t in enumerate(lineas, start=1)],
                     sangria="       ")
    codigo = doc.paginas[inicio_codigo:]
    resumen = {"paginas_codigo_total": len(codigo), "extremos": extremos, "paginas_codigo_omitidas": 0}
    if extremos and len(codigo) > 2 * extremos:
        omitidas = len(codigo) - 2 * extremos
        aviso = Pagina("código fuente")
        aviso.lineas = [(CUERPO, ""), (12, f"[Se omiten {omitidas} páginas de código fuente: de la {extremos + 1} a la "
                                           f"{len(codigo) - extremos} de {len(codigo)}.]"),
                        (CUERPO, ""), (CUERPO, "El código completo está en el paquete ZIP (sha256 en el índice).")]
        doc.paginas = doc.paginas[:inicio_codigo] + codigo[:extremos] + [aviso] + codigo[-extremos:]
        resumen["paginas_codigo_omitidas"] = omitidas
    resumen["paginas_total"] = len(doc.paginas)
    return doc.pdf(f"Deslinde 1.0 · copia identificativa · {sha7}", "Deslinde 1.0 · copia identificativa"), resumen


def nota_autoria(arbol: Arbol, autor: str, fecha: str) -> bytes:
    doc = Documento()
    doc.escribir("nota de autoría", _texto_md(arbol, DOC_NOTA, autor, fecha))
    return doc.pdf(f"Deslinde 1.0 · nota de autoría · {arbol.sha[:7]}", "Deslinde 1.0 · nota de autoría")


README = """# Paquete para el Registro de la Propiedad Intelectual de Deslinde

Generado por `herramientas/preparar_paquete_pi.py` {gen} desde el commit `{sha}` ({fecha} UTC).
Deslinde {version} (definición formal {vdef}). {n} ficheros ({bytes} bytes) en `{zip}`.

- `{zip}`: `paquetes/deslinde/`, `{doc}` y los estudios que cita ({estudios}).
- `{pdf}`: portada, descripción, índice con sha256 y código fuente ({paginas} páginas; {omitidas}).
- `{nota}`: lo que definió y decidió el autor (declaración de autoría humana).
- `MANIFIESTO.txt` y `SHA256SUMS`: huellas; `MANIFEST.json`: tamaño y sha256 de cada fichero del ZIP.

Verificar: `sha256sum -c SHA256SUMS`. Reproducir (mismos bytes):
`python herramientas/preparar_paquete_pi.py --commit {sha} --autor "<autor>" --fecha {fecha_portada}{ext}{excl}`
"""


def generar(raiz: Path, commit: str, salida: Path, excluir: list[str], con_zip: bool = True,
            autor: str = AUTOR_MARCADOR, fecha: str | None = None, extremos: int = 0) -> dict:
    arbol = Arbol(raiz, commit)
    sel = seleccionar(arbol, excluir)
    hallazgos = detectar_secretos(arbol, sel["incluidos"] + [DOC_DESCRIPCION, DOC_NOTA])
    if hallazgos:
        lineas = "\n".join(f"  {r}: {n}" for r, n in hallazgos)
        raise PaqueteError(f"patrones de secreto o correo en {len(hallazgos)} caso(s):\n{lineas}")
    fecha = fecha or arbol.fecha_utc()[:10]
    ficheros = [{"ruta": r, "bytes": len(arbol.leer(r)), "sha256": hashlib.sha256(arbol.leer(r)).hexdigest()}
                for r in sel["incluidos"]]
    version = version_deslinde(arbol)
    datos_zip = zip_determinista(arbol, sel["incluidos"])
    datos_pdf, resumen_pdf = copia_identificativa(arbol, ficheros, autor, fecha, extremos, version)
    datos_nota = nota_autoria(arbol, autor, fecha)
    sha = {n: hashlib.sha256(d).hexdigest() for n, d in
           ((NOMBRE_ZIP, datos_zip), (NOMBRE_PDF, datos_pdf), (NOMBRE_NOTA, datos_nota))}
    manifiesto = {
        "esquema": "ddd.paquete_pi.v2",
        "generador": {"herramienta": "herramientas/preparar_paquete_pi.py", "version": VERSION},
        "commit": arbol.sha,
        "fecha_utc": arbol.fecha_utc(),
        "fecha_portada": fecha,
        "autor_es_marcador": autor == AUTOR_MARCADOR,
        "deslinde_version": version,
        "definicion_version": version_definicion(arbol),
        "estudios_citados": sel["estudios"],
        "zip": {"nombre": NOMBRE_ZIP, "bytes": len(datos_zip), "sha256": sha[NOMBRE_ZIP],
                "formato": "ZIP_STORED, orden por ruta, fecha 1980-01-01T00:00:00, 0644"},
        "pdf": {"nombre": NOMBRE_PDF, "bytes": len(datos_pdf), "sha256": sha[NOMBRE_PDF], **resumen_pdf},
        "nota": {"nombre": NOMBRE_NOTA, "bytes": len(datos_nota), "sha256": sha[NOMBRE_NOTA]},
        "total_ficheros": len(ficheros),
        "total_bytes": sum(f["bytes"] for f in ficheros),
        "excluidos_por_politica": sel["excluidos_por_politica"],
        "excluidos_explicitos": sel["excluidos_explicitos"],
        "avisos": detectar_avisos(arbol, sel["incluidos"]),
        "paquetes_del_repo_importados_no_incluidos": sel["paquetes_del_repo_importados_no_incluidos"],
        "ficheros": ficheros,
    }
    salida.mkdir(parents=True, exist_ok=True)
    texto_manifiesto = json.dumps(manifiesto, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (salida / "MANIFEST.json").write_text(texto_manifiesto, encoding="utf-8")
    sha["MANIFEST.json"] = hashlib.sha256(texto_manifiesto.encode("utf-8")).hexdigest()
    orden = (NOMBRE_ZIP, NOMBRE_PDF, NOMBRE_NOTA, "MANIFEST.json")
    (salida / "SHA256SUMS").write_text("".join(f"{sha[n]}  {n}\n" for n in orden), encoding="utf-8")
    (salida / "MANIFIESTO.txt").write_text(
        "MANIFIESTO · Deslinde 1.0 · Registro de la Propiedad Intelectual\n\n"
        f"Autor: {autor}\nFecha: {fecha}\nVersión del código: {version}\nCommit: {arbol.sha}\n"
        f"Fecha del commit (UTC): {arbol.fecha_utc()}\n"
        f"Generador: herramientas/preparar_paquete_pi.py {VERSION}\n\n"
        "sha256 de cada entregable (formato sha256sum):\n"
        + "".join(f"{sha[n]}  {n}\n" for n in orden), encoding="utf-8")
    if con_zip:
        (salida / NOMBRE_ZIP).write_bytes(datos_zip)
    (salida / NOMBRE_PDF).write_bytes(datos_pdf)
    (salida / NOMBRE_NOTA).write_bytes(datos_nota)
    excl = "".join(f" --excluir {r}" for r in sel["excluidos_explicitos"])
    omit = (f"se omiten {resumen_pdf['paginas_codigo_omitidas']} de {resumen_pdf['paginas_codigo_total']} de código"
            if resumen_pdf["paginas_codigo_omitidas"] else f"código completo, {resumen_pdf['paginas_codigo_total']}")
    (salida / "README.md").write_text(README.format(
        gen=VERSION, sha=arbol.sha, fecha=manifiesto["fecha_utc"], version=version, vdef=manifiesto["definicion_version"],
        n=len(ficheros), bytes=manifiesto["total_bytes"], zip=NOMBRE_ZIP, doc=DOC_DESLINDE, pdf=NOMBRE_PDF,
        nota=NOMBRE_NOTA, estudios=", ".join(sel["estudios"]) or "ninguno", paginas=resumen_pdf["paginas_total"],
        omitidas=omit, fecha_portada=fecha, ext=f" --extremos {extremos}" if extremos else "", excl=excl),
        encoding="utf-8")
    return manifiesto


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--commit", default="HEAD")
    ap.add_argument("--salida", default="propiedad_intelectual")
    ap.add_argument("--raiz", default=str(ROOT))
    ap.add_argument("--autor", default=AUTOR_MARCADOR, help="nombre del autor en la portada (no se versiona)")
    ap.add_argument("--fecha", default=None, help="fecha de la portada AAAA-MM-DD (por defecto, la del commit)")
    ap.add_argument("--extremos", type=int, default=0,
                    help="si > 0, imprime solo las N primeras y N últimas páginas de código fuente")
    ap.add_argument("--excluir", action="append", default=[], help="ruta de la lista blanca que se deja fuera")
    ap.add_argument("--sin-zip", action="store_true", help="no escribe el ZIP (su sha256 sí va al manifiesto)")
    a = ap.parse_args(argv)
    raiz = Path(a.raiz).resolve()
    salida = Path(a.salida)
    salida = salida if salida.is_absolute() else raiz / salida
    if a.fecha and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.fecha):
        print("::error::paquete PI: --fecha debe ser AAAA-MM-DD", file=sys.stderr)
        return 2
    try:
        m = generar(raiz, a.commit, salida, a.excluir, con_zip=not a.sin_zip, autor=a.autor, fecha=a.fecha,
                    extremos=a.extremos)
    except PaqueteError as exc:
        print(f"::error::paquete PI: {exc}", file=sys.stderr)
        return 2
    print(f"paquete PI: {m['total_ficheros']} ficheros, {m['total_bytes']} bytes, commit {m['commit'][:12]}, "
          f"Deslinde {m['deslinde_version']}, estudios {len(m['estudios_citados'])}, zip {m['zip']['sha256'][:12]}, "
          f"pdf {m['pdf']['sha256'][:12]} ({m['pdf']['paginas_total']} págs.), avisos {len(m['avisos'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
