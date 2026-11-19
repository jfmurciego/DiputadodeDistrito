#!/usr/bin/env python3
"""Reúne las tres páginas de DDD y sus recursos en un HTML autónomo.

Uso:
    python3 generar_portada_autonoma.py --source web --output DDD_portada.html

Requiere Python 3.10 o posterior y solo usa su biblioteca estándar.
No descarga recursos ni modifica los originales.
Las imágenes y los recursos locales de CSS se incorporan como URI de datos.
La navegación de las tres páginas utiliza plantillas inertes y el historial del
navegador. El inicializador compartido debe exponerse como window.DDDInit.
"""

from __future__ import annotations

import argparse
import base64
from html import escape, unescape
from html.parser import HTMLParser
import json
import mimetypes
from pathlib import Path
import re
import sys
from urllib.parse import quote, unquote, urlsplit


PAGES = {
    "index.html": "inicio",
    "comprender.html": "comprender",
    "auditoria-registro.html": "registro",
}
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg", ".ico"}
CSS_URL = re.compile(r"url\(\s*(?P<q>['\"]?)(?P<url>.*?)(?P=q)\s*\)", re.I)


class BuildError(Exception):
    pass


def script_safe(text: str) -> str:
    """Evita que el analizador HTML cierre un script por un literal de JS."""
    return re.sub(r"</script", lambda m: "<\\/" + m.group(0)[2:], text,
                  flags=re.I)


def json_for_script(value: object) -> str:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c").replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029"))


class Bundler:
    def __init__(self, source: Path):
        self.source = source.resolve()
        self.resources: dict[Path, str] = {}

    def local_path(self, url: str, relative_to: Path) -> tuple[Path, str]:
        parts = urlsplit(url)
        if parts.scheme or parts.netloc:
            raise BuildError(f"Recurso externo sin incorporar: {url}")
        path_text = unquote(parts.path)
        path = ((self.source / path_text.lstrip("/")) if path_text.startswith("/")
                else (relative_to / path_text)).resolve()
        if not path.is_relative_to(self.source):
            raise BuildError(f"El recurso sale de la carpeta de origen: {url}")
        if not path.is_file():
            raise BuildError(f"Falta el recurso local: {path}")
        return path, parts.fragment

    def data_url(self, url: str, relative_to: Path) -> str:
        value = url.strip()
        if value.startswith(("data:", "#")):
            return value
        path, fragment = self.local_path(value, relative_to)
        if path not in self.resources:
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            self.resources[path] = f"data:{mime};base64,{encoded}"
        return self.resources[path] + ("#" + fragment if fragment else "")

    def css(self, css_text: str, relative_to: Path) -> str:
        # Un @import exige resolver otra hoja; es preferible fallar a entregar
        # una versión que silenciosamente siga dependiendo de la red.
        if re.search(r"@import\s", css_text, flags=re.I):
            raise BuildError("styles.css contiene @import; reúna las hojas antes de generar.")
        return CSS_URL.sub(
            lambda m: 'url("' + self.data_url(m.group("url"), relative_to) + '")',
            css_text,
        )

    def srcset(self, value: str, relative_to: Path) -> str:
        # Los archivos de origen emplean URL locales. Una URI de datos única
        # ya autónoma se conserva; no se divide por su coma interna.
        if value.lstrip().startswith("data:"):
            return value
        result = []
        for candidate in value.split(","):
            fields = candidate.strip().split()
            if not fields:
                continue
            if len(fields) > 2:
                raise BuildError(f"srcset no válido: {value}")
            descriptor = " " + fields[1] if len(fields) == 2 else ""
            result.append(self.data_url(fields[0], relative_to) + descriptor)
        return ", ".join(result)

    def link(self, value: str, view: str, relative_to: Path) -> str:
        parts = urlsplit(value)
        if parts.scheme or parts.netloc:
            return value
        if value.startswith("#"):
            anchor = quote(unquote(parts.fragment), safe="-_.~")
            return "#" + view + ("/" + anchor if anchor else "")
        path_text = unquote(parts.path)
        if not path_text:
            return value
        target = ((self.source / path_text.lstrip("/")) if path_text.startswith("/")
                  else relative_to / path_text).resolve()
        try:
            relative = target.relative_to(self.source).as_posix()
        except ValueError:
            return value
        if relative in PAGES:
            if parts.query:
                raise BuildError(f"Ruta de página con parámetros no admitidos: {value}")
            anchor = quote(unquote(parts.fragment), safe="-_.~")
            return "#" + PAGES[relative] + ("/" + anchor if anchor else "")
        if target.suffix.lower() in IMAGE_SUFFIXES:
            return self.data_url(value, relative_to)
        if target.suffix.lower() in {".html", ".htm"}:
            raise BuildError(f"La página enlazada no forma parte de la entrega: {value}")
        return value


