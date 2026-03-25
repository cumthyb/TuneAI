import { useEffect, useState } from 'react'

interface LoadingStateProps {
  message?: string
}

// 音波条动画
function AudioBars() {
  const [bars, setBars] = useState([0.3, 0.5, 0.8, 0.4, 0.6, 0.7, 0.5, 0.3, 0.6, 0.4])

  useEffect(() => {
    const interval = setInterval(() => {
      setBars(prev => prev.map(() => 0.2 + Math.random() * 0.8))
    }, 80)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex items-center justify-center gap-0.5">
      {bars.map((height, i) => (
        <div
          key={i}
          className="w-1.5 bg-gradient-to-t from-cyan-400 to-indigo-400 rounded-full transition-all duration-75"
          style={{ height: `${height * 32}px` }}
        />
      ))}
    </div>
  )
}

// DNA 螺旋音符
function MusicDNALoader() {
  const [rotation, setRotation] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setRotation(r => r + 2)
    }, 50)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="relative h-28 w-28">
      {/* 外圈 */}
      <div
        className="absolute inset-0 rounded-full border-2 border-cyan-500/30"
        style={{ animation: 'spin 3s linear infinite' }}
      />

      {/* 中圈 - 反向 */}
      <div
        className="absolute inset-2 rounded-full border-2 border-indigo-500/40"
        style={{ animation: 'spin 2s linear infinite reverse' }}
      />

      {/* 内圈 */}
      <div
        className="absolute inset-4 rounded-full border border-violet-500/50"
        style={{ animation: 'spin 1.5s linear infinite' }}
      />

      {/* 中心脉冲 */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="absolute h-12 w-12 rounded-full bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 blur-xl animate-pulse" />
        <div className="relative flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-indigo-600 shadow-lg shadow-cyan-500/30">
          {/* 音符图标 */}
          <svg className="h-5 w-5 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z" />
          </svg>
        </div>
      </div>

      {/* 旋转指示器 */}
      <svg
        className="absolute inset-0 h-full w-full"
        style={{ transform: `rotate(${rotation}deg)` }}
      >
        <circle
          cx="50%"
          cy="0%"
          r="3"
          fill="#06b6d4"
          className="animate-pulse"
        />
      </svg>

      {/* 十字指示线 */}
      <div className="absolute left-1/2 top-0 h-1/2 w-px -translate-x-1/2 bg-gradient-to-b from-cyan-400/60 to-transparent" />
      <div className="absolute bottom-0 left-1/2 h-1/2 w-px -translate-x-1/2 bg-gradient-to-t from-indigo-400/60 to-transparent" />
      <div className="absolute left-0 top-1/2 h-px w-1/2 -translate-y-1/2 bg-gradient-to-r from-transparent to-violet-400/60" />
      <div className="absolute right-0 top-1/2 h-px w-1/2 -translate-y-1/2 bg-gradient-to-l from-transparent to-cyan-400/60" />
    </div>
  )
}

export default function LoadingState({ message = 'AI Transposing...' }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-8 space-y-6">
      {/* 主加载动画 */}
      <MusicDNALoader />

      {/* 音频可视化条 */}
      <div className="h-16">
        <AudioBars />
      </div>

      {/* 消息 */}
      <div className="flex flex-col items-center gap-3">
        <p className="font-mono text-sm font-medium tracking-wider text-cyan-300">{message}</p>

        {/* 状态点 */}
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" style={{ animationDelay: '0ms' }} />
          <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse" style={{ animationDelay: '150ms' }} />
          <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse" style={{ animationDelay: '300ms' }} />
          <span className="h-1.5 w-1.5 rounded-full bg-fuchsia-400 animate-pulse" style={{ animationDelay: '450ms' }} />
        </div>
      </div>

      {/* 进度条 */}
      <div className="relative h-1.5 w-48 overflow-hidden rounded-full bg-slate-800/50">
        <div
          className="absolute inset-y-0 left-0 w-2/3 rounded-full bg-gradient-to-r from-cyan-500 via-indigo-500 to-violet-500"
          style={{
            animation: 'shimmer 2s ease-in-out infinite',
          }}
        />
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      </div>

      {/* 处理流程 */}
      <div className="flex items-center gap-2 font-mono text-[10px] tracking-widest">
        <span className="text-cyan-500/80">OCR</span>
        <span className="text-slate-600">→</span>
        <span className="text-indigo-500/80">ANALYZE</span>
        <span className="text-slate-600">→</span>
        <span className="text-violet-500/80">TRANSPOSE</span>
        <span className="text-slate-600">→</span>
        <span className="text-slate-500">RENDER</span>
      </div>

      {/* CSS 动画 */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
