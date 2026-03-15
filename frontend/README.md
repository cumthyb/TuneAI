# TuneAI 前端

基于 **React** + **Tailwind CSS**，使用 **Vite** 打包，源码为 **TypeScript**（`.ts` / `.tsx`），便于阅读与维护。

## 技术栈

- **TypeScript** — 源码与类型
- **React** — UI 与状态
- **SCSS** — 样式（替代纯 CSS，支持变量、嵌套等）
- **Tailwind CSS** — 工具类（在 SCSS 中通过 @tailwind 引入）
- **Vite** — 开发服务器与生产构建

## 脚本

- `npm run dev` — 启动 Vite 开发服务器（热更新）
- `npm run build` — 生产构建，输出到 `dist/`（由后端在方案 A 下托管）
- `npm run preview` — 本地预览构建结果

## 模块职责（与架构文档对应）

- 上传：选图、目标调、提交 `POST /api/transpose`
- 加载状态：处理中、错误提示
- 结果展示：原图/结果图对比、warnings
- 下载：结果图、JSON、调试信息（含 request_id）
- 前端日志：操作与请求摘要（可与后端 request_id 关联）

## 与后端联调

- 生产/联调：先 `npm run build`，后端托管 `frontend/dist`，同一端口访问。
- 纯前端开发：`npm run dev`，在 Vite 中配置代理将 `/api` 转发到后端端口，或后端开启 CORS。