class PageParser(HTMLParser):
    def __init__(self, bundler: Bundler, path: Path, view: str):
        super().__init__(convert_charrefs=False)
        self.bundler = bundler
        self.path = path
        self.view = view
        self.parts: list[str] = []
        self.body = False
        self.seen_body = False
        self.in_title = False
        self.title_parts: list[str] = []
        self.description = ""
        self.body_class = ""
        self.skip_script = False
        self.in_style = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, False)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, True)

    def _start(self, tag: str, attrs: list[tuple[str, str | None]], closed: bool) -> None:
        values = dict(attrs)
        if tag == "title" and not self.body:
            self.in_title = True
            return
        if tag == "meta" and (values.get("name") or "").lower() == "description":
            self.description = values.get("content") or ""
        if tag == "body":
            self.body = self.seen_body = True
            self.body_class = values.get("class") or ""
            return
        if not self.body:
            return
        if tag == "script":
            self.skip_script = True
            return
        if self.skip_script:
            return
        rewritten = []
        for key, value in attrs:
            if value is not None:
                if key == "srcset":
                    value = self.bundler.srcset(value, self.path.parent)
                elif key in {"src", "poster"} and tag in {"img", "source", "video", "input"}:
                    value = self.bundler.data_url(value, self.path.parent)
                elif key in {"href", "xlink:href"} and tag in {"image", "use"}:
                    value = self.bundler.data_url(value, self.path.parent)
                elif key == "href" and tag == "a":
                    value = self.bundler.link(value, self.view, self.path.parent)
                elif key == "style":
                    value = self.bundler.css(value, self.path.parent)
            rewritten.append(key if value is None else f'{key}="{escape(value, quote=True)}"')
        attr_text = " " + " ".join(rewritten) if rewritten else ""
        self.parts.append("<" + tag + attr_text + (" />" if closed else ">"))
        if tag == "style":
            self.in_style = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self.in_title:
            self.in_title = False
            return
        if tag == "script" and self.skip_script:
            self.skip_script = False
            return
        if tag == "body":
            self.body = False
            return
        if self.body and not self.skip_script and tag not in VOID_TAGS:
            self.parts.append("</" + tag + ">")
        if tag == "style":
            self.in_style = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.body and not self.skip_script:
            self.parts.append(self.bundler.css(data, self.path.parent) if self.in_style else data)

    def handle_entityref(self, name: str) -> None:
        self.handle_data("&" + name + ";")

    def handle_charref(self, name: str) -> None:
        self.handle_data("&#" + name + ";")

    def handle_comment(self, data: str) -> None:
        if self.body and not self.skip_script:
            self.parts.append("<!--" + data + "-->")

    def result(self) -> tuple[str, dict[str, str]]:
        if not self.seen_body:
            raise BuildError(f"No se encuentra body en {self.path.name}")
        return "".join(self.parts), {
            "title": unescape("".join(self.title_parts).strip()) or "Diputado de Distrito",
            "description": self.description,
            "bodyClass": self.body_class,
        }


