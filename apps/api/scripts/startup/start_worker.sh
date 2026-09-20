#!/bin/zsh
# Studio Celery worker + beat 常驻启动（launchd 调用）
cd /Users/mshengran/Project/AIContentStudio/apps/api
set -a
source ./scripts/startup/runtime.env
set +a
export TASK_QUEUE_ENABLED=true
export CELERY_BROKER_URL=redis://localhost:6379/2
exec .venv/bin/python -m celery -A app.tasks.celery_app worker -Q default,llm,ingestion,export -B -c 1 --loglevel=info
