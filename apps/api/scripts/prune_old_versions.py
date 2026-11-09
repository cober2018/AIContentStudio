"""One-off cleanup for video works finalized before old versions were deleted automatically.

cd apps/api && .venv/bin/python scripts/prune_old_versions.py          # list only
cd apps/api && .venv/bin/python scripts/prune_old_versions.py --apply  # delete
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import runtime_config  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import ContentUnit, SystemSetting  # noqa: E402
from app.services import version_prune  # noqa: E402


def main(apply: bool) -> None:
    with SessionLocal() as db:
        runtime_config.load_from_db(db)
        row = db.get(SystemSetting, "video_chain")
        total = 0
        for unit_id in sorted(int(key) for key in (row.value or {}) if key.isdigit()) if row else []:
            unit = db.get(ContentUnit, unit_id)
            if unit is None:
                continue
            found = version_prune.plan(db, unit.project_id, unit_id)
            if found is None or not (found["executions"] or found["candidates"] or found["files"] or found["folders"]):
                continue
            info = version_prune.summary(found)
            total += info["bytes"]
            print(f"作品 #{unit_id} {unit.title}：保留任务 #{info['kept_execution_id']}；删任务 {info['execution_ids']}，"
                  f"候选 {info['candidate_ids']}，文件 {info['file_count']}，文件夹 {info['folder_count']}，{info['bytes'] / 1048576:.1f} MB")
            for path in info["files"] + info["folders"]:
                print(f"    {path}")
            if apply:
                version_prune.prune(db, unit.project_id, unit_id, "prune_old_versions")
        print(f"合计 {total / 1048576:.1f} MB" + ("，已删除" if apply else "；加 --apply 才会真删"))


if __name__ == "__main__":
    main("--apply" in sys.argv)
