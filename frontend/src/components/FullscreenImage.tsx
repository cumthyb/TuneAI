import { useCallback, useEffect, useRef, useState } from 'react'

interface FullscreenImageProps {
  src: string
  alt: string
  className: string
}

export default function FullscreenImage({ src, alt, className }: FullscreenImageProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const handleFullscreenChange = useCallback(() => {
    setIsFullscreen(document.fullscreenElement !== null)
  }, [])

  useEffect(() => {
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
      if (document.fullscreenElement) {
        void document.exitFullscreen()
      }
    }
  }, [handleFullscreenChange])

  const toggleFullscreen = useCallback(() => {
    const el = containerRef.current
    if (!el) return
    if (document.fullscreenElement) {
      void document.exitFullscreen()
      return
    }
    void el.requestFullscreen()
  }, [])

  return (
    <div
      ref={containerRef}
      className={`fullscreen-image-wrapper group relative flex min-h-[200px] flex-1 items-center justify-center overflow-hidden bg-slate-950/30 ${className}`}
    >
      <img
        src={src}
        alt={alt}
        className="max-h-full max-w-full object-contain transition-all duration-300 group-hover:scale-[1.02]"
      />

      {/* 全屏按钮 */}
      <button
        type="button"
        onClick={toggleFullscreen}
        className="absolute right-4 top-4 z-50 inline-flex items-center gap-2 rounded-xl border border-cyan-500/30 bg-slate-900/90 px-4 py-2 text-xs font-bold uppercase tracking-wider text-cyan-300 opacity-0 shadow-lg shadow-cyan-500/10 backdrop-blur-sm transition-all duration-300 hover:border-cyan-400/50 hover:bg-slate-800 hover:text-cyan-200 group-hover:opacity-100"
        title={isFullscreen ? '退出全屏 (Esc)' : '全屏查看'}
      >
        {isFullscreen ? (
          <>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span className="hidden sm:inline">Exit</span>
          </>
        ) : (
          <>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            <span className="hidden sm:inline">Fullscreen</span>
          </>
        )}
      </button>

      {/* 底部信息栏 */}
      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/90 via-slate-950/60 to-transparent p-4 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
        <span className="font-mono text-xs text-cyan-400/70">{alt}</span>
      </div>

      {/* 边框发光效果 */}
      <div className="absolute inset-0 rounded-lg border border-transparent opacity-0 transition-all duration-300 group-hover:border-cyan-500/20 group-hover:opacity-100 pointer-events-none" />
    </div>
  )
}
