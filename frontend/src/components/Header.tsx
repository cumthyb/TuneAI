import { useEffect, useState } from 'react'
import { TARGET_KEYS, type TargetKey } from '../types/api'

interface HeaderProps {
  selectedFile: File | null
  targetKey: TargetKey
  llmProvider: string
  llmProviders: string[]
  visionLlmProvider: string
  visionLlmProviders: string[]
  ocrProvider: string
  ocrProviders: string[]
  controlError: string | null
  isLoading: boolean
  systemOnline: boolean
  apiReady: boolean
  isCheckingStatus: boolean
  onTargetKeyChange: (key: TargetKey) => void
  onLlmProviderChange: (provider: string) => void
  onVisionLlmProviderChange: (provider: string) => void
  onOcrProviderChange: (provider: string) => void
  onSubmit: () => void
}

// 音频可视化柱状图组件
function AudioBars({ count = 5, active = false }: { count?: number; active?: boolean }) {
  const [bars, setBars] = useState<number[]>(Array(count).fill(0.2))

  useEffect(() => {
    if (!active) {
      setBars(Array(count).fill(0.2))
      return
    }
    const interval = setInterval(() => {
      setBars(prev => prev.map(() => 0.3 + Math.random() * 0.7))
    }, 100)
    return () => clearInterval(interval)
  }, [active, count])

  return (
    <div className="flex items-end gap-0.5">
      {bars.map((height, i) => (
        <div
          key={i}
          className="w-1 bg-gradient-to-t from-cyan-400 to-indigo-400 rounded-sm transition-all duration-100"
          style={{ height: `${height * 16}px` }}
        />
      ))}
    </div>
  )
}

// 音符符号装饰
function MusicNote({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z" />
    </svg>
  )
}

