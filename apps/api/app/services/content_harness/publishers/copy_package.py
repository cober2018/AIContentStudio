"""publisher.copy@1（D25）：通用兜底 Publisher——构建本地成品包，不触远端。"""

from __future__ import annotations

from typing import Any

from ..contracts import PublisherCapability, PublisherResult


class CopyPackagePublisher:
    key = "publisher.copy"
    version = "1"

    def capability(self, channel: str, content_form: str, account_ref: str) -> PublisherCapability:
        # 任何渠道都可用：copy package 是 universal fallback（spec: delivery-router-v1）
        return PublisherCapability(
            publisher_key=self.key, channel=channel, content_form=content_form,
            action="copy_package", available=True, reason=None,
        )

    def deliver(self, manifest: dict[str, Any], target, attempt) -> PublisherResult:
        # 包构建在 delivery.build_copy_package 完成（本地字节，无远端调用）；
        # deliver 只负责声明本次"交付动作"完成，等待人工发布后回填 receipt。
        return PublisherResult(
            status="succeeded",
            metadata={"package": True, "remote_call": False, "action": getattr(target, "action", "copy_package")},
        )
