# TuneAI 前端

基于 **React** + **TypeScript** + **Tailwind CSS**，使用 **Vite** 打包，负责：

- 上传简谱图片与目标调；  
- 轮询 `GET /api/meta` 获取服务状态与可用 providers；  
- 通过 `POST /api/transpose` 获取移调结果图片与结构化 JSON，并提供结果展示与下载。

> 整体项目结构、后端架构与部署方式请以根目录的 `README.md` 为准，此处只介绍前端内部细节。

## 技术栈

- **TypeScript** — 源码与类型。  
- **React** — UI 与状态管理（单页应用，无前端路由库）。  
- **SCSS** — 样式（支持变量与嵌套）。  
- **Tailwind CSS** — 原子化工具类（在 SCSS 中通过 `@tailwind` 引入）。  
- **Vite** — 开发服务器与生产构建。  

## 脚本

- `npm run dev` — 启动 Vite 开发服务器（热更新）。  
- `npm run build` — 生产构建，输出到 `dist/`（在方案 A 下由后端托管）。  
- `npm run preview` — 本地预览构建结果。  

## 模块职责（与架构文档对应）

- 上传与表单：选图、目标调与 provider 选择、提交 `POST /api/transpose`。  
- 加载状态：处理中动画、错误提示、重试操作。  
- 结果展示：原图/结果图查看、结果 JSON 查看、warnings 展示。  
- 下载：结果图、JSON、调试信息（含 `request_id`）。  
- 前端日志：记录用户操作与请求摘要（可与后端 `request_id` 关联）。  

## 与后端联调

- 生产/联调：先 `npm run build`，再通过后端托管 `frontend/dist`，同一端口访问（详见根目录 `README.md` 的“部署与生产模式”章节）。  
- 纯前端开发：`npm run dev`，由 Vite 将 `/api` 代理到后端端口（代理目标由根目录 `config.json` 中的 `server` 配置决定）。  
