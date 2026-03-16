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

const labelBase = 'shrink-0 border-b border-purple-500/20 px-4 py-3 text-sm font-semibold tracking-wide'

export default function OutputPanel({ pageState, onRetry }: OutputPanelProps) {
  const [viewMode, setViewMode] = useState<'image' | 'json'>('image')

  const isSuccess = pageState.status === 'success'
  const scoreJson = isSuccess ? pageState.scoreJson : null

  return (
    <div className="ai-card flex flex-col overflow-hidden rounded-2xl lg:min-h-[60vh] neon-box">
      {/* 标题栏 */}
      <div className={`${labelBase} flex items-center justify-between bg-gradient-to-r from-purple-500/10 via-purple-500/5 to-transparent text-purple-200`}>
        <div className="flex items-center gap-3">
          <div className="flex h-6 w-6 items-center justify-center rounded bg-purple-500/20">
            <svg className="h-4 w-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z" />
            </svg>
          </div>
          <span className="font-semibold">OUTPUT_01</span>
        </div>

        <div className="flex items-center gap-2">
          {isSuccess && (
            <button
              type="button"
              onClick={() => setViewMode(prev => prev === 'image' ? 'json' : 'image')}
              className="inline-flex items-center gap-1.5 rounded border border-purple-500/30 bg-slate-900/60 px-2 py-1 text-[10px] font-medium text-purple-300 transition-all hover:border-purple-400/50 hover:bg-purple-500/10"
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
          <span className="font-mono text-xs text-purple-500/40">AI GEN</span>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="relative flex min-h-[320px] flex-1 flex-col bg-slate-950/50">
        <div className="absolute left-2 top-2 h-3 w-3 border-l border-t border-purple-500/30" />
        <div className="absolute right-2 top-2 h-3 w-3 border-r border-t border-purple-500/30" />
        <div className="absolute bottom-2 left-2 h-3 w-3 border-b border-l border-purple-500/30" />
        <div className="absolute bottom-2 right-2 h-3 w-3 border-b border-r border-purple-500/30" />

        {pageState.status === 'idle' && (
          <div className="flex flex-1 flex-col items-center justify-center rounded-lg border border-dashed border-cyan-500/20 bg-slate-900/30 p-8 text-center">
            <div className="mb-4 relative">
              <div className="absolute inset-0 rounded-full bg-cyan-500/20 blur-xl animate-pulse" />
              <div className="relative rounded-full border border-cyan-500/30 bg-cyan-950/50 p-4">
                <svg className="h-8 w-8 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
            <p className="text-slate-300 font-medium">等待处理</p>
            <p className="mt-1 text-xs text-slate-500 font-mono">UPLOAD SOURCE → INIT TRANSPOSITION</p>
          </div>
        )}

        {pageState.status === 'loading' && (
          <div className="flex flex-1 flex-col items-center justify-center p-8">
            <LoadingState message="AI 处理中…" />
            <div className="mt-6 flex flex-col items-center gap-2">
              <div className="flex items-center gap-2 font-mono text-xs text-cyan-500/60">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-400" />
                ANALYZING PATTERN
              </div>
              <div className="h-px w-32 bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
              <div className="font-mono text-[10px] text-slate-600">NEURAL NETWORK: ACTIVE</div>
            </div>
          </div>
        )}

        {pageState.status === 'error' && (
          <div className="flex flex-1 flex-col items-center justify-center p-8">
            <div className="rounded-2xl border border-red-500/30 bg-red-950/40 p-6 text-center backdrop-blur-xl">
              <div className="mb-4 inline-flex rounded-full bg-red-500/20 p-3">
                <svg className="h-8 w-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="font-medium text-red-300">{pageState.error}</p>
              {pageState.errorCode && <p className="mt-1 text-sm text-red-400/80">错误码：{pageState.errorCode}</p>}
              {pageState.requestId && (
                <p className="mt-2 font-mono text-xs text-slate-500">request_id: {pageState.requestId}</p>
              )}
              <button
                type="button"
                onClick={onRetry}
                className="mt-5 inline-flex items-center gap-2 rounded-xl bg-red-600/80 px-5 py-2.5 text-sm font-medium text-white backdrop-blur-sm transition-all hover:bg-red-600 hover:shadow-lg hover:shadow-red-500/30"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                重新上传
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
