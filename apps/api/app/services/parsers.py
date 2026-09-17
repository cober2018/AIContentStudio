"""Source 解析器：统一产出 ParsedDocument（text + blocks + metadata）。执行计划 STU-023。"""

import csv
import io
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Protocol

import pypdf


@dataclass
class ParsedBlock:
    type: str  # paragraph / heading / table_row / list_item
    text: str
    locator: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    text: str
    blocks: list[ParsedBlock]
    metadata: dict[str, Any] = field(default_factory=dict)


class SourceParser(Protocol):
    def can_parse(self, mime_type: str | None, extension: str | None) -> bool: ...

    def parse(self, content: bytes, filename: str = "") -> ParsedDocument: ...


def _paragraph_blocks(text: str) -> list[ParsedBlock]:
    blocks = []
    for i, para in enumerate(p for p in text.split("\n\n") if p.strip()):
        is_heading = para.lstrip().startswith("#")
        blocks.append(
            ParsedBlock(
                type="heading" if is_heading else "paragraph",
                text=para.strip(),
                locator={"block": i},
            )
        )
    return blocks


class TextParser:
    def can_parse(self, mime_type: str | None, extension: str | None) -> bool:
        return (mime_type or "").startswith("text/plain") or extension in {".txt", ""}

    def parse(self, content: bytes, filename: str = "") -> ParsedDocument:
        text = content.decode("utf-8", errors="replace")
        return ParsedDocument(text=text, blocks=_paragraph_blocks(text))


class MarkdownParser:
    def can_parse(self, mime_type: str | None, extension: str | None) -> bool:
        return (mime_type or "") in {"text/markdown", "text/x-markdown"} or extension in {".md", ".markdown"}

    def parse(self, content: bytes, filename: str = "") -> ParsedDocument:
        text = content.decode("utf-8", errors="replace")
        return ParsedDocument(text=text, blocks=_paragraph_blocks(text), metadata={"format": "markdown"})


class CsvParser:
    def can_parse(self, mime_type: str | None, extension: str | None) -> bool:
        return (mime_type or "") == "text/csv" or extension == ".csv"

    def parse(self, content: bytes, filename: str = "") -> ParsedDocument:
        text = content.decode("utf-8", errors="replace")
        rows = list(csv.reader(io.StringIO(text)))
        if not rows:
            return ParsedDocument(text="", blocks=[])
        header = rows[0]
        blocks = [
            ParsedBlock(
                type="table_row",
                text=" | ".join(f"{k}={v}" for k, v in zip(header, row, strict=False)),
                locator={"row": i},
            )
            for i, row in enumerate(rows[1:], start=1)
            if row
        ]
        rendered = "\n".join(b.text for b in blocks)
        return ParsedDocument(text=rendered, blocks=blocks, metadata={"columns": header, "row_count": len(blocks)})


class JsonParser:
    def can_parse(self, mime_type: str | None, extension: str | None) -> bool:
        return (mime_type or "") in {"application/json"} or extension == ".json"

    def parse(self, content: bytes, filename: str = "") -> ParsedDocument:
        data = json.loads(content.decode("utf-8", errors="replace"))
        blocks = []

        def walk(node: Any, path: str) -> None:
            if isinstance(node, dict):
                for k, v in node.items():
                    walk(v, f"{path}.{k}" if path else str(k))
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, f"{path}[{i}]")
            else:
                blocks.append(
                    ParsedBlock(type="paragraph", text=f"{path} = {node}", locator={"json_path": path})
                )

        walk(data, "")
        rendered = "\n".join(b.text for b in blocks)
        return ParsedDocument(text=rendered, blocks=blocks, metadata={"json": data})


class PdfTextParser:
    def can_parse(self, mime_type: str | None, extension: str | None) -> bool:
        return (mime_type or "") == "application/pdf" or extension == ".pdf"

    def parse(self, content: bytes, filename: str = "") -> ParsedDocument:
        reader = pypdf.PdfReader(io.BytesIO(content))
        blocks = []
        for page_no, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            for para in (p.strip() for p in page_text.split("\n\n") if p.strip()):
                blocks.append(
                    ParsedBlock(type="paragraph", text=re.sub(r"\s+", " ", para), locator={"page": page_no + 1})
                )
        rendered = "\n".join(b.text for b in blocks)
        return ParsedDocument(text=rendered, blocks=blocks, metadata={"page_count": len(reader.pages)})


class _HTMLTextExtractor(HTMLParser):
    _SKIP_TAGS = frozenset({"script", "style", "noscript", "svg", "head"})

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip_depth = 0
        self.title = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data.strip():
            self._chunks.append(data.strip())


class HtmlParser:
    """URL 导入用的轻量正文抽取：去标签、去脚本样式。不追求 readability 级别精确。"""

    def can_parse(self, mime_type: str | None, extension: str | None) -> bool:
        return (mime_type or "").startswith("text/html") or extension in {".html", ".htm"}

    def parse(self, content: bytes, filename: str = "") -> ParsedDocument:
        extractor = _HTMLTextExtractor()
        extractor.feed(content.decode("utf-8", errors="replace"))
        text = "\n".join(extractor._chunks)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return ParsedDocument(
            text=text,
            blocks=_paragraph_blocks(text),
            metadata={"title": extractor.title},
        )


ALL_PARSERS: list[SourceParser] = [
    MarkdownParser(),
    CsvParser(),
    JsonParser(),
    PdfTextParser(),
    HtmlParser(),
    TextParser(),  # 兜底放最后
]


def get_parser(mime_type: str | None, extension: str | None) -> SourceParser:
    for parser in ALL_PARSERS:
        if parser.can_parse(mime_type, extension):
            return parser
    return TextParser()
