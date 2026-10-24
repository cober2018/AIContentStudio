"""媒体 Provider 注册（D17/§6.15/2.8–2.9）。

- asset_provider：生图 provider（首批 = wewrite image-gen 薄包装，旧函数继续可用）；
- material_search：素材搜索 provider 契约。V1 无内置实现——未配置时上层 API
  返回 422 capability_unavailable，绝不返回假数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .contracts import MaterialSearchResult
from .registry import registry


class AssetProvider(Protocol):
    key: str
    version: str

    def generate(self, prompt: str, out_path: Path) -> bool: ...


@dataclass(frozen=True, slots=True)
class MediaOutput:
    status: str
    content: bytes = b""
    mime_type: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MediaRenderOutput:
    status: str
    content: bytes = b""
    mime_type: str | None = None
    render_input_hash: str | None = None
    canvas_id: str | None = None
    metadata: dict = field(default_factory=dict)


class MediaRenderer(Protocol):
    key: str
    version: str
    modality: str
    schema: str
    output_mimes: tuple[str, ...]
    supported_forms: tuple[tuple[str, str], ...]
    def runtime_fingerprint(self) -> str | None: ...
    def render_master(self, request: dict) -> MediaRenderOutput: ...


class ImageProvider(Protocol):
    key: str
    version: str
    def runtime_fingerprint(self) -> str | None: ...
    def generate(self, request: dict) -> MediaOutput: ...


class VideoProvider(ImageProvider, Protocol):
    pass


class TTSProvider(ImageProvider, Protocol):
    pass


class ASRProvider(Protocol):
    key: str
    version: str
    def runtime_fingerprint(self) -> str | None: ...
    def transcribe(self, request: dict) -> dict: ...


class WewriteImageProvider:
    """wewrite image-gen 薄包装：生图未启用/失败返回 False，由调用方降级。"""

    key = "asset_provider.wewrite_image"
    version = "1"

    def runtime_fingerprint(self) -> str | None:
        # Installed CLI retries uncertain calls and reads mutable global config.
        # A launcher hash cannot attest the actual model, endpoint or credentials.
        return None

    def generate(self, prompt: str | dict, out_path: Path | None = None) -> bool | MediaOutput:
        if isinstance(prompt, dict):
            return MediaOutput("unavailable")
        from ...services.writing_pipeline import generate_cover_image

        return generate_cover_image(prompt, out_path)


class MaterialSearchProvider(Protocol):
    key: str
    version: str

    def search(self, query: str, limit: int = 10) -> MaterialSearchResult: ...


class SearchProvider(MaterialSearchProvider, Protocol):
    def runtime_fingerprint(self) -> str | None: ...
    def fetch(self, candidate: dict) -> MediaOutput: ...


class CapabilityUnavailable(LookupError):
    """要求的 capability 没有已配置 provider（上层映射 422 capability_unavailable）。"""


def resolve_asset_provider() -> AssetProvider:
    try:
        return registry.resolve("asset_provider", "asset_provider.wewrite_image", "1")  # type: ignore[return-value]
    except Exception as exc:
        raise CapabilityUnavailable("asset_provider.wewrite_image 未注册") from exc


def resolve_material_search() -> MaterialSearchProvider:
    """无已配置 Provider 时抛 CapabilityUnavailable（禁止假数据，§6.15）。"""
    try:
        return registry.resolve("material_search", "material_search.web", "1")  # type: ignore[return-value]
    except Exception as exc:
        raise CapabilityUnavailable("未配置可用素材搜索 Provider") from exc


def bootstrap_media_providers() -> None:
    from ..cpa_image_provider import CPAImageProvider
    from ..local_graphic_renderer import LocalGraphicRenderer
    from ..local_mlx_asr_provider import bootstrap as bootstrap_local_asr
    from ..material_search import WikimediaSearchProvider
    from ..minimax_cli_provider import bootstrap as bootstrap_minimax_cli
    from ..native_model_adapters import bootstrap_native_model_adapters
    from ..openai_image_provider import OpenAIImageProvider

    bootstrap_native_model_adapters()
    bootstrap_minimax_cli()
    bootstrap_local_asr(registry)

    if OpenAIImageProvider.key not in {d.key for d in registry.list("image_provider")}:
        registry.register("image_provider", OpenAIImageProvider.key, "1", OpenAIImageProvider(), label="Configured OpenAI image preview (explicit acceptance required)")

    cpa_image = CPAImageProvider()
    if "openai.compatible" not in {d.key for d in registry.list("model_provider")}:
        registry.register("model_provider", "openai.compatible", "1", cpa_image,
                          label="Registered CPA OpenAI-compatible image protocol")
    if cpa_image.key not in {d.key for d in registry.list("image_provider")}:
        registry.register("image_provider", cpa_image.key, "1", cpa_image,
                          label="Registered CPA image generation (explicit acceptance required)")
    for kind in ("model_provider", "image_provider"):
        if ("openai.compatible", "2") not in {(d.key, d.version) for d in registry.list(kind)}:
            registry.register(kind, "openai.compatible", "2", CPAImageProvider("2"),
                              label="Registered CPA Gemini native image protocol (explicit acceptance required)")

    if LocalGraphicRenderer.key not in {d.key for d in registry.list("renderer")}:
        registry.register("renderer", LocalGraphicRenderer.key, "1", LocalGraphicRenderer(), label="Local Graphic Chromium renderer (explicit runtime required)")

    if WikimediaSearchProvider.key not in {d.key for d in registry.list("search_provider")}:
        registry.register("search_provider", WikimediaSearchProvider.key, "1", WikimediaSearchProvider(), label="Wikimedia Commons public search (rights acceptance required)")
    from ..open_media import register as register_open_media

    register_open_media(registry)
    if "asset_provider.wewrite_image" not in {d.key for d in registry.list("asset_provider")}:
        registry.register(
            "asset_provider", "asset_provider.wewrite_image", "1", WewriteImageProvider(), label="wewrite AI 生图"
        )
    if "asset_provider.wewrite_image" not in {d.key for d in registry.list("image_provider")}:
        registry.register("image_provider", "asset_provider.wewrite_image", "1", WewriteImageProvider(), label="WeWrite image preview (acceptance required)")
    # material_search 不注册内置实现：能力显式不可用
