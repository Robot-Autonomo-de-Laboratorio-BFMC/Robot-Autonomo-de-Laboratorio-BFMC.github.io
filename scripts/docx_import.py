#!/usr/bin/env python3
"""Convierte un .docx a paginas Markdown para MkDocs, partiendo por capitulo.

Uso:
    python3 scripts/docx_import.py <archivo.docx> <directorio-destino>

Parte el documento en una pagina por cada Heading 1, extrae las imagenes
embebidas al subdirectorio img/, y conserva negritas, cursivas, listas,
tablas e hipervinculos.

No requiere dependencias externas: un .docx es un ZIP con XML adentro.
"""

import os
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

HEADING_LEVEL = {
    "Title": 1, "Heading1": 1, "Heading2": 2,
    "Heading3": 3, "Heading4": 4, "Heading5": 5,
}


def slugify(text, fallback="seccion"):
    text = text.lower().strip()
    for a, b in zip("áéíóúàèñüç", "aeiouaenuc"):
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:60] or fallback


def esc(t):
    return re.sub(r"([*_`\[\]<>])", r"\\\1", t)


class Converter:
    def __init__(self, path, out_dir):
        self.z = zipfile.ZipFile(path)
        self.out_dir = out_dir
        self.rels = self._load_rels()
        self.images = {}
        self.img_count = 0

    def _load_rels(self):
        rels = {}
        for r in ET.fromstring(self.z.read("word/_rels/document.xml.rels")):
            rels[r.get("Id")] = (r.get("Type").rsplit("/", 1)[-1], r.get("Target"))
        return rels

    # --- inline ----------------------------------------------------------
    def runs(self, node):
        """Convierte los runs de un parrafo (o hipervinculo) a Markdown."""
        out = []
        for child in node:
            tag = child.tag
            if tag == W + "hyperlink":
                inner = self.runs(child)
                rid = child.get(R + "id")
                target = self.rels.get(rid, (None, None))[1]
                # los mailto: se descartan a proposito: el sitio es publico e
                # indexable, y son direcciones de personas reales
                if target and target.lower().startswith("mailto:"):
                    out.append(inner)
                elif target and inner:
                    out.append(f"[{inner}]({target})")
                else:
                    out.append(inner)
            elif tag == W + "r":
                out.append(self.run(child))
            elif tag in (W + "ins", W + "smartTag", W + "sdt", W + "sdtContent"):
                out.append(self.runs(child))
        return "".join(out)

    def run(self, r):
        img = self.image_in(r)
        if img:
            return f"\n\n![]({img})\n\n"
        text = "".join(t.text or "" for t in r.iter(W + "t"))
        if r.find(W + "br") is not None and not text:
            return "\n"
        if not text:
            return ""
        piece = esc(text)
        pr = r.find(W + "rPr")
        if pr is not None:
            def on(name):
                el = pr.find(W + name)
                return el is not None and el.get(W + "val") not in ("0", "false", "none")
            if on("b"):
                piece = f"**{piece}**" if piece.strip() else piece
            if on("i"):
                piece = f"*{piece}*" if piece.strip() else piece
            if on("strike"):
                piece = f"~~{piece}~~"
        return piece

    def image_in(self, node):
        blip = None
        for b in node.iter(A + "blip"):
            blip = b
            break
        if blip is None:
            return None
        rid = blip.get(R + "embed")
        if not rid or rid not in self.rels:
            return None
        target = self.rels[rid][1]
        if rid in self.images:
            return self.images[rid]
        src = "word/" + target.lstrip("/")
        try:
            data = self.z.read(src)
        except KeyError:
            return None
        self.img_count += 1
        ext = os.path.splitext(target)[1] or ".png"
        name = f"fig-{self.img_count:03d}{ext}"
        dest = os.path.join(self.out_dir, "img", name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        rel = f"img/{name}"
        self.images[rid] = rel
        return rel

    # --- bloques ---------------------------------------------------------
    def paragraph(self, p):
        pr = p.find(W + "pPr")
        style = ""
        if pr is not None:
            st = pr.find(W + "pStyle")
            if st is not None:
                style = st.get(W + "val") or ""
        text = self.runs(p).strip()

        level = HEADING_LEVEL.get(style)
        if level:
            # Word deja parrafos con estilo de titulo pero sin texto (saltos de
            # pagina, separadores). Como encabezado vacio abren un hueco en la
            # pagina, asi que se descartan.
            if not text.strip():
                return ("para", 0, "")
            return ("heading", level, text)

        if pr is not None and pr.find(W + "numPr") is not None:
            ilvl = pr.find(f"{W}numPr/{W}ilvl")
            depth = int(ilvl.get(W + "val")) if ilvl is not None else 0
            return ("list", depth, text)

        if style.startswith("Quote") or style == "IntenseQuote":
            return ("quote", 0, text)
        return ("para", 0, text)

    def table(self, tbl):
        rows = []
        for tr in tbl.findall(W + "tr"):
            cells = []
            for tc in tr.findall(W + "tc"):
                parts = [self.runs(p).strip() for p in tc.findall(W + "p")]
                cells.append(" ".join(x for x in parts if x).replace("|", "\\|"))
            if cells:
                rows.append(cells)
        if not rows:
            return []
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        out = ["| " + " | ".join(rows[0]) + " |",
               "|" + "---|" * width]
        for r in rows[1:]:
            out.append("| " + " | ".join(r) + " |")
        return out + [""]

    # --- recorrido -------------------------------------------------------
    def blocks(self):
        root = ET.fromstring(self.z.read("word/document.xml"))
        yield from self.walk(root.find(W + "body"))

    def walk(self, parent):
        """Recorre solo los hijos directos: los <w:p> de adentro de una tabla
        los consume self.table(), no deben emitirse tambien como parrafos."""
        for el in parent:
            if el.tag == W + "p":
                yield self.paragraph(el)
            elif el.tag == W + "tbl":
                yield ("table", 0, self.table(el))
            elif el.tag in (W + "sdt", W + "sdtContent"):
                yield from self.walk(el)


def render(items):
    lines = []
    for kind, level, value in items:
        if kind == "heading":
            lines += ["", "#" * min(max(level, 2), 6) + " " + value, ""]
        elif kind == "list":
            lines.append("    " * level + "- " + value)
        elif kind == "quote":
            lines += ["", "> " + value, ""]
        elif kind == "table":
            lines += [""] + value
        elif kind == "para":
            if value:
                lines += [value, ""]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    docx, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    conv = Converter(docx, out_dir)

    # agrupar por Heading1
    chapters = []
    current = None
    for kind, level, value in conv.blocks():
        if kind == "heading" and level == 1:
            if value.strip().lower().startswith("pesta"):
                continue          # artefacto de Google Docs
            current = {"title": value, "items": []}
            chapters.append(current)
            continue
        if current is None:
            current = {"title": "Portada", "items": []}
            chapters.append(current)
        current["items"].append((kind, level, value))

    # descartar capitulos vacios (saltos de pagina) y el indice autogenerado
    # "Informe etico (pa inf)" es una nota interna del borrador, no parte del
    # informe entregado: se excluye a proposito.
    DESCARTAR = ("contenido", "indice", "índice", "informe ético (pa inf)",
                 "informe etico (pa inf)")
    chapters = [c for c in chapters
                if c["title"].strip()
                and c["title"].strip().lower() not in DESCARTAR
                and any(v for _, _, v in c["items"])]

    used, nav = set(), []
    for i, ch in enumerate(chapters):
        slug = slugify(ch["title"]) or f"cap-{i:02d}"
        base, n = slug, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        body = render(ch["items"])
        path = os.path.join(out_dir, f"{slug}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {ch['title']}\n\n{body}")
        words = len(body.split())
        print(f"  {ch['title'][:55]:<57} {words:>5} palabras  -> {slug}.md")
        nav.append((ch["title"], slug))

    print(f"\n{conv.img_count} imagenes extraidas a {out_dir}/img/")
    print("\nPara el nav: de mkdocs.yml:\n")
    rel = out_dir.replace("docs/", "", 1)
    for title, slug in nav:
        print(f"      - {title}: {rel}/{slug}.md")


if __name__ == "__main__":
    main()
