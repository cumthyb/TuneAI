import { useCallback, useRef, useState, useEffect } from 'react'

const ACCEPT = 'image/png,image/jpeg,image/jpg'

export interface DropzoneProps {
  onFileSelect: (file: File) => void
  disabled?: boolean
}

// 音符装饰组件
function MusicNote({ className = '', style = {} }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg className={className} style={style} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z" />
    </svg>
  )
}

// 音波动画组件
function Waveform({ active = false }: { active?: boolean }) {
  const [bars, setBars] = useState([0.3, 0.5, 0.8, 0.4, 0.6, 0.7, 0.5, 0.3])

  useEffect(() => {
    if (!active) {
      setBars([0.3, 0.5, 0.8, 0.4, 0.6, 0.7, 0.5, 0.3])
      return
    }
    const interval = setInterval(() => {
      setBars(prev => prev.map(() => 0.2 + Math.random() * 0.8))
    }, 80)
    return () => clearInterval(interval)
  }, [active])

  return (
    <div className="flex items-center justify-center gap-0.5">
      {bars.map((height, i) => (
        <div
          key={i}
          className="w-1.5 bg-gradient-to-t from-cyan-400 to-indigo-400 rounded-full transition-all duration-75"
          style={{ height: `${height * 24}px` }}
        />
      ))}
    </div>
  )
}

// 五线谱装饰
function StaffLines({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 100 40" fill="none" stroke="currentColor" strokeWidth="0.5">
      {[5, 12, 19, 26, 33].map((y) => (
        <line key={y} x1="0" y1={y} x2="100" y2={y} />
      ))}
    </svg>
  )
}

