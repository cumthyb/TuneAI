import { useCallback, useEffect, useRef, useState } from 'react'

export interface FullscreenImageProps {
  src: string
  alt: string
  /** 外层容器类名，用于与父布局配合 */
  className?: string
  /** 图片类名 */
  imgClassName?: string
}

/**
 * 使用 Fullscreen API 支持全屏查看的图片预览器。
 * 点击「全屏」将当前容器全屏，ESC 或「退出全屏」可退出。
 */
export default function FullscreenImage({
  src,
  alt,
  className = '',
  imgClassName = '',
}: FullscreenImageProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const handleFullscreenChange = useCallback(() => {
    const el = document.fullscreenElement ?? (document as Document & { webkitFullscreenElement?: Element }).webkitFullscreenElement
    setIsFullscreen(!!el)
  }, [])

  useEffect(() => {
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
      if (document.fullscreenElement ?? (document as Document & { webkitFullscreenElement?: Element }).webkitFullscreenElement) {
        document.exitFullscreen?.() ?? (document as Document & { webkitExitFullscreen?: () => Promise<void> }).webkitExitFullscreen?.()
      }
    }
  }, [handleFullscreenChange])

  const toggleFullscreen = useCallback(() => {
    const el = containerRef.current
    if (!el) return
    const doc = document as Document & {
      fullscreenElement?: Element
      webkitFullscreenElement?: Element
      exitFullscreen?: () => Promise<void>
      webkitExitFullscreen?: () => Promise<void>
    }
    const requestFs = el.requestFullscreen?.bind(el) ?? (el as HTMLDivElement & { webkitRequestFullscreen?: () => Promise<void> }).webkitRequestFullscreen?.bind(el)
    if (doc.fullscreenElement ?? doc.webkitFullscreenElement) {
      ;(doc.exitFullscreen ?? doc.webkitExitFullscreen)?.()
    } else if (requestFs) {
      void requestFs()
    }
  }, [])

  return (
    <div
      ref={containerRef}
      className={`fullscreen-image-wrapper group relative flex min-h-[200px] flex-1 items-center justify-center overflow-hidden bg-slate-950/50 ${className}`}
    >
      <img
        src={src}
        alt={alt}
        className={`max-h-full max-w-full object-contain transition-transform duration-300 ${imgClassName}`}
      />

      {/* 右上角全屏/退出按钮 */}
      <button
        type="button"
        onClick={toggleFullscreen}
        className="absolute right-4 top-4 z-50 inline-flex items-center gap-2 rounded-lg border border-cyan-500/30 bg-slate-900/90 px-3 py-2 text-xs font-medium text-cyan-300 opacity-0 shadow-lg backdrop-blur-sm transition-all duration-300 hover:border-cyan-400/50 hover:bg-slate-800 hover:text-cyan-200 group-hover:opacity-100"
        title={isFullscreen ? '退出全屏 (Esc)' : '全屏查看'}
      >
        {isFullscreen ? (
          <>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span className="hidden sm:inline">退出</span>
          </>
        ) : (
          <>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            <span className="hidden sm:inline">全屏</span>
          </>
        )}
      </button>

      {/* 底部悬浮信息栏（仅显示文件名） */}
      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/90 to-transparent p-4 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
        <span className="text-xs text-slate-400">{alt}</span>
      </div>
    </div>
  )
}
