import re
from typing import Any

AdfNode = dict[str, Any]

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
BULLET_RE = re.compile(r"^[-*]\s+(.+)$")
CODE_FENCE_RE = re.compile(r"^```(\w*)$")

LINK_RE = re.compile(r"\[(.+?)\]\(([^)]+)\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def _text_node(text: str, marks: list[AdfNode] | None = None) -> AdfNode:
    node: AdfNode = {"type": "text", "text": text}
    if marks:
        node["marks"] = marks
    return node


def _parse_inline(text: str) -> list[AdfNode]:
    nodes: list[AdfNode] = []
    pattern = re.compile(
        r"(\*\*(.+?)\*\*)"
        r"|(\[(.+?)\]\(([^)]+)\))"
        r"|(`([^`]+)`)"
    )

    last_end = 0
    for match in pattern.finditer(text):
        start = match.start()
        if start > last_end:
            nodes.append(_text_node(text[last_end:start]))

        if match.group(2):
            inner_nodes = _parse_inline(match.group(2))
            for node in inner_nodes:
                marks = node.get("marks", [])
                marks.append({"type": "strong"})
                node["marks"] = marks
            nodes.extend(inner_nodes)
        elif match.group(4):
            link_text = match.group(4)
            link_href = match.group(5)
            nodes.append(_text_node(link_text, [{"type": "link", "attrs": {"href": link_href}}]))
        elif match.group(7):
            nodes.append(_text_node(match.group(7), [{"type": "code"}]))

        last_end = match.end()

    if last_end < len(text):
        nodes.append(_text_node(text[last_end:]))

    return nodes if nodes else [_text_node(text)]


def _paragraph(content: list[AdfNode]) -> AdfNode:
    return {"type": "paragraph", "content": content}


def _heading(level: int, content: list[AdfNode]) -> AdfNode:
    return {"type": "heading", "attrs": {"level": level}, "content": content}


def _bullet_list(items: list[list[AdfNode]]) -> AdfNode:
    list_items = [
        {"type": "listItem", "content": [_paragraph(item_content)]}
        for item_content in items
    ]
    return {"type": "bulletList", "content": list_items}


def _code_block(text: str, language: str = "") -> AdfNode:
    node: AdfNode = {"type": "codeBlock", "content": [_text_node(text)]}
    if language:
        node["attrs"] = {"language": language}
    return node


def _normalize_newlines(text: str) -> str:
    text = text.replace("\\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def markdown_to_adf(markdown: str) -> AdfNode:
    markdown = _normalize_newlines(markdown)
    lines = markdown.split("\n")
    doc_content: list[AdfNode] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        fence_match = CODE_FENCE_RE.match(line.strip())
        if fence_match:
            language = fence_match.group(1)
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not CODE_FENCE_RE.match(lines[i].strip()):
                code_lines.append(lines[i])
                i += 1
            i += 1
            doc_content.append(_code_block("\n".join(code_lines), language))
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            doc_content.append(_heading(level, _parse_inline(text)))
            i += 1
            continue

        bullet_match = BULLET_RE.match(line)
        if bullet_match:
            items: list[list[AdfNode]] = []
            while i < len(lines):
                bm = BULLET_RE.match(lines[i])
                if not bm:
                    break
                items.append(_parse_inline(bm.group(1)))
                i += 1
            doc_content.append(_bullet_list(items))
            continue

        if not line.strip():
            i += 1
            continue

        doc_content.append(_paragraph(_parse_inline(line)))
        i += 1

    if not doc_content:
        doc_content.append(_paragraph([_text_node(markdown)]))

    return {"type": "doc", "version": 1, "content": doc_content}
