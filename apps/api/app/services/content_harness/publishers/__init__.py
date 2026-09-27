"""Publisher Registry（D23）：唯一远端副作用入口的插件层。

capability() 必须如实报告（unverified 平台不得显示为 verified 自动发布）；
deliver() 只消费批准 render payload，不得修改 title/正文/封面（D24）。
"""

from __future__ import annotations

from ..registry import registry
from .base import PublisherPlugin
from .copy_package import CopyPackagePublisher
from .wechat_wewrite import WechatWewritePublisher

__all__ = ["CopyPackagePublisher", "PublisherPlugin", "WechatWewritePublisher", "bootstrap_publishers"]

_BOOTSTRAPPED = False


def bootstrap_publishers() -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    for plugin in (CopyPackagePublisher(), WechatWewritePublisher()):
        if plugin.key not in {d.key for d in registry.list("publisher")}:
            registry.register(
                "publisher", plugin.key, plugin.version, plugin,
                label=plugin.key, side_effect=plugin.key != "publisher.copy",
            )
    _BOOTSTRAPPED = True
