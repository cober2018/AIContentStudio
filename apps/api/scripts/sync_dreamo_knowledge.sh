#!/bin/zsh
# 从 DreamOAgents 同步领域知识三件套到 Studio 知识目录（幂等，可重复执行）。
# 用法：./scripts/sync_dreamo_knowledge.sh [DreamOAgents仓库根目录]
# 同步后立即生效（mtime 缓存自动失效），无需重启 API。

set -euo pipefail

SRC_ROOT="${1:-/Users/mshengran/Project/DreamOAgents}"
SRC_DIR="$SRC_ROOT/docs/review"
DST="$(dirname "$0")/../app/llm/knowledge"

for f in 方法论.md 指标字典.md 复盘看板指标定义与财经写作方法论.md; do
  if [[ -f "$SRC_DIR/$f" ]]; then
    cp "$SRC_DIR/$f" "$DST/$f"
    echo "✓ $f（$(wc -l < "$DST/$f" | tr -d ' ') 行）"
  else
    echo "✗ 缺少 $SRC_DIR/$f"
    MISSING=1
  fi
done

if [[ -n "${MISSING:-}" ]]; then
  echo "部分文档未就绪，仅同步了已有文件。"
  exit 1
fi
echo "全部同步完成 → $DST"
