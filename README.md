# TuneAI

印刷简谱移调：上传 PNG/JPG 简谱图，选择目标调，输出保留原布局的移调图。

## 目录结构

- `frontend/` — 前端（**React + Tailwind CSS**，**Vite** 打包，npm 管理依赖）
- `backend/tuneai/` — 后端（FastAPI + 核心流水线，Poetry 管理 Python 依赖）
- `data/samples/` — 测试样本；`data/outputs/` — 临时输出
- `assets/fonts/` — 渲染字体
- `docs/` — 项目文档
- `tests/` — 测试

## 依赖管理

- **Python**：Poetry（`pyproject.toml`）
- **前端**：npm（`frontend/package.json`），React + Tailwind CSS，Vite 构建

## 配置

复制 `config.example.json` 为 `config.json`（项目根目录），按需修改：

- **server**：`host`、`port`
- **llm**：文本模型配置（可纯配置切换 Qwen/GLM），包含 `provider`、`base_url`、`api_key`、`model`、`client_class`、`client_kwargs`、`model_kwargs`、`extra_body`、`temperature`、`max_tokens`、`timeout_seconds`
- **vision_llm**：视觉模型配置（可纯配置切换 Qwen/GLM），字段同上（通常不需要 `temperature`）
- **ocr**：OCR 配置位于 `providers.<name>.ocr`，其中 `runner` 为 `module:function` 动态入口（例如 `tuneai.core.adapters.ocr.providers.qwen:run_qwen_ocr`、`tuneai.core.adapters.ocr.providers.glm:run_glm_ocr`）
- 前端提交时支持分别选择 `llm_provider`、`vision_llm_provider`、`ocr_provider`，默认值来自 `/api/meta` 的 `default_*_provider`
- **pipeline**：请求超时、临时目录、是否自动清理
- **logging**：`level`（DEBUG/INFO/WARNING/ERROR）、`format`（json/text）、`request_id_header`
- **frontend**：`build_dir`（Vite 默认 `frontend/dist`）、`dev_port`（开发服务器端口，默认 5173）

`config.json` 已加入 `.gitignore`，不会提交；敏感项建议用环境变量覆盖（如 `TUNEAI_LLM_API_KEY`、`TUNEAI_LLM_PROVIDER`、`TUNEAI_LLM_MODEL`、`TUNEAI_VISION_LLM_API_KEY`、`TUNEAI_VISION_LLM_PROVIDER`、`TUNEAI_VISION_LLM_MODEL`、`TUNEAI_OCR_PROVIDER`、`TUNEAI_OCR_RUNNER`、`TUNEAI_OCR_API_KEY`、`TUNEAI_OCR_BASE_URL`、`TUNEAI_OCR_MODEL`）。

### 前端与部署（方案 A，单端口）

前端使用 **React + Tailwind CSS**，由 **Vite** 打包。生产部署采用方案 A：同一端口提供页面与 API。

1. 在 `frontend/` 下执行 `npm run build`，构建产物输出到 `frontend/dist`（可在 config 中通过 `frontend.build_dir` 修改）。
2. 启动后端后，访问同一端口即可：页面与 `POST /api/transpose` 均由后端提供，SPA 路由由后端回退到 `index.html`。

## 本地运行

### 入口约定（必须遵守）

- 面向开发者的统一入口是 `Makefile`：日常启动、测试、构建只使用 `make ...`
- `backend/run.py` 保留为后端启动实现，不作为团队日常手动入口
- 仅在调试启动参数或排查 `Makefile` 本身时，才直接执行 `python backend/run.py --mode ...`

### 1. 安装 Python 依赖（Poetry）

```bash
poetry install
```

### 2. 安装前端依赖并构建（npm + Vite）

```bash
cd frontend && npm install && npm run build && cd ..
```

### 3. 启动后端（托管前端构建产物与 API，单端口）

```bash
# 开发模式（启用 reload）
make dev
# 生产模式（关闭 reload）
make prod
```

访问配置的端口（默认 8000）即可使用上传页与 API。

### 前端开发（热更新，单独端口）

```bash
make web
# Vite 开发服务器端口由 config.json 的 frontend.dev_port 决定（默认 5173），/api 已代理到后端 server.port
```

### 生成 requirements.txt（部署用）

```bash
poetry export -f requirements.txt -o requirements.txt --without-hashes
```

详见 `docs/项目架构与模块说明.md` 与 `docs/TuneAI_完整执行方案.md`。
