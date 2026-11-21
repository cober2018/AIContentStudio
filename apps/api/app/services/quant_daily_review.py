"""量化研究专家每日复盘：取数据中台的复盘数据，只留事实字段，出图表，交给第三方模型（MCP）写稿，停在「稿子」等用户。

作品、事实和图表记在 SystemSetting「quant_review」里，同一天再调用会复用。
"""
from __future__ import annotations

import io
import json
import os
import re
from datetime import date, timedelta
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from ..models import Connector, ContentPersona, SystemSetting, User, utcnow

TZ = ZoneInfo("Asia/Taipei")
KEY = "quant_review"
CONNECTOR = "数据中台复盘（对外展示）"
PERSONA = "量化研究专家"
PROJECT_TITLE = SERIES_NAME = "每日复盘"
CHART_LAYOUT = "v3"
FONT = ("/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/STHeiti Medium.ttc")
# Words that turn a review into investment advice; a draft containing any is refused at save.
ADVICE = re.compile(r"买入|卖出|加仓|减仓|建仓|抄底|止损|止盈|仓位|推荐|看好|看空|布局|机会来了|目标价|必涨|稳赚|建议关注|值得关注|可以关注|逢低|上车")


REASONS = {
    "api_key_missing": "缺少数据中台密钥（服务端环境变量 DREAMO_REVIEW_API_KEY）",
    "connector_missing": "数据接入里没有「数据中台复盘（对外展示）」连接",
    "api_key_no_access": "数据中台密钥没有复盘服务的权限，请找数据中台管理员",
    "persona_missing": "找不到量化研究专家这个角色",
    "not_owner": "每日复盘属于量化研究专家的主人，当前登录的账号不是",
    "data_not_ready": "数据中台这一天的数据还没生成",
    "chart_font_missing": "出图找不到中文字体",
}


class ReviewError(Exception):
    pass


# ---------- 数据：取数与白名单 ----------

def _connector(db) -> Connector:
    row = db.scalar(select(Connector).where(Connector.name == CONNECTOR, Connector.is_active.is_(True)))
    if row is None:
        raise ReviewError("connector_missing")
    if not os.environ.get(row.api_key_env or ""):
        raise ReviewError("api_key_missing")
    return row


def _get(connector: Connector, service: str, params: dict, *, pages: int = 10) -> tuple[list[dict], dict]:
    """Rows plus the envelope; the envelope's trade_date is the day the rows really belong to, which can be earlier than asked."""
    headers = {connector.auth_header_name or "X-API-Key": os.environ[connector.api_key_env]}
    rows, offset, envelope = [], 0, {}
    with httpx.Client(timeout=60, trust_env=False) as client:
        for _ in range(pages):
            response = client.get(f"{connector.base_url.rstrip('/')}/api/v1/data/apis/{service}/records",
                                  headers=headers, params={**params, "limit": 500, "offset": offset})
            response.raise_for_status()
            envelope = response.json().get("data") or {}
            rows += envelope.get("rows") or []
            page = envelope.get("pagination") or {}
            if not page.get("has_more"):
                break
            offset = page["next_offset"]
    return rows, envelope


def _day_rows(connector, service, day, **params) -> list[dict]:
    """Rows of exactly that trading day; a service that answers with an older day counts as not having it."""
    rows, envelope = _get(connector, service, {"trade_date": day, **params})
    return rows if envelope.get("trade_date") == day else []


def _optional(connector, service, day, **params) -> list[dict]:
    # Every service read here is in the aicontent package, so a refusal means the key or package is misconfigured, not "not offered".
    try:
        return _day_rows(connector, service, day, **params)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in {401, 403}:
            raise ReviewError("api_key_no_access") from exc
        raise


def _short(value):
    # Some calendar rows put a whole sentence where the number should be; those are left blank.
    text = str(value or "").strip()
    return text if text and len(text) <= 12 and re.search(r"\d", text) and "未公布" not in text else None


def _num(value, scale=1.0, digits=2):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    return round(value * scale) if digits == 0 else round(value * scale, digits)


def latest_trade_date(connector, today: date) -> str | None:
    """The newest finished day before today: a day's data is produced between 21:00 and 02:00, so today is never taken."""
    rows, envelope = _get(connector, "public-market-participation", {"trade_date": (today - timedelta(days=1)).isoformat()}, pages=1)
    return envelope.get("trade_date") if rows and str(envelope.get("trade_date") or "") < today.isoformat() else None


