"""Built-in camera moves, looks and motion strength for product shots, and the video prompt they make."""
import json
import re
from functools import cache

from .product_categories import CATALOG

INTENSITIES = ("subtle", "normal", "strong")
MAX_STACK = 2


@cache
def catalog() -> dict:
    return json.loads((CATALOG / "motion.json").read_text(encoding="utf-8"))


def _cameras() -> dict:
    return {item["id"]: item for item in catalog()["camera"]}


def _looks() -> dict:
    return {item["id"]: item for item in catalog()["looks"]}


def stack_problem(ids: list[str]) -> str | None:
    """Why these camera moves cannot be stacked, or None when they can."""
    cameras = _cameras()
    unknown = [item for item in ids if item not in cameras]
    if unknown:
        return f"运镜库里没有：{', '.join(unknown)}"
    if len(ids) > MAX_STACK:
        return "运镜最多叠两个"
    if len(set(ids)) != len(ids):
        return "同一个运镜不能叠两次"
    # A move that ends by holding still cannot run "at the same time" as one that keeps moving.
    if len(ids) == 2 and cameras[ids[0]].get("holds") != cameras[ids[1]].get("holds"):
        return f"「{cameras[ids[0]]['name']}」和「{cameras[ids[1]]['name']}」一个定住一个在动，不能同时用"
    return None


def shot_problems(shot: dict) -> list[str]:
    board = shot.get("board") or {}
    problems = []
    presets = board.get("camera_presets")
    if presets is not None:
        problem = "运镜格式不对" if type(presets) is not list or any(type(item) is not str for item in presets) else stack_problem(presets)
        if problem:
            problems.append(f"{shot.get('id')}：{problem}")
    if board.get("look") is not None and board["look"] not in _looks():
        problems.append(f"{shot.get('id')}：光线色调不在平台列表里")
    if board.get("intensity") is not None and board["intensity"] not in INTENSITIES:
        problems.append(f"{shot.get('id')}：运镜强度只能是轻 / 中 / 强")
    if board.get("chain_from_previous") is not None and type(board["chain_from_previous"]) is not bool:
        problems.append(f"{shot.get('id')}：接上一镜只能是是或否")
    return problems


def _picture(board: dict) -> str:
    # Lines about overlaid text are post-production work (AE); sent to an image or video model they get painted into the frame.
    visual = str(board.get("visual") or board.get("message") or "")
    kept = [part for part in re.split(r"(?<=[；。;])", visual) if not ("叠" in part and "字" in part)]
    return "".join(kept).strip("；;。 ")


def still_prompt(board: dict, *, people: bool, person: str = "", setting: str = "") -> str:
    """A first-frame still in four parts: capture, person, action and camera, setting (studio.video.prompt-direction)."""
    looks = _looks()
    # Without a look, people shots default to the fixed phone-footage wording so they read as real filming.
    capture = looks[board["look"]]["image"] if board.get("look") in looks else looks["phone-raw"]["image"] if people else ""
    who = "；".join(filter(None, [person.strip(), str(board.get("attitude") or "").strip(), catalog()["realism"]["zh"] if people else ""]))
    parts = [("拍摄方式", capture), ("人物", who), ("动作与镜头", _picture(board)), ("场景", setting.strip())]
    return "\n".join(f"{name}：{text}" for name, text in parts if text) + "\n画面里不出现任何文字、字幕、标志和水印。"


def motion_prompt(board: dict, *, people: bool, english: bool) -> str:
    """One video prompt: what moves, how the camera moves, light, strength and the fixed product / stability rules."""
    data = catalog()
    cameras, looks = _cameras(), _looks()
    lang = "en" if english else "zh"
    # The person's attitude leads (studio.video.prompt-direction): it directs face, body and rhythm together.
    parts = [str(board.get("attitude") or "").strip(), _picture(board)]
    moves = [cameras[item]["motion_en" if english else "motion"] for item in board.get("camera_presets") or [] if item in cameras]
    if moves:
        parts.append(("Camera: " if english else "运镜：") + ("; at the same time, " if english else "，同时").join(moves))
    if board.get("look") in looks:
        parts.append(looks[board["look"]]["motion"] if english else looks[board["look"]]["image"])
    strength = data["intensity"].get(board.get("intensity") or "normal")
    if strength:
        parts.append(strength["motion_en"] if english else f"运镜强度：{strength['name']}")
    if people:
        parts.append(data["realism"][lang])
    parts += data["video_rules"][lang]
    return ("。" if not english else ". ").join(part.rstrip("。. ") for part in parts if part)
