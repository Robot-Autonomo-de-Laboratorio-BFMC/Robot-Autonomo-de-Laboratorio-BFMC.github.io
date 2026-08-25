#!/usr/bin/env python3
"""Extrae el texto de un .pptx como esquema Markdown, slide por slide.

Uso:
    python3 scripts/pptx_outline.py <archivo.pptx> [salida.md]

Sirve para que el contenido de una presentacion sea buscable desde el sitio
aunque las diapositivas se publiquen como PDF embebido.

Nota: los .pptx exportados desde Canva parten cada letra en dos runs con
distinto kerning, lo que produce texto tipo "RROOBBOOTT". El script lo detecta
y lo colapsa.
"""

import re
import sys
import zipfile
from xml.etree import ElementTree as ET

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"


def para_text(p):
    """Texto de un parrafo, deshaciendo el duplicado por-letra de Canva.

    Canva parte cada caracter en dos runs con distinto kerning, asi que el
    texto sale como "RROOBBOOTT". La firma es que TODOS los runs del parrafo
    son de un solo caracter; solo en ese caso colapsamos pares adyacentes
    iguales, para no romper dobles legitimas como "CARRILES".
    """
    runs = [(t.text or "") for t in p.iter(A + "t")]
    if len(runs) >= 4 and all(len(r) <= 1 for r in runs):
        out, i = [], 0
        while i < len(runs):
            if i + 1 < len(runs) and runs[i] == runs[i + 1]:
                out.append(runs[i])
                i += 2
            else:
                out.append(runs[i])
                i += 1
        return "".join(out).strip()
    return "".join(runs).strip()


def slide_text(xml):
    root = ET.fromstring(xml)
    out = []
    for sp in root.iter(P + "sp"):
        lines = []
        for p in sp.iter(A + "p"):
            t = para_text(p)
            if t:
                lines.append(t)
        if lines:
            out.append(lines)
    n_img = len(list(root.iter(P + "pic")))
    return out, n_img


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    z = zipfile.ZipFile(path)
    slides = sorted(
        (n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
        key=lambda s: int(re.search(r"\d+", s.split("/")[-1]).group()),
    )
    lines = []
    for i, name in enumerate(slides, 1):
        shapes, n_img = slide_text(z.read(name))
        flat = [x for sh in shapes for x in sh]
        title = flat[0] if flat else f"Diapositiva {i}"
        lines.append(f"**{i}. {title}**")
        rest = flat[1:]
        if rest:
            lines.append("")
            for r in rest:
                lines.append(f"    {r}")
        lines.append("")
    text = "\n".join(lines)
    if len(sys.argv) > 2:
        open(sys.argv[2], "w", encoding="utf-8").write(text)
        print(f"{len(slides)} diapositivas -> {sys.argv[2]}")
    else:
        print(text)


if __name__ == "__main__":
    main()
