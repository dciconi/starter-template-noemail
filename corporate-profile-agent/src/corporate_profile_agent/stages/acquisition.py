"""Stage 3 — Document acquisition.

Downloads every discovered source, stores it with URL + retrieval date +
sha256 (traceability), and produces page-addressed text for extraction.

PDF handling matters most in LatAm: filed financials are usually PDFs and
often scanned. Strategy per PDF page:
  1. pdfplumber text + table extraction
  2. if a page yields almost no text and OCR deps are installed, OCR it
     (Spanish + Portuguese tessdata)

Both pdfplumber and the OCR stack are optional imports so the rest of the
pipeline works without them.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import httpx

from ..models import SourceDocument, SourceTier

log = logging.getLogger(__name__)

_MIN_CHARS_BEFORE_OCR = 40  # per page; below this we assume a scanned page


@dataclass
class AcquiredDocument:
    meta: SourceDocument
    # One entry per page for PDFs; single entry for HTML/JSON.
    pages: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(
            f"[page {i + 1}]\n{p}" for i, p in enumerate(self.pages) if p.strip()
        )


def acquire(sources: list[dict], out_dir: Path, timeout: float = 60.0) -> list[AcquiredDocument]:
    out_dir.mkdir(parents=True, exist_ok=True)
    acquired: list[AcquiredDocument] = []
    manifest = []

    for src in sources:
        try:
            doc = _fetch_one(src, out_dir, timeout)
        except Exception as exc:
            log.warning("failed to acquire %s: %s", src["url"], exc)
            continue
        acquired.append(doc)
        manifest.append(doc.meta.model_dump(mode="json"))

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)
    )
    return acquired


def _fetch_one(src: dict, out_dir: Path, timeout: float) -> AcquiredDocument:
    resp = httpx.get(
        src["url"], timeout=timeout, follow_redirects=True,
        headers={"User-Agent": "corporate-profile-agent/0.1 (research)"},
    )
    resp.raise_for_status()
    body = resp.content
    sha = hashlib.sha256(body).hexdigest()
    content_type = resp.headers.get("content-type", "").split(";")[0].strip()
    is_pdf = "pdf" in content_type or src["url"].lower().endswith(".pdf")

    ext = "pdf" if is_pdf else "json" if "json" in content_type else "html"
    local = out_dir / f"{sha[:12]}.{ext}"
    local.write_bytes(body)

    meta = SourceDocument(
        doc_id=sha[:12],
        url=src["url"],
        tier=SourceTier(src["tier"]),
        title=src.get("title", ""),
        content_type=content_type,
        sha256=sha,
        local_path=str(local),
        publisher_domain=urlparse(src["url"]).netloc.removeprefix("www."),
    )

    if is_pdf:
        pages, ocr_used = _extract_pdf(local)
        meta.ocr_applied = ocr_used
    elif "json" in content_type:
        pages = [body.decode("utf-8", errors="replace")]
    else:
        pages = [_strip_html(body.decode("utf-8", errors="replace"))]

    return AcquiredDocument(meta=meta, pages=pages)


def _extract_pdf(path: Path) -> tuple[list[str], bool]:
    try:
        import pdfplumber
    except ImportError:
        log.warning("pdfplumber not installed — storing %s without text", path)
        return [], False

    pages: list[str] = []
    ocr_used = False
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for table in page.extract_tables() or []:
                rows = [
                    " | ".join("" if c is None else str(c) for c in row)
                    for row in table
                ]
                text += "\n[table]\n" + "\n".join(rows)
            if len(text.strip()) < _MIN_CHARS_BEFORE_OCR:
                ocr_text = _ocr_page(page)
                if ocr_text:
                    text, ocr_used = ocr_text, True
            pages.append(text)
    return pages, ocr_used


def _ocr_page(page) -> str:
    try:
        import pytesseract
    except ImportError:
        return ""
    try:
        image = page.to_image(resolution=300).original
        return pytesseract.image_to_string(image, lang="spa+por")
    except Exception as exc:
        log.debug("OCR failed: %s", exc)
        return ""


def _strip_html(html: str) -> str:
    import re

    html = re.sub(r"(?is)<(script|style|nav|footer)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    return " ".join(text.split())
