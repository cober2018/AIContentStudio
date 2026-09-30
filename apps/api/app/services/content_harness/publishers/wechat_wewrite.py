"""publisher.wechat.wewrite@1（D24）：公众号草稿箱自动创建（wewrite CLI）。

- 只消费批准 render payload（title/digest/markdown/cover 来自 manifest），不得临时改写；
  平台长度限制不满足时 fail（candidate invalid → 用户修订 → re-render → re-approve）；
- 超时无法确认 → status=unknown（不自动重发，走 reconcile）；
- 真实远端测试不进默认 pytest（手工 acceptance script）。
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ..contracts import PublisherCapability, PublisherResult

WEWRITE_TIMEOUT_SEC = 180


class WechatWewritePublisher:
    key = "publisher.wechat.wewrite"
    version = "1"

    def capability(self, channel: str, content_form: str, account_ref: str) -> PublisherCapability:
        if channel != "wechat":
            return PublisherCapability(
                publisher_key=self.key, channel=channel, content_form=content_form,
                action="auto_draft", available=False, reason="publisher 仅支持 wechat",
            )
        return PublisherCapability(
            publisher_key=self.key, channel=channel, content_form=content_form,
            action="auto_draft", available=True,
            reason=None,
        )

    def verified(self) -> bool:
        """真实账号验证状态：V1 未完成真实发布验证 → unverified（PRD：不得伪装 verified）。"""
        return False

    def deliver(self, manifest: dict[str, Any], target, attempt) -> PublisherResult:
        render = (manifest or {}).get("render") or {}
        payload = render.get("payload") or {}
        title = payload.get("title")
        markdown = payload.get("markdown")
        if not title or not markdown:
            return PublisherResult(status="failed", error="render payload 缺少 title/markdown（candidate invalid）")
        if len(title) > 64:
            # D24：不临时截断——candidate 需修订后重新批准
            return PublisherResult(status="failed", error=f"标题超公众号 64 字限制（{len(title)}），请修订候选后重新批准")
        # R2-B3：digest 只取批准载荷，禁止截断改写（截断值未进 candidate hash）
        digest = payload.get("digest") or title
        if len(digest) > 120:
            return PublisherResult(status="failed", error=f"摘要超公众号 120 字限制（{len(digest)}），请修订候选后重新批准")
        # R2-B3：无已批准封面字节 → fail（candidate blocker → 回 Review Center 补图 → 新 Candidate），
        # 禁止现场生成 placeholder 冒充已批准媒体
        cover_bytes = (manifest.get("_cover_bytes") or b"")  # delivery 层注入（已批准媒体字节）
        if not cover_bytes:
            return PublisherResult(status="failed", error="缺少已批准封面（media_requirements cover=required），请回审核中心补图后重新批准")
        with tempfile.TemporaryDirectory() as tmp:
            md_path = Path(tmp) / "article.md"
            md_path.write_text(markdown, encoding="utf-8")
            cover_suffix = ".jpg" if manifest.get("_cover_mime") == "image/jpeg" else ".png"
            cover_path = Path(tmp) / f"cover{cover_suffix}"
            cover_path.write_bytes(cover_bytes)
            cmd = [
                "wewrite", "publish", str(md_path),
                "--cover", str(cover_path), "--title", title, "--digest", digest,
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=WEWRITE_TIMEOUT_SEC, check=False)
            except subprocess.TimeoutExpired:
                return PublisherResult(status="unknown", error=f"wewrite 超时（{WEWRITE_TIMEOUT_SEC}s），远端结果未确认")
            if proc.returncode != 0:
                return PublisherResult(status="failed", error="publisher_execution_failed")
            match = re.search(r"Draft created! media_id: ([A-Za-z0-9_-]{1,128})(?:\s|$)", proc.stdout or "")
            if match is None:
                return PublisherResult(status="unknown", error="publisher_result_unconfirmed")
        media_id = match.group(1)
        return PublisherResult(
            status="succeeded", remote_id=media_id,
            metadata={"channel": "wechat", "verified": self.verified(), "draft_box": True},
        )
