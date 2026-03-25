import { useState } from 'react'
import type { ScoreJson } from '../types/api'
import LoadingState from './LoadingState'
import FullscreenImage from './FullscreenImage'
import ScoreView from './ScoreView'

interface OutputPanelProps {
  pageState:
    | { status: 'idle' }
    | { status: 'loading' }
    | { status: 'error'; error: string; errorCode?: string; requestId?: string }
    | { status: 'success'; outputImage: string; scoreJson: ScoreJson; requestId: string }
  onRetry: () => void
}

export default function OutputPanel({ pageState, onRetry }: OutputPanelProps) {
  const [viewMode, setViewMode] = useState<'image' | 'json'>('image')

  const isSuccess = pageState.status === 'success'
  const scoreJson = isSuccess ? pageState.scoreJson : null

  return (
    <div className="group relative flex flex-col overflow-hidden rounded-2xl lg:min-h-[60vh] border border-violet-500/20 bg-gradient-to-br from-slate-950/90 via-indigo-950/80 to-violet-950/60 backdrop-blur-xl">
      {/* 边框发光 */}
      <div className="absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-500 group-hover:opacity-100">
        <div className="absolute inset-0 rounded-2xl border border-violet-400/30 shadow-lg shadow-violet-500/10" />
      </div>

      {/* 顶部标签栏 */}
      <div className="relative flex items-center justify-between border-b border-violet-500/20 bg-gradient-to-r from-violet-500/10 via-transparent to-transparent px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 shadow-inner">
            <svg className="h-4 w-4 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z" />
            </svg>
          </div>
          <span className="font-mono text-sm font-bold uppercase tracking-widest text-violet-200">
            Output
          </span>
        </div>

        <div className="flex items-center gap-2">
          {isSuccess && (
            <button
              type="button"
              onClick={() => setViewMode(prev => prev === 'image' ? 'json' : 'image')}
              className="inline-flex items-center gap-1.5 rounded-lg border border-violet-500/30 bg-slate-900/80 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-violet-300 transition-all hover:border-violet-400/50 hover:bg-violet-500/10 hover:text-violet-200"
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
          <span className="font-mono text-[10px] uppercase tracking-wider text-violet-500/40">
            AI Generated
          </span>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="relative flex min-h-[320px] flex-1 flex-col bg-slate-950/40">
        {/* 角落装饰 */}
        <div className="absolute left-3 top-3 h-4 w-4 border-l-2 border-t-2 border-violet-500/30 transition-colors group-hover:border-violet-400/50" />
        <div className="absolute right-3 top-3 h-4 w-4 border-r-2 border-t-2 border-violet-500/30 transition-colors group-hover:border-violet-400/50" />
        <div className="absolute bottom-3 left-3 h-4 w-4 border-b-2 border-l-2 border-violet-500/30 transition-colors group-hover:border-violet-400/50" />
        <div className="absolute bottom-3 right-3 h-4 w-4 border-b-2 border-r-2 border-violet-500/30 transition-colors group-hover:border-violet-400/50" />

        {pageState.status === 'idle' && (
          <div className="flex flex-1 flex-col items-center justify-center rounded-lg border border-dashed border-violet-500/20 bg-slate-900/20 p-8 text-center">
            {/* 装饰性音符 */}
            <div className="relative mb-6">
              <div className="absolute inset-0 rounded-full bg-violet-500/20 blur-2xl animate-pulse" />
              <div className="relative flex h-16 w-16 items-center justify-center rounded-full border border-violet-500/30 bg-gradient-to-br from-violet-950/80 to-indigo-950/80">
                <svg className="h-8 w-8 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
            <p className="font-mono text-sm font-medium text-slate-300">等待处理</p>
            <p className="mt-2 font-mono text-xs tracking-widest text-slate-600">
              UPLOAD SOURCE → INIT TRANSPOSITION
            </p>
          </div>
        )}

        {pageState.status === 'loading' && (
          <div className="flex flex-1 flex-col items-center justify-center p-8">
            <LoadingState message="AI Transposing..." />
            <div className="mt-6 flex flex-col items-center gap-3">
              <div className="flex items-center gap-2 font-mono text-xs text-violet-500/60">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-violet-400" />
                ANALYZING PATTERN
              </div>
              <div className="h-px w-40 bg-gradient-to-r from-transparent via-violet-500/30 to-transparent" />
              <div className="font-mono text-[10px] text-slate-600">NEURAL NETWORK: ACTIVE</div>
            </div>
          </div>
        )}

        {pageState.status === 'error' && (
          <div className="flex flex-1 flex-col items-center justify-center p-8">
            <div className="relative rounded-2xl border border-red-500/30 bg-gradient-to-br from-red-950/60 to-slate-950/80 p-6 text-center shadow-xl shadow-red-500/10 backdrop-blur-xl">
              {/* 错误图标 */}
              <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-full bg-red-500/20">
                <svg className="h-8 w-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="font-medium text-red-200">{pageState.error}</p>
              {pageState.errorCode && (
                <p className="mt-2 font-mono text-xs text-red-400/80">Error Code: {pageState.errorCode}</p>
              )}
              {pageState.requestId && (
                <p className="mt-2 font-mono text-xs text-slate-500">Request ID: {pageState.requestId}</p>
              )}
              <button
                type="button"
                onClick={onRetry}
                className="mt-6 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-red-600/80 to-red-700/80 px-6 py-2.5 text-sm font-bold text-white shadow-lg backdrop-blur-sm transition-all hover:from-red-600 hover:to-red-700 hover:shadow-red-500/30 active:scale-95"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Retry Upload
              </button>
            </div>
          </div>
        )}

        {pageState.status === 'success' && (
          viewMode === 'json' && scoreJson ? (
            <ScoreView scoreJson={scoreJson} className="flex-1" />
          ) : (
            <FullscreenImage
              src={`data:image/png;base64,${pageState.outputImage}`}
              alt="移调后的简谱"
              className="flex-1 p-4"
            />
          )
        )}
      </div>
    </div>
  )
}
