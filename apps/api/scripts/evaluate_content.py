"""Golden 评测 CLI（EPIC-15）：对 golden_topics.json 全量跑 生成→FactCheck，输出质量指标。

用法：cd apps/api && python scripts/evaluate_content.py [--limit N]
说明：
- 强制 LLM_PROVIDER=mock（评测的是管线与确定性基线，接真实模型后同一数据集对比）
- 使用独立临时 SQLite 库，不污染开发数据
- 指标：生成成功率 / 无来源数字率 / Fact 覆盖率 / 校验通过率
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("MOCK_INJECT_UNFACT_NUMBER", "false")

from app.config import get_settings

get_settings.cache_clear()

from app.db import Base, SessionLocal
from app.models import (
    Draft,
    Fact,
    FactPack,
    FactPackItem,
    FactPackStatus,
    FactStatus,
    ParseStatus,
    SourceDocument,
    TopicBrief,
)
from app.services import factchecker
from app.services.factpack_service import fact_checksum
from app.services.generation import orchestrator

GOLDEN_PATH = Path(__file__).resolve().parents[1] / "evals" / "golden_topics.json"
REPORT_DIR = Path(__file__).resolve().parents[1] / "evals" / "reports"

CHANNEL_NAMES = {"douyin": "抖音", "xiaohongshu": "小红书", "wechat": "公众号"}


def setup_database() -> None:
    """评测用临时库：换掉引擎指向再建表。"""
    tmp = tempfile.mkdtemp(prefix="studio-eval-")
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/eval.db"
    from app import config

    config.get_settings.cache_clear()
    import app.db as dbmod

    dbmod.engine = dbmod.create_engine(os.environ["DATABASE_URL"])
    dbmod.SessionLocal = dbmod.sessionmaker(bind=dbmod.engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(dbmod.engine)
    # 重绑定脚本内使用的 engine/SessionLocal
    global engine, SessionLocal
    engine, SessionLocal = dbmod.engine, dbmod.SessionLocal


def used_fact_ids(structured: dict | None) -> set[str]:
    if not structured:
        return set()
    used: set[str] = set()
    for scene in structured.get("scenes", []) or []:
        used.update(scene.get("fact_ids", []) or [])
    for claim in structured.get("claim_fact_map", []) or []:
        used.update(claim.get("fact_ids", []) or [])
    return used


def seed_topic(db, spec: dict) -> tuple[TopicBrief, list[Fact]]:
    as_of = spec.get("as_of")
    doc = SourceDocument(
        title=f"[golden] {spec['id']} {spec['title'][:40]}",
        source_type="text",
        mime_type="text/plain",
        as_of=as_of,
        trust_level=1.0,
        raw_text=spec["source_text"],
        parse_status=ParseStatus.done.value,
    )
    db.add(doc)
    db.flush()

    facts = []
    for f in spec["facts"]:
        fact = Fact(
            source_document_id=doc.id,
            statement=f["statement"],
            fact_type="metric",
            subject=f.get("subject"),
            predicate=f.get("predicate"),
            value_json={"value": f["value"]},
            unit=f.get("unit") or None,
            as_of=f.get("as_of") or as_of,
            confidence=1.0,
            status=FactStatus.confirmed.value,
            created_by="eval",
        )
        db.add(fact)
        facts.append(fact)
    db.flush()

    pack = FactPack(
        name=f"[golden] {spec['id']}",
        version=1,
        status=FactPackStatus.frozen.value,
        checksum=fact_checksum(facts),
        frozen_at=datetime.now(UTC),
    )
    db.add(pack)
    db.flush()
    for fact in facts:
        db.add(FactPackItem(fact_pack_id=pack.id, fact_id=fact.id))

    topic = TopicBrief(
        title=spec["title"],
        audience=spec.get("audience"),
        goal=spec.get("goal"),
        angle=spec.get("angle"),
        core_thesis=spec.get("core_thesis"),
        cta=spec.get("cta"),
        channels=spec["channels"],
        must_include_json=spec.get("must_include", []),
        forbidden_json=spec.get("forbidden", []),
        fact_pack_id=pack.id,
        fact_pack_version=pack.version,
        created_by="eval",
    )
    db.add(topic)
    db.commit()
    return topic, facts


def evaluate_topic(db, spec: dict) -> dict:
    topic, facts = seed_topic(db, spec)
    jobs = orchestrator.create_jobs_for_topic(db, topic, spec["channels"])

    drafts: list[Draft] = []
    failed_channels: list[str] = []
    for job in jobs:
        try:
            drafts.append(orchestrator.run_generation_for_job(db, job))
        except orchestrator.GenerationError:
            failed_channels.append(job.channel)
    db.commit()

    topic_text = " ".join(filter(None, [topic.title, topic.core_thesis, topic.angle, topic.goal]))
    pack_facts = {f"F{f.id:03d}": f for f in facts}

    row = {
        "id": spec["id"],
        "category": spec["category"],
        "title": spec["title"],
        "channel_total": len(jobs),
        "channel_failed": failed_channels,
        "drafts": [],
    }
    for draft in drafts:
        result = factchecker.run_deterministic_check(
            draft.body,
            [
                {
                    "id": fid,
                    "statement": f.statement,
                    "value": (f.value_json or {}).get("value"),
                    "unit": f.unit,
                    "as_of": f.as_of,
                }
                for fid, f in pack_facts.items()
            ],
            topic_text,
            topic.forbidden_json or [],
            spec["source_text"],
        ) if draft else None
        number_blockers = [i for i in (result.issues if result else []) if i.category == "number" and i.severity == "blocker"]
        coverage = len(used_fact_ids(draft.structured_json) & set(pack_facts)) / len(pack_facts) if pack_facts else 0
        row["drafts"].append(
            {
                "channel": draft.content_job.channel if draft else "?",
                "revision": draft.revision_no,
                "check": result.result if result else "error",
                "blockers": len([i for i in (result.issues if result else []) if i.severity == "blocker"]),
                "warnings": len([i for i in (result.issues if result else []) if i.severity == "warning"]),
                "unfact_numbers": len(number_blockers),
                "fact_coverage": round(coverage, 3),
            }
        )
    return row


def summarize(rows: list[dict]) -> dict:
    all_drafts = [d for r in rows for d in r["drafts"]]
    total_jobs = sum(r["channel_total"] for r in rows)
    total_failed = sum(len(r["channel_failed"]) for r in rows)
    return {
        "topics": len(rows),
        "jobs_total": total_jobs,
        "jobs_failed": total_failed,
        "generation_success_rate": round(1 - total_failed / total_jobs, 4) if total_jobs else 0,
        "drafts_checked": len(all_drafts),
        "unfact_number_rate": round(sum(1 for d in all_drafts if d["unfact_numbers"] > 0) / len(all_drafts), 4) if all_drafts else 0,
        "blocked_rate": round(sum(1 for d in all_drafts if d["check"] == "blocker") / len(all_drafts), 4) if all_drafts else 0,
        "warning_rate": round(sum(1 for d in all_drafts if d["check"] == "warning") / len(all_drafts), 4) if all_drafts else 0,
        "pass_rate": round(sum(1 for d in all_drafts if d["check"] == "pass") / len(all_drafts), 4) if all_drafts else 0,
        "avg_fact_coverage": round(sum(d["fact_coverage"] for d in all_drafts) / len(all_drafts), 4) if all_drafts else 0,
    }


def write_reports(rows: list[dict], summary: dict) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    json_path = REPORT_DIR / f"eval-{stamp}.json"
    json_path.write_text(json.dumps({"summary": summary, "topics": rows}, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Golden 评测报告",
        "",
        f"- 时间：{datetime.now(UTC).isoformat()}",
        f"- Provider：{os.environ.get('LLM_PROVIDER', 'mock')}",
        "",
        "| 指标 | 数值 |",
        "|---|---|",
    ]
    labels = {
        "topics": "Topic 数",
        "jobs_total": "生成任务数",
        "jobs_failed": "失败任务数",
        "generation_success_rate": "生成成功率",
        "drafts_checked": "评测稿件数",
        "unfact_number_rate": "无来源数字率（稿件维度）",
        "blocked_rate": "blocker 稿件占比",
        "warning_rate": "warning 稿件占比",
        "pass_rate": "全 pass 稿件占比",
        "avg_fact_coverage": "Fact 平均覆盖率",
    }
    for key, label in labels.items():
        lines.append(f"| {label} | {summary[key]} |")
    lines += ["", "## 明细", "", "| Topic | 渠道 | 校验 | blocker | warning | 无来源数字 | 覆盖率 |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        for d in r["drafts"]:
            lines.append(
                f"| {r['id']} {r['title'][:18]} | {CHANNEL_NAMES.get(d['channel'], d['channel'])} "
                f"| {d['check']} | {d['blockers']} | {d['warnings']} | {d['unfact_numbers']} | {d['fact_coverage']} |"
            )
    md_path = REPORT_DIR / f"eval-{stamp}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"报告：{md_path}\n      {json_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="只跑前 N 个 topic（调试用）")
    args = parser.parse_args()

    setup_database()
    spec_data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    topics = spec_data["topics"]
    if args.limit:
        topics = topics[: args.limit]

    rows = []
    with SessionLocal() as db:
        for spec in topics:
            row = evaluate_topic(db, spec)
            rows.append(row)
            status = "OK" if not row["channel_failed"] else f"FAILED: {row['channel_failed']}"
            print(f"[{row['id']}] {status}")

    summary = summarize(rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    write_reports(rows, summary)


if __name__ == "__main__":
    main()
