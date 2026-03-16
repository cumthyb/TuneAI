# TuneAI — 统一命令入口
# 用法: make <target>
#
# 快速启动：
#   make dev       先构建前端，再启动后端开发服务器（reload on）
#   make prod      先构建前端，再启动后端生产服务器（reload off）
#   make test      运行所有单元测试（OCR/LLM/Music/API/Pipeline 均 mock 外部引擎）
#
# 其他：
#   make web       启动前端开发服务器（Vite, port 来自 config.json）
#   make install   安装所有依赖（前端 npm + 后端 poetry）
#   make build     构建前端产物（frontend/dist）
#   make test-int  运行集成测试（需要真实 OCR 模型 + LLM 服务）
#   make lint      检查前端代码风格
#   make help      显示此帮助

.PHONY: help dev prod web test test-int install build lint
# Note: $(VENV)/bin/python is intentionally NOT .PHONY — Make uses it as a file sentinel
.DEFAULT_GOAL := help

# 使用项目内 .venv（Python 3.12）
VENV    := .venv
PYTHON  := $(VENV)/bin/python
PYTEST  := $(VENV)/bin/pytest
POETRY  := $(VENV)/bin/poetry

FRONTEND_DIR := frontend
RUN_ENTRY := backend/run.py

# 统一后端导入路径：run.py / pytest 都依赖 tuneai 包
export PYTHONPATH := backend

SERVER_PORT := $(shell $(PYTHON) -c "from tuneai.config import get_server_port; print(get_server_port())" 2>/dev/null || echo unknown)
FRONTEND_PORT := $(shell $(PYTHON) -c "from tuneai.config import get_frontend_config; print(get_frontend_config().get('dev_port', 'unknown'))" 2>/dev/null || echo unknown)

# ── 默认目标 ────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  TuneAI 命令入口"
	@echo ""
	@echo "  make dev        先构建前端再启动后端 (uvicorn + reload → http://localhost:$(SERVER_PORT))"
	@echo "  make prod       先构建前端再启动后端 (uvicorn no-reload → http://localhost:$(SERVER_PORT))"
	@echo "  make web        启动前端开发服务器  (Vite → http://localhost:$(FRONTEND_PORT))"
	@echo "  make test       运行所有单元测试     (外部引擎均 mock，无需 OCR 模型/LLM 服务)"
	@echo "  make test-int   运行集成测试         (需要真实 OCR 模型 + LLM 服务)"
	@echo "  make install    安装所有依赖         (前端 npm + 后端 poetry)"
	@echo "  make build      构建前端产物         (frontend/dist)"
	@echo "  make lint       前端代码检查"
	@echo ""

# ── 启动 ────────────────────────────────────────────────────────────────────

dev: build
	@echo "→ 启动后端开发服务器 (http://localhost:$(SERVER_PORT), reload=on) ..."
	@echo "  文档: http://localhost:$(SERVER_PORT)/docs"
	$(PYTHON) $(RUN_ENTRY) --mode dev

prod: build
	@echo "→ 启动后端生产服务器 (http://localhost:$(SERVER_PORT), reload=off) ..."
	@echo "  文档: http://localhost:$(SERVER_PORT)/docs"
	$(PYTHON) $(RUN_ENTRY) --mode prod

web:
	@echo "→ 启动前端开发服务器 (http://localhost:$(FRONTEND_PORT)) ..."
	cd $(FRONTEND_DIR) && npm run dev

# ── 测试 ────────────────────────────────────────────────────────────────────

# 单元测试：所有外部引擎（PaddleOCR、LLM）均通过 mock 替换
# 涵盖：tests/ 下按模块目录组织的全部单测
test:
	@echo "→ 运行单元测试（外部引擎均 mock）..."
	$(PYTEST) tests/ -v

# 集成测试：需要本地 OCR 模型已下载 + LLM 服务可访问
test-int:
	@echo "→ 运行集成测试（需要真实 OCR 模型 + LLM 服务）..."
	$(PYTEST) tests/ --run-integration -v

# ── 安装 / 构建 ─────────────────────────────────────────────────────────────

install:
	@echo "→ 安装前端依赖..."
	cd $(FRONTEND_DIR) && npm install
	@echo "→ 安装后端依赖 (使用 .venv/bin/poetry) ..."
	POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_VIRTUALENVS_CREATE=true $(POETRY) install
	@echo "✓ 安装完成"

build:
	@echo "→ 构建前端产物 (frontend/dist) ..."
	cd $(FRONTEND_DIR) && npm run build
	@echo "✓ 构建完成，产物位于 frontend/dist/"

lint:
	@echo "→ 前端代码检查..."
	cd $(FRONTEND_DIR) && npm run lint
