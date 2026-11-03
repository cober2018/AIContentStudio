"""Find pictures for a product or a tech subject on readable web pages.

Big marketplaces block scraping, so they are skipped and the user pastes those by hand.
A page whose content only appears after its scripts run is opened once more in a
headless Chrome with a throwaway profile. The run keeps links only; a picture is
downloaded and saved as a material when the user picks it.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AuditLog, ContentUnit, ProductSku, ProductSkuRevision, SystemSetting, User, WebMaterialSearch, utcnow
from . import discovery_search
from .chrome_profiles import CHROME_APP
from .url_fetch import _validate_target, safe_fetch

SITES_KEY = "web_material_sites"
MARKETPLACES = ("taobao.com", "tmall.com", "tmall.hk", "jd.com", "jd.hk", "pinduoduo.com", "yangkeduo.com", "1688.com",
                "douyin.com", "jinritemai.com", "xiaohongshu.com", "kuaishou.com")
MAX_PAGES = 10
MAX_IMAGES = 30
MAX_TEXT = 30000
RENDER_SECONDS = 20
# Sites answer a plain client with an empty page or a 403 more often than a browser.
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
           "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6"}
_SKIP_IMAGE = re.compile(r"icon|logo|qr-?code|qrcode|sprite|avatar|loading|blank|placeholder|pixel|spacer|badge|arrow|\.svg|\.gif"
                         r"|login|btn|button|share|weixin|wechat|wx\d|kefu|客服|wpa\.qq|usernoimg|header_user", re.I)
# Under this many matching pieces of the search words, a page is about something else.
RELEVANCE = 0.5
_CATEGORY_HINTS = (
    ("certificate", re.compile(r"证书|认证|检测|报告|资质|certif|cert|licen[cs]e|report", re.I)),
    ("specification", re.compile(r"参数|规格|配料|营养|成分|spec|ingredient|nutrition", re.I)),
    ("dimensions", re.compile(r"尺寸|dimension|size", re.I)),
    ("detail", re.compile(r"细节|detail", re.I)),
)

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="web-material-search")
_active: set[int] = set()
_active_lock = threading.Lock()


def _fail(status: int, code: str, message: str):
    raise HTTPException(status, {"code": code, "message": message})


def _host(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def _matches(host: str, domains) -> bool:
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def sites(db: Session) -> list[str]:
    row = db.get(SystemSetting, SITES_KEY)
    value = (row.value or {}).get("sites") if row else None
    return list(value) if isinstance(value, list) else []


_DOMAIN = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$")


def put_sites(db: Session, user: User, values: list[str]) -> dict:
    cleaned = []
    for value in values:
        domain = re.sub(r"^https?://", "", value.strip().lower()).split("/")[0].removeprefix("www.")
        if not domain:
            continue
        if not _DOMAIN.match(domain):
            _fail(422, "web_material_site_invalid", f"「{value[:60]}」不是网站域名，例如 oppo.com")
        if domain not in cleaned:
            cleaned.append(domain)
    row = db.get(SystemSetting, SITES_KEY) or SystemSetting(key=SITES_KEY)
    row.value, row.updated_by = {"sites": cleaned[:50]}, user.email
    db.add(row)
    db.commit()
    return {"sites": cleaned[:50]}


class _Page(HTMLParser):
    """Title, pictures (largest srcset entry), product JSON-LD and visible text of one page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.images, self.text, self.ld = "", [], [], []
        self._stack: list[str] = []
        self._ld = False

    def handle_starttag(self, tag, attrs):
        data = {key: value or "" for key, value in attrs}
        if tag in {"script", "style", "noscript", "title", "template"}:
            self._stack.append(tag)
            self._ld = tag == "script" and data.get("type") == "application/ld+json"
        if tag == "meta" and data.get("property", data.get("name", "")).lower() in {"og:image", "og:image:url", "twitter:image"}:
            self.images.append((data.get("content", ""), "封面图"))
        if tag in {"img", "source"}:
            if any(data.get(side, "").isdigit() and int(data[side]) < 120 for side in ("width", "height")):
                return
            best = _largest(data.get("srcset") or data.get("data-srcset") or "")
            src = best or data.get("data-src") or data.get("data-original") or data.get("data-lazy-src") or data.get("src") or ""
            self.images.append((src, data.get("alt", "") or data.get("title", "")))

    def handle_endtag(self, tag):
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()
            self._ld = False

    def handle_data(self, data):
        if self._stack and self._stack[-1] == "title":
            self.title += data
        elif self._ld:
            self.ld.append(data)
        elif not self._stack and data.strip():
            self.text.append(data.strip())


