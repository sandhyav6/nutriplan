"""Extract a readable Markdown version of a .docx file (standard library only).

Preserves headings, paragraphs, bullet lists and tables. The source .docx is
opened read-only and never modified.

Usage:
    python scripts/extract_docx.py docs/requirements/NutriPlan-SRS.docx
Writes the Markdown file next to the source (same name, .md extension).
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def paragraph_text(p: ET.Element) -> str:
    parts: list[str] = []
    for node in p.iter():
        if node.tag == f"{W}t" and node.text:
            parts.append(node.text)
        elif node.tag == f"{W}tab":
            parts.append(" ")
        elif node.tag in (f"{W}br", f"{W}cr"):
            parts.append(" ")
    return "".join(parts).strip()


def paragraph_style(p: ET.Element) -> str:
    style = p.find(f"{W}pPr/{W}pStyle")
    return style.get(f"{W}val", "") if style is not None else ""


def is_list_item(p: ET.Element) -> bool:
    return p.find(f"{W}pPr/{W}numPr") is not None


def has_image(p: ET.Element) -> bool:
    return any(node.tag.endswith("}drawing") for node in p.iter())


def table_to_markdown(tbl: ET.Element) -> str:
    rows: list[list[str]] = []
    for tr in tbl.findall(f"{W}tr"):
        cells = []
        for tc in tr.findall(f"{W}tc"):
            text = " ".join(t for t in (paragraph_text(p) for p in tc.findall(f".//{W}p")) if t)
            cells.append(text.replace("|", "\\|"))
        rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + " --- |" * width]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


def convert(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    body = root.find(f"{W}body")
    out: list[str] = [f"<!-- Auto-extracted from {path.name}. The .docx file is the authoritative source. -->", ""]
    for block in body:
        if block.tag == f"{W}tbl":
            out += [table_to_markdown(block), ""]
            continue
        if block.tag != f"{W}p":
            continue
        text = paragraph_text(block)
        if has_image(block):
            out += ["> **[Image in source document – review the .docx manually]**", ""]
        if not text:
            continue
        style = paragraph_style(block).lower()
        if style.startswith("heading"):
            level = "".join(ch for ch in style if ch.isdigit()) or "1"
            out += [f"{'#' * min(int(level) + 1, 6)} {text}", ""]
        elif style == "title":
            out += [f"# {text}", ""]
        elif style.startswith("toc"):
            continue  # skip the table of contents
        elif is_list_item(block):
            out.append(f"- {text}")
        else:
            out += [text, ""]
    return "\n".join(out).rstrip() + "\n"


def main() -> None:
    for arg in sys.argv[1:]:
        source = Path(arg)
        target = source.with_suffix(".md")
        target.write_text(convert(source), encoding="utf-8")
        print(f"Wrote {target}")


if __name__ == "__main__":
    main()
