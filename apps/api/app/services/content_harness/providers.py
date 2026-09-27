"""媒体 Provider 注册（D17/§6.15/2.8–2.9）。

- asset_provider：生图 provider（首批 = wewrite image-gen 薄包装，旧函数继续可用）；
- material_search：素材搜索 provider 契约。V1 无内置实现——未配置时上层 API
  返回 422 capability_unavailable，绝不返回假数据。
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .contracts import MaterialSearchResult
from .registry import registry


class AssetProvider(Protocol):
    key: str
    version: str

    def generate(self, prompt: str, out_path: Path) -> bool: ...


class WewriteImageProvider:
    """wewrite image-gen 薄包装：生图未启用/失败返回 False，由调用方降级。"""

    key = "asset_provider.wewrite_image"
    version = "1"

    def generate(self, prompt: str, out_path: Path) -> bool:
        from ...services.writing_pipeline import generate_cover_image

        return generate_cover_image(prompt, out_path)


class MaterialSearchProvider(Protocol):
    key: str
    version: str

    def search(self, query: str, limit: int = 10) -> MaterialSearchResult: ...


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
    if "asset_provider.wewrite_image" not in {d.key for d in registry.list("asset_provider")}:
        registry.register(
            "asset_provider", "asset_provider.wewrite_image", "1", WewriteImageProvider(), label="wewrite AI 生图"
        )
    # material_search 不注册内置实现：能力显式不可用
