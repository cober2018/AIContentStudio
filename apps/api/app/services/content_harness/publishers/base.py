"""Publisher 插件契约（D23）。"""

from __future__ import annotations

from typing import Any, Protocol

from ..contracts import PublisherCapability, PublisherResult


class PublisherPlugin(Protocol):
    key: str
    version: str

    def capability(self, channel: str, content_form: str, account_ref: str) -> PublisherCapability: ...

    def deliver(self, manifest: dict[str, Any], target, attempt) -> PublisherResult: ...
