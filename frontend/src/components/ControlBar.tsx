import { TARGET_KEYS, type TargetKey } from '../types/api'

export interface ControlBarProps {
  file: File | null
  targetKey: TargetKey
  llmProvider: string
  llmProviders: string[]
  visionLlmProvider: string
  visionLlmProviders: string[]
  ocrProvider: string
  ocrProviders: string[]
  onTargetKeyChange: (key: TargetKey) => void
  onLlmProviderChange: (provider: string) => void
  onVisionLlmProviderChange: (provider: string) => void
  onOcrProviderChange: (provider: string) => void
  onSubmit: () => void
  disabled?: boolean
  error?: string | null
}

export default function ControlBar({
  file,
  targetKey,
  llmProvider,
  llmProviders,
  visionLlmProvider,
  visionLlmProviders,
  ocrProvider,
  ocrProviders,
  onTargetKeyChange,
  onLlmProviderChange,
  onVisionLlmProviderChange,
  onOcrProviderChange,
  onSubmit,
  disabled,
  error,
}: ControlBarProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-4">
        {/* 目标调选择器 - AI风格（并排布局） */}
        <div className="group flex items-center gap-3">
          <label htmlFor="target-key" className="flex items-center gap-1.5 text-xs font-medium text-cyan-400/80">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z" />
            </svg>
            TARGET_KEY
          </label>
          <div className="relative">
            <select
              id="target-key"
              value={targetKey}
              onChange={(e) => onTargetKeyChange(e.target.value as TargetKey)}
              disabled={disabled}
              className="appearance-none rounded-lg border border-cyan-500/30 bg-slate-950/80 px-3 py-1.5 pr-8 text-sm font-mono font-medium text-cyan-100 backdrop-blur-sm transition-all hover:border-cyan-400/50 hover:bg-slate-900/80 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 disabled:opacity-50"
            >
              {TARGET_KEYS.map((k) => (
                <option key={k} value={k} className="bg-slate-950 font-mono">
                  {k}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-cyan-500">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>

        {/* LLM Provider */}
        <div className="group flex items-center gap-3">
          <label htmlFor="llm-provider" className="flex items-center gap-1.5 text-xs font-medium text-cyan-400/80">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1-1-3 1 1-3-1-1 3-.75M12 3v4m0 0l-2-2m2 2l2-2m-6 6h8m-8 4h8" />
            </svg>
            LLM
          </label>
          <div className="relative">
            <select
              id="llm-provider"
              value={llmProvider}
              onChange={(e) => onLlmProviderChange(e.target.value)}
              disabled={disabled}
              className="appearance-none rounded-lg border border-cyan-500/30 bg-slate-950/80 px-3 py-1.5 pr-8 text-sm font-mono font-medium uppercase text-cyan-100 backdrop-blur-sm transition-all hover:border-cyan-400/50 hover:bg-slate-900/80 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 disabled:opacity-50"
            >
              {llmProviders.map((item) => (
                <option key={item} value={item} className="bg-slate-950 font-mono">
                  {item}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-cyan-500">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>

        {/* Vision LLM Provider */}
        <div className="group flex items-center gap-3">
          <label htmlFor="vision-llm-provider" className="flex items-center gap-1.5 text-xs font-medium text-cyan-400/80">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7h18M3 12h18M3 17h18" />
            </svg>
            VISION
          </label>
          <div className="relative">
            <select
              id="vision-llm-provider"
              value={visionLlmProvider}
              onChange={(e) => onVisionLlmProviderChange(e.target.value)}
              disabled={disabled}
              className="appearance-none rounded-lg border border-cyan-500/30 bg-slate-950/80 px-3 py-1.5 pr-8 text-sm font-mono font-medium uppercase text-cyan-100 backdrop-blur-sm transition-all hover:border-cyan-400/50 hover:bg-slate-900/80 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 disabled:opacity-50"
            >
              {visionLlmProviders.map((item) => (
                <option key={item} value={item} className="bg-slate-950 font-mono">
                  {item}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-cyan-500">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>

        {/* OCR Provider */}
        <div className="group flex items-center gap-3">
          <label htmlFor="ocr-provider" className="flex items-center gap-1.5 text-xs font-medium text-cyan-400/80">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7h16v10H4zM8 11h8" />
            </svg>
            OCR
          </label>
          <div className="relative">
            <select
              id="ocr-provider"
              value={ocrProvider}
              onChange={(e) => onOcrProviderChange(e.target.value)}
              disabled={disabled}
              className="appearance-none rounded-lg border border-cyan-500/30 bg-slate-950/80 px-3 py-1.5 pr-8 text-sm font-mono font-medium uppercase text-cyan-100 backdrop-blur-sm transition-all hover:border-cyan-400/50 hover:bg-slate-900/80 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 disabled:opacity-50"
            >
              {ocrProviders.map((item) => (
                <option key={item} value={item} className="bg-slate-950 font-mono">
                  {item}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-cyan-500">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>

        {/* 处理参数显示 */}
        <div className="hidden sm:flex flex-col gap-1">
          <span className="text-[10px] font-medium text-slate-500 uppercase">Algorithm</span>
          <span className="text-xs font-mono text-cyan-400/70">12-TET Neural</span>
        </div>

        <div className="hidden sm:flex flex-col gap-1">
          <span className="text-[10px] font-medium text-slate-500 uppercase">Precision</span>
          <span className="text-xs font-mono text-cyan-400/70">99.8%</span>
        </div>

        {/* AI处理按钮 */}
        <div className="flex items-center">
          <button
            type="button"
            onClick={onSubmit}
            disabled={disabled || !file}
            className="group relative overflow-hidden rounded-lg border border-cyan-500/50 bg-gradient-to-r from-cyan-600/80 to-blue-600/80 px-5 py-2 text-sm font-bold text-white shadow-lg shadow-cyan-500/20 backdrop-blur-sm transition-all hover:border-cyan-400 hover:shadow-cyan-500/40 hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
          >
            <span className="relative z-10 flex items-center gap-2">
              <svg className="h-4 w-4 transition-transform group-hover:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span className="font-mono tracking-wider">PROCESS</span>
            </span>
            {/* 扫描线效果 */}
            <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-cyan-400/30 to-transparent transition-transform duration-700 group-hover:translate-x-full" />
            {/* 脉冲光效 */}
            <div className="absolute inset-0 rounded-lg opacity-0 transition-opacity duration-300 group-hover:opacity-100">
              <div className="absolute inset-0 rounded-lg border border-cyan-400/50" />
            </div>
          </button>
        </div>
      </div>

      {/* 错误提示 - 科技风格 */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-950/50 px-3 py-2 text-sm text-red-300 backdrop-blur-sm" role="alert">
          <svg className="h-4 w-4 flex-shrink-0 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="font-mono text-xs uppercase">ERROR:</span>
          {error}
        </div>
      )}
    </div>
  )
}
