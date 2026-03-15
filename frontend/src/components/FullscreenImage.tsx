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
      className={`fullscreen-image-wrapper relative flex min-h-[200px] flex-1 items-center justify-center overflow-hidden bg-slate-100 ${className}`}
    >
      <img
        src={src}
        alt={alt}
        className={`max-h-full max-w-full object-contain ${imgClassName}`}
      />
      <button
        type="button"
        onClick={toggleFullscreen}
        className="absolute right-2 top-2 rounded-lg border border-slate-300 bg-white/90 px-3 py-1.5 text-sm font-medium text-slate-700 shadow hover:bg-white"
        title={isFullscreen ? '退出全屏 (Esc)' : '全屏查看'}
      >
        {isFullscreen ? '退出全屏' : '全屏'}
      </button>
    </div>
  )
}
