"""Open stock libraries for script-driven matching: search returns links and license facts; bytes only on explicit accept."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import marshal
import re
import time
from urllib.parse import urlencode, urlsplit

import httpx

from ..config import get_settings
from .content_harness import providers
from .url_fetch import OUTBOUND_HTTP_POLICIES, outbound_scope, pinned_transport, resolve_addresses

_PROXY_FAKE_IP = ipaddress.ip_network("198.18.0.0/15")


def _proxy_fake_ip(host: str) -> bool:
    """A local proxy in fake-IP mode answers every name from 198.18/15 and forwards the connection itself."""
    settings = get_settings()
    if settings.app_env == "production" or not settings.ssrf_allow_private:
        return False
    addresses = [ipaddress.ip_address(info[4][0]) for info in resolve_addresses(host, 443)]
    return bool(addresses) and all(address in _PROXY_FAKE_IP for address in addresses)

# Wikimedia throttles agents without contact details (its User-Agent policy), which showed up as 429 on downloads.
USER_AGENT = "AIContentStudio/0.1 (https://github.com/cober2018/AIContentStudio; local script material matching)"
DOWNLOAD_BYTES = 30 * 1024 * 1024
THUMB_BYTES = 3 * 1024 * 1024
# Accept codes the platform's acceptance path understands; each library license maps onto one of them.
ACCEPT_CODES = {"cc0": "CC0", "pdm": "PDM", "by-4.0": "CC-BY-4.0", "by": "CC-BY", "pexels": "provider_terms",
                "pixabay": "provider_terms", "nasa": "provider_terms", "coverr": "provider_terms",
                "commons-cc0": "CC0", "commons-by-4.0": "CC-BY-4.0"}
LICENSE_NAMES = {"cc0": "CC0 公共领域", "pdm": "公有领域标记", "by": "CC BY", "by-4.0": "CC BY 4.0", "pexels": "Pexels 许可",
                 "pixabay": "Pixabay 内容许可", "nasa": "NASA 媒体使用准则", "coverr": "Coverr 许可"}
# Keys saved on the settings page win; a source never saved there keeps the key from runtime.env.
SETTINGS_KEY = "open_media_sources"


def open_get(url: str, *, hosts: set[str] | None, policy: str, max_bytes: int, headers: dict | None = None) -> tuple[bytes, str]:
    """Bounded HTTPS GET pinned to public addresses; optional host allowlist holds across redirects."""
    limits = OUTBOUND_HTTP_POLICIES[policy]
    limit = min(max_bytes, limits.response_bytes)
    deadline = time.monotonic() + limits.timeout_seconds
    current = url
    for _ in range(4):
        parsed = urlsplit(current)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in {None, 443}:
            raise ValueError("open_media_url_forbidden")
        if hosts is not None and parsed.hostname not in hosts:
            raise ValueError("open_media_host_forbidden")
        with outbound_scope(deadline):
            transport = pinned_transport(current, allow_private=_proxy_fake_ip(parsed.hostname))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            transport.close()
            raise ValueError("open_media_deadline")
        with (
            outbound_scope(deadline),
            httpx.Client(timeout=min(30, remaining), follow_redirects=False, trust_env=False, transport=transport) as client,
            client.stream("GET", current, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity", **(headers or {})}) as response,
        ):
            if response.status_code in {301, 302, 303, 307, 308}:
                current = str(httpx.URL(current).join(response.headers["location"]))
                continue
            response.raise_for_status()
            if response.headers.get("content-encoding", "identity").strip().lower() != "identity":
                raise ValueError("open_media_compressed")
            if int(response.headers.get("content-length", "0") or 0) > limit:
                raise ValueError("open_media_too_large")
            chunks, total = [], 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > limit or time.monotonic() > deadline:
                    raise ValueError("open_media_too_large")
                chunks.append(chunk)
            return b"".join(chunks), response.headers.get("content-type", "").split(";")[0].strip()
    raise ValueError("open_media_redirects")


def _json(url: str, hosts: set[str], headers: dict | None = None) -> dict:
    content, mime = open_get(url, hosts=hosts, policy="open_media", max_bytes=3_000_000, headers=headers)
    if "json" not in mime:
        raise ValueError("open_media_metadata_invalid")
    return json.loads(content)


def _text(value, maximum=300) -> str:
    return re.sub(r"\s+", " ", value).strip()[:maximum] if isinstance(value, str) else ""


def _orientation(width: int | None, height: int | None) -> str | None:
    if not width or not height:
        return None
    ratio = width / height
    return "portrait" if ratio < 0.9 else "landscape" if ratio > 1.1 else "square"


class OpenMediaProvider:
    key = ""
    version = "1"
    label = ""
    # Libraries the user cannot get a key for stay out of pages and default runs until one is configured.
    hidden_unless_configured = False
    media_types: frozenset = frozenset()
    download_hosts: set[str] | None = None
    needs_key = "none"  # none | optional | required
    env_field = ""
    about = {}

    def _stored(self) -> dict:
        from .. import runtime_config

        return (runtime_config.get_runtime(SETTINGS_KEY) or {}).get(self.key) or {}

    def api_key(self) -> str:
        stored = self._stored()
        if "api_key" in stored:
            return stored["api_key"] or ""
        return getattr(get_settings(), self.env_field, "") if self.env_field else ""

    def enabled(self) -> bool:
        return self._stored().get("enabled", True) is not False

    def configured(self) -> bool:
        return self.needs_key != "required" or bool(self.api_key())

    def runtime_fingerprint(self) -> str:
        code = b"".join(marshal.dumps(getattr(type(self), name).__code__, 2) for name in ("find", "fetch") if hasattr(type(self), name))
        return hashlib.sha256(f"{self.key}:{self.version}".encode() + code + marshal.dumps(open_get.__code__, 2)).hexdigest()

    def find(self, query: str, media_type: str, orientation: str | None, limit: int) -> list[dict]:
        raise NotImplementedError

    def fetch(self, payload: dict) -> providers.MediaOutput:
        content, mime = open_get(payload["download_url"], hosts=self.download_hosts, policy="open_media_download", max_bytes=DOWNLOAD_BYTES)
        expected = payload.get("mime_type")
        return providers.MediaOutput("succeeded", content, expected if expected and mime in {expected, "application/octet-stream", "binary/octet-stream"} else mime)

    def hit(self, **values) -> dict:
        values.setdefault("tags", [])
        values["provider"] = self.key
        values["license"]["accept_code"] = ACCEPT_CODES[values["license"]["code"]]
        values["license"].setdefault("name", LICENSE_NAMES.get(values["license"]["code"], values["license"]["code"]))
        return values


class PexelsProvider(OpenMediaProvider):
    key, label = "stock.pexels", "Pexels"
    hidden_unless_configured = True
    media_types = frozenset({"image", "video"})
    download_hosts = {"images.pexels.com", "videos.pexels.com", "player.vimeo.com", "vod-progressive.akamaized.net"}
    needs_key, env_field = "required", "pexels_api_key"
    about = {"blurb": "生活方式、人物、城市、自然的高清视频和图片，竖拍较多", "license": "Pexels 许可：可商用，不强制署名",
             "signup": "https://www.pexels.com/api/"}

    def find(self, query, media_type, orientation, limit):
        params = {"query": query, "per_page": min(limit, 30), **({"orientation": orientation} if orientation else {})}
        headers = {"Authorization": self.api_key()}
        terms = {"code": "pexels", "url": "https://www.pexels.com/license/"}
        if media_type == "image":
            data = _json("https://api.pexels.com/v1/search?" + urlencode(params), {"api.pexels.com"}, headers)
            return [self.hit(source_id=f"pexels.photo.{item['id']}", title=_text(item.get("alt")) or f"Pexels 照片 {item['id']}",
                             media_type="image", width=item.get("width"), height=item.get("height"), duration_ms=None,
                             page_url=item.get("url"), thumb_url=item["src"].get("medium"), download_url=item["src"].get("large2x"),
                             mime_type="image/jpeg", creator=_text(item.get("photographer")), license=dict(terms),
                             attribution_text=f"Photo by {_text(item.get('photographer'))} on Pexels")
                    for item in data.get("photos", []) if isinstance(item, dict) and item.get("src")]
        data = _json("https://api.pexels.com/videos/search?" + urlencode(params), {"api.pexels.com"}, headers)
        hits = []
        for item in data.get("videos", []):
            files = [entry for entry in item.get("video_files", []) if entry.get("file_type") == "video/mp4" and entry.get("width") and entry.get("height")]
            if not files:
                continue
            user = item.get("user") or {}
            hits.append(self.hit(source_id=f"pexels.video.{item['id']}", title=_text(item.get("url", "").rstrip("/").rsplit("/", 1)[-1].replace("-", " ")) or f"Pexels 视频 {item['id']}",
                                 media_type="video", width=item.get("width"), height=item.get("height"), duration_ms=int(item.get("duration") or 0) * 1000 or None,
                                 page_url=item.get("url"), thumb_url=item.get("image"), files=[{"url": entry["link"], "width": entry["width"], "height": entry["height"]} for entry in files],
                                 mime_type="video/mp4", creator=_text(user.get("name")), license=dict(terms),
                                 attribution_text=f"Video by {_text(user.get('name'))} on Pexels"))
        return hits


class PixabayProvider(OpenMediaProvider):
    key, label = "stock.pixabay", "Pixabay"
    media_types = frozenset({"image", "video"})
    download_hosts = {"pixabay.com", "cdn.pixabay.com"}
    needs_key, env_field = "required", "pixabay_api_key"
    about = {"blurb": "视频、图片、插画，题材广", "license": "Pixabay 内容许可：可商用", "signup": "https://pixabay.com/api/docs/"}

    def find(self, query, media_type, orientation, limit):
        params = {"key": self.api_key(), "q": query[:100], "per_page": max(3, min(limit, 50)), "safesearch": "true",
                  **({"lang": "zh"} if re.search(r"[一-鿿]", query) else {})}
        terms = {"code": "pixabay", "url": "https://pixabay.com/service/license-summary/"}
        if media_type == "image":
            if orientation in {"portrait", "landscape"}:
                params["orientation"] = "vertical" if orientation == "portrait" else "horizontal"
            data = _json("https://pixabay.com/api/?" + urlencode({**params, "image_type": "photo"}), {"pixabay.com"})
            return [self.hit(source_id=f"pixabay.photo.{item['id']}", title=_text(item.get("tags")) or f"Pixabay 图片 {item['id']}",
                             tags=[tag.strip() for tag in str(item.get("tags", "")).split(",") if tag.strip()][:12],
                             media_type="image", width=item.get("imageWidth"), height=item.get("imageHeight"), duration_ms=None,
                             page_url=item.get("pageURL"), thumb_url=item.get("webformatURL"), download_url=item.get("largeImageURL"),
                             mime_type="image/jpeg", creator=_text(item.get("user")), license=dict(terms),
                             attribution_text=f"Image by {_text(item.get('user'))} from Pixabay")
                    for item in data.get("hits", []) if isinstance(item, dict) and item.get("largeImageURL")]
        data = _json("https://pixabay.com/api/videos/?" + urlencode(params), {"pixabay.com"})
        hits = []
        for item in data.get("hits", []):
            variants = item.get("videos") or {}
            files = [{"url": entry["url"], "width": entry["width"], "height": entry["height"], "size": entry.get("size")}
                     for entry in variants.values() if isinstance(entry, dict) and entry.get("url") and entry.get("width")]
            if not files:
                continue
            largest = max(files, key=lambda entry: entry["width"] * entry["height"])
            thumb = next((variants[size]["thumbnail"] for size in ("tiny", "small", "medium", "large")
                          if isinstance(variants.get(size), dict) and variants[size].get("thumbnail")), None)
            hits.append(self.hit(source_id=f"pixabay.video.{item['id']}", title=_text(item.get("tags")) or f"Pixabay 视频 {item['id']}",
                                 tags=[tag.strip() for tag in str(item.get("tags", "")).split(",") if tag.strip()][:12],
                                 media_type="video", width=largest["width"], height=largest["height"], duration_ms=int(item.get("duration") or 0) * 1000 or None,
                                 page_url=item.get("pageURL"), thumb_url=thumb, files=files, mime_type="video/mp4",
                                 creator=_text(item.get("user")), license=dict(terms), attribution_text=f"Video by {_text(item.get('user'))} from Pixabay"))
        return hits


class OpenverseProvider(OpenMediaProvider):
    key, label = "stock.openverse", "Openverse"
    media_types = frozenset({"image"})
    download_hosts = None
    needs_key, env_field = "optional", "openverse_api_token"
    about = {"blurb": "聚合多个开放库的图片；不填令牌也能用，填了限额更高", "license": "只取 CC0、公有领域、CC BY，逐条登记",
             "signup": "https://api.openverse.org/v1/#tag/auth"}

    def find(self, query, media_type, orientation, limit):
        params = {"q": query[:200], "page_size": min(limit, 20), "license": "cc0,pdm,by", "mature": "false",
                  **({"aspect_ratio": {"portrait": "tall", "landscape": "wide", "square": "square"}[orientation]} if orientation else {})}
        token = self.api_key()
        data = _json("https://api.openverse.org/v1/images/?" + urlencode(params), {"api.openverse.org"},
                     {"Authorization": f"Bearer {token}"} if token else None)
        hits = []
        for item in data.get("results", []):
            code = str(item.get("license", "")).lower()
            version = str(item.get("license_version") or "")
            if code not in {"cc0", "pdm", "by"} or not item.get("url"):
                continue
            license_code = "by-4.0" if code == "by" and version == "4.0" else code
            hits.append(self.hit(source_id=f"openverse.{item['id']}", title=_text(item.get("title")) or "Openverse 图片",
                                 tags=[_text(tag.get("name"), 60) for tag in item.get("tags") or [] if isinstance(tag, dict)][:12],
                                 media_type="image", width=item.get("width"), height=item.get("height"), duration_ms=None,
                                 page_url=item.get("foreign_landing_url"), thumb_url=item.get("thumbnail"), download_url=item.get("url"),
                                 mime_type=None, creator=_text(item.get("creator")),
                                 license={"code": license_code, "url": item.get("license_url"), "version": version},
                                 attribution_text=_text(item.get("attribution"), 1000) or None))
        return hits


class NasaProvider(OpenMediaProvider):
    key, label = "stock.nasa", "NASA Images"
    media_types = frozenset({"image", "video"})
    download_hosts = {"images-assets.nasa.gov", "images-api.nasa.gov"}
    about = {"blurb": "太空、地球、航天器、科学影像", "license": "NASA 媒体使用准则：一般可用，不能暗示 NASA 背书", "signup": ""}

    def find(self, query, media_type, orientation, limit):
        params = {"q": query[:200], "media_type": media_type, "page_size": min(limit, 20)}
        data = _json("https://images-api.nasa.gov/search?" + urlencode(params), {"images-api.nasa.gov"})
        hits = []
        for item in (data.get("collection") or {}).get("items", [])[:limit]:
            meta = (item.get("data") or [{}])[0]
            nasa_id = meta.get("nasa_id")
            thumb = next((link.get("href") for link in item.get("links") or [] if link.get("rel") == "preview"), None)
            if not nasa_id or not thumb:
                continue
            quoted = str(nasa_id).replace(" ", "%20")
            download = (f"https://images-assets.nasa.gov/image/{quoted}/{quoted}~large.jpg" if media_type == "image"
                        else f"https://images-assets.nasa.gov/video/{quoted}/{quoted}~medium.mp4")
            hits.append(self.hit(source_id=f"nasa.{nasa_id}", title=_text(meta.get("title")) or str(nasa_id),
                                 tags=[_text(tag, 60) for tag in meta.get("keywords") or []][:12], description=_text(meta.get("description"), 600),
                                 media_type=media_type, width=None, height=None, duration_ms=None,
                                 page_url=f"https://images.nasa.gov/details/{quoted}", thumb_url=thumb, download_url=download,
                                 mime_type="image/jpeg" if media_type == "image" else "video/mp4", creator=_text(meta.get("center")) or "NASA",
                                 license={"code": "nasa", "url": "https://www.nasa.gov/nasa-brand-center/images-and-media/"},
                                 attribution_text=f"Courtesy of NASA ({_text(meta.get('center')) or 'NASA'})"))
        return hits


def _cc_code(url: str | None) -> str | None:
    """Only licenses that allow reuse and editing: CC0, public domain mark and CC BY (any version)."""
    match = re.search(r"creativecommons\.org/(publicdomain/(zero|mark)|licenses/by/(\d\.\d))", url or "")
    if not match:
        return None
    if match.group(2):
        return "cc0" if match.group(2) == "zero" else "pdm"
    return "by-4.0" if match.group(3) == "4.0" else "by"


class InternetArchiveProvider(OpenMediaProvider):
    key, label = "stock.archive", "Internet Archive"
    media_types = frozenset({"image", "video"})
    download_hosts = None
    about = {"blurb": "老影片、历史资料、公有领域影像", "license": "只取 CC0、公有领域、CC BY，逐条登记", "signup": ""}

    def find(self, query, media_type, orientation, limit):
        # Whole items above this size are long recordings whose files cannot fit the acceptance bound anyway.
        params = {"q": f"({query[:200]}) AND mediatype:({'movies' if media_type == 'video' else 'image'}) AND licenseurl:* AND item_size:[1 TO 32000000]",
                  "fl[]": ["identifier", "title", "description", "subject", "licenseurl", "creator"], "rows": min(limit * 4, 50), "output": "json"}
        data = _json("https://archive.org/advancedsearch.php?" + urlencode(params, doseq=True), {"archive.org"})
        hits = []
        for item in (data.get("response") or {}).get("docs", []):
            code = _cc_code(item.get("licenseurl"))
            identifier = item.get("identifier")
            if not code or not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,200}", identifier):
                continue
            subjects = item.get("subject") or []
            creator = item.get("creator")
            creator = _text(creator[0] if isinstance(creator, list) and creator else creator) or "Internet Archive"
            title = _text(item.get("title") if isinstance(item.get("title"), str) else identifier)
            hits.append(self.hit(source_id=f"archive.{identifier}", title=title, media_type=media_type, width=None, height=None, duration_ms=None,
                                 tags=[_text(tag, 60) for tag in (subjects if isinstance(subjects, list) else [subjects])][:12],
                                 description=_text(item.get("description") if isinstance(item.get("description"), str) else "", 600),
                                 page_url=f"https://archive.org/details/{identifier}", thumb_url=f"https://archive.org/services/img/{identifier}",
                                 download_url=f"archive:{identifier}", mime_type="video/mp4" if media_type == "video" else None, creator=creator,
                                 license={"code": code, "url": item.get("licenseurl"),
                                          "name": {"cc0": "CC0 公共领域", "pdm": "公有领域标记", "by-4.0": "CC BY 4.0", "by": "CC BY"}[code]},
                                 attribution_text=f"“{title}” by {creator}, via Internet Archive"))
            if len(hits) >= limit:
                break
        return hits

    def fetch(self, payload):
        identifier = payload["download_url"].removeprefix("archive:")
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,200}", identifier):
            raise ValueError("open_media_url_forbidden")
        files = _json(f"https://archive.org/metadata/{identifier}", {"archive.org"}).get("files", [])
        video = payload.get("mime_type") == "video/mp4"
        suffixes = (".mp4",) if video else (".jpg", ".jpeg", ".png")
        usable = [entry for entry in files if str(entry.get("name", "")).lower().endswith(suffixes) and "thumb" not in str(entry.get("format", "")).lower()
                  and 0 < int(entry.get("size") or 0) <= DOWNLOAD_BYTES and "/" not in str(entry.get("name"))]
        if not usable:
            raise ValueError("open_media_too_large")
        chosen = max(usable, key=lambda entry: int(entry["size"]))
        content, mime = open_get(f"https://archive.org/download/{identifier}/{chosen['name']}", hosts=None, policy="open_media_download", max_bytes=DOWNLOAD_BYTES)
        expected = "video/mp4" if video else "image/png" if chosen["name"].lower().endswith(".png") else "image/jpeg"
        return providers.MediaOutput("succeeded", content, expected if mime in {expected, "application/octet-stream", "binary/octet-stream", ""} else mime)


def _commons_code(short_name: str) -> str | None:
    name = (short_name or "").strip().lower()
    if not name or any(tag in name for tag in ("sa", "nc", "nd")) and "cc" in name:
        return None
    if name.startswith(("public domain", "pd")) or name == "no restrictions":
        return "pdm"
    if name.startswith("cc0"):
        return "cc0"
    match = re.fullmatch(r"cc[ -]by[ -](\d\.\d)", name)
    if match:
        return "by-4.0" if match.group(1) == "4.0" else "by"
    return None


class CommonsAdapter(OpenMediaProvider):
    """Wikimedia Commons stills; historical public-domain material is common here, so licenses are read per file."""
    key, label = "stock.commons", "Wikimedia Commons"
    media_types = frozenset({"image"})
    download_hosts = {"upload.wikimedia.org"}
    about = {"blurb": "地点、历史、科普、实物的图片", "license": "只取 CC0、CC BY 4.0，逐条登记", "signup": ""}

    def find(self, query, media_type, orientation, limit):
        params = {"action": "query", "format": "json", "formatversion": "2", "generator": "search", "gsrnamespace": "6",
                  "gsrsearch": f"{query[:200]} filetype:bitmap", "gsrlimit": min(limit * 3, 30), "prop": "imageinfo",
                  "iiprop": "url|mime|size|sha1|extmetadata", "iiurlwidth": "480",
                  "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|ImageDescription|ObjectName"}
        data = _json("https://commons.wikimedia.org/w/api.php?" + urlencode(params), {"commons.wikimedia.org"})
        hits = []
        for page in (data.get("query") or {}).get("pages", []):
            info = (page.get("imageinfo") or [{}])[0]
            meta = info.get("extmetadata") or {}
            value = lambda key: _plain((meta.get(key) or {}).get("value", ""))
            code = _commons_code(value("LicenseShortName"))
            if (code is None or info.get("mime") not in {"image/jpeg", "image/png", "image/webp"}
                    or not 0 < int(info.get("size") or 0) <= DOWNLOAD_BYTES or not re.fullmatch(r"[0-9a-f]{40}", info.get("sha1") or "")):
                continue
            artist = value("Artist")[:200] or "Wikimedia Commons"
            title = _text(value("ObjectName") or str(page.get("title", "")).removeprefix("File:"))
            hits.append(self.hit(source_id=f"commons.{page['pageid']}", title=title, media_type="image",
                                 width=info.get("width"), height=info.get("height"), duration_ms=None,
                                 description=_text(value("ImageDescription"), 600), page_url=info.get("descriptionurl"),
                                 thumb_url=info.get("thumburl"), download_url=info.get("url"), mime_type=info["mime"], source_sha1=info["sha1"],
                                 creator=artist, license={"code": code, "url": value("LicenseUrl") or None,
                                                          "name": {"pdm": "公有领域", "cc0": "CC0", "by-4.0": "CC BY 4.0", "by": value("LicenseShortName")}[code]},
                                 attribution_text=f"{title} — {artist}, via Wikimedia Commons ({value('LicenseShortName')})"))
            if len(hits) >= limit:
                break
        return hits

    def fetch(self, payload):
        content, mime = open_get(payload["download_url"], hosts=self.download_hosts, policy="open_media_download", max_bytes=DOWNLOAD_BYTES)
        if payload.get("source_sha1") and hashlib.sha1(content).hexdigest() != payload["source_sha1"]:
            raise ValueError("open_media_source_changed")
        return providers.MediaOutput("succeeded", content, payload.get("mime_type") or mime)


def _plain(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value or "")).strip()


class CoverrProvider(OpenMediaProvider):
    key, label = "stock.coverr", "Coverr"
    hidden_unless_configured = True
    media_types = frozenset({"video"})
    download_hosts = None
    needs_key = "required"
    about = {"blurb": "竖屏和横屏的短视频空镜：生活、科技、办公", "license": "Coverr 许可：可商用，不强制署名",
             "signup": "mailto:team@coverr.co"}

    def find(self, query, media_type, orientation, limit):
        if media_type != "video":
            return []
        params = {"query": query[:100], "page_size": min(limit, 20), "urls": "true"}
        data = _json("https://api.coverr.co/videos?" + urlencode(params), {"api.coverr.co"}, {"Authorization": f"Bearer {self.api_key()}"})
        hits = []
        for item in data.get("hits", []):
            urls = item.get("urls") or {}
            # mp4_download saves the file directly, which Coverr counts itself; the preview mp4 would need a stats ping.
            if not isinstance(item, dict) or not item.get("id") or not urls.get("mp4_download"):
                continue
            hits.append(self.hit(source_id=f"coverr.{item['id']}", title=_text(item.get("title")) or f"Coverr 视频 {item['id']}",
                                 tags=[_text(tag, 60) for tag in item.get("tags") or [] if isinstance(tag, str)][:12],
                                 media_type="video", width=item.get("max_width"), height=item.get("max_height"),
                                 duration_ms=int(float(item.get("duration") or 0) * 1000) or None,
                                 page_url=f"https://coverr.co/videos/{item['id']}", thumb_url=item.get("thumbnail") or item.get("poster"),
                                 download_url=urls["mp4_download"], mime_type="video/mp4", creator="Coverr",
                                 license={"code": "coverr", "url": "https://coverr.co/license"}, attribution_text="Video from Coverr"))
        return hits


PROVIDERS: dict[str, OpenMediaProvider] = {provider.key: provider for provider in
                                           (PixabayProvider(), InternetArchiveProvider(), CommonsAdapter(), OpenverseProvider(), NasaProvider(),
                                            PexelsProvider(), CoverrProvider())}


def register(registry) -> None:
    for provider in PROVIDERS.values():
        if provider.key not in {entry.key for entry in registry.list("stock_provider")}:
            registry.register("stock_provider", provider.key, provider.version, provider, label=f"{provider.label} (rights acceptance required)")


def status() -> list[dict]:
    return [{"key": provider.key, "label": provider.label, "media_types": sorted(provider.media_types), "configured": provider.configured()}
            for provider in visible()]


def visible() -> list[OpenMediaProvider]:
    return [provider for provider in PROVIDERS.values()
            if provider.enabled() and (provider.configured() or not provider.hidden_unless_configured)]


def settings_view() -> list[dict]:
    from .system_settings import mask_secret

    rows = []
    for provider in PROVIDERS.values():
        stored = provider._stored()
        rows.append({"key": provider.key, "label": provider.label, "media_types": sorted(provider.media_types), **provider.about,
                     "needs_key": provider.needs_key, "api_key": mask_secret(provider.api_key()) if provider.needs_key != "none" else None,
                     "key_from": "page" if "api_key" in stored else "env" if provider.api_key() else None,
                     "enabled": provider.enabled(), "configured": provider.configured()})
    return rows


def save_settings(db, changes: dict, updated_by: str) -> None:
    """Only listed fields change: an omitted api_key keeps the current one, an empty string clears it."""
    from fastapi import HTTPException

    from .. import runtime_config
    from ..models import SystemSetting

    if set(changes) - set(PROVIDERS):
        raise HTTPException(422, {"code": "open_media_source_unknown"})
    row = db.get(SystemSetting, SETTINGS_KEY)
    value = {key: dict(item) for key, item in ((row.value or {}) if row else {}).items()}
    for key, change in changes.items():
        entry = value.setdefault(key, {})
        if "enabled" in change:
            entry["enabled"] = bool(change["enabled"])
        if "api_key" in change and PROVIDERS[key].needs_key != "none":
            entry["api_key"] = change["api_key"].strip()
    runtime_config.validate_persisted_configuration(value)
    if row is None:
        row = SystemSetting(key=SETTINGS_KEY)
        db.add(row)
    row.value, row.updated_by = value, updated_by
    db.flush()
    runtime_config.set_runtime(SETTINGS_KEY, value)


def test_source(key: str) -> dict:
    """One small search, no download, so a key can be checked without importing anything."""
    provider = PROVIDERS.get(key)
    if provider is None:
        return {"ok": False, "reason": "open_media_source_unknown"}
    if not provider.configured():
        return {"ok": False, "reason": "未配置 Key"}
    media_type = "video" if "video" in provider.media_types else "image"
    started = time.monotonic()
    try:
        hits = provider.find("ocean", media_type, None, 3)
    except Exception as exc:  # noqa: BLE001 - the page shows why, never the key
        return {"ok": False, "reason": _test_reason(exc), "elapsed_ms": int((time.monotonic() - started) * 1000)}
    return {"ok": True, "hits": len(hits), "elapsed_ms": int((time.monotonic() - started) * 1000)}


def _test_reason(exc: Exception) -> str:
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status in {401, 403}:
        return "Key 无效或没有权限"
    if status == 429:
        return "请求太频繁，稍后再试"
    if isinstance(exc, httpx.TimeoutException):
        return "连接超时"
    return type(exc).__name__


def choose_file(hit: dict, min_short_side: int) -> dict | None:
    """Smallest rendition that still meets the requested short side keeps downloads within the acceptance bound."""
    files = hit.get("files")
    if not files:
        return {"url": hit.get("download_url"), "width": hit.get("width"), "height": hit.get("height")} if hit.get("download_url") else None
    usable = [entry for entry in files if min(entry["width"], entry["height"]) >= min_short_side and (entry.get("size") or 0) <= DOWNLOAD_BYTES]
    if usable:
        return min(usable, key=lambda entry: entry["width"] * entry["height"])
    fitting = [entry for entry in files if (entry.get("size") or 0) <= DOWNLOAD_BYTES]
    return max(fitting, key=lambda entry: entry["width"] * entry["height"]) if fitting else None