export default function Dropzone({ onFileSelect, disabled }: DropzoneProps) {
  const [dragOver, setDragOver] = useState(false)
  const [pulseActive, setPulseActive] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  // 脉冲动画
  useEffect(() => {
    const interval = setInterval(() => {
      setPulseActive(p => !p)
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      const f = e.dataTransfer.files[0]
      if (f) onFileSelect(f)
    },
    [onFileSelect]
  )

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }, [])

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }, [])

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0]
      if (f) onFileSelect(f)
      e.target.value = ''
    },
    [onFileSelect]
  )

  return (
    <div
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      onClick={() => inputRef.current?.click()}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      className={`
        group relative flex h-full min-h-0 flex-col items-center justify-center overflow-hidden rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-500
        ${dragOver
          ? 'border-cyan-400 bg-gradient-to-br from-cyan-500/15 to-indigo-500/15 shadow-2xl shadow-cyan-500/30 scale-[1.02]'
          : 'border-slate-700/50 bg-slate-950/20 hover:border-indigo-500/50 hover:bg-gradient-to-br hover:from-slate-900/40 hover:to-indigo-950/30'}
        ${disabled ? 'pointer-events-none opacity-40' : 'cursor-pointer'}
      `}
    >
      {/* 背景网格 - 细密科技感 */}
      <div
        className={`
          absolute inset-0 transition-opacity duration-500
          ${dragOver ? 'opacity-40' : 'opacity-20'}
        `}
        style={{
          backgroundImage: `
            linear-gradient(rgba(6, 182, 212, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(6, 182, 212, 0.08) 1px, transparent 1px)
          `,
          backgroundSize: '24px 24px',
        }}
      />

      {/* 五线谱装饰 - 音乐感 */}
      <div className={`absolute inset-x-8 top-8 transition-opacity duration-500 ${dragOver ? 'opacity-60' : 'opacity-15'}`}>
        <StaffLines className="w-full text-indigo-400/50" />
        {/* 五线谱上的音符 */}
        <MusicNote
          className="absolute left-[20%] top-2 h-4 w-4 text-cyan-400"
          style={{ filter: 'drop-shadow(0 0 4px rgba(6, 182, 212, 0.5))' }}
        />
        <MusicNote
          className="absolute left-[50%] top-0 h-5 w-5 text-indigo-400"
          style={{ filter: 'drop-shadow(0 0 6px rgba(99, 102, 241, 0.5))' }}
        />
        <MusicNote
          className="absolute left-[75%] top-3 h-3 w-3 text-violet-400"
          style={{ filter: 'drop-shadow(0 0 4px rgba(139, 92, 246, 0.5))' }}
        />
      </div>

      {/* 扫描线效果 */}
      <div
        className={`
          absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-400/70 to-transparent
          transition-opacity duration-300
          ${dragOver ? 'opacity-100' : 'opacity-0'}
        `}
        style={{ animation: 'scan 2s linear infinite' }}
      />

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        onChange={onInputChange}
        className="absolute inset-0 cursor-pointer opacity-0"
        disabled={disabled}
        aria-hidden
      />

      {/* 中央图标区域 */}
      <div
        className={`
          relative mb-6 flex flex-col items-center justify-center
          transition-all duration-500
          ${dragOver ? 'scale-110' : 'group-hover:scale-105'}
        `}
      >
        {/* 外围光环 */}
        <div
          className={`
            absolute inset-0 rounded-2xl blur-xl transition-all duration-500
            ${dragOver ? 'bg-cyan-500/30 scale-110' : 'bg-indigo-500/10 scale-100'}
          `}
        />

        {/* 旋转边框 */}
        <div
          className="absolute inset-0 rounded-2xl p-px"
          style={{
            background: dragOver
              ? 'conic-gradient(from 0deg, #06b6d4, #6366f1, #8b5cf6, #06b6d4)'
              : 'conic-gradient(from 0deg, #475569, #334155, #475569)',
            animation: 'spin 3s linear infinite',
          }}
        />

        {/* 图标容器 */}
        <div
          className={`
            relative flex h-20 w-20 items-center justify-center rounded-2xl
            bg-gradient-to-br from-slate-900 via-slate-950 to-black
            transition-all duration-500
            ${dragOver ? 'border border-cyan-400/50' : 'border border-slate-700/50'}
          `}
        >
          {/* 音波图标 */}
          <Waveform active={dragOver} />

          {/* 音符装饰 */}
          <MusicNote
            className={`
              absolute -right-2 -top-2 h-5 w-5 transition-all duration-300
              ${dragOver ? 'text-cyan-400 scale-110' : 'text-slate-600 scale-100'}
            `}
            style={{
              filter: dragOver ? 'drop-shadow(0 0 8px rgba(6, 182, 212, 0.6))' : 'none',
            }}
          />
        </div>

        {/* 脉冲点 */}
        <div className="absolute -bottom-1 -right-1 flex h-4 w-4 items-center justify-center">
          <span
            className={`
              absolute inline-flex h-full w-full rounded-full
              ${dragOver ? 'bg-cyan-400' : 'bg-indigo-500'}
              ${pulseActive ? 'animate-ping' : ''}
              opacity-75
            `}
          />
          <span
            className={`
              relative inline-flex h-2 w-2 rounded-full
              ${dragOver ? 'bg-cyan-300' : 'bg-indigo-400'}
            `}
          />
        </div>
      </div>

      {/* 文字标签 */}
      <div className="space-y-2">
        <p
          className={`
            relative font-mono text-base font-bold tracking-wider transition-colors duration-300
            ${dragOver ? 'text-cyan-300' : 'text-slate-300 group-hover:text-white'}
          `}
        >
          {dragOver ? (
            'RELEASE TO UPLOAD'
          ) : (
            <>
              <span className="text-slate-500">{'<'}</span>
              <span className="text-indigo-400">DROP_SCORE</span>
              <span className="text-slate-500">_HERE</span>
              <span className="text-slate-500">/</span>
              <span className="text-cyan-500">{'>'}</span>
            </>
          )}
        </p>

        <div className="flex items-center justify-center gap-3">
          <p
            className={`
              relative font-mono text-[10px] tracking-widest transition-colors duration-300
              ${dragOver ? 'text-cyan-400/80' : 'text-slate-600 group-hover:text-slate-500'}
            `}
          >
            ACCEPT: PNG, JPG
          </p>
          <span className="text-slate-700">|</span>
          <p
            className={`
              relative font-mono text-[10px] tracking-widest transition-colors duration-300
              ${dragOver ? 'text-cyan-400/80' : 'text-slate-600 group-hover:text-slate-500'}
            `}
          >
            MAX: 20MB
          </p>
        </div>
      </div>

      {/* 底部装饰 - 钢琴键风格 */}
      <div className="absolute bottom-4 left-1/2 flex -translate-x-1/2 gap-0.5">
        {Array.from({ length: 9 }).map((_, i) => (
          <div
            key={i}
            className={`
              h-1.5 rounded-sm transition-all duration-300
              ${i % 3 === 0
                ? 'w-2 bg-gradient-to-t from-cyan-500/60 to-indigo-500/60'
                : 'w-1.5 bg-gradient-to-t from-slate-600/40 to-slate-700/40'}
              ${dragOver
                ? i % 3 === 0
                  ? 'bg-gradient-to-t from-cyan-400 to-indigo-400 shadow-lg shadow-cyan-500/30'
                  : 'bg-gradient-to-t from-slate-500 to-slate-600'
                : ''}
            `}
          />
        ))}
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