def _board(name):
    # Second- and third-level boards of one industry share the same figures and differ only by the Ⅱ/Ⅲ suffix.
    return re.sub(r"[ⅡⅢ]$", "", str(name or "").strip())


# The history view takes one index per request; these five cover large caps, small caps and the growth boards.
LINE_INDICES = {"000001.SH": "上证综指", "000300.SH": "沪深300", "000852.SH": "中证1000", "399006.SZ": "创业板指", "000688.SH": "科创50"}


def _history(connector, service, day, field, **params) -> list[list]:
    rows, _ = _get(connector, service, {"trade_date": day, **params})
    # history-position comes back unsorted, and nothing after the review day may leak into it.
    points = sorted({str(r.get("date"))[:10]: r.get(field) for r in rows if r.get("date") and isinstance(r.get(field), (int, float))}.items())
    return [[d, v] for d, v in points if d <= day]


def _series(connector, day) -> dict:
    try:
        return {"turnover_yi": _history(connector, "public-market-participation", day, "turnover", view="history", sessions=60),
                "compensation_pct": _history(connector, "public-market-compensation", day, "compensation_pct", view="history-position"),
                "indices": {name: _history(connector, "public-market-index-position", day, "close", view="history", index_code=code, sessions=20)
                            for code, name in LINE_INDICES.items()}}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in {401, 403}:
            raise ReviewError("api_key_no_access") from exc
        raise


