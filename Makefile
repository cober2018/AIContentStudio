.PHONY: dev dev-web dev-token worker beat stop seed migrate test lint format backup prune-logs compose-up compose-down

# 备份放项目外（库里有明文密钥，避免被同步盘/打包带走）；历史备份已迁至该目录
BACKUP_DIR ?= $(HOME)/Backups/AIContentStudio/make-backups
BACKUP_KEEP ?= 7

# 启动后端（默认 SQLite，零依赖）。本机令牌文件存在后，API 拒绝没有 X-Studio-Local-Token 的请求。
dev: dev-token
	cd apps/api && . .venv/bin/activate 2>/dev/null || true; \
	LOCAL_DEV_TOKEN=$$(cat scripts/startup/local-dev-token) python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Celery worker：消费 default/llm/ingestion/export 队列（需 Redis，先 compose-up）
worker:
	cd apps/api && . .venv/bin/activate 2>/dev/null || true; \
	python -m celery -A app.tasks.celery_app worker -Q default,llm,ingestion,export --loglevel=INFO -c 2

# 启动前端。代理会带上和后端相同的本机令牌，浏览器本身拿不到这串值。
dev-web: dev-token
	cd apps/web && npm run dev

dev-token:
	@mkdir -p apps/api/scripts/startup
	@if [ ! -s apps/api/scripts/startup/local-dev-token ]; then umask 077; openssl rand -hex 32 > apps/api/scripts/startup/local-dev-token; fi

# 初始化数据库 + 种子数据（管理员、渠道模板、Brand Voice、Prompt 版本）
seed:
	cd apps/api && python -m app.seed

# 执行数据库迁移（生产/PostgreSQL 环境建表走这里，替代 create_all）
migrate:
	cd apps/api && . .venv/bin/activate 2>/dev/null || true; \
	python -m alembic upgrade head

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
# BACKUP_DIR 已是绝对路径，cd apps/api 后 sqlite3 .backup 直接用绝对目标
backup:
	@mkdir -p $(BACKUP_DIR)
	@stamp=$$(date +%Y%m%d-%H%M%S); \
	cd apps/api && sqlite3 content_studio.db ".backup '$(BACKUP_DIR)/content_studio-$$stamp.db'"; \
	echo "已备份: $(BACKUP_DIR)/content_studio-$$stamp.db"; \
	ls -t $(BACKUP_DIR)/content_studio-*.db 2>/dev/null | tail -n +$$(($(BACKUP_KEEP) + 1)) | xargs rm -f 2>/dev/null || true

# 清理 7 天前的本地日志（uvicorn/worker 重定向产物无自动轮转）
prune-logs:
	find logs -type f -mtime +7 -delete 2>/dev/null || true; \
	echo "logs/ 已清理（保留近 7 天），当前大小: $$(du -sh logs 2>/dev/null | cut -f1)"