def _largest(srcset: str) -> str:
    best, size = "", -1.0
    for part in srcset.split(","):
        bits = part.strip().split()
        if not bits:
            continue
        try:
            value = float(bits[1][:-1]) if len(bits) > 1 and bits[1][-1] in "wx" else 1.0
        except ValueError:
            value = 1.0
        if value > size:
            best, size = bits[0], value
    return best


def _ld_images(chunks: list[str]) -> list[str]:
    found = []

    def walk(node):
        if isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            if str(node.get("@type", "")).lower() == "product":
                image = node.get("image")
                for item in image if isinstance(image, list) else [image]:
                    url = item.get("url") if isinstance(item, dict) else item
                    if isinstance(url, str):
                        found.append(url)
            for value in node.values():
                if isinstance(value, (list, dict)):
                    walk(value)

    for chunk in chunks:
        try:
            walk(json.loads(chunk))
        except ValueError:
            continue
    return found


def _category(text: str) -> str:
    return next((key for key, pattern in _CATEGORY_HINTS if pattern.search(text)), "real_product")


def parse(html: str, url: str) -> dict:
    page = _Page()
    try:
        page.feed(html)
    except Exception:  # noqa: BLE001 Broken markup still yields what was read before the break.
        pass
    seen, images = set(), []
    for src, alt in [(item, "商品图") for item in _ld_images(page.ld)] + page.images:
        src = (src or "").strip()
        if not src or src.startswith("data:"):
            continue
        full = urljoin(url, src)
        if urlsplit(full).scheme not in {"http", "https"} or full in seen or _SKIP_IMAGE.search(urlsplit(full).path + " " + alt):
            continue
        seen.add(full)
        images.append({"url": full[:2000], "alt": re.sub(r"\s+", " ", alt).strip()[:200],
                       "category": _category(f"{alt} {urlsplit(full).path}")})
    return {"title": re.sub(r"\s+", " ", page.title).strip()[:300], "images": images[:MAX_IMAGES],
            "text": "\n".join(page.text)[:MAX_TEXT]}