def collect(connector, day: str) -> dict:
    """Only factual numbers survive: stages, groups, tags, signals, scores, budgets and scenario texts never leave this function."""
    participation = (_day_rows(connector, "public-market-participation", day) or [{}])[0]
    industries = _day_rows(connector, "public-industry-review", day, view="overview")
    if not participation or not industries:
        raise ReviewError("data_not_ready")
    omitted = []
    # On the newest day the platform still repeats the previous day's sector change (seen 2026-11-10, all 496 boards);
    # such moves are left out rather than published as that day's.
    previous_day = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
    previous_rows, previous_envelope = _get(connector, "public-industry-review", {"trade_date": previous_day, "view": "overview"})
    previous = {r.get("industry_code"): r.get("change_pct") for r in previous_rows} if previous_envelope.get("trade_date") != day else {}
    same = sum(1 for r in industries if r.get("change_pct") is not None and previous.get(r.get("industry_code")) == r.get("change_pct"))
    moves_ok = not previous or same < 0.9 * len(industries)
    if not moves_ok:
        omitted.append("行业当日涨跌幅（数据中台当天的数和前一交易日完全一样，当天不用）")
    boards, seen = [], set()
    for row in industries:
        name, change, flow = _board(row.get("industry_name")), _num(row.get("change_pct")), _num(row.get("net_inflow_5d"))
        if not name or name in seen:
            continue
        seen.add(name)
        boards.append({"name": name, "change_pct": change, "turnover_yi": _num(row.get("turnover"), 1, 1), "net_inflow_5d_yi": flow})
    def top(key, reverse):
        rows, figures = [], set()
        for board in sorted((b for b in boards if b[key] is not None), key=lambda b: b[key], reverse=reverse):
            if board[key] not in figures:
                figures.add(board[key])
                rows.append(board)
        return rows[:10]
    indices = [{"name": r.get("index_name"), "close": _num(r.get("close")), "change_pct": _num(r.get("return_1d_pct")),
                "change_20d_pct": _num(r.get("return_20d_pct")), "drawdown_1y_pct": _num(r.get("drawdown_pct")),
                "pe": _num(r.get("valuation")), "pe_position_5y_pct": _num(r.get("valuation_position_5y_pct"), 1, 1)}
               for r in _optional(connector, "public-market-index-position", day, view="overview") if r.get("index_name")]
    compensation = (_optional(connector, "public-market-compensation", day) or [{}])[0]
    feedback = (_optional(connector, "public-market-short-feedback", day) or [{}])[0]
    def known(key, digits=1):
        item = feedback.get(key) or {}
        return _num(item.get("value"), 1, digits) if item.get("available") else None
    start, end = date.fromisoformat(day), date.fromisoformat(day) + timedelta(days=7)
    events = []
    for event in _optional(connector, "public-forward-risk-events", day, view="calendar-facts", window_days=7):
        # The facts view writes 说明暂不可用 where a text is missing; that placeholder must not reach the article.
        country = "" if event.get("country") == "说明暂不可用" else str(event.get("country") or "").strip()
        when = str(event.get("event_date") or "")
        title = re.sub(r"\s+", " ", str(event.get("title") or "")).strip()
        while country and title.startswith(country):
            title = title[len(country):].strip()
        # Most rows are auctions and inventories tagged UNKNOWN; only named macro indicators make the article's calendar.
        if event.get("indicator_code") in (None, "", "UNKNOWN") or not title or not when or not start < date.fromisoformat(when[:10]) <= end:
            continue
        importance = event.get("source_importance")
        events.append({"date": when[:10], "time": event.get("event_time") or None, "country": country, "title": title, "period": event.get("period") or None,
                       "previous": _short(event.get("previous_value")), "forecast": _short(event.get("consensus_value")),
                       "importance": importance if isinstance(importance, int) else 0})
    events = sorted(sorted(events, key=lambda e: -e["importance"])[:10], key=lambda e: (e["date"], e["time"] or ""))
    return {
        "trade_date": day,
        "market": {"turnover_yi": _num(participation.get("turnover"), 1, 0), "relative_turnover": _num(participation.get("relative_turnover")),
                   "recent_position_pct": _num(participation.get("recent_position_pct"), 1, 1),
                   "long_position_pct": _num(participation.get("long_position_pct"), 1, 1),
                   "low_participation_days": participation.get("low_participation_days"),
                   "selling_pressure_pct": _num(participation.get("selling_pressure_pct"), 1, 1),
                   "pressure_change_pp": _num(participation.get("pressure_change_pp"))},
        "indices": indices,
        "compensation": {"index": compensation.get("index_name"), "compensation_pct": _num(compensation.get("compensation_pct")),
                         "earnings_yield_pct": _num(compensation.get("earnings_yield_pct")), "bond_yield_pct": _num(compensation.get("bond_yield_pct"), 1, 3),
                         "change_20d_bp": _num(compensation.get("change_20d_bp"), 1, 1),
                         "historical_position_pct": _num(compensation.get("historical_position_pct"), 1, 1)},
        "limit": {"seal_rate_pct": known("seal_rate_pct"), "consecutive_count": known("consecutive_count", 0), "maximum_boards": known("maximum_boards", 0),
                  "first_board_return_pct": known("first_board_return_pct"), "repair_rate_pct": known("repair_rate_pct")},
        "sectors_up": [{k: b[k] for k in ("name", "change_pct", "turnover_yi")} for b in top("change_pct", True)] if moves_ok else [],
        "sectors_down": [{k: b[k] for k in ("name", "change_pct", "turnover_yi")} for b in top("change_pct", False)] if moves_ok else [],
        "flow_in": [{k: b[k] for k in ("name", "net_inflow_5d_yi")} for b in top("net_inflow_5d_yi", True)],
        "flow_out": [{k: b[k] for k in ("name", "net_inflow_5d_yi")} for b in top("net_inflow_5d_yi", False)],
        "events": events,
        "series": _series(connector, day),
        "omitted": omitted,
        "units": "成交额、资金净流入单位为亿元；涨跌幅、占比、位置均为百分数；bp 是基点（0.01 个百分点）。",
        "glossary": GLOSSARY,
    }


