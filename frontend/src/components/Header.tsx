import ControlBar from './ControlBar'
import AIBadge from './AIBadge'
import type { TargetKey } from '../types/api'

interface HeaderProps {
  selectedFile: File | null
  targetKey: TargetKey
  controlError: string | null
  isLoading: boolean
  systemOnline: boolean
  apiReady: boolean
  isCheckingStatus: boolean
  onTargetKeyChange: (key: TargetKey) => void
  onSubmit: () => void
}

export default function Header({
  selectedFile,
  targetKey,
  controlError,
  isLoading,
  systemOnline,
  apiReady,
  isCheckingStatus,
  onTargetKeyChange,
  onSubmit,
}: HeaderProps) {
  const systemDotClass = systemOnline ? 'bg-emerald-400' : 'bg-rose-400'
  const systemTextClass = systemOnline ? 'text-emerald-300' : 'text-rose-300'
  const apiDotClass = isCheckingStatus ? 'bg-amber-400' : apiReady ? 'bg-cyan-400' : 'bg-rose-400'
  const apiTextClass = isCheckingStatus ? 'text-amber-300' : apiReady ? 'text-cyan-300' : 'text-rose-300'
  const apiLabel = isCheckingStatus ? 'API CHECKING' : apiReady ? 'API READY' : 'API DEGRADED'

  return (
    <header className="relative shrink-0 border-b border-cyan-500/10 bg-slate-950/60 px-4 py-5 backdrop-blur-xl sm:px-6 lg:px-8 xl:px-10">
      <div className="w-full">
        <div className="mb-4 flex items-center gap-4">
          {/* AI Logo */}
          <div className="relative flex h-12 w-12 items-center justify-center">
            {/* 外发光环 */}
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 opacity-50 blur-lg animate-pulse" />
            {/* 主图标 */}
            <div className="relative flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 shadow-lg">
              <svg className="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z" />
              </svg>
            </div>
            {/* 状态指示点 */}
            <div className="absolute -right-1 -top-1 flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-cyan-400" />
            </div>
          </div>
          
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="neon-text bg-gradient-to-r from-white via-cyan-200 to-purple-200 bg-clip-text text-2xl font-bold tracking-tight text-transparent sm:text-3xl">
                TuneAI
              </h1>
              <AIBadge text="AI v2.0" size="sm" />
            </div>
            <p className="text-xs text-cyan-400/60 font-mono tracking-wide">NEURAL TRANSPOSITION ENGINE</p>
          </div>

          {/* 右侧状态信息 */}
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
        
        <ControlBar
          file={selectedFile}
          targetKey={targetKey}
          onTargetKeyChange={onTargetKeyChange}
          onSubmit={onSubmit}
          disabled={isLoading}
          error={controlError}
        />
      </div>
    </header>
  )
}
