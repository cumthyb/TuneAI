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

const labelBase = 'shrink-0 border-b border-cyan-500/20 px-4 py-3 text-sm font-semibold tracking-wide'

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
    <div className="ai-card flex flex-col overflow-hidden rounded-2xl lg:min-h-[60vh] neon-box">
      {/* 标题栏 */}
      <div className={`${labelBase} flex items-center justify-between gap-2 bg-gradient-to-r from-cyan-500/10 via-cyan-500/5 to-transparent text-cyan-200`}>
        <div className="flex items-center gap-3">
          <div className="flex h-6 w-6 items-center justify-center rounded bg-cyan-500/20">
            <svg className="h-4 w-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <span className="font-semibold">INPUT_01</span>
            {selectedFile && (
              <span className="ml-2 font-mono text-xs text-cyan-400/60">
                {selectedFile.name}
              </span>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* 视图切换按钮 */}
          {isSuccess && scoreJson && (
            <button
              type="button"
              onClick={() => setViewMode(prev => prev === 'image' ? 'json' : 'image')}
              className="inline-flex items-center gap-1.5 rounded border border-cyan-500/30 bg-slate-900/60 px-2 py-1 text-[10px] font-medium text-cyan-300 transition-all hover:border-cyan-400/50 hover:bg-cyan-500/10"
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
                  <span className="hidden sm:inline">IMG</span>
                </>
              )}
            </button>
          )}
          
          <span className="font-mono text-xs text-cyan-500/40">SRC</span>
          
          {selectedFile && !isLoading && (
            <button
              type="button"
              onClick={() => onFileChange(null)}
              className="rounded-lg p-1.5 text-slate-400 transition-all hover:bg-white/10 hover:text-white"
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
      <div className="relative flex min-h-[320px] flex-1 flex-col bg-slate-950/50">
        {/* 角落装饰 */}
        <div className="absolute left-2 top-2 h-3 w-3 border-l border-t border-cyan-500/30" />
        <div className="absolute right-2 top-2 h-3 w-3 border-r border-t border-cyan-500/30" />
        <div className="absolute bottom-2 left-2 h-3 w-3 border-b border-l border-cyan-500/30" />
        <div className="absolute bottom-2 right-2 h-3 w-3 border-b border-r border-cyan-500/30" />
        
        {isSuccess && scoreJson && viewMode === 'json' ? (
          <ScoreView scoreJson={scoreJson} className="flex-1" />
        ) : leftImageUrl ? (
          <FullscreenImage
            src={leftImageUrl}
            alt="简谱原图"
            className="flex-1 p-4"
            imgClassName=""
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