# What each field means; the model reads only these, so it cannot misname a metric.
GLOSSARY = {
    "market.turnover_yi": "两市成交额（亿元）", "market.relative_turnover": "成交额相对参考水平的倍数，1 倍为持平",
    "market.recent_position_pct / long_position_pct": "市场参与程度在近期 / 较长时期里的相对位置，越低越冷清",
    "market.low_participation_days": "低参与状态已持续的交易日数", "market.selling_pressure_pct": "卖压相对强度，越高卖压越大",
    "market.pressure_change_pp": "当日卖压变化（百分点），负数为缓和",
    "indices": "主要指数：close 收盘点位，change_pct 当日涨跌幅，change_20d_pct 20 日涨跌幅，drawdown_1y_pct 距近一年高点的回撤，pe 市盈率（倍），pe_position_5y_pct 市盈率在近 5 年里的位置",
    "compensation": "股权风险补偿（股债性价比）：compensation_pct 补偿 = 盈利收益率减国债收益率，earnings_yield_pct 盈利收益率，bond_yield_pct 10 年国债收益率，change_20d_bp 近 20 日补偿变化（基点），historical_position_pct 补偿在自身历史里的位置",
    "limit": "涨停接力：seal_rate_pct 封板率，consecutive_count 连板家数，maximum_boards 最高连板数，first_board_return_pct 昨日首板股今天的平均涨跌幅，repair_rate_pct 炸板后即时回封的比例；空着就是当天没有",
    "sectors_up / sectors_down": "当日涨幅、跌幅居前的行业板块：change_pct 当日涨跌幅，turnover_yi 成交额（亿元）",
    "flow_in / flow_out": "近 5 个交易日资金净流入最多、净流出最多的行业（亿元，负数为流出），不是当天一天的数",
    "events": "未来 7 天的宏观数据日程：previous 前值，forecast 预期，空着就是没有",
    "series_summary": "画折线图用的历史数据里的几个关键点：turnover_60d 近 60 个交易日两市成交额（亿元）的最高、最低和所在日期；compensation 股权风险补偿历史走势的起点、最高、最低（%）",
    "omitted": "当天没有可靠数据、被拿掉的内容；文章里不要提，也不要补",
}


# ---------- 图表 ----------

def _font(size):
    from PIL import ImageFont

    for path in FONT:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise ReviewError("chart_font_missing")


def _canvas(title, height, day):
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (1080, height), "#ffffff")
    draw = ImageDraw.Draw(image)
    draw.text((48, 36), title, font=_font(40), fill="#111827")
    draw.text((48, height - 46), f"数据：DreamO 数据中台 · 交易日 {day}", font=_font(22), fill="#9ca3af")
    return image, draw


def _png(image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, "PNG", optimize=True)
    return buffer.getvalue()


def _value(value, suffix=""):
    return "—" if value is None else f"{value:,}{suffix}" if isinstance(value, int) else f"{value}{suffix}"


def bar_chart(title, items, day, unit) -> bytes:
    """Horizontal bars around zero: red for gains or inflow, green for losses or outflow (A-share convention)."""
    image, draw = _canvas(title, 150 + 52 * len(items) + 70, day)
    peak = max((abs(v) for _, v in items), default=1) or 1
    # Room for an 8-character name on the left and a value label at either bar end inside the 1080 canvas.
    middle, half = 640, 260
    draw.line((middle, 116, middle, 120 + 52 * len(items)), fill="#d1d5db", width=2)
    for index, (label, value) in enumerate(items):
        y = 124 + index * 52
        draw.text((48, y + 4), label[:8], font=_font(26), fill="#374151")
        length = int(abs(value) / peak * half)
        color = "#dc2626" if value >= 0 else "#16a34a"
        box = (middle, y + 6, middle + length, y + 38) if value >= 0 else (middle - length, y + 6, middle, y + 38)
        draw.rectangle(box, fill=color)
        text = f"{value:+.2f}{unit}"
        width = draw.textlength(text, font=_font(24))
        draw.text((box[2] + 10 if value >= 0 else box[0] - 10 - width, y + 8), text, font=_font(24), fill=color)
    return _png(image)


LINE_COLORS = ("#2563eb", "#dc2626", "#d97706", "#7c3aed", "#0891b2")


