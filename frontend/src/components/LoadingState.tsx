interface LoadingStateProps {
  message?: string
}

export default function LoadingState({ message = '正在识别与移调，请稍候…' }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      {/* AI神经网络风格加载动画 */}
      <div className="relative h-24 w-24">
        <div className="absolute inset-0 h-24 w-24 animate-[spin_4s_linear_infinite] rounded-full border border-cyan-500/10" />
        <div className="absolute inset-0 h-24 w-24 animate-[spin_4s_linear_infinite] rounded-full border-t border-cyan-500/40" style={{ animationDelay: '-1s' }} />
        <div className="absolute inset-2 h-20 w-20 animate-[spin_3s_linear_infinite_reverse] rounded-full border border-blue-500/20" />
        <div className="absolute inset-2 h-20 w-20 animate-[spin_3s_linear_infinite_reverse] rounded-full border-b border-blue-500/50" style={{ animationDelay: '-0.5s' }} />
        <div className="absolute inset-4 h-16 w-16 animate-[spin_2s_linear_infinite] rounded-full border border-purple-500/30" />
        <div className="absolute inset-4 h-16 w-16 animate-pulse rounded-full border border-purple-500/20" />
        <div className="absolute left-1/2 top-1/2 h-8 w-8 -translate-x-1/2 -translate-y-1/2">
          <div className="absolute inset-0 animate-ping rounded-full bg-cyan-500/30" />
          <div className="relative flex h-full w-full items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/50">
            <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        </div>
        <div className="absolute left-1/2 top-0 h-1/2 w-px -translate-x-1/2 bg-gradient-to-b from-cyan-500/50 to-transparent" />
        <div className="absolute bottom-0 left-1/2 h-1/2 w-px -translate-x-1/2 bg-gradient-to-t from-purple-500/50 to-transparent" />
        <div className="absolute left-0 top-1/2 h-px w-1/2 -translate-y-1/2 bg-gradient-to-r from-transparent to-cyan-500/50" />
        <div className="absolute right-0 top-1/2 h-px w-1/2 -translate-y-1/2 bg-gradient-to-l from-transparent to-purple-500/50" />
      </div>

      <div className="mt-6 flex flex-col items-center gap-2">
        <p className="font-mono text-sm tracking-wider text-cyan-300">{message}</p>
        <div className="flex items-center gap-2">
          <span className="h-1 w-1 rounded-full bg-cyan-400 animate-pulse" style={{ animationDelay: '0s' }} />
          <span className="h-1 w-1 rounded-full bg-cyan-400 animate-pulse" style={{ animationDelay: '0.2s' }} />
          <span className="h-1 w-1 rounded-full bg-cyan-400 animate-pulse" style={{ animationDelay: '0.4s' }} />
        </div>
      </div>

      <div className="mt-4 flex items-center gap-2">
        <div className="h-1 w-32 overflow-hidden rounded-full bg-slate-800">
          <div className="h-full w-full animate-[shimmer_2s_infinite] rounded-full bg-gradient-to-r from-cyan-500/0 via-cyan-500/80 to-cyan-500/0" />
        </div>
        <span className="font-mono text-[10px] text-cyan-500/60">LOADING</span>
      </div>

      <div className="mt-3 flex items-center gap-3 font-mono text-[10px] text-slate-600">
        <span className="text-cyan-500/60">OCR</span>
        <span className="text-slate-700">→</span>
        <span className="text-cyan-500/60">ANALYZE</span>
        <span className="text-slate-700">→</span>
        <span className="text-cyan-500/60">TRANSPOSE</span>
        <span className="text-slate-700">→</span>
        <span className="text-slate-600">RENDER</span>
      </div>
    </div>
  )
}
