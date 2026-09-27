"""统一 Plugin Registry（D6/§6.3）：node/rule/renderer/publisher/asset_provider/material_search/skill_runtime。

同一 (kind, key, version) 重复注册直接报错；resolve 按 version 精确解析（版本钉死）。
"""

from __future__ import annotations

from .contracts import PluginDescriptor

RegistryKinds = (
    "node",
    "rule",
    "renderer",
    "publisher",
    "asset_provider",
    "material_search",
    "skill_runtime",
)


class RegistryError(Exception):
    pass


class PluginRegistry:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str, str], object] = {}
        self._descriptors: dict[tuple[str, str, str], PluginDescriptor] = {}

    def register(
        self,
        kind: str,
        key: str,
        version: str,
        provider: object,
        *,
        label: str | None = None,
        human_gate: bool = False,
        side_effect: bool = False,
    ) -> None:
        if kind not in RegistryKinds:
            raise RegistryError(f"未知 registry kind: {kind}")
        token = (kind, key, str(version))
        if token in self._items:
            raise RegistryError(f"plugin 重复注册: {kind}/{key}@{version}")
        self._items[token] = provider
        self._descriptors[token] = PluginDescriptor(
            kind=kind, key=key, version=str(version), label=label, human_gate=human_gate, side_effect=side_effect
        )

    def resolve(self, kind: str, key: str, version: str | None = None) -> object:
        token = (kind, key, str(version or "1"))
        if token not in self._items:
            raise RegistryError(f"plugin 未注册: {kind}/{key}@{token[2]}")
        return self._items[token]

    def descriptor(self, kind: str, key: str, version: str | None = None) -> PluginDescriptor:
        token = (kind, key, str(version or "1"))
        if token not in self._descriptors:
            raise RegistryError(f"plugin 未注册: {kind}/{key}@{token[2]}")
        return self._descriptors[token]

    def list(self, kind: str) -> list[PluginDescriptor]:
        return [d for (k, _key, _v), d in sorted(self._descriptors.items()) if k == kind]


registry = PluginRegistry()


def register(kind: str, key: str, version: str, provider: object, **meta) -> None:
    """模块级便捷入口。"""
    registry.register(kind, key, version, provider, **meta)


def resolve(kind: str, key: str, version: str | None = None) -> object:
    return registry.resolve(kind, key, version)


def descriptor(kind: str, key: str, version: str | None = None) -> PluginDescriptor:
    return registry.descriptor(kind, key, version)