def render(url: str) -> str:
    """Open the page in headless Chrome so script-built content exists, with a profile deleted right after."""
    if not CHROME_APP.exists():
        return ""
    binary = CHROME_APP / "Contents/MacOS/Google Chrome"
    with tempfile.TemporaryDirectory(prefix="web-material-chrome-") as profile:
        try:
            done = subprocess.run(
                [str(binary), "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                 # Updates and background services stay off so a render never touches the installed Chrome.
                 "--disable-component-update", "--disable-background-networking", "--disable-sync", "--disable-extensions",
                 "--mute-audio", f"--user-data-dir={profile}", f"--virtual-time-budget={(RENDER_SECONDS - 5) * 1000}",
                 "--dump-dom", url],
                capture_output=True, timeout=RENDER_SECONDS + 10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return ""
    return done.stdout[:5 * 1024 * 1024].decode("utf-8", "ignore")


def _public(url: str) -> bool:
    try:
        _validate_target(url)
        return True
    except Exception:  # noqa: BLE001 Any doubt about the address keeps Chrome away from it.
        return False


def read_page(url: str) -> dict:
    try:
        body, mime = safe_fetch(url, headers=HEADERS)
    except Exception:  # noqa: BLE001 Fetch errors can carry the URL's query; only the reason is kept.
        # Some sites always send compressed pages, which the safe fetch refuses; Chrome may read them, but only on a public address.
        html = render(url) if _public(url) else ""
        data = parse(html, url) if html else None
        if not data or not (data["images"] or data["text"]):
            return {"readable": False, "reason": "连不上或被拒绝"}
        return {"readable": True, **data, "rendered": True}
    if "html" not in (mime or ""):
        return {"readable": False, "reason": "不是网页"}
    data = parse(body.decode("utf-8", "ignore"), url)
    data["rendered"] = False
    # The safe fetch already checked this host; only then may Chrome open it.
    if not data["images"] and len(data["text"]) < 1500:
        html = render(url)
        if html:
            rendered = parse(html, url)
            if rendered["images"] or len(rendered["text"]) > len(data["text"]):
                data = {**rendered, "title": rendered["title"] or data["title"], "rendered": True}
    if not data["images"] and not data["text"]:
        return {"readable": False, "reason": "页面内容读不到", "title": data["title"]}
    return {"readable": True, **data}


def _queries(kind: str, query: str) -> list[str]:
    if kind == "product":
        return [f"{query} 官网", f"{query} 参数 规格", f"{query} 证书 检测报告"]
    return [f"{query} 官网", f"{query} 参数", f"{query} 评测"]


def _pieces(text: str) -> set[str]:
    text = text.lower()
    words = set(re.findall(r"[a-z0-9]+", text))
    han = re.sub(r"[^\u4e00-\u9fff]", "", text)
    return words | {han[i:i + 2] for i in range(len(han) - 1)}


def relevance(query: str, text: str) -> float:
    wanted = _pieces(query)
    return len(wanted & _pieces(text)) / len(wanted) if wanted else 1.0


def _variant_found(variant: str, title: str) -> bool | None:
    key = re.sub(r"\s+", "", variant or "").lower()
    if not key or len(key) > 40:
        return None
    return key in re.sub(r"\s+", "", title).lower()


def _json(row: WebMaterialSearch) -> dict:
    result = copy.deepcopy(row.result_json or {})
    for page in result.get("pages", []):
        page["has_text"] = bool(page.pop("text", ""))
    return {"id": row.id, "sku_id": row.sku_id, "project_id": row.project_id, "unit_id": row.unit_id, "query": row.query,
            "status": row.status, "progress": row.progress_json or {}, "error_code": row.error_code,
            "pages": result.get("pages", []), "skipped": result.get("skipped", []), "queries": result.get("queries", []),
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None}


def _settle(db: Session, row: WebMaterialSearch) -> None:
    with _active_lock:
        alive = row.id in _active
    if row.status in {"queued", "running"} and not alive:
        row.status, row.error_code = "interrupted", "web_material_search_interrupted"
        db.commit()


def _save(db: Session, row: WebMaterialSearch, result: dict, **progress) -> None:
    row.result_json = copy.deepcopy(result)
    row.progress_json = {**(row.progress_json or {}), **progress}
    row.updated_at = utcnow()
    db.commit()


def _execute(search_id: int) -> None:
    from ..db import SessionLocal
    from .model_registration import topic_search_vendor

    try:
        with SessionLocal() as db:
            row = db.get(WebMaterialSearch, search_id)
            row.status, row.error_code = "running", None
            db.commit()
            result = {"queries": _queries("product" if row.sku_id else "topic", row.query), "pages": [], "skipped": []}
            try:
                _save(db, row, result, stage="searching", done=0, total=0)
                provider = topic_search_vendor()
                found, hits = [], 0
                for query in result["queries"]:
                    try:
                        rows = discovery_search.search(query, provider=provider, limit=10)
                    except discovery_search.SearchUnavailable:
                        continue
                    hits += 1
                    for item in rows:
                        host = _host(item["url"])
                        if _matches(host, MARKETPLACES):
                            if not any(entry["url"] == item["url"] for entry in result["skipped"]):
                                result["skipped"].append({"url": item["url"], "title": item["title"], "reason": "大电商平台读不到"})
                        elif all(entry["url"] != item["url"] for entry in found + result["skipped"]):
                            if relevance(row.query, f"{item['title']} {item.get('snippet', '')}") < RELEVANCE:
                                result["skipped"].append({"url": item["url"], "title": item["title"], "reason": "和搜索词对不上"})
                            else:
                                found.append(item)
                if not hits:
                    row.status, row.error_code, row.finished_at = "failed", "web_material_search_unavailable", utcnow()
                    _save(db, row, result)
                    return
                preferred = sites(db)
                found.sort(key=lambda item: not _matches(_host(item["url"]), preferred))
                found = found[:MAX_PAGES]
                variant = ""
                if row.sku_id:
                    sku = db.get(ProductSku, row.sku_id)
                    revision = db.scalar(select(ProductSkuRevision).where(ProductSkuRevision.sku_id == row.sku_id,
                                                                          ProductSkuRevision.revision == sku.revision))
                    variant = ((revision.product_json or {}) if revision else {}).get("variant") or ""
                _save(db, row, result, stage="reading", done=0, total=len(found))
                # Pages are read three at a time; a Chrome render can take its full 20 seconds.
                with ThreadPoolExecutor(max_workers=3) as pool:
                    jobs = {pool.submit(read_page, item["url"]): index for index, item in enumerate(found, start=1)}
                    for job in as_completed(jobs):
                        index, page = jobs[job], job.result()
                        item = found[index - 1]
                        title = page.get("title") or item["title"]
                        result["pages"].append({
                            "id": f"p{index}", "url": item["url"], "site": _host(item["url"]).removeprefix("www."),
                            "title": title, "preferred": _matches(_host(item["url"]), preferred),
                            "variant_found": _variant_found(variant, f"{title} {item['title']}"),
                            "readable": page["readable"], "reason": page.get("reason"), "rendered": page.get("rendered", False),
                            "images": [{"id": f"p{index}-{n}", **image} for n, image in enumerate(page.get("images", []), start=1)],
                            "text": page.get("text", "")})
                        result["pages"].sort(key=lambda entry: int(entry["id"][1:]))
                        _save(db, row, result, stage="reading", done=len(result["pages"]), total=len(found))
                row.status, row.finished_at = "completed", utcnow()
                _save(db, row, result, stage="done")
            except Exception:  # noqa: BLE001 Pages read so far stay; the user can search again.
                db.rollback()
                row = db.get(WebMaterialSearch, search_id)
                row.status, row.error_code, row.finished_at = "failed", "web_material_search_failed", utcnow()
                db.commit()
    finally:
        with _active_lock:
            _active.discard(search_id)


def _target(db: Session, user: User, sku_id: int | None, project_id: int | None, unit_id: int | None) -> tuple[int | None, int | None, int | None]:
    if sku_id:
        sku = db.get(ProductSku, sku_id)
        if sku is None or sku.owner_user_id != user.id:
            _fail(404, "product_sku_not_found", "商品不存在")
        return sku_id, None, None
    if unit_id:
        unit = db.get(ContentUnit, unit_id)
        if unit is None or (project_id and unit.project_id != project_id):
            _fail(404, "content_unit_not_found", "作品不存在")
        project_id = unit.project_id
    if not project_id:
        _fail(422, "web_material_search_target_missing", "要指定商品或项目")
    from .project_authorization import lock_project_context

    lock_project_context(db, project_id, user)
    return None, project_id, unit_id


def start(db: Session, user: User, *, query: str, sku_id: int | None = None, project_id: int | None = None, unit_id: int | None = None) -> dict:
    query = re.sub(r"\s+", " ", query or "").strip()
    if not 2 <= len(query) <= 120:
        _fail(422, "web_material_search_query_invalid", "搜索词要 2–120 个字")
    sku_id, project_id, unit_id = _target(db, user, sku_id, project_id, unit_id)
    row = WebMaterialSearch(owner_user_id=user.id, sku_id=sku_id, project_id=project_id, unit_id=unit_id, query=query,
                            status="queued", progress_json={"stage": "queued", "done": 0, "total": 0}, result_json={})
    db.add(row)
    db.commit()
    with _active_lock:
        _active.add(row.id)
    _executor.submit(_execute, row.id)
    return _json(row)


def _owned(db: Session, user: User, search_id: int) -> WebMaterialSearch:
    row = db.get(WebMaterialSearch, search_id)
    if row is None or row.owner_user_id != user.id:
        _fail(404, "web_material_search_not_found", "搜索记录不存在")
    _settle(db, row)
    return row


def read(db: Session, user: User, search_id: int) -> dict:
    return _json(_owned(db, user, search_id))


def latest(db: Session, user: User, *, sku_id: int | None, project_id: int | None) -> dict | None:
    if not sku_id and not project_id:
        _fail(422, "web_material_search_target_missing", "要指定商品或项目")
    statement = select(WebMaterialSearch).where(WebMaterialSearch.owner_user_id == user.id)
    statement = statement.where(WebMaterialSearch.sku_id == sku_id) if sku_id else statement.where(WebMaterialSearch.project_id == project_id)
    row = db.scalar(statement.order_by(WebMaterialSearch.id.desc()).limit(1))
    if row is None:
        return None
    _settle(db, row)
    return _json(row)


def _image(row: WebMaterialSearch, image_id: str) -> tuple[dict, dict]:
    for page in (row.result_json or {}).get("pages", []):
        for image in page.get("images", []):
            if image["id"] == image_id:
                return page, image
    _fail(404, "web_material_image_not_found", "图片不在这次搜索结果里")


def _download(page: dict, image: dict) -> tuple[bytes, str]:
    try:
        # Many shops refuse pictures requested without their own page as the referrer.
        content, mime = safe_fetch(image["url"], headers={**HEADERS, "Referer": page["url"]})
    except Exception:  # noqa: BLE001 Picture URLs can be signed; never echo them.
        _fail(502, "web_material_image_unavailable", "这张图下载不了")
    mime = (mime or "").split(";")[0].strip().lower()
    if not mime.startswith("image/") or mime == "image/svg+xml":
        _fail(422, "web_material_image_unavailable", "这张图不是可用的图片")
    return content, mime


def preview(db: Session, user: User, search_id: int, image_id: str) -> tuple[bytes, str]:
    page, image = _image(_owned(db, user, search_id), image_id)
    return _download(page, image)


def accept(db: Session, user: User, search_id: int, image_ids: list[str]) -> dict:
    from ..routers.project_assets import MaterialReferenceIn, attach_material_reference
    from . import materials as materials_service
    from .material_dedupe import existing_revision

    row = _owned(db, user, search_id)
    picked = []
    for image_id in dict.fromkeys(image_ids):
        page, image = _image(row, image_id)
        if image.get("accepted"):
            picked.append({"image_id": image_id, **image["accepted"], "category": image["category"]})
            continue
        content, mime = _download(page, image)
        mime = materials_service.validate_upload(content, mime)
        revision = existing_revision(db, hashlib.sha256(content).hexdigest())
        if revision is None:
            material = materials_service.create_material(db, kind="image", title=(page["title"] or page["site"])[:120] or "网上图片",
                                                         tags=["网上搜索"], created_by=user.email)
            # Picking the picture is the user's decision to use it; the page it came from stays on record.
            revision = materials_service.create_revision(
                db, material, content=content, suffix="." + mime.split("/")[-1].replace("jpeg", "jpg")[:5], declared_mime=mime,
                source_kind="web_search", source_url=page["url"][:1000], rights_status="cleared", public_use_allowed=True,
                model_use_allowed=True, attribution_text=f"来源网页：{page['url']}"[:1000],
                metadata={"web_material_search_id": row.id, "site": page["site"], "image_url_hash": hashlib.sha256(image["url"].encode()).hexdigest()},
                created_by=user.email)
            db.add(AuditLog(event="material.uploaded", actor=user.email, entity_type="material", entity_id=str(material.id),
                            detail_json={"hash": revision.content_hash, "source_kind": "web_search"}))
            db.commit()
        if row.project_id:
            attach_material_reference(MaterialReferenceIn(material_revision_id=revision.id, note=f"网上找到：{page['site']}"[:500]),
                                      row.project_id, db, user)
        saved = {"material_id": revision.material_id, "material_revision_id": revision.id, "content_hash": revision.content_hash}
        row = db.get(WebMaterialSearch, search_id)
        result = copy.deepcopy(row.result_json or {})
        for entry in result.get("pages", []):
            for item in entry.get("images", []):
                if item["id"] == image_id:
                    item["accepted"] = saved
        row.result_json, row.updated_at = result, utcnow()
        db.commit()
        picked.append({"image_id": image_id, **saved, "category": image["category"]})
    return {"items": picked}


def save_source(db: Session, user: User, search_id: int, page_id: str) -> dict:
    from ..models import SourceDocument
    from ..routers.sources import _parse_and_store

    row = _owned(db, user, search_id)
    page = next((item for item in (row.result_json or {}).get("pages", []) if item["id"] == page_id), None)
    if page is None:
        _fail(404, "web_material_page_not_found", "网页不在这次搜索结果里")
    if page.get("source_id"):
        return {"source_id": page["source_id"]}
    text = (page.get("text") or "").strip()
    if not text:
        _fail(422, "web_material_page_text_missing", "这个网页没有读到文字")
    data = text.encode()
    doc = SourceDocument(title=(page["title"] or page["site"])[:500], source_type="url", source_url=page["url"][:2000],
                         mime_type="text/plain", as_of=datetime.now().date().isoformat(), trust_level=0.6,
                         sha256=hashlib.sha256(data).hexdigest(), metadata_json={"final_url": page["url"], "web_material_search_id": row.id})
    db.add(doc)
    db.flush()
    _parse_and_store(db, doc, data, "text/plain", ".txt")
    result = copy.deepcopy(row.result_json or {})
    for entry in result.get("pages", []):
        if entry["id"] == page_id:
            entry["source_id"] = doc.id
    row.result_json = result
    db.commit()
    return {"source_id": doc.id}


def clean(db: Session, *, cutoff: datetime, batch: int) -> dict:
    """Searches older than the candidate window go; saved pictures and sources stay because they are separate records."""
    rows = db.scalars(select(WebMaterialSearch).where(WebMaterialSearch.created_at < cutoff,
                                                      WebMaterialSearch.status.not_in(["queued", "running"])).limit(batch)).all()
    for row in rows:
        db.delete(row)
    db.commit()
    return {"web_material_searches_deleted": len(rows)}
