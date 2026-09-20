"""写作质量管线：把已验证的 wewrite skills 体系注入 Studio 生成链。

来源与分工（对应 Antigravity「自媒体文章造梦机」真实工作流）：
- style.yaml（~/.wewrite/style.yaml，知数Talk / tech-coder 人格）→ 长文 Prompt 注入
- wewrite-write 五段式叙事 + humanizer-zh 反模式 → Prompt 固化 + humanize 二次精炼节点
- content-censor（new_media/.agents/skills）→ 红黄绿合规审查 + 自动合规改写 + 平台免责声明
- wewrite hotspots / image-gen CLI → 热点注入荐题、AI 封面生成

全部为薄封装：skill/配置缺失时安全降级，不阻断主链。
"""

import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

WEWRITE_HOME = Path.home() / ".wewrite"
STYLE_PATH = WEWRITE_HOME / "style.yaml"
# Antigravity 自媒体项目的 skills 目录（content-censor 等的真正来源）
NEW_MEDIA_SKILLS = Path.home() / "Project" / "new_media" / ".agents" / "skills"
CENSOR_SCRIPTS = NEW_MEDIA_SKILLS / "content-censor" / "scripts"

YELLOW_WORDS = [
    "必看", "惊呆", "震撼", "逆天", "王炸", "杀疯了", "彻底颠覆", "史诗级",
    "风口", "财富自由", "暴富",
]


def load_style() -> dict[str, Any]:
    """读 wewrite 风格配置；缺失/损坏返回空 dict（调用方降级）。"""
    try:
        data = yaml.safe_load(STYLE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, yaml.YAMLError):
        return {}


def style_prompt_block(style: dict[str, Any] | None = None) -> str:
    """风格 + 五段式 + 反 AI 腔指令块（wechat 长文 Prompt 注入）。"""
    style = style if style is not None else load_style()
    if not style:
        return ""
    blacklist = "、".join((style.get("blacklist") or {}).get("words") or [])
    return f"""
【写作人格与风格（必须贯彻全文）】
- 人格：{(style.get('writing_persona') or 'tech-coder')} —— {style.get('voice') or '第一人称工程师'}
- 公众号定位：{style.get('name') or ''}｜受众：{style.get('target_audience') or ''}
- 语气：{style.get('tone') or ''}｜字数：{style.get('word_count') or '2000-3500'}
- 叙事结构（五段闭环，依次为章节主体）：
  1) 痛点引子——一个真实、具体的工程/数据踩坑场景开场，直接进入，不写空泛背景
  2) 根因剖析——问题到底出在哪，数据/代码/流程层面的诚实拆解
  3) 核心架构——我们怎么解决的，讲清取舍与边界，不吹完美方案
  4) 硬规则落地——可直接照做的规则/清单/参数，工程师视角的实操
  5) 反思总结——哪些仍未解决、代价是什么，承认局限
- 语言铁律（去 AI 腔）：
  * 禁用：至关重要、深度赋能、不难看出、值得一提的是、总而言之、赋能、抓手、闭环生态
  * 不用三段式排比、不用金句收尾、不搞二元对比修辞；句长要有变化，两项优于三项
  * 允许并鼓励：第一人称、自嘲、口语、真实的不确定（"我也没完全想明白"）
  * 数字只能来自事实清单，表述时保留原口径与日期
- 禁词（出现即违规）：{blacklist or '（风格未配置）'}
""".strip()


def fetch_hotspots(limit: int = 20) -> list[str]:
    """wewrite hotspots 拉全网热点（荐题 Prompt 注入）；失败返回空列表不阻断。"""
    try:
        proc = subprocess.run(
            ["wewrite", "hotspots", "--limit", str(limit)],
            capture_output=True, text=True, timeout=30, check=False,
        )
        if proc.returncode != 0:
            return []
        lines = [ln.strip().lstrip("-*·0123456789. ").strip() for ln in proc.stdout.splitlines()]
        return [ln for ln in lines if 4 <= len(ln) <= 60][:limit]
    except (OSError, subprocess.SubprocessError):
        return []


def generate_cover_image(prompt: str, out_path: Path) -> bool:
    """wewrite image-gen 生成 16:9 封面（多 provider fallback 由 CLI 内部处理）。"""
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            ["wewrite", "image-gen", "--prompt", prompt, "--output", str(out_path), "--size", "cover"],
            capture_output=True, text=True, timeout=300, check=False,
        )
        return proc.returncode == 0 and out_path.is_file()
    except (OSError, subprocess.SubprocessError):
        return False


HUMANIZE_SYSTEM = """你是资深文字编辑，任务是把一篇技术长文改得更像真人写的。逐段执行：
1. 删除 AI 腔：至关重要/深度赋能/不难看出/值得一提的是/总而言之/赋能/抓手；三段式排比拆成两项或直接陈述；金句收尾改平实陈述
2. 打破公式：句长要有长短变化；段落收尾方式多样化；二元对比（"不是X而是Y"）最多出现一次
3. 注入人味：第一人称视角、真实的犹豫与自嘲（"说实话这里我卡了两天"）、对事实有态度而非中立罗列
4. 铁律：所有数字、日期、专有名词、事实表述一字不改；不增删任何事实；不改变章节结构与标题；篇幅变化不超过 ±15%
输出只包含改写后的全文。"""


def _censor_module():
    """加载 Antigravity content-censor 的 scan_text（词表+合规改写由 skill 维护）。"""
    if not CENSOR_SCRIPTS.is_dir():
        return None
    path_str = str(CENSOR_SCRIPTS)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
    try:
        import censor

        return censor
    except Exception:  # noqa: BLE001  skill 缺依赖时不阻断
        return None


def censor_text(text: str, platform: str = "wechat", style: dict[str, Any] | None = None) -> dict[str, Any]:
    """合规审查：优先用 content-censor skill（红黄绿 + 自动合规改写 + 平台免责声明）。

    返回 result(blocker/warning/pass)、issues、patched_text（自动改写+免责声明后的全文）。
    skill 缺失时降级为内置黄词扫描。
    """
    module = _censor_module()
    if module is not None and hasattr(module, "scan_text"):
        issues, rewritten, _blocked = module.scan_text(text, platform=platform)
        red = [i for i in issues if i.get("level") == "RED"]
        yellow = [i for i in issues if i.get("level") == "YELLOW"]
        disclaimer = (module.DISCLAIMERS.get(platform) or module.DISCLAIMERS.get("general") or "").strip()
        has_disclaimer = "风险提示" in text or "免责声明" in text or "投资建议" in text
        final = rewritten if red else text  # 有 RED 才替换为合规改写稿
        if not has_disclaimer and disclaimer:
            final = f"{final}\n\n---\n\n{disclaimer}"
        return {
            "result": "blocker" if red else ("warning" if yellow else "pass"),
            "issues": [
                {"word": i.get("word"), "level": i.get("level"),
                 "replacement": i.get("replacement"), "reason": i.get("reason")}
                for i in issues
            ],
            "disclaimer_appended": not has_disclaimer,
            "patched_text": final if final != text else None,
        }
    # 降级：内置黄词扫描（无改写能力）
    hits = sorted({w for w in YELLOW_WORDS if w in text})
    return {
        "result": "warning" if hits else "pass",
        "issues": [{"word": w, "level": "YELLOW"} for w in hits],
        "disclaimer_appended": False,
        "patched_text": None,
    }