def _line(draw, box, series, fmt, mark_last=True):
    """Line plot inside box; series is [(label, [[date, value], ...])]. Y labels use fmt; dates are shown at both ends and the middle."""
    left, top, right, bottom = box
    values = [v for _, points in series for _, v in points]
    low, high = min(values), max(values)
    pad = (high - low) * .08 or abs(high) * .05 or 1
    low, high = low - pad, high + pad
    plot_left = left + 110
    for step in range(5):
        y = bottom - (bottom - top) * step / 4
        draw.line((plot_left, y, right, y), fill="#eef0f3", width=2)
        label = fmt(low + (high - low) * step / 4)
        draw.text((plot_left - 14 - draw.textlength(label, font=_font(22)), y - 13), label, font=_font(22), fill="#9ca3af")
    dates = [d for d, _ in max((points for _, points in series), key=len)]
    span = max(len(dates) - 1, 1)
    index = {d: i for i, d in enumerate(dates)}
    for at in sorted({0, span // 2, span}):
        text = dates[at][5:]
        x = plot_left + (right - plot_left) * at / span
        draw.text((x - draw.textlength(text, font=_font(22)) / 2, bottom + 12), text, font=_font(22), fill="#9ca3af")
    for (label, points), color in zip(series, LINE_COLORS):
        xy = [(plot_left + (right - plot_left) * index.get(d, 0) / span, bottom - (bottom - top) * (v - low) / (high - low)) for d, v in points]
        if len(xy) > 1:
            draw.line(xy, fill=color, width=4, joint="curve")
        if mark_last and xy:
            x, y = xy[-1]
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color)


def _legend(draw, y, series):
    x = 48
    for (label, _), color in zip(series, LINE_COLORS):
        draw.rectangle((x, y + 8, x + 28, y + 16), fill=color)
        draw.text((x + 38, y), label, font=_font(24), fill="#374151")
        x += 60 + draw.textlength(label, font=_font(24))


def _position_bars(draw, y, items):
    """0–100% position bars with the value at the marker; empty values are drawn as a grey track with a dash."""
    for label, value in items:
        draw.text((48, y), label, font=_font(26), fill="#374151")
        left, right = 360, 940
        draw.rounded_rectangle((left, y + 6, right, y + 30), radius=12, fill="#f1f3f6")
        if value is None:
            draw.text((right + 16, y), "—", font=_font(26), fill="#9ca3af")
        else:
            x = left + (right - left) * max(0, min(value, 100)) / 100
            draw.rounded_rectangle((left, y + 6, max(x, left + 24), y + 30), radius=12, fill="#2563eb")
            draw.text((right + 16, y), f"{value}%", font=_font(26), fill="#111827")
        y += 64
    return y


def _tiles(draw, y, items):
    width = (1080 - 96 - 24 * (len(items) - 1)) // len(items)
    for index, (label, value) in enumerate(items):
        x = 48 + index * (width + 24)
        draw.rounded_rectangle((x, y, x + width, y + 150), radius=18, fill="#f8fafc", outline="#e5e7eb", width=2)
        draw.text((x + 28, y + 22), label, font=_font(26), fill="#6b7280")
        draw.text((x + 28, y + 66), value, font=_font(56), fill="#111827")
    return y + 150


def market_chart(facts) -> bytes:
    market, day, points = facts["market"], facts["trade_date"], facts["series"]["turnover_yi"]
    image, draw = _canvas("大盘环境", 1000, day)
    draw.text((48, 104), f"两市成交额（近 {len(points)} 个交易日，万亿元）· 当天 {_value(market['turnover_yi'], ' 亿元')}", font=_font(26), fill="#374151")
    if points:
        _line(draw, (48, 160, 1032, 560), [("成交额", [[d, v / 10000] for d, v in points])], lambda v: f"{v:.1f}")
    _position_bars(draw, 680, [("近期参与位置", market["recent_position_pct"]), ("长期参与位置", market["long_position_pct"]),
                               ("卖压相对强度", market["selling_pressure_pct"])])
    return _png(image)


def index_chart(facts) -> bytes:
    day = facts["trade_date"]
    series = [(name, [[d, v / points[0][1] * 100] for d, v in points]) for name, points in facts["series"]["indices"].items() if points]
    image, draw = _canvas("主要指数近 20 个交易日", 760, day)
    draw.text((48, 104), "每个指数以第一天为 100，看谁走得强", font=_font(26), fill="#6b7280")
    _legend(draw, 150, series)
    if series:
        _line(draw, (48, 210, 1032, 640), series, lambda v: f"{v:.0f}")
    return _png(image)


def limit_chart(facts) -> bytes:
    limit, day = facts["limit"], facts["trade_date"]
    image, draw = _canvas("涨停接力", 520, day)
    _tiles(draw, 110, [("连板家数", _value(limit["consecutive_count"], " 家")), ("最高连板", _value(limit["maximum_boards"], " 板")),
                       ("昨日首板今日", _value(limit["first_board_return_pct"], "%"))])
    _position_bars(draw, 300, [("封板率", limit["seal_rate_pct"]), ("炸板即时回封率", limit["repair_rate_pct"])])
    return _png(image)


def valuation_chart(facts) -> bytes:
    compensation, day, points = facts["compensation"], facts["trade_date"], facts["series"]["compensation_pct"]
    positions = [(f"{i['name']}市盈率", i["pe_position_5y_pct"]) for i in facts["indices"] if i["pe_position_5y_pct"] is not None]
    image, draw = _canvas("估值与股债性价比", 720 + 64 * len(positions), day)
    draw.text((48, 104), f"{compensation['index'] or ''}股权风险补偿（%）· 当天 {_value(compensation['compensation_pct'], '%')}"
              f"，盈利收益率 {_value(compensation['earnings_yield_pct'], '%')}，10 年国债 {_value(compensation['bond_yield_pct'], '%')}",
              font=_font(24), fill="#374151")
    if points:
        _line(draw, (48, 160, 1032, 520), [("补偿", points)], lambda v: f"{v:.1f}")
    draw.text((48, 590), "各指数市盈率在近 5 年里的位置", font=_font(26), fill="#6b7280")
    _position_bars(draw, 640, positions)
    return _png(image)


def calendar_chart(facts) -> bytes:
    """A vertical timeline: one node per day, that day's events listed beside it with previous and consensus values."""
    day, events = facts["trade_date"], facts["events"]
    days = sorted({e["date"] for e in events})
    image, draw = _canvas("未来一周宏观日历", 170 + 56 * len(days) + 52 * len(events) + 60, day)
    y = 116
    draw.line((92, y + 10, 92, 116 + 56 * len(days) + 52 * len(events) - 20), fill="#e5e7eb", width=4)
    for when in days:
        draw.ellipse((80, y + 2, 104, y + 26), fill="#2563eb")
        weekday = "一二三四五六日"[date.fromisoformat(when).weekday()]
        draw.text((128, y), f"{when[5:]} 周{weekday}", font=_font(28), fill="#111827")
        y += 56
        for event in (e for e in events if e["date"] == when):
            text = f"{event['time'] or '待定'}  {event['country']}{event['title']}"
            font = _font(24)
            while draw.textlength(text, font=font) > 640 and len(text) > 4:
                text = text[:-2] + "…"
            draw.text((128, y), text, font=font, fill="#374151")
            figures = f"前值 {_value(event['previous'])} · 预期 {_value(event['forecast'])}"
            draw.text((1032 - draw.textlength(figures, font=_font(22)), y + 2), figures, font=_font(22), fill="#6b7280")
            y += 52
    return _png(image)


def charts(facts: dict) -> list[dict]:
    day = facts["trade_date"]
    specs = [
        ("market", "大盘环境", "近 60 个交易日成交额走势，参与度和卖压位置", lambda: market_chart(facts)),
        ("indices", "主要指数", "主要指数近 20 个交易日走势（首日为 100）", lambda: index_chart(facts)),
        ("sectors_up", "行业涨幅居前", "当日涨幅居前的行业板块", lambda: bar_chart(
            "行业涨幅居前", [(s["name"], s["change_pct"]) for s in facts["sectors_up"]], day, "%")),
        ("sectors_down", "行业跌幅居前", "当日跌幅居前的行业板块", lambda: bar_chart(
            "行业跌幅居前", [(s["name"], s["change_pct"]) for s in facts["sectors_down"]], day, "%")),
        ("flow", "行业五日资金净流入前后各五", "近 5 个交易日资金净流入最多和流出最多的行业", lambda: bar_chart(
            "行业近 5 日资金净流入（亿元）", [(s["name"], s["net_inflow_5d_yi"]) for s in facts["flow_in"][:5]]
            + [(s["name"], s["net_inflow_5d_yi"]) for s in reversed(facts["flow_out"][:5])], day, "")),
        ("limit", "涨停接力", "连板家数、最高连板，封板率和炸板回封率", lambda: limit_chart(facts)),
        ("valuation", "估值与股债性价比", "股权风险补偿的历史走势和各指数市盈率位置", lambda: valuation_chart(facts)),
        ("events", "未来一周宏观日历", "接下来 7 天的重要宏观数据发布", lambda: calendar_chart(facts)),
    ]
    present = {"indices": any(facts["series"]["indices"].values()), "sectors_up": facts["sectors_up"], "sectors_down": facts["sectors_down"],
               "flow": facts["flow_in"], "limit": any(v is not None for v in facts["limit"].values()), "events": facts["events"]}
    return [{"key": key, "title": title, "about": about, "render": render} for key, title, about, render in specs if present.get(key, True)]


# ---------- 平台对象 ----------

def _setting(db) -> SystemSetting:
    row = db.get(SystemSetting, KEY, populate_existing=True)
    if row is None:
        row = SystemSetting(key=KEY, value={"days": {}})
        db.add(row)
        db.flush()
    return row


def _save(db, row, value):
    row.value = value
    flag_modified(row, "value")
    db.commit()


def _owner(db) -> tuple[ContentPersona, User]:
    persona = db.scalar(select(ContentPersona).where(ContentPersona.name == PERSONA, ContentPersona.status == "active"))
    if persona is None:
        raise ReviewError("persona_missing")
    return persona, db.get(User, persona.owner_user_id)


def _container(db, value, persona, user) -> dict:
    """The long-running project and the persona's column; created once, then reused every day."""
    from ..models import ContentProject, ContentSeries
    from ..routers.content_projects import ProjectIn, create_project
    from .content_identity import create_editorial_series

    project = db.get(ContentProject, value.get("project_id") or 0)
    if project is None or project.status == "archived":
        project_id = create_project(ProjectIn(title=PROJECT_TITLE, objective="量化研究专家每个交易日的市场复盘，持续追踪大盘、行业、资金和情绪。"),
                                    db, user)["id"]
        value["project_id"] = project_id
    series = db.get(ContentSeries, value.get("series_id") or 0)
    if series is None or series.status != "active":
        value["series_id"] = create_editorial_series(db, user, persona.id, name=SERIES_NAME).id
    return value


def _unit(db, value, day, persona, user) -> int:
    from ..routers.content_projects import UnitIn, create_unit

    record = value["days"].setdefault(day, {})
    if not record.get("unit_id"):
        record["unit_id"] = create_unit(UnitIn(title=f"{day} 复盘", persona_id=persona.id, series_id=value["series_id"], modality="text",
                                               channel_id="wechat"), value["project_id"], db, user)["id"]
    return record["unit_id"]


def _store_charts(db, user, facts) -> list[dict]:
    from .materials import create_material, create_revision

    stored = []
    for spec in charts(facts):
        content = spec["render"]()
        material = create_material(db, kind="chart", title=f"{facts['trade_date']} 复盘 · {spec['title']}", tags=["每日复盘"], created_by=user.email)
        revision = create_revision(db, material, content=content, suffix=".png", declared_mime="image/png", source_kind="chart",
                                   source_metadata={"quant_review": facts["trade_date"], "chart": spec["key"]},
                                   public_use_allowed=True, model_use_allowed=True, commercial_use_allowed=True, created_by=user.email)
        stored.append({"key": spec["key"], "title": spec["title"], "about": spec["about"], "material_revision_id": revision.id})
    db.commit()
    return stored


def _model_facts(facts: dict) -> dict:
    """The model gets the turning points of the history lines, not hundreds of raw points it might quote out of context."""
    series = facts.get("series") or {}
    def ends(points):
        if not points:
            return None
        top, bottom = max(points, key=lambda p: p[1]), min(points, key=lambda p: p[1])
        return {"from_date": points[0][0], "start": points[0][1], "max": top[1], "max_date": top[0], "min": bottom[1], "min_date": bottom[0]}
    summary = {"turnover_60d": ends(series.get("turnover_yi")), "compensation": ends(series.get("compensation_pct"))}
    return {**{k: v for k, v in facts.items() if k != "series"}, "series_summary": summary}


# ---------- 交给第三方模型写稿（MCP） ----------

RULES = """你是这个角色本人，写一篇当天 A 股市场复盘文章（公众号文章，以图为主，600–1000 字）。
- 以图为主：每一节先放图，再用一两句话点出图里最关键的一两个数或变化；不要把图里的数一条条复述，也不要写成数据清单。
- charts 里每张图都要插一次，不要重复；图用 chart 块，material_revision_id 照抄 charts 里的值，caption 写一句图注。
- 只写 facts 里有的数字，单位照 facts.units，指标含义严格按 facts.glossary；不要自己算新的百分比、比值或合计，不要编造数字、个股、新闻或原因。
- 数据来源只说「数据中台」，不要虚构系统或机构名称，也不要说行业属于申万或其他分类标准。
- 只陈述事实和变化，不做预测，不给任何投资建议：不出现买入、卖出、加仓、减仓、仓位、推荐、看好、布局、抄底、关注某板块之类的话，不点名个股。存稿时平台会查这些词，查到就拒绝。
- 字段为空（null）就是当天没有这个数，不要写成 0，也不要猜；facts.omitted 里的内容不要提。
- flow_in / flow_out 是近 5 个交易日的累计数，要写明「近 5 日」，不能说成当天。
- events 不为空时，结尾一节「接下来几天的数据日程」放宏观日历图，再用一句话点出最重要的一两项；events 为空就不写这一节。
- 文末加一句：本文仅为数据复盘，不构成投资建议。"""

PAYLOAD_EXAMPLE = {"title": "标题", "document": {"schema": "studio.text.document.v1", "citations": [], "blocks": [
    {"id": "b1", "type": "heading", "level": 2, "content": [{"text": "小标题", "marks": []}]},
    {"id": "b2", "type": "chart", "material_revision_id": 0, "alt_text": "图表标题", "caption": "一句图注"},
    {"id": "b3", "type": "paragraph", "content": [{"text": "正文一两句", "marks": []}]}]}}


def advice_problem(payload: dict) -> str | None:
    """The first advice term in a daily review draft; the closing disclaimer itself is allowed."""
    blocks = ((payload or {}).get("document") or {}).get("blocks") or []
    text = str((payload or {}).get("title") or "") + "".join(
        str(part.get("text") or "") for block in blocks for part in (block.get("content") or []) if isinstance(part, dict))
    text += "".join(str(block.get("caption") or "") for block in blocks)
    found = ADVICE.search(text.replace("不构成投资建议", ""))
    return found.group(0) if found else None


def _reference_charts(db, user, project_id, stored):
    from ..models import ProjectMaterialReference

    # Masters may only embed material the project has referenced.
    for chart in stored:
        if db.scalar(select(ProjectMaterialReference.id).where(ProjectMaterialReference.project_id == project_id,
                     ProjectMaterialReference.material_revision_id == chart["material_revision_id"])) is None:
            db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=chart["material_revision_id"], origin="system_reference",
                                            status="active", attached_by=user.email, note="每日复盘图表"))
    db.commit()


