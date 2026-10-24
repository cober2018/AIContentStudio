"""Finance / tech wording patterns that channel variant checks look for (deterministic, no LLM)."""

from __future__ import annotations

import re

# 收益保证类禁止表述（雪球等财经形态）
FINANCE_FORBIDDEN_PATTERNS = [
    r"保证[收本]?收益", r"稳赚", r"必涨", r"包赚", r"零风险.{0,6}(收益|回报)", r"确定(性)?获得.{0,6}收益",
]
# 代码可信标注模式（掘金）
VERIFIED_RUNNABLE_PATTERN = re.compile(r"verified[-_ ]?runnable", re.IGNORECASE)
