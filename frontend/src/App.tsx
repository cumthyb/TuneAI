import { useCallback, useEffect, useState } from 'react'
import { transpose } from './lib/api'
import { logger } from './lib/logger'
import type { ScoreJson, Warning } from './types/api'
import type { TargetKey } from './types/api'
import ControlBar from './components/ControlBar'
import Dropzone from './components/Dropzone'
import LoadingState from './components/LoadingState'
import DownloadPanel from './components/DownloadPanel'
import FullscreenImage from './components/FullscreenImage'
import TechBackground from './components/TechBackground'
import AIBadge from './components/AIBadge'
import ScoreView from './components/ScoreView'

const MAX_SIZE_MB = 20

function validateFile(f: File): string | null {
  const okType = ['image/png', 'image/jpeg', 'image/jpg'].some((t) => f.type === t)
  if (!okType) return '请上传 PNG 或 JPG 图片'
  if (f.size > MAX_SIZE_MB * 1024 * 1024) return `图片大小不超过 ${MAX_SIZE_MB}MB`
  return null
}

type PageState =
  | { status: 'idle' }
  | { status: 'loading'; previewUrl: string }
  | {
      status: 'error'
      error: string
      errorCode?: string
      requestId?: string
    }
  | {
      status: 'success'
      originalPreview: string
      outputImage: string
      scoreJson: ScoreJson
      warnings: Warning[]
      requestId: string
      processingTimeMs: number
    }

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedPreviewUrl, setSelectedPreviewUrl] = useState<string | null>(null)
  const [targetKey, setTargetKey] = useState<TargetKey>('C')
  const [controlError, setControlError] = useState<string | null>(null)
  const [pageState, setPageState] = useState<PageState>({ status: 'idle' })
  
  // 左右面板的视图模式：'image' | 'json'
  const [leftViewMode, setLeftViewMode] = useState<'image' | 'json'>('image')
  const [rightViewMode, setRightViewMode] = useState<'image' | 'json'>('image')

  // 为选中的文件维护 object URL，清除时 revoke
  useEffect(() => {
    if (!selectedFile) {
      if (selectedPreviewUrl) {
        URL.revokeObjectURL(selectedPreviewUrl)
        setSelectedPreviewUrl(null)
      }
      return
    }
    const url = URL.createObjectURL(selectedFile)
    setSelectedPreviewUrl(url)
    return () => {
      URL.revokeObjectURL(url)
      setSelectedPreviewUrl(null)
    }
  }, [selectedFile])

  const handleFileChange = useCallback((file: File | null) => {
    setControlError(null)
    if (!file) {
      setSelectedFile(null)
      return
    }
    const err = validateFile(file)
    if (err) {
      setControlError(err)
      setSelectedFile(null)
      return
    }
    setSelectedFile(file)
  }, [])

  const handleSubmit = useCallback(async () => {
    if (!selectedFile || !selectedPreviewUrl) return
    setPageState({ status: 'loading', previewUrl: selectedPreviewUrl })
    try {
      const res = await transpose({ image: selectedFile, targetKey })
      if (res.success) {
        setPageState({
          status: 'success',
          originalPreview: selectedPreviewUrl,
          outputImage: res.output_image,
          scoreJson: res.score_json,
          warnings: res.warnings ?? [],
          requestId: res.request_id,
          processingTimeMs: res.processing_time_ms,
        })
      } else {
        setPageState({
          status: 'error',
          error: res.error_message,
          errorCode: res.error_code,
          requestId: res.request_id,
        })
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '网络或服务器错误'
      logger.error('transpose fetch failed', { error: message })
      setPageState({ status: 'error', error: message })
    }
  }, [selectedFile, selectedPreviewUrl, targetKey])

  const handleRetry = useCallback(() => {
    setPageState({ status: 'idle' })
  }, [])

  const handleContinueUpload = useCallback(() => {
    setSelectedFile(null)
    setPageState({ status: 'idle' })
  }, [])

  const isLoading = pageState.status === 'loading'
  const isSuccess = pageState.status === 'success'

  // 左侧简谱图：有原图时显示，否则为拖拽区
  const leftImageUrl =
    pageState.status === 'success'
      ? pageState.originalPreview
      : selectedPreviewUrl

  const panelBase =
    'ai-card flex flex-col overflow-hidden rounded-2xl lg:min-h-[60vh] neon-box'
  const labelBase =
    'shrink-0 border-b border-cyan-500/20 px-4 py-3 text-sm font-semibold tracking-wide'

  return (
    <main className="relative flex min-h-screen flex-col bg-[#050508]">
      {/* 科技感背景 */}
      <TechBackground />
      
      {/* 顶部霓虹发光条 */}
      <div className="relative h-1 w-full overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500" />
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent animate-[shimmer_2s_infinite]" />
      </div>

      {/* 上：标题 + 目标调与开始移调 */}
      <header className="relative shrink-0 border-b border-cyan-500/10 bg-slate-950/60 backdrop-blur-xl px-4 py-5 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <div className="mb-4 flex items-center gap-4">
            {/* AI Logo */}
            <div className="relative flex h-12 w-12 items-center justify-center">
              {/* 外发光环 */}
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 opacity-50 blur-lg animate-pulse" />
              {/* 主图标 */}
              <div className="relative flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 shadow-lg">
                <svg className="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z" />
                </svg>
              </div>
              {/* 状态指示点 */}
              <div className="absolute -right-1 -top-1 flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-cyan-400" />
              </div>
            </div>
            
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <h1 className="neon-text bg-gradient-to-r from-white via-cyan-200 to-purple-200 bg-clip-text text-2xl font-bold tracking-tight text-transparent sm:text-3xl">
                  TuneAI
                </h1>
                <AIBadge text="AI v2.0" size="sm" />
              </div>
              <p className="text-xs text-cyan-400/60 font-mono tracking-wide">NEURAL TRANSPOSITION ENGINE</p>
            </div>

            {/* 右侧状态信息 */}
            <div className="hidden sm:flex items-center gap-4 text-xs font-mono text-slate-500">
              <div className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
                SYSTEM ONLINE
              </div>
              <div className="text-cyan-500/60">API READY</div>
            </div>
          </div>
          
          <ControlBar
            file={selectedFile}
            targetKey={targetKey}
            onTargetKeyChange={setTargetKey}
            onSubmit={handleSubmit}
            disabled={isLoading}
            error={controlError}
          />
        </div>
      </header>

      {/* 下：左右结构，简谱图片预览 */}
      <div className="flex-1 px-4 py-6 sm:px-6">
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-6 lg:grid-cols-2 lg:gap-8">
          {/* 左：原图 / 上传前简谱 */}
          <div className={panelBase}>
            <div
              className={`${labelBase} flex items-center justify-between gap-2 bg-gradient-to-r from-cyan-500/10 via-cyan-500/5 to-transparent text-cyan-200`}
            >
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
                {/* 视图切换按钮 - 仅在有内容时显示 */}
                {pageState.status === 'success' && (
                  <button
                    type="button"
                    onClick={() => setLeftViewMode(prev => prev === 'image' ? 'json' : 'image')}
                    className="inline-flex items-center gap-1.5 rounded border border-cyan-500/30 bg-slate-900/60 px-2 py-1 text-[10px] font-medium text-cyan-300 transition-all hover:border-cyan-400/50 hover:bg-cyan-500/10"
                    title={leftViewMode === 'image' ? '切换到解析数据' : '切换到图片'}
                  >
                    {leftViewMode === 'image' ? (
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
                    onClick={() => handleFileChange(null)}
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
            <div className="relative flex min-h-[320px] flex-1 flex-col bg-slate-950/50">
              {/* 角落装饰 */}
              <div className="absolute left-2 top-2 h-3 w-3 border-l border-t border-cyan-500/30" />
              <div className="absolute right-2 top-2 h-3 w-3 border-r border-t border-cyan-500/30" />
              <div className="absolute bottom-2 left-2 h-3 w-3 border-b border-l border-cyan-500/30" />
              <div className="absolute bottom-2 right-2 h-3 w-3 border-b border-r border-cyan-500/30" />
              
              {pageState.status === 'success' && leftViewMode === 'json' ? (
                <ScoreView scoreJson={pageState.scoreJson} className="flex-1" />
              ) : leftImageUrl ? (
                <FullscreenImage
                  src={leftImageUrl}
                  alt="简谱原图"
                  className="flex-1 p-4"
                />
              ) : (
                <Dropzone
                  onFileSelect={(f) => handleFileChange(f)}
                  disabled={isLoading}
                />
              )}
            </div>
          </div>

          {/* 右：移调结果 / 上传后简谱 */}
          <div className={panelBase}>
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
                {/* 视图切换按钮 - 仅在有内容时显示 */}
                {pageState.status === 'success' && (
                  <button
                    type="button"
                    onClick={() => setRightViewMode(prev => prev === 'image' ? 'json' : 'image')}
                    className="inline-flex items-center gap-1.5 rounded border border-purple-500/30 bg-slate-900/60 px-2 py-1 text-[10px] font-medium text-purple-300 transition-all hover:border-purple-400/50 hover:bg-purple-500/10"
                    title={rightViewMode === 'image' ? '切换到解析数据' : '切换到图片'}
                  >
                    {rightViewMode === 'image' ? (
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
            <div className="relative flex min-h-[320px] flex-1 flex-col bg-slate-950/50">
              {/* 角落装饰 */}
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
                  <p className="mt-1 text-xs text-slate-500 font-mono">
                    UPLOAD SOURCE → INIT TRANSPOSITION
                  </p>
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
                    <div className="font-mono text-[10px] text-slate-600">
                      NEURAL NETWORK: ACTIVE
                    </div>
                  </div>
                </div>
              )}
              {pageState.status === 'error' && (
                <div className="flex flex-1 flex-col items-center justify-center p-8">
                  <LoadingState
                    error={pageState.error}
                    errorCode={pageState.errorCode}
                    requestId={pageState.requestId}
                    onRetry={handleRetry}
                  />
                </div>
              )}
              {pageState.status === 'success' && (
                rightViewMode === 'json' ? (
                  <ScoreView scoreJson={pageState.scoreJson} className="flex-1" />
                ) : (
                  <FullscreenImage
                    src={
                      pageState.outputImage.startsWith('data:')
                        ? pageState.outputImage
                        : `data:image/png;base64,${pageState.outputImage}`
                    }
                    alt="移调后的简谱"
                    className="flex-1 p-4"
                  />
                )
              )}
            </div>
          </div>
        </div>

        {/* 成功时：提示、下载、继续上传 */}
        {isSuccess && (
          <div className="mx-auto mt-8 max-w-6xl space-y-4">
            <div className="flex items-center justify-center gap-3 text-sm">
              <div className="flex items-center gap-1.5 rounded-full border border-green-500/30 bg-green-950/30 px-3 py-1.5">
                <span className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
                <span className="font-mono text-xs text-green-400">COMPLETE</span>
              </div>
              <span className="text-slate-500">|</span>
              <div className="flex items-center gap-2 text-slate-400">
                <svg className="h-4 w-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-mono text-cyan-300">{pageState.processingTimeMs}ms</span>
              </div>
            </div>
            {pageState.warnings.length > 0 && (
              <div className="rounded-xl border border-amber-500/30 bg-amber-950/30 p-4 backdrop-blur">
                <p className="mb-2 flex items-center gap-2 text-sm font-medium text-amber-300">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  提示与复核建议
                </p>
                <ul className="list-inside list-disc space-y-1 text-sm text-amber-200/80">
                  {pageState.warnings.map((w, i) => (
                    <li key={i}>
                      {w.measure != null && `小节 ${w.measure}：`}
                      {w.message}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <DownloadPanel
              outputImage={pageState.outputImage}
              scoreJson={pageState.scoreJson}
              requestId={pageState.requestId}
              processingTimeMs={pageState.processingTimeMs}
            />
            <div className="text-center">
              <button
                type="button"
                onClick={handleContinueUpload}
                className="group inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-slate-900/60 px-5 py-2 text-sm text-indigo-300 backdrop-blur-sm transition-all hover:border-indigo-400/50 hover:bg-indigo-500/10 hover:text-indigo-200"
              >
                <svg className="h-4 w-4 transition-transform group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                继续上传另一张简谱
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
