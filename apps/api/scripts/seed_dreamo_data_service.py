"""DreamO 复盘看板数据服务接入（幂等，可重复执行）。

背景：DreamOAgents 平台已把复盘中心 4 张看板以「一表一服务」标准透出
（docs/api/review-dashboards-data-service-api.md，2026-09-19 v1.0）：
  GET https://dreamotech.cn/api/v1/data/apis/{service_key}/records
  鉴权 X-API-Key（env: DREAMO_DATA_API_KEY）；参数白名单 trade_date/industry_code/idx_type/limit/offset；
  限流 60 次/分钟；trade_date=latest 返回最新交易日；*_json 列需二次 JSON 解析。

本脚本：
  1. 把「DreamO 量化平台（生产）」Connector 切到 X-API-Key 鉴权（原 bearer JWT 无 dm:apis 权限，且 8h 过期）；
  2. 删除旧的 3 个临时端点（/api/v1/review/sentiment|industry，已被标准数据服务取代）；
  3. upsert 4 个 v2 映射端点覆盖 5 张看板（行业复盘与行业生命周期共用同一张 190 列 ADS 宽表，
     按 API 文档「按需取用字段」约定，单端点同时服务两张看板，避免重复拉取）。

事实精选策略（防止 1031 行/日 × 190 列的宽表灌爆事实库）：
  每个交易日每端点产出约 15-25 条高信号事实（大盘上下文、情绪/风险摘要、
  生命周期分布、RRG 领先行业、focus 行业清单），全量行数据经 raw_keep_fields
  瘦身后存入 SourceDocument.raw_text 供查证。

执行：cd apps/api && python3 scripts/seed_dreamo_data_service.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal  # noqa: E402
from app.models import Connector, ConnectorEndpoint  # noqa: E402

CONNECTOR_NAME = "DreamO 量化平台（生产）"
SERVICE_PATH = "/api/v1/data/apis/{key}/records"

SENTIMENT_STAGE_AGG = {
    "mode": "aggregate",
    "facts": [
        {
            "statement": "A股市场情绪总分 {emotion_total_score}（满分 {emotion_total_max}），市场状态：{emotion_state_label}",
            "value": "{emotion_total_score}",
            "subject": "市场情绪",
            "predicate": "情绪总分",
            "unit": "分",
            "when_present": ["emotion_total_score", "emotion_state_label"],
        },
        {
            "statement": "市场估值区间：{valuation_bucket_label}（置信度 {valuation_confidence}）",
            "value": "{valuation_confidence}",
            "subject": "市场估值",
            "predicate": "估值区间",
            "when_present": ["valuation_bucket_label", "valuation_confidence"],
        },
        {
            "statement": "底部共振：{resonance_label_text}（未触发时为「未形成底部共振」口径，见状态）",
            "value": "{emotion_confidence}",
            "subject": "市场情绪",
            "predicate": "底部共振",
            "when": {"resonance_triggered": 1},
            "when_present": ["resonance_label_text"],
        },
        {
            "statement": "衍生品维度得分 {derivatives_score}",
            "value": "{derivatives_score}",
            "subject": "市场情绪",
            "predicate": "衍生品得分",
            "when_present": ["derivatives_score"],
        },
        {
            "statement": "市场广度得分 {breadth_score}",
            "value": "{breadth_score}",
            "subject": "市场情绪",
            "predicate": "广度得分",
            "when_present": ["breadth_score"],
        },
        {
            "statement": "微观结构得分 {microstructure_score}",
            "value": "{microstructure_score}",
            "subject": "市场情绪",
            "predicate": "微观结构得分",
            "when_present": ["microstructure_score"],
        },
        {
            "statement": "拥挤度与流动性得分 {crowding_liquidity_score}",
            "value": "{crowding_liquidity_score}",
            "subject": "市场情绪",
            "predicate": "拥挤流动性得分",
            "when_present": ["crowding_liquidity_score"],
        },
        {
            "statement": "估值风险补偿（ERP）区间：{erp_regime_label}",
            "value": "{erp_filter_score}",
            "subject": "市场估值",
            "predicate": "ERP区间",
            "when_present": ["erp_regime_label", "erp_filter_score"],
        },
    ],
}
SENTIMENT_STAGE_INDICATORS = {
    "mode": "expand",
    "expand_field": "indicators_json",
    "key_into": "indicator",
    "facts": [
        {
            "statement": "情绪指标 {indicator} 得分 {score}（信号 {signal}，{level}）",
            "value": "{score}",
            "subject": "{indicator}",
            "predicate": "情绪指标得分",
            "when_present": ["score", "level"],
        }
    ],
}

FORWARD_RISK_STAGES = [
    {
        "mode": "aggregate",
        "facts": [
            {
                "statement": "未来10日综合风险评分 {overall_risk_score}/100（风险等级 {overall_risk_level}，趋势 {risk_trend}）",
                "value": "{overall_risk_score}",
                "subject": "市场风险",
                "predicate": "10日综合风险",
                "when_present": ["overall_risk_score", "overall_risk_level"],
            },
            {
                "statement": "尾部风险：{tail_risk}；风险聚集度：{risk_cluster}",
                "value": "{tail_risk}",
                "subject": "市场风险",
                "predicate": "尾部风险",
                "when_present": ["tail_risk"],
            },
            {
                "statement": "主导风险因子：{dominant_risk_factor}；市场定价程度 {pricing_degree}/100",
                "value": "{pricing_degree}",
                "subject": "市场风险",
                "predicate": "定价程度",
                "when_present": ["dominant_risk_factor", "pricing_degree"],
            },
            {
                "statement": "未来日历事件 {event_count} 个（数据模式 {source_mode}）",
                "value": "{event_count}",
                "subject": "市场风险",
                "predicate": "事件数量",
                "when_present": ["event_count"],
            },
        ],
    },
    {
        "mode": "expand",
        "expand_field": "horizons_json",
        "key_into": "horizon",
        "facts": [
            {
                "statement": "未来 {horizon} 风险评分 {risk_score}/100（{risk_level}，趋势 {risk_trend}）",
                "value": "{risk_score}",
                "subject": "市场风险",
                "predicate": "分期风险",
                "when_present": ["risk_score", "risk_level"],
            }
        ],
    },
    {
        "mode": "expand",
        "expand_field": "focus_event_json",
        "facts": [
            {
                "statement": "焦点风险事件：{title}（{event_date}，{event_type_label}，重要性 {importance}，风险等级 {risk_level}，距今 {days_to_event} 天）",
                "value": "{importance}",
                "subject": "{event_type_label}",
                "predicate": "焦点事件",
                "fact_type": "event",
                "when_present": ["title", "event_date"],
            }
        ],
    },
]

INDUSTRY_RAW_KEEP = [
    "trade_date", "sector_code", "sector_name", "idx_type", "lifecycle_phase", "phase_confidence",
    "review_group", "sector_return", "sector_return_5d", "sector_return_20d", "amount", "turnover_rate",
    "net_flow_1d", "net_flow_5d", "net_flow_20d", "crowding_score", "crowding_percentile_60d",
    "rrg_v3_quadrant", "rrg_v3_rs_z", "rrg_v3_momentum_z", "opportunity_tags", "risk_tags",
    "primary_turning_signal_label", "signal_priority_label", "signal_priority_score",
    "market_ctx_index_code", "market_ctx_index_change_pct", "market_ctx_up_count",
    "market_ctx_down_count", "market_ctx_turnover_billion",
]

INDUSTRY_STAGES = [
    {
        "mode": "aggregate",
        "facts": [
            {
                "statement": "大盘：沪深300 涨跌 {market_ctx_index_change_pct}%，上涨 {market_ctx_up_count} 家、下跌 {market_ctx_down_count} 家",
                "value": "{market_ctx_index_change_pct}",
                "subject": "大盘",
                "predicate": "沪深300涨跌幅",
                "unit": "%",
                "when_present": ["market_ctx_index_code", "market_ctx_index_change_pct"],
            },
            {
                "statement": "全市场成交额 {market_ctx_turnover_billion}（平台口径亿元）",
                "value": "{market_ctx_turnover_billion}",
                "subject": "大盘",
                "predicate": "成交额",
                "when_present": ["market_ctx_index_code", "market_ctx_turnover_billion"],
            },
        ],
    },
    {
        "mode": "join",
        "filter": {"idx_type": "行业板块"},
        "count_by": "lifecycle_phase",
        "facts": [
            {
                "statement": "行业生命周期分布（行业板块）：{__counts__}",
                "value": "{__count__}",
                "subject": "行业结构",
                "predicate": "生命周期分布",
                "when_present": ["__counts__"],
            }
        ],
    },
    {
        "mode": "join",
        "filter": {"idx_type": "行业板块", "rrg_v3_quadrant": "leading"},
        "sort_by": "-rrg_v3_rs_z",
        "join_field": "sector_name",
        "limit": 10,
        "facts": [
            {
                "statement": "RRG 领先行业（相对沪深300，按相对强度排序）：{__joined__}（共 {__count__} 个）",
                "value": "{__count__}",
                "subject": "行业结构",
                "predicate": "RRG领先行业",
                "when_present": ["__joined__"],
            }
        ],
    },
    {
        "mode": "item",
        "filter": {"idx_type": "行业板块", "review_group": "focus"},
        "sort_by": "-phase_confidence",
        "limit": 15,
        "derived": {"sector_return_pct": ["sector_return", 100], "crowding_pct": ["crowding_percentile_60d", 100]},
        "facts": [
            {
                "statement": "{sector_name}：生命周期 {lifecycle_phase}（置信度 {phase_confidence}），当日涨跌 {sector_return_pct}%，5日主力净流入 {net_flow_5d} 亿，拥挤度60日分位 {crowding_pct}%，机会标签：{opportunity_tags}",
                "value": "{sector_return_pct}",
                "unit": "%",
                "subject": "{sector_name}",
                "predicate": "当日涨跌幅",
                "when_present": ["sector_return", "lifecycle_phase", "sector_return_pct"],
            }
        ],
    },
]

RRG_RAW_KEEP = [
    "trade_date", "industry_code", "idx_type", "rrg_quadrant",
    "relative_strength", "relative_momentum", "raw_rs_20d", "raw_mom_5d", "benchmark_code",
]

RRG_STAGES = [
    {
        # RRG 轨迹表只有板块代码没有名称，代码清单对内容生产无意义；
        # 保留全市场（行业+概念+地域）象限分布，与 lifecycle 端点的行业板块分布互补
        "mode": "join",
        "count_by": "rrg_quadrant",
        "facts": [
            {
                "statement": "行业 RRG 象限分布（相对沪深300）：{__counts__}",
                "value": "{__count__}",
                "subject": "行业结构",
                "predicate": "RRG象限分布",
                "when_present": ["__counts__"],
            }
        ],
    },
]

# service_key → 端点配置（name 唯一，upsert 依据）
ENDPOINTS = [
    {
        "name": "DreamO 市场情绪看板",
        "service_key": "review-market-sentiment",
        "title_template": "DreamO 市场情绪看板 {today}",
        "interval_minutes": 1440,
        "fact_mapping": {
            "items_path": "data.rows",
            "as_of_field": "trade_date",
            "stages": [SENTIMENT_STAGE_AGG, SENTIMENT_STAGE_INDICATORS],
        },
        "pagination": None,
    },
    {
        "name": "DreamO 前瞻风险看板",
        "service_key": "review-forward-risk",
        "title_template": "DreamO 前瞻风险看板 {today}",
        "interval_minutes": 1440,
        "fact_mapping": {
            "items_path": "data.rows",
            "as_of_field": "trade_date",
            "stages": FORWARD_RISK_STAGES,
        },
        "pagination": None,
    },
    {
        "name": "DreamO 行业复盘×生命周期看板（行业板块）",
        "service_key": "review-industry-lifecycle",
        "title_template": "DreamO 行业复盘看板 {today}",
        "interval_minutes": 1440,
        "fact_mapping": {
            "items_path": "data.rows",
            "as_of_field": "trade_date",
            "raw_keep_fields": INDUSTRY_RAW_KEEP,
            "stages": INDUSTRY_STAGES,
        },
        "pagination": {"type": "offset", "limit_param": "limit", "offset_param": "offset",
                       "page_size": 150, "offset_start": 0, "max_pages": 8},
    },
    {
        "name": "DreamO 行业 RRG 轨迹",
        "service_key": "review-industry-rrg-trails",
        "title_template": "DreamO 行业 RRG 轨迹 {today}",
        "interval_minutes": 1440,
        "fact_mapping": {
            "items_path": "data.rows",
            "as_of_field": "trade_date",
            "raw_keep_fields": RRG_RAW_KEEP,
            "stages": RRG_STAGES,
        },
        "pagination": {"type": "offset", "limit_param": "limit", "offset_param": "offset",
                       "page_size": 500, "offset_start": 0, "max_pages": 5},
    },
]

def main() -> None:
    with SessionLocal() as db:
        connector = db.query(Connector).filter(Connector.name == CONNECTOR_NAME).first()
        if not connector:
            print(f"✗ 未找到 Connector「{CONNECTOR_NAME}」，请先在页面创建")
            sys.exit(1)

        connector.auth_style = "header"
        connector.auth_header_name = "X-API-Key"
        connector.api_key_env = "DREAMO_DATA_API_KEY"

        removed = 0
        for ep in list(connector.endpoints):
            if ep.path.startswith("/api/v1/review/"):
                db.delete(ep)
                removed += 1

        created = updated = 0
        for spec in ENDPOINTS:
            ep = db.query(ConnectorEndpoint).filter(
                ConnectorEndpoint.connector_id == connector.id,
                ConnectorEndpoint.name == spec["name"],
            ).first()
            values = {
                "path": SERVICE_PATH.format(key=spec["service_key"]),
                "method": "GET",
                "params_json": {},
                "title_template": spec["title_template"],
                "as_of_path": "data.rows.0.trade_date",
                "trust_level": 0.95,
                "fact_mapping_json": spec["fact_mapping"],
                "pagination_json": spec["pagination"],
                "interval_minutes": spec["interval_minutes"],
            }
            if ep is None:
                db.add(ConnectorEndpoint(connector_id=connector.id, name=spec["name"], **values))
                created += 1
            else:
                for k, v in values.items():
                    setattr(ep, k, v)
                updated += 1
        db.commit()
        print(f"✓ Connector 切换到 X-API-Key（env: DREAMO_DATA_API_KEY）")
        print(f"✓ 删除旧临时端点 {removed} 个；新建 {created} 个，更新 {updated} 个")
        for ep in connector.endpoints:
            print(f"  - {ep.name} → {ep.path}（{ep.interval_minutes or 0} 分钟周期，0=仅手动）")


if __name__ == "__main__":
    main()
