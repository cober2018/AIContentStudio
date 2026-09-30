"""Explicit local browser runtime; previews never attest or save a Master."""

import base64
import hashlib
import io
import json
import os
import re
import signal
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageFont
from PIL import __version__ as pillow_version

from . import graphic_documents
from .content_harness.providers import MediaRenderOutput


class LocalGraphicRenderer:
    key = "graphic.chromium"
    version = "1"
    modality = "graphic"
    schema = "graphic.master.v2"
    output_mimes = ("image/png",)
    supported_forms = (("xiaohongshu", "image_note"),)
    script = Path(__file__).with_name("local_graphic_renderer.cjs")

    def _runtime(self):
        values = [os.environ.get(f"GRAPHIC_RENDER_{key}", "") for key in ("NODE", "BROWSER", "PLAYWRIGHT", "FONT")]
        if not all(values) or not all(Path(value).is_absolute() for value in values):
            raise ValueError("runtime_unconfigured")
        node, browser, package, font = (Path(value).resolve(strict=True) for value in values)
        if not all(path.is_file() for path in (node, browser, font)) or not package.is_dir():
            raise ValueError("runtime_unconfigured")
        # Runtime files are operator configuration, never provider/client paths.
        manifest = json.loads((package / "package.json").read_text())
        if manifest.get("name") != "playwright":
            raise ValueError("runtime_unconfigured")
        core = package.parent / "playwright-core"
        if not core.is_dir() or json.loads((core / "package.json").read_text()).get("name") != "playwright-core":
            raise ValueError("runtime_unconfigured")
        return node, browser, package, core, font

    def runtime_fingerprint(self):
        try:
            node, browser, package, core, font = self._runtime()
            digest = hashlib.sha256(pillow_version.encode())
            paths = [Path(__file__), Path(graphic_documents.__file__), Path(ImageFont.__file__),
                     Path(ImageFont.core.__file__), self.script, node, browser, font]
            if any(parent.suffix == ".app" for parent in browser.parents):
                bundle = next(parent for parent in browser.parents if parent.suffix == ".app")
                paths.extend(sorted(path for path in bundle.rglob("*") if path.is_file()))
            # Include dependency code, not merely its claimed package version.
            for root in (package, core):
                paths.extend(sorted(path for path in root.rglob("*") if path.is_file() and path.suffix in {".js", ".cjs", ".json"}))
            for index, path in enumerate(paths):
                digest.update(str(index).encode())
                digest.update(path.name.encode())
                with path.open("rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        digest.update(chunk)
            return digest.hexdigest()
        except Exception:  # noqa: BLE001 Configuration errors must not expose local paths.
            return None

    def render_master(self, request):
        if self.runtime_fingerprint() is None:
            return MediaRenderOutput("unavailable")
        try:
            node, browser, package, _, font = self._runtime()
            if not re.fullmatch(r"[0-9a-f]{64}", request.get("render_input_hash", "")):
                raise ValueError("invalid_input")
            payload = graphic_documents.canonical_payload(request["payload"])
            canvas = next(item for item in payload["canvases"] if item["id"] == request["canvas_id"])
            if type(canvas["width"]) is not int or type(canvas["height"]) is not int or canvas["width"] * canvas["height"] > 16_000_000:
                raise ValueError("unsupported_dimensions")
            font_bytes = font.read_bytes()
            if not font_bytes or len(font_bytes) > 30 * 1024 * 1024:
                raise ValueError("unsupported_font")
            font_probe = ImageFont.truetype(io.BytesIO(font_bytes), 32)
            missing = bytes(font_probe.getmask("\U0010ffff"))
            for layer in canvas["layers"]:
                if layer["type"] == "text":
                    if len({run["style"]["align"] for run in layer["runs"]}) != 1:
                        raise ValueError("mixed_alignment_unsupported")
                    if any(run["style"]["weight"] != 400 or run["style"]["italic"] for run in layer["runs"]):
                        raise ValueError("font_variant_unsupported")
                    characters = set("".join(run["text"] for run in layer["runs"]))
                    if any(not char.isspace() and bytes(font_probe.getmask(char)) == missing for char in characters):
                        raise ValueError("font_coverage_unsupported")
            assets = {}
            total = 0
            for source in request.get("source_assets", []):
                content = source["content"]
                total += len(content)
                if total > 30 * 1024 * 1024 or source["revision_id"] in assets:
                    raise ValueError("source_budget")
                if hashlib.sha256(content).hexdigest() != source["content_hash"] or source["mime_type"] not in {"image/png", "image/jpeg", "image/webp"}:
                    raise ValueError("source_integrity")
                image = Image.open(io.BytesIO(content))
                if image.width * image.height > 16_000_000 or image.format not in {"PNG", "JPEG", "WEBP"}:
                    raise ValueError("source_integrity")
                image.load()
                if getattr(image, "is_animated", False):
                    raise ValueError("animated_source_unsupported")
                assets[source["revision_id"]] = {"content": base64.b64encode(content).decode(), "mime": source["mime_type"]}
            for layer in canvas["layers"]:
                if layer["type"] in {"image", "chart"} and layer["material_revision_id"] not in assets:
                    raise ValueError("source_missing")
            data = json.dumps({"canvas": canvas, "assets": assets, "font": base64.b64encode(font_bytes).decode()}, ensure_ascii=True).encode()
            with tempfile.TemporaryDirectory(prefix="studio-graphic-render-") as directory:
                output = Path(directory) / "render.png"
                environment = {"PATH": str(node.parent), "HOME": directory, "TMPDIR": directory, "LANG": "en_US.UTF-8"}
                process = subprocess.Popen([str(node), str(self.script), str(package), str(browser), str(output)],
                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    env=environment, start_new_session=True)
                try:
                    process.communicate(data, timeout=25)
                except BaseException:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    raise
                if process.returncode or not output.is_file() or output.stat().st_size > 30 * 1024 * 1024:
                    raise ValueError("render_failed")
                content = output.read_bytes()
            return MediaRenderOutput("succeeded", content, "image/png", request["render_input_hash"], request["canvas_id"])
        except Exception:  # noqa: BLE001 Provider diagnostics are never public runtime paths/errors.
            return MediaRenderOutput("failed")