ROUTER = r"""
(function () {
  'use strict';
  const root = document.getElementById('ddd-app');
  const pages = __DDD_PAGE_META__;
  const anchors = { investigacion: 'inicio', 'sobre-autor': 'registro', juridica: 'registro' };
  let activeView = null;
  let renderedURL = null;

  function decoded(value) {
    try { return decodeURIComponent(value); } catch (_) { return value; }
  }
  function route(hash) {
    const value = (hash || '').replace(/^#/, '');
    const slash = value.indexOf('/');
    const head = decoded(slash < 0 ? value : value.slice(0, slash));
    const tail = slash < 0 ? '' : decoded(value.slice(slash + 1));
    if (Object.prototype.hasOwnProperty.call(pages, head)) return { view: head, anchor: tail };
    if (Object.prototype.hasOwnProperty.call(anchors, head)) return { view: anchors[head], anchor: head };
    return { view: 'inicio', anchor: '' };
  }
  function saveScroll() {
    try {
      history.replaceState(Object.assign({}, history.state || {}, {
        dddScroll: window.scrollY
      }), '', location.href);
    } catch (_) { /* Algunos visores restringen history sobre archivos locales. */ }
  }
  function position(view, restore) {
    requestAnimationFrame(function () {
      const target = view.anchor ? document.getElementById(view.anchor) : null;
      const hasSaved = restore && history.state && Number.isFinite(history.state.dddScroll);
      if (hasSaved) {
        window.scrollTo({ top: history.state.dddScroll, left: 0, behavior: 'instant' });
      } else if (target) {
        target.scrollIntoView({ block: 'start', behavior: 'instant' });
      } else {
        window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
      }
    });
  }
  function render(options) {
    const settings = options || {};
    const view = route(location.hash);
    const changed = activeView !== view.view;
    if (changed) {
      const template = document.getElementById('ddd-view-' + view.view);
      root.replaceChildren(template.content.cloneNode(true));
      document.body.className = pages[view.view].bodyClass || '';
      document.title = pages[view.view].title;
      const description = document.querySelector('meta[name="description"]');
      if (description) description.content = pages[view.view].description || '';
      activeView = view.view;
      if (typeof window.DDDInit === 'function') window.DDDInit(root);
      if (settings.focus) {
        const heading = root.querySelector('main h1, h1');
        if (heading) {
          const hadIndex = heading.hasAttribute('tabindex');
          if (!hadIndex) heading.setAttribute('tabindex', '-1');
          heading.focus({ preventScroll: true });
          if (!hadIndex) heading.addEventListener('blur', function () {
            heading.removeAttribute('tabindex');
          }, { once: true });
        }
      }
      document.dispatchEvent(new CustomEvent('ddd:route', { detail: view }));
    }
    renderedURL = location.href;
    position(view, Boolean(settings.restore));
  }
  document.addEventListener('click', function (event) {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey ||
        event.shiftKey || event.altKey) return;
    const link = event.target instanceof Element ? event.target.closest('a[href]') : null;
    if (!link || !root.contains(link) || link.hasAttribute('download') ||
        (link.target && link.target !== '_self')) return;
    const href = link.getAttribute('href');
    if (!href || href.charAt(0) !== '#') return;
    event.preventDefault();
    saveScroll();
    if (location.hash !== href) {
      try {
        history.pushState({ dddScroll: 0 }, '', href);
      } catch (_) {
        location.hash = href;
        return;
      }
    }
    render({ focus: true });
  });
  window.addEventListener('popstate', function () { render({ restore: true, focus: true }); });
  window.addEventListener('hashchange', function () {
    if (renderedURL !== location.href) render({ focus: true });
  });
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  render({ restore: true });
})();
"""


def build(source: Path, output: Path) -> dict[str, object]:
    source = source.resolve()
    output = output.resolve()
    if not source.is_dir():
        raise BuildError(f"No existe la carpeta de origen: {source}")
    required = [*PAGES, "styles.css", "app.js", "catalogo-mapas.js"]
    for name in required:
        if not (source / name).is_file():
            raise BuildError(f"Falta el archivo requerido: {name}")
    if output in {(source / name).resolve() for name in required}:
        raise BuildError("El destino no puede sobrescribir uno de los archivos de origen.")
    bundler = Bundler(source)
    templates = []
    metadata = {}
    for filename, view in PAGES.items():
        parser = PageParser(bundler, source / filename, view)
        parser.feed((source / filename).read_text(encoding="utf-8-sig"))
        parser.close()
        body, meta = parser.result()
        metadata[view] = meta
        templates.append(f'<template id="ddd-view-{view}">\n{body}\n</template>')
    css = bundler.css((source / "styles.css").read_text(encoding="utf-8-sig"), source)
    css = re.sub(r"</style", lambda m: "\\3C /" + m.group(0)[2:], css, flags=re.I)
    app = (source / "app.js").read_text(encoding="utf-8-sig")
    catalog = (source / "catalogo-mapas.js").read_text(encoding="utf-8-sig")
    router = ROUTER.replace("__DDD_PAGE_META__", json_for_script(metadata))
    result = "\n".join([
        '<!DOCTYPE html>', '<html lang="es">', '<head>', '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>' + escape(metadata["inicio"]["title"]) + '</title>',
        '<meta name="description" content="' + escape(metadata["inicio"]["description"], quote=True) + '">',
        '<style>\n' + css + '\n</style>', '</head>', '<body>',
        '<div id="ddd-app"></div>',
        '<noscript><p>Activa JavaScript para recorrer esta presentación. '
        'También puedes <a href="https://diputadodedistrito.es/v3/">abrir el visor de Diputado de Distrito</a>.</p></noscript>',
        *templates,
        '<script>\n' + script_safe(catalog) + '\n</script>',
        '<script>\n' + script_safe(app) + '\n</script>',
        '<script>\n' + script_safe(router) + '\n</script>',
        '</body>', '</html>', '',
    ])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding="utf-8")
    return {
        "output": str(output),
        "bytes": output.stat().st_size,
        "pages": len(PAGES),
        "embedded_resources": len(bundler.resources),
        "resources": sorted(p.relative_to(source).as_posix() for p in bundler.resources),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, type=Path, help="Carpeta de los HTML, CSS, JS y assets")
    parser.add_argument("--output", required=True, type=Path, help="HTML autónomo de destino")
    args = parser.parse_args()
    try:
        report = build(args.source, args.output)
    except (BuildError, OSError, UnicodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
