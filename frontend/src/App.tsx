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
    'flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-slate-100 lg:min-h-[60vh]'
  const labelBase =
    'shrink-0 border-b border-slate-200 px-3 py-2 text-sm font-medium'

  return (
    <main className="flex min-h-screen flex-col bg-gradient-to-b from-slate-50 to-slate-100">
      {/* 上：标题 + 目标调与开始移调 */}
      <header className="shrink-0 border-b border-slate-200 bg-white px-4 py-4 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <h1 className="mb-4 font-serif text-xl font-semibold tracking-tight text-slate-800 sm:text-2xl">
            TuneAI 简谱移调
          </h1>
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
      <div className="flex-1 px-4 py-4 sm:px-6">
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-4 lg:grid-cols-2 lg:gap-6">
          {/* 左：原图 / 上传前简谱 */}
          <div className={panelBase}>
            <div
              className={`${labelBase} flex items-center justify-between gap-2 bg-slate-50 text-slate-600`}
            >
              <span>
                原图
                {selectedFile && (
                  <span className="ml-1 font-normal text-slate-500">
                    · {selectedFile.name}
                  </span>
                )}
              </span>
              {selectedFile && !isLoading && (
                <button
                  type="button"
                  onClick={() => handleFileChange(null)}
                  className="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-600"
                  title="清除"
                  aria-label="清除已选文件"
                >
                  ×
                </button>
              )}
            </div>
            <div className="flex min-h-[280px] flex-1 flex-col">
              {leftImageUrl ? (
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
            <p className={`${labelBase} bg-amber-50 text-amber-800`}>
              移调结果
            </p>
            <div className="flex min-h-[280px] flex-1 flex-col">
              {pageState.status === 'idle' && (
                <div className="flex flex-1 flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50/50 p-8 text-center">
                  <p className="text-slate-500">移调结果将显示在此处</p>
                  <p className="mt-1 text-xs text-slate-400">
                    选择文件并点击「开始移调」
                  </p>
                </div>
              )}
              {pageState.status === 'loading' && (
                <div className="flex flex-1 items-center justify-center p-8">
                  <LoadingState message="正在识别与移调，请稍候…" />
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
                <FullscreenImage
                  src={
                    pageState.outputImage.startsWith('data:')
                      ? pageState.outputImage
                      : `data:image/png;base64,${pageState.outputImage}`
                  }
                  alt="移调后的简谱"
                  className="flex-1 p-4"
                />
              )}
            </div>
          </div>
        </div>

        {/* 成功时：提示、下载、继续上传 */}
        {isSuccess && (
          <div className="mx-auto mt-6 max-w-6xl space-y-4">
            <p className="text-center text-sm text-slate-500">
              处理耗时 <strong>{pageState.processingTimeMs}</strong> ms
            </p>
            {pageState.warnings.length > 0 && (
              <div className="rounded-xl border border-amber-200 bg-amber-50/80 p-4">
                <p className="mb-2 text-sm font-medium text-amber-800">
                  提示与复核建议
                </p>
                <ul className="list-inside list-disc space-y-1 text-sm text-amber-900">
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
                className="text-sm text-amber-600 hover:underline"
              >
                继续上传另一张简谱
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
