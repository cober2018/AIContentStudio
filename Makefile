.PHONY: dev dev-web worker stop seed test lint format backup compose-up compose-down

BACKUP_DIR ?= backups
BACKUP_KEEP ?= 7

# 启动后端（默认 SQLite，零依赖）
dev:
	cd apps/api && . .venv/bin/activate 2>/dev/null || true; \
	python -m uvicorn app.main:app --reload --port 8000

# Celery worker：消费 default/llm/ingestion/export 队列（需 Redis，先 compose-up）
worker:
	cd apps/api && . .venv/bin/activate 2>/dev/null || true; \
	python -m celery -A app.tasks.celery_app worker -Q default,llm,ingestion,export --loglevel=INFO -c 2

# 启动前端
dev-web:
	cd apps/web && npm run dev

# 初始化数据库 + 种子数据（管理员、渠道模板、Brand Voice、Prompt 版本）
seed:
	cd apps/api && python -m app.seed

test:
	cd apps/api && python -m pytest tests -q

lint:
	cd apps/api && python -m ruff check app tests

format:
	cd apps/api && python -m ruff format app tests

compose-up:
	docker compose up -d

compose-down:
	docker compose down

stop:
	pkill -f "uvicorn app.main:app" || true

# 在线备份 SQLite 开发库（生产 PostgreSQL 用 pg_dump，见 docs/runbooks/backup-restore.md）
backup:
	@mkdir -p $(BACKUP_DIR)
	@stamp=$$(date +%Y%m%d-%H%M%S); \
	cd apps/api && sqlite3 content_studio.db ".backup '../../$(BACKUP_DIR)/content_studio-$$stamp.db'"; \
	echo "已备份: $(BACKUP_DIR)/content_studio-$$stamp.db"; \
	ls -t $(BACKUP_DIR)/content_studio-*.db 2>/dev/null | tail -n +$$(($(BACKUP_KEEP) + 1)) | xargs rm -f 2>/dev/null || true
