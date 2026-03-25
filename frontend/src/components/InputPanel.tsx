import { useState } from 'react'
import type { ScoreJson } from '../types/api'
import Dropzone from './Dropzone'
import FullscreenImage from './FullscreenImage'
import ScoreView from './ScoreView'

interface InputPanelProps {
  selectedFile: File | null
  leftImageUrl: string | null
  scoreJson: ScoreJson | null
  isLoading: boolean
  isSuccess: boolean
  onFileChange: (file: File | null) => void
}

export default function InputPanel({
  selectedFile,
  leftImageUrl,
  scoreJson,
  isLoading,
  isSuccess,
  onFileChange,
}: InputPanelProps) {
  const [viewMode, setViewMode] = useState<'image' | 'json'>('image')

  return (
    <div className="group relative flex flex-col overflow-hidden rounded-2xl lg:min-h-[60vh] border border-cyan-500/20 bg-gradient-to-br from-slate-950/90 via-slate-900/80 to-indigo-950/60 backdrop-blur-xl">
      {/* 边框发光效果 */}
      <div className="absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-500 group-hover:opacity-100">
        <div className="absolute inset-0 rounded-2xl border border-cyan-400/30 shadow-lg shadow-cyan-500/10" />
      </div>

      {/* 顶部标签栏 */}
      <div className="relative flex items-center justify-between gap-2 border-b border-cyan-500/20 bg-gradient-to-r from-cyan-500/10 via-transparent to-transparent px-4 py-3">
        {/* 标签 */}
        <div className="flex items-center gap-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 shadow-inner">
            <svg className="h-4 w-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <span className="font-mono text-sm font-bold uppercase tracking-widest text-cyan-200">
              Input
            </span>
            {selectedFile && (
              <span className="ml-3 font-mono text-xs text-cyan-400/50">
                {selectedFile.name.length > 20
                  ? selectedFile.name.slice(0, 17) + '...'
                  : selectedFile.name}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* 视图切换 */}
          {isSuccess && scoreJson && (
            <button
              type="button"
              onClick={() => setViewMode(prev => prev === 'image' ? 'json' : 'image')}
              className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-500/30 bg-slate-900/80 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-cyan-300 transition-all hover:border-cyan-400/50 hover:bg-cyan-500/10 hover:text-cyan-200"
            >
              {viewMode === 'image' ? (
                <>
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                  <span className="hidden sm:inline">JSON</span>
                </>
              ) : (
                <>
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span className="hidden sm:inline">Image</span>
                </>
              )}
            </button>
          )}

          {/* 状态徽章 */}
          <span className="font-mono text-[10px] uppercase tracking-wider text-cyan-500/40">
            Source
          </span>

          {/* 清除按钮 */}
          {selectedFile && !isLoading && (
            <button
              type="button"
              onClick={() => onFileChange(null)}
              className="rounded-lg p-1.5 text-slate-500 transition-all hover:bg-red-500/10 hover:text-red-400"
              title="清除"
              aria-label="清除已选文件"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* 内容区域 */}
      <div className="relative flex min-h-[320px] flex-1 flex-col bg-slate-950/40">
        {/* 角落装饰 - 科技边框 */}
        <div className="absolute left-3 top-3 h-4 w-4 border-l-2 border-t-2 border-cyan-500/30 transition-colors group-hover:border-cyan-400/50" />
        <div className="absolute right-3 top-3 h-4 w-4 border-r-2 border-t-2 border-cyan-500/30 transition-colors group-hover:border-cyan-400/50" />
        <div className="absolute bottom-3 left-3 h-4 w-4 border-b-2 border-l-2 border-cyan-500/30 transition-colors group-hover:border-cyan-400/50" />
        <div className="absolute bottom-3 right-3 h-4 w-4 border-b-2 border-r-2 border-cyan-500/30 transition-colors group-hover:border-cyan-400/50" />

        {isSuccess && scoreJson && viewMode === 'json' ? (
          <ScoreView scoreJson={scoreJson} className="flex-1" />
        ) : leftImageUrl ? (
          <FullscreenImage
            src={leftImageUrl}
            alt="简谱原图"
            className="flex-1 p-4"
          />
        ) : (
          <Dropzone
            onFileSelect={(f) => onFileChange(f)}
            disabled={isLoading}
          />
        )}
      </div>
    </div>
  )
}
