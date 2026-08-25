#!/usr/bin/env python3
"""Importa una pagina publica de Notion a Markdown para MkDocs.

Uso:
    python3 scripts/notion_import.py <url-publica> <directorio-destino>

Ejemplo:
    python3 scripts/notion_import.py \
        https://abaft-locust-6f5.notion.site/2b0a28003c7380d2bfaafcb3333ce5b4 \
        docs/archivo/notion/jetson

Requisitos: la pagina tiene que estar publicada ("Share to web") en Notion.
No necesita token ni la API oficial: usa el mismo endpoint publico que consume
el sitio de Notion en el navegador.

Descarga tambien las imagenes adjuntas y reescribe los links para que apunten
a los archivos locales, de modo que el resultado no dependa de que Notion siga
existiendo.
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request

CHUNK_LIMIT = 200


def dashed(page_id):
    """Normaliza un id de Notion a la forma 8-4-4-4-12."""
    s = re.sub(r"[^0-9a-fA-F]", "", page_id)
    if len(s) != 32:
        return page_id
    return f"{s[0:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:32]}"


def post(host, path, payload):
    req = urllib.request.Request(
        f"https://{host}{path}",
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json", "user-agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def load_page(host, page_id):
    """Trae todos los chunks de una pagina y devuelve el mapa de bloques."""
    blocks = {}
    cursor = {"stack": []}
    chunk = 0
    while True:
        data = post(host, "/api/v3/loadPageChunk", {
            "pageId": page_id,
            "limit": CHUNK_LIMIT,
            "cursor": cursor,
            "chunkNumber": chunk,
            "verticalColumns": False,
        })
        rm = data.get("recordMap", {})
        for bid, wrapper in rm.get("block", {}).items():
            value = wrapper.get("value", {})
            # el endpoint anida value.value en las respuestas nuevas
            blocks[bid] = value.get("value", value)
        cursor = data.get("cursor") or {"stack": []}
        chunk += 1
        if not cursor.get("stack"):
            break
    return blocks


# --- rich text -------------------------------------------------------------

def esc(text):
    return re.sub(r"([*_`\[\]])", r"\\\1", text)


def rich(prop):
    """Convierte el formato rich-text de Notion a Markdown inline."""
    if not prop:
        return ""
    out = []
    for span in prop:
        text = span[0] if span else ""
        marks = span[1] if len(span) > 1 and span[1] else []
        if text == "‣":
            # referencia a pagina/usuario/fecha: sin texto util
            for m in marks:
                if m[0] == "d" and len(m) > 1:
                    start = (m[1] or {}).get("start_date")
                    if start:
                        out.append(start)
            continue
        piece = esc(text)
        link = None
        for m in marks:
            kind = m[0]
            if kind == "b":
                piece = f"**{piece}**"
            elif kind == "i":
                piece = f"*{piece}*"
            elif kind == "c":
                piece = f"`{text}`"
            elif kind == "s":
                piece = f"~~{piece}~~"
            elif kind == "a" and len(m) > 1:
                link = m[1]
        if link:
            piece = f"[{piece}]({link})"
        out.append(piece)
    return "".join(out)


def title_of(block):
    return rich(block.get("properties", {}).get("title"))


def plain(prop):
    return "".join(s[0] for s in prop or [])


# --- imagenes --------------------------------------------------------------

def slugify(text, fallback="pagina"):
    text = re.sub(r"[*_`\[\]]", "", text)
    text = text.lower()
    for a, b in zip("áéíóúñü", "aeiounu"):
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:60] or fallback


def download_image(host, block, out_dir, seen):
    src = plain(block.get("properties", {}).get("source"))
    if not src:
        return None
    name = plain(block.get("properties", {}).get("title")) or "image.png"
    ext = os.path.splitext(name)[1] or ".png"
    fname = f"{block['id'].replace('-', '')[-12:]}{ext}"
    dest = os.path.join(out_dir, "img", fname)
    if fname in seen:
        return f"img/{fname}"
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    if src.startswith("http"):
        url = src
    else:
        url = (f"https://{host}/image/{urllib.parse.quote(src, safe='')}"
               f"?table=block&id={block['id']}&cache=v2")
    try:
        req = urllib.request.Request(url, headers={"user-agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        seen.add(fname)
        print(f"    imagen: img/{fname} ({len(data)//1024} KiB)")
        return f"img/{fname}"
    except Exception as e:            # noqa: BLE001
        print(f"    !! no se pudo bajar la imagen {block['id']}: {e}")
        return None


# --- conversion ------------------------------------------------------------

CALLOUT_ICON_ADMONITION = {
    "⚠️": "warning", "❗": "warning", "🚨": "danger", "❌": "danger",
    "💡": "tip", "✅": "success", "📌": "note", "ℹ️": "info",
}


def render(host, blocks, root_id, out_dir, subpages, seen_img):
    """Recorre los hijos del bloque raiz y devuelve lineas de Markdown."""
    lines = []
    numbering = 0

    def is_next_sibling_list(ids, bid):
        """True si el hermano siguiente es otro item de la misma lista."""
        try:
            nxt = ids[ids.index(bid) + 1]
        except (ValueError, IndexError):
            return False
        return (blocks.get(nxt) or {}).get("type") in (
            "bulleted_list", "numbered_list", "to_do")

    def walk(ids, depth=0):
        nonlocal numbering, lines
        pad = "    " * depth
        for bid in ids:
            b = blocks.get(bid)
            if not b or b.get("alive") is False:
                continue
            t = b.get("type")
            text = title_of(b)

            if t == "text":
                numbering = 0
                if text.strip():
                    lines.append(pad + text)
                    lines.append("")
            elif t == "header":
                numbering = 0
                lines += ["## " + text, ""]
            elif t == "sub_header":
                numbering = 0
                lines += ["### " + text, ""]
            elif t == "sub_sub_header":
                numbering = 0
                lines += ["#### " + text, ""]
            elif t == "bulleted_list":
                numbering = 0
                lines.append(f"{pad}- {text}")
                walk(b.get("content", []), depth + 1)
                if not is_next_sibling_list(ids, bid):
                    lines.append("")
                continue
            elif t == "numbered_list":
                numbering += 1
                lines.append(f"{pad}{numbering}. {text}")
                walk(b.get("content", []), depth + 1)
                if not is_next_sibling_list(ids, bid):
                    lines.append("")
                continue
            elif t == "to_do":
                done = plain(b.get("properties", {}).get("checked")) == "Yes"
                lines.append(f"{pad}- [{'x' if done else ' '}] {text}")
                continue
            elif t == "toggle":
                lines += ["??? note \"" + re.sub(r'"', "'", text) + "\"", ""]
                walk(b.get("content", []), depth + 1)
                lines.append("")
                continue
            elif t == "code":
                lang = plain(b.get("properties", {}).get("language") or []).lower()
                lang = {"plain text": "", "shell": "bash"}.get(lang, lang)
                raw = plain(b.get("properties", {}).get("title"))
                lines += [f"```{lang}", raw, "```", ""]
            elif t == "quote":
                lines += ["> " + text.replace("\n", "\n> "), ""]
            elif t == "callout":
                icon = (b.get("format") or {}).get("page_icon", "")
                kind = CALLOUT_ICON_ADMONITION.get(icon, "note")
                body = "\n".join("    " + ln for ln in text.split("\n"))
                lines += [f'!!! {kind} ""', body, ""]
            elif t == "divider":
                lines += ["---", ""]
            elif t == "image":
                rel = download_image(host, b, out_dir, seen_img)
                caption = rich(b.get("properties", {}).get("caption"))
                alt = plain(b.get("properties", {}).get("caption")) or "captura"
                alt = re.sub(r'[\[\]]', "", alt)[:120]
                if rel:
                    lines += [f"![{alt}]({rel})", ""]
                if caption:
                    lines += [f"*{caption}*", ""]
            elif t in ("video", "embed", "bookmark", "external_object_instance"):
                src = plain(b.get("properties", {}).get("source"))
                fmt = b.get("format") or {}
                src = src or fmt.get("original_url") or ""
                if src:
                    lines += [f"[{text or src}]({src})", ""]
            elif t == "page":
                subpages.append(bid)
                lines += [f"- [{text}]({slugify(text)}.md)", ""]
            elif t == "column_list":
                walk(b.get("content", []), depth)
                continue
            elif t == "column":
                walk(b.get("content", []), depth)
                continue
            else:
                if text.strip():
                    lines.append(pad + text)
                    lines.append("")

            if t not in ("bulleted_list", "numbered_list", "toggle", "page"):
                walk(b.get("content", []), depth)

    walk(blocks.get(root_id, {}).get("content", []))
    return lines


def export(host, page_id, out_dir, done, depth=0):
    page_id = dashed(page_id)
    if page_id in done:
        return None
    done.add(page_id)

    blocks = load_page(host, page_id)
    root = blocks.get(page_id, {})
    title = title_of(root) or "Sin titulo"
    slug = "index" if depth == 0 else slugify(title)
    print(f"{'  ' * depth}> {title}  ({len(blocks)} bloques)")

    subpages = []
    seen_img = set()
    body = render(host, blocks, page_id, out_dir, subpages, seen_img)

    os.makedirs(out_dir, exist_ok=True)
    header = [f"# {title}", ""]
    path = os.path.join(out_dir, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(header + body).rstrip() + "\n")
    print(f"{'  ' * depth}  -> {path}")

    children = []
    for sid in subpages:
        child = export(host, sid, out_dir, done, depth + 1)
        if child:
            children.append(child)
    return {"title": title, "slug": slug, "children": children}


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    url, out_dir = sys.argv[1], sys.argv[2]
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc
    last = [p for p in parsed.path.split("/") if p][-1]
    page_id = last.split("-")[-1]

    tree = export(host, page_id, out_dir, set())

    print("\nAgregá esto al nav: de mkdocs.yml (ajustando la ruta):\n")
    rel = out_dir.replace("docs/", "", 1)

    def emit(node, indent):
        print(f"{' ' * indent}- {node['title']}: {rel}/{node['slug']}.md")
        for c in node["children"]:
            emit(c, indent + 2)

    emit(tree, 6)


if __name__ == "__main__":
    main()