export default function Header({
  selectedFile,
  targetKey,
  llmProvider,
  llmProviders,
  visionLlmProvider,
  visionLlmProviders,
  ocrProvider,
  ocrProviders,
  controlError,
  isLoading,
  systemOnline,
  apiReady,
  isCheckingStatus,
  onTargetKeyChange,
  onLlmProviderChange,
  onVisionLlmProviderChange,
  onOcrProviderChange,
  onSubmit,
}: HeaderProps) {
  const systemTextClass = systemOnline ? 'text-emerald-300' : 'text-rose-300'
  const systemDotClass = systemOnline ? 'bg-emerald-400' : 'bg-rose-400'
  const apiTextClass = isCheckingStatus ? 'text-amber-300' : apiReady ? 'text-cyan-300' : 'text-rose-300'
  const apiLabel = isCheckingStatus ? 'CHECKING' : apiReady ? 'ONLINE' : 'DEGRADED'

  return (
    <header className="relative shrink-0 border-b border-cyan-500/20 bg-gradient-to-b from-slate-950/90 via-slate-950/80 to-slate-950/90 px-4 py-4 backdrop-blur-xl sm:px-6 lg:px-8 xl:px-10">
      {/* 顶部渐变条 */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-400/50 via-30% to-indigo-500/50 to-70% from-transparent" />

      <div className="w-full">
        {/* 标题行 */}
        <div className="mb-4 flex items-center gap-4">
          {/* Logo - 增强版 */}
          <div className="relative flex h-14 w-14 items-center justify-center">
            {/* 外围光环 */}
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 blur-xl animate-pulse" />
            {/* 旋转边框 */}
            <div
              className="absolute inset-0 rounded-2xl p-px"
              style={{
                background: 'conic-gradient(from 0deg, #06b6d4, #6366f1, #8b5cf6, #06b6d4)',
                animation: 'spin 4s linear infinite',
              }}
            />
            {/* Logo 背景 */}
            <div className="relative flex h-full w-full items-center justify-center rounded-2xl bg-slate-950">
              {/* 音波图标 */}
              <div className="flex items-center gap-0.5">
                <div className="h-3 w-1 bg-gradient-to-t from-cyan-400 to-indigo-400 rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
                <div className="h-4 w-1 bg-gradient-to-t from-cyan-400 to-indigo-400 rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
                <div className="h-5 w-1 bg-gradient-to-t from-cyan-400 to-indigo-400 rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
                <div className="h-4 w-1 bg-gradient-to-t from-cyan-400 to-indigo-400 rounded-full animate-pulse" style={{ animationDelay: '450ms' }} />
                <div className="h-3 w-1 bg-gradient-to-t from-cyan-400 to-indigo-400 rounded-full animate-pulse" style={{ animationDelay: '600ms' }} />
              </div>
              <MusicNote className="absolute -right-1 -top-1 h-4 w-4 text-cyan-400/60" />
            </div>
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-3">
              {/* 标题 */}
              <h1 className="text-2xl font-black tracking-tight sm:text-3xl">
                <span className="bg-gradient-to-r from-white via-cyan-100 to-white bg-clip-text text-transparent">
                  Tune
                </span>
                <span className="bg-gradient-to-r from-cyan-400 via-indigo-400 to-violet-400 bg-clip-text text-transparent">
                  AI
                </span>
              </h1>

              {/* AI 状态徽章 */}
              <div className="group relative">
                <div className="flex items-center gap-1.5 rounded-full border border-cyan-500/30 bg-gradient-to-r from-slate-950 to-indigo-950/50 px-3 py-1 backdrop-blur-sm">
                  <AudioBars count={4} active={isLoading} />
                  <span className="font-mono text-[10px] font-bold tracking-widest text-cyan-400">
                    {isLoading ? 'PROCESSING' : 'AI'}
                  </span>
                </div>
                {/* 悬停光效 */}
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 opacity-0 blur-sm transition-opacity group-hover:opacity-100" />
              </div>

              {/* 版本号 */}
              <span className="hidden text-[10px] font-mono text-slate-600 sm:block">v2.0</span>
            </div>

            {/* 副标题 - 音乐符号装饰 */}
            <div className="mt-1 flex items-center gap-2">
              <MusicNote className="h-3 w-3 text-indigo-400/50" />
              <p className="font-mono text-xs tracking-widest text-slate-500">
                NEURAL TRANSPOSITION ENGINE
              </p>
              <MusicNote className="h-3 w-3 text-indigo-400/50" />
            </div>
          </div>

          {/* 状态指示器 */}
          <div className="hidden items-center gap-5 text-xs font-mono sm:flex">
            {/* 系统状态 */}
            <div className="flex items-center gap-2">
              <div className={`flex h-2 w-2 items-center justify-center ${systemTextClass}`}>
                <span className={`h-2 w-2 rounded-full ${systemDotClass} ${systemOnline ? 'animate-pulse' : ''}`} />
              </div>
              <span className={`${systemTextClass}`}>
                {systemOnline ? 'SYSTEM ONLINE' : 'OFFLINE'}
              </span>
            </div>

            {/* API 状态 */}
            <div className="flex items-center gap-2">
              <AudioBars count={3} active={apiReady && !isCheckingStatus} />
              <span className={apiTextClass}>
                API {apiLabel}
              </span>
            </div>
          </div>
        </div>

        {/* 控制栏 - 玻璃态面板 */}
        <div className="relative">
          {/* 背景装饰 */}
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-cyan-500/5 via-indigo-500/5 to-violet-500/5 backdrop-blur-sm" />

          <div className="relative flex flex-col gap-3 rounded-2xl border border-cyan-500/10 bg-slate-950/60 p-4 backdrop-blur-sm">
            <div className="flex flex-wrap items-center gap-4">
              {/* 目标调 - 钢琴键风格 */}
              <div className="group flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <div className="flex h-6 w-6 items-center justify-center rounded bg-gradient-to-br from-cyan-500/20 to-indigo-500/20">
                    <MusicNote className="h-3.5 w-3.5 text-cyan-400" />
                  </div>
                  <label htmlFor="target-key" className="text-xs font-bold uppercase tracking-wider text-cyan-400/80">
                    Target
                  </label>
                </div>
                <div className="relative">
                  <select
                    id="target-key"
                    value={targetKey}
                    onChange={(e) => onTargetKeyChange(e.target.value as TargetKey)}
                    disabled={isLoading}
                    className="appearance-none rounded-lg border border-cyan-500/30 bg-gradient-to-r from-slate-900 to-indigo-950/50 px-4 py-2 pr-10 font-mono text-sm font-bold text-white shadow-lg shadow-cyan-500/10 transition-all hover:border-cyan-400/50 hover:shadow-cyan-500/20 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 disabled:opacity-50"
                  >
                    {TARGET_KEYS.map((k) => (
                      <option key={k} value={k} className="bg-slate-950 font-mono">{k}</option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-cyan-500">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* 分隔线 */}
              <div className="hidden h-8 w-px bg-gradient-to-b from-transparent via-cyan-500/30 to-transparent sm:block" />

              {/* LLM Provider */}
              <div className="group flex items-center gap-3">
                <label htmlFor="llm-provider" className="text-xs font-bold uppercase tracking-wider text-indigo-400/80">
                  LLM
                </label>
                <div className="relative">
                  <select
                    id="llm-provider"
                    value={llmProvider}
                    onChange={(e) => onLlmProviderChange(e.target.value)}
                    disabled={isLoading}
                    className="appearance-none rounded-lg border border-indigo-500/30 bg-slate-950/80 px-3 py-1.5 pr-8 text-xs font-mono uppercase tracking-wider text-indigo-100 backdrop-blur-sm transition-all hover:border-indigo-400/50 focus:border-indigo-500 focus:outline-none disabled:opacity-50"
                  >
                    {llmProviders.map((item) => (
                      <option key={item} value={item} className="bg-slate-950 font-mono">{item}</option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-indigo-500">
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Vision LLM */}
              <div className="group flex items-center gap-3">
                <label htmlFor="vision-llm-provider" className="text-xs font-bold uppercase tracking-wider text-violet-400/80">
                  Vision
                </label>
                <div className="relative">
                  <select
                    id="vision-llm-provider"
                    value={visionLlmProvider}
                    onChange={(e) => onVisionLlmProviderChange(e.target.value)}
                    disabled={isLoading}
                    className="appearance-none rounded-lg border border-violet-500/30 bg-slate-950/80 px-3 py-1.5 pr-8 text-xs font-mono uppercase tracking-wider text-violet-100 backdrop-blur-sm transition-all hover:border-violet-400/50 focus:border-violet-500 focus:outline-none disabled:opacity-50"
                  >
                    {visionLlmProviders.map((item) => (
                      <option key={item} value={item} className="bg-slate-950 font-mono">{item}</option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-violet-500">
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* OCR */}
              <div className="group flex items-center gap-3">
                <label htmlFor="ocr-provider" className="text-xs font-bold uppercase tracking-wider text-emerald-400/80">
                  OCR
                </label>
                <div className="relative">
                  <select
                    id="ocr-provider"
                    value={ocrProvider}
                    onChange={(e) => onOcrProviderChange(e.target.value)}
                    disabled={isLoading}
                    className="appearance-none rounded-lg border border-emerald-500/30 bg-slate-950/80 px-3 py-1.5 pr-8 text-xs font-mono uppercase tracking-wider text-emerald-100 backdrop-blur-sm transition-all hover:border-emerald-400/50 focus:border-emerald-500 focus:outline-none disabled:opacity-50"
                  >
                    {ocrProviders.map((item) => (
                      <option key={item} value={item} className="bg-slate-950 font-mono">{item}</option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-emerald-500">
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Spacer */}
              <div className="flex-1" />

              {/* 提交按钮 - 增强发光 */}
              <button
                type="button"
                onClick={onSubmit}
                disabled={isLoading || !selectedFile}
                className="group relative overflow-hidden rounded-xl border border-cyan-500/50 bg-gradient-to-r from-cyan-600/90 via-indigo-600/90 to-violet-600/90 px-6 py-2.5 text-sm font-bold text-white shadow-xl shadow-cyan-500/25 transition-all hover:border-cyan-400 hover:shadow-cyan-500/40 hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:scale-100 disabled:hover:shadow-cyan-500/25"
              >
                {/* 内部光泽 */}
                <div className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent" />

                <span className="relative z-10 flex items-center gap-2.5">
                  {/* 处理中的动画 */}
                  {isLoading ? (
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  )}
                  <span className="font-mono tracking-widest">
                    {isLoading ? 'PROCESSING' : 'TRANSPOSE'}
                  </span>
                  <AudioBars count={3} active={isLoading} />
                </span>

                {/* 悬停时的流光效果 */}
                <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-700 group-hover:translate-x-full" />
              </button>
            </div>

            {/* 错误提示 */}
            {controlError && (
              <div className="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-950/50 px-4 py-2.5 text-sm backdrop-blur-sm" role="alert">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-red-500/20">
                  <svg className="h-4 w-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <span className="font-mono text-xs uppercase tracking-wider text-red-300">
                  Error:
                </span>
                <span className="text-red-200">{controlError}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* CSS 动画 */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </header>
  )
}
