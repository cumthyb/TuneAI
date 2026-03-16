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
  const apiTextClass = isCheckingStatus ? 'text-amber-300' : apiReady ? 'text-indigo-300' : 'text-rose-300'
  const apiDotClass = isCheckingStatus ? 'bg-amber-400' : apiReady ? 'bg-indigo-400' : 'bg-rose-400'
  const apiLabel = isCheckingStatus ? 'API CHECKING' : apiReady ? 'API READY' : 'API DEGRADED'

  return (
    <header className="relative shrink-0 border-b border-indigo-500/10 bg-slate-950/60 px-4 py-5 backdrop-blur-xl sm:px-6 lg:px-8 xl:px-10">
      <div className="w-full">
        {/* 标题行 */}
        <div className="mb-4 flex items-center gap-4">
          {/* Logo */}
          <div className="relative flex h-12 w-12 items-center justify-center">
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 opacity-50 blur-lg animate-pulse" />
            <div className="relative flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg">
              <svg className="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z" />
              </svg>
            </div>
            <div className="absolute -right-1 -top-1 flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-indigo-400" />
            </div>
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="neon-text bg-gradient-to-r from-white via-indigo-200 to-violet-200 bg-clip-text text-2xl font-bold tracking-tight text-transparent sm:text-3xl">
                TuneAI
              </h1>
              {/* AI badge */}
              <span className="inline-flex items-center gap-1.5 rounded-full border border-indigo-500/30 bg-gradient-to-r from-indigo-950/80 to-violet-950/80 px-2 py-0.5 font-mono text-[10px] font-semibold tracking-wider text-indigo-400 backdrop-blur-sm">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-indigo-400" />
                </span>
                AI v2.0
              </span>
            </div>
            <p className="text-xs text-indigo-400/60 font-mono tracking-wide">NEURAL TRANSPOSITION ENGINE</p>
          </div>

          {/* 状态指示 */}
          <div className="hidden items-center gap-4 text-xs font-mono text-slate-500 sm:flex">
            <div className={`flex items-center gap-1.5 ${systemTextClass}`}>
              <span className={`h-1.5 w-1.5 rounded-full animate-pulse ${systemDotClass}`} />
              {systemOnline ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
            </div>
            <div className={`flex items-center gap-1.5 ${apiTextClass}`}>
              <span className={`h-1.5 w-1.5 rounded-full animate-pulse ${apiDotClass}`} />
              {apiLabel}
            </div>
          </div>
        </div>

        {/* 控制栏 */}
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-4">
            {/* 目标调 */}
            <div className="group flex items-center gap-3">
              <label htmlFor="target-key" className="flex items-center gap-1.5 text-xs font-medium text-indigo-400/80">
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
                  disabled={isLoading}
                  className="appearance-none rounded-lg border border-indigo-500/30 bg-slate-950/80 px-3 py-1.5 pr-8 text-sm font-mono font-medium text-indigo-100 backdrop-blur-sm transition-all hover:border-indigo-400/50 hover:bg-slate-900/80 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50"
                >
                  {TARGET_KEYS.map((k) => (
                    <option key={k} value={k} className="bg-slate-950 font-mono">{k}</option>
                  ))}
                </select>
                <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-indigo-500">
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>

            {/* LLM Provider */}
            <div className="group flex items-center gap-3">
              <label htmlFor="llm-provider" className="flex items-center gap-1.5 text-xs font-medium text-indigo-400/80">
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
                  disabled={isLoading}
                  className="appearance-none rounded-lg border border-indigo-500/30 bg-slate-950/80 px-3 py-1.5 pr-8 text-sm font-mono font-medium uppercase text-indigo-100 backdrop-blur-sm transition-all hover:border-indigo-400/50 hover:bg-slate-900/80 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50"
                >
                  {llmProviders.map((item) => (
                    <option key={item} value={item} className="bg-slate-950 font-mono">{item}</option>
                  ))}
                </select>
                <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-indigo-500">
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Vision LLM Provider */}
            <div className="group flex items-center gap-3">
              <label htmlFor="vision-llm-provider" className="flex items-center gap-1.5 text-xs font-medium text-indigo-400/80">
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
                  disabled={isLoading}
                  className="appearance-none rounded-lg border border-indigo-500/30 bg-slate-950/80 px-3 py-1.5 pr-8 text-sm font-mono font-medium uppercase text-indigo-100 backdrop-blur-sm transition-all hover:border-indigo-400/50 hover:bg-slate-900/80 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50"
                >
                  {visionLlmProviders.map((item) => (
                    <option key={item} value={item} className="bg-slate-950 font-mono">{item}</option>
                  ))}
                </select>
                <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-indigo-500">
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>

            {/* OCR Provider */}
            <div className="group flex items-center gap-3">
              <label htmlFor="ocr-provider" className="flex items-center gap-1.5 text-xs font-medium text-indigo-400/80">
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
                  disabled={isLoading}
                  className="appearance-none rounded-lg border border-indigo-500/30 bg-slate-950/80 px-3 py-1.5 pr-8 text-sm font-mono font-medium uppercase text-indigo-100 backdrop-blur-sm transition-all hover:border-indigo-400/50 hover:bg-slate-900/80 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50"
                >
                  {ocrProviders.map((item) => (
                    <option key={item} value={item} className="bg-slate-950 font-mono">{item}</option>
                  ))}
                </select>
                <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-indigo-500">
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="hidden sm:flex flex-col gap-1">
              <span className="text-[10px] font-medium text-slate-500 uppercase">Algorithm</span>
              <span className="text-xs font-mono text-indigo-400/70">12-TET Neural</span>
            </div>

            {/* 提交按钮 */}
            <div className="flex items-center">
              <button
                type="button"
                onClick={onSubmit}
                disabled={isLoading || !selectedFile}
                className="group relative overflow-hidden rounded-lg border border-indigo-500/50 bg-gradient-to-r from-indigo-600/80 to-violet-600/80 px-5 py-2 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 backdrop-blur-sm transition-all hover:border-indigo-400 hover:shadow-indigo-500/40 hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
              >
                <span className="relative z-10 flex items-center gap-2">
                  <svg className="h-4 w-4 transition-transform group-hover:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span className="font-mono tracking-wider">PROCESS</span>
                </span>
                <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-indigo-400/30 to-transparent transition-transform duration-700 group-hover:translate-x-full" />
                <div className="absolute inset-0 rounded-lg opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                  <div className="absolute inset-0 rounded-lg border border-indigo-400/50" />
                </div>
              </button>
            </div>
          </div>

          {/* 错误提示 */}
          {controlError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-950/50 px-3 py-2 text-sm text-red-300 backdrop-blur-sm" role="alert">
              <svg className="h-4 w-4 flex-shrink-0 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="font-mono text-xs uppercase">ERROR:</span>
              {controlError}
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
