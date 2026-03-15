# TuneAI

印刷简谱移调：上传 PNG/JPG 简谱图，选择目标调，输出保留原布局的移调图。

## 目录结构

- `frontend/` — 前端（Jinja2 模板 + 静态资源）
- `backend/tuneai/` — 后端（FastAPI + 核心流水线）
- `data/samples/` — 测试样本；`data/outputs/` — 临时输出
- `assets/fonts/` — 渲染字体
- `docs/` — 项目文档
- `tests/` — 测试

## 本地运行

```bash
pip install -r requirements.txt
python run.py
# 或: uvicorn backend.tuneai.main:app --reload
```

详见 `docs/项目架构与模块说明.md` 与 `TuneAI_完整执行方案.md`。