def prepare(db, user, trade_date: str | None = None) -> dict:
    """Make sure the day's piece, facts and charts exist, and hand them to the third-party model with the writing rules."""
    from ..models import ContentUnit
    from .persona_brief import persona_brief

    persona, owner = _owner(db)
    if owner is None or owner.id != user.id:
        raise ReviewError("not_owner")
    connector = _connector(db)
    day = trade_date or latest_trade_date(connector, utcnow().astimezone(TZ).date())
    if not day:
        raise ReviewError("data_not_ready")
    row = _setting(db)
    value = json.loads(json.dumps(row.value or {"days": {}}))
    value.setdefault("days", {})
    _container(db, value, persona, user)
    unit_id = _unit(db, value, day, persona, user)
    record = value["days"][day]
    # Records from the scheduled job carry the old table charts; only charts of the current layout are reused.
    if record.get("layout") != CHART_LAYOUT:
        record["facts"] = collect(connector, day)
        _save(db, row, value)
        record["charts"] = _store_charts(db, user, record["facts"])
        record["layout"] = CHART_LAYOUT
        _save(db, _setting(db), value)
    _reference_charts(db, user, value["project_id"], record["charts"])
    return {"project_id": value["project_id"], "unit_id": unit_id, "trade_date": day,
            "persona": persona_brief(db, user, db.get(ContentUnit, unit_id)), "facts": _model_facts(record["facts"]),
            "charts": [{k: c[k] for k in ("key", "title", "about", "material_revision_id")} for c in record["charts"]],
            "rules": RULES, "payload_example": PAYLOAD_EXAMPLE,
            "next": "按 rules 写好整篇，用 save_article_draft（project_id、unit_id、payload=text.master.v2）存稿，然后停下等用户在页面上采用或写意见；"
                    "之后用 get_article_decision 读意见，有意见就再存一版。"}
