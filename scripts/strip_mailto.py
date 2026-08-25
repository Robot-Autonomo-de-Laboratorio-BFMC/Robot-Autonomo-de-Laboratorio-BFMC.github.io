#!/usr/bin/env python3
"""Quita los enlaces mailto: de un PDF o un PPTX.

Uso:
    python3 scripts/strip_mailto.py <archivo.pdf|archivo.pptx> [...]

El sitio es publico e indexable, y estos documentos llevan las direcciones de
correo de los autores como destino de hipervinculo: invisibles en el texto,
pero perfectamente legibles para un scraper.

En el PDF el reemplazo es *in situ y de igual longitud*, para no correr las
posiciones que la tabla xref tiene anotadas; se rellena con una query string
inocua. En el PPTX se reescribe el .rels, que no tiene esa restriccion.
"""

import os
import re
import shutil
import sys
import zipfile

REEMPLAZO = "https://www.austral.edu.ar/ingenieria/"
PAT = re.compile(rb"mailto:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def relleno(largo):
    """Una URL valida de exactamente `largo` bytes."""
    if largo <= len(REEMPLAZO):
        return REEMPLAZO[:largo].encode()
    extra = largo - len(REEMPLAZO) - 1
    return (REEMPLAZO + "?" + "r" * extra).encode()


def limpiar_pdf(path):
    data = open(path, "rb").read()
    encontrados = set(PAT.findall(data))
    if not encontrados:
        print(f"  {os.path.basename(path)}: sin mailto")
        return 0

    def sub(m):
        return relleno(len(m.group(0)))

    nuevo = PAT.sub(sub, data)
    assert len(nuevo) == len(data), "el reemplazo cambio el tamano del PDF"
    shutil.copy2(path, path + ".bak")
    open(path, "wb").write(nuevo)
    print(f"  {os.path.basename(path)}: {len(encontrados)} mailto removidos "
          f"(tamano intacto: {len(nuevo)} bytes)")
    return len(encontrados)


def limpiar_ooxml(path):
    zin = zipfile.ZipFile(path)
    items = [(i, zin.read(i.filename)) for i in zin.infolist()]
    total = 0
    salida = []
    for info, data in items:
        if info.filename.endswith((".rels", ".xml")) and b"mailto:" in data:
            n = len(PAT.findall(data))
            data = PAT.sub(REEMPLAZO.encode(), data)
            total += n
            print(f"    {info.filename}: {n} mailto")
        salida.append((info, data))
    if not total:
        print(f"  {os.path.basename(path)}: sin mailto")
        return 0
    shutil.copy2(path, path + ".bak")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, data in salida:
            zout.writestr(info, data)
    print(f"  {os.path.basename(path)}: {total} mailto removidos")
    return total


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for path in sys.argv[1:]:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":
            limpiar_pdf(path)
        elif ext in (".pptx", ".docx", ".xlsx"):
            limpiar_ooxml(path)
        else:
            print(f"  {path}: formato no soportado")


if __name__ == "__main__":
    main()
