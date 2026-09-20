#!/bin/zsh
# Studio API 常驻启动（launchd 调用；也可手工执行）
cd /Users/mshengran/Project/AIContentStudio/apps/api
set -a
source ./scripts/startup/runtime.env
set +a
exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
