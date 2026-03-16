# LLM / 视觉 / OCR 选型对比（DashScope vs BigModel）

> 更新时间：2026-03（基于当前项目讨论稿，后续以官方文档为准）

## 阿里云百炼（DashScope）— Qwen 系列

- 平台：`dashscope.aliyuncs.com`

### LLM 文本

| 推荐模型 | 说明 |
|---|---|
| `qwen3-max` | 旗舰，支持思考/非思考双模式 |
| `qwen3.5-plus` | 新一代均衡款，纯文本+视觉三合一 |
| `qwen3.5-flash` | 低成本高速，适合高频任务 |
| `qwen3-235b-a22b` | 开源 MoE 超大参数 |

- 备注：支持联网搜索 `enable_search=True`；上下文最大 128K。

### 视觉模型

| 推荐模型 | 说明 |
|---|---|
| `qwen3-vl-plus` | 图像+视频理解旗舰，支持思考模式 |
| `qwen3-vl-flash` | 快速视觉推理，低延迟低成本 |
| `qvq-max` | 视觉推理增强，擅长图表/数学/科学题 |

- 备注：支持本地图片 base64 / 图片 URL / 视频片段；最大 3600 张图/请求。

### 多模态

| 推荐模型 | 说明 |
|---|---|
| `qwen3-omni-flash` | 文本+图像+语音+视频全模态，支持音频流输出 |
| `qwen3-vl-embedding` | 文本/图像/视频 -> 统一向量空间 |

- 备注：Omni 需设置 `modalities` 参数；Embedding 需 DashScope 专属 SDK。

### OCR

| 推荐模型 | 说明 |
|---|---|
| `qwen-vl-ocr-latest` | 专用文字提取，支持票据/表格/手写体/公式识别 |
| `qwen-vl-ocr-2025-08-28` | OCR 固定快照版本 |

- 备注：内置任务含信息抽取、表格解析、多语种识别（26 种语言）；接口同视觉模型，`max_tokens` 默认 4096，可申请 8192。

---

## 智谱AI（BigModel / Z.ai）— GLM 系列

- 平台：`open.bigmodel.cn`

### LLM 文本

| 推荐模型 | 说明 |
|---|---|
| `GLM-5` | 最新旗舰基座，编码对标 Claude Opus 4.5，擅长 Agentic 长程规划；200K 上下文，128K 输出 |
| `GLM-4.7` | 高智能通用，推理+编程全面升级 |
| `GLM-4.7-FlashX` | 轻量高速，适合中文写作/翻译/情感角色扮演 |
| `GLM-4.6` | 高级编码+推理+工具调用，200K 上下文 |

- 备注：支持深度思考模式；兼容 OpenAI Chat 接口格式。

### 视觉模型

| 推荐模型 | 说明 |
|---|---|
| `GLM-4.6V` | 旗舰视觉推理（106B-A12B），原生工具调用，128K 视觉上下文，可处理约 150 页文档或 1 小时视频 |
| `GLM-4.6V-Flash` | 轻量版（9B），免费可用，支持本地部署 |
| `GLM-4.1V-Thinking` | 多模态推理增强版（9B，强化学习），部分基准超越 GPT-4o |
| `GLM-4V-Flash` | 免费图像理解，支持 26 种语言 |

- 备注：`GLM-4.6V` 支持 SGLang / vLLM / transformers 框架本地部署。

### 多模态

| 推荐模型 | 说明 |
|---|---|
| `GLM-Realtime` | 端到端多模态，近实时视频理解+语音交互，支持 Function Call，2 分钟长记忆 |
| `GLM-4.5` | 推理/代码/Agentic 原生融合的 Agent 基座模型，开源 SOTA |
| `embedding-3` | 文本向量化，支持 2048 维 |

- 备注：`GLM-Realtime` 需 WebSocket 接口；`GLM-4.5` 已开源可本地部署。

### OCR

| 推荐模型/方案 | 说明 |
|---|---|
| `GLM-OCR`（预览） | 专用 OCR 模型（2026-01 已有 GitHub 仓库），专注复杂视觉场景文字提取与文档理解 |
| `GLM-4.6V`（通用替代） | 视觉旗舰直接做 OCR，128K 上下文适合长文档 |
| 独立 OCR 服务 API | 平台提供工具化 OCR 能力（`docs.bigmodel.cn/cn/guide/tools/zhipu-ocr`） |

- 备注：`GLM-OCR` API 正式版尚未完全开放，现阶段可先用 `GLM-4.6V` 替代。

---

## 工程落地建议（面向 TuneAI）

| 能力层 | 建议配置键 | 备注 |
|---|---|---|
| 文本 LLM | `llm` | 保持 OpenAI-compatible 抽象（`base_url` / `api_key` / `model`） |
| 视觉理解 | `vision_llm` | 与文本层解耦，独立模型与参数 |
| OCR | `ocr.provider + ocr.config` | 用 provider 路由（如 `aliyun` / `dashscope_vl_ocr` / `bigmodel_vlm_ocr`） |

## `config.json` 示例

### 示例 A：DashScope（Qwen）

```json
{
  "llm": {
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key": "YOUR_DASHSCOPE_API_KEY",
    "model": "qwen3.5-plus",
    "temperature": 0.1,
    "max_tokens": 1024,
    "timeout_seconds": 30
  },
  "vision_llm": {
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key": "YOUR_DASHSCOPE_API_KEY",
    "model": "qwen3-vl-plus",
    "timeout_seconds": 30
  },
  "ocr": {
    "provider": "qwen",
    "config": {
      "access_key_id": "YOUR_ALIYUN_ACCESS_KEY_ID",
      "access_key_secret": "YOUR_ALIYUN_ACCESS_KEY_SECRET",
      "endpoint": "ocr-api.cn-hangzhou.aliyuncs.com",
      "timeout_seconds": 15
    }
  }
}
```

### 示例 B：BigModel（GLM）

```json
{
  "llm": {
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "api_key": "YOUR_BIGMODEL_API_KEY",
    "model": "GLM-4.7",
    "temperature": 0.1,
    "max_tokens": 1024,
    "timeout_seconds": 30
  },
  "vision_llm": {
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "api_key": "YOUR_BIGMODEL_API_KEY",
    "model": "GLM-4.6V",
    "timeout_seconds": 30
  },
  "ocr": {
    "provider": "bigmodel_vlm_ocr",
    "config": {
      "base_url": "https://open.bigmodel.cn/api/paas/v4",
      "api_key": "YOUR_BIGMODEL_API_KEY",
      "model": "GLM-4.6V",
      "timeout_seconds": 30
    }
  }
}
```

> 说明：示例 B 的 `ocr.provider = "bigmodel_vlm_ocr"` 代表目标接入形态；若当前代码尚未实现该 provider，可先临时使用 `qwen`，待 provider 实现后无缝切换。

