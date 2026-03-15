import { useCallback, useState } from 'react'
import type { ScoreJson } from '../types/api'

export interface DownloadPanelProps {
  /** 结果图 base64（可带或不带 data: 前缀） */
  outputImage: string
  scoreJson: ScoreJson
  requestId: string
  processingTimeMs?: number
}

function ensureDataUrl(base64: string): string {
  if (base64.startsWith('data:')) return base64
  return `data:image/png;base64,${base64}`
}

export default function DownloadPanel({
  outputImage,
  scoreJson,
  requestId,
  processingTimeMs,
}: DownloadPanelProps) {
  const [copied, setCopied] = useState(false)
  const downloadImage = useCallback(() => {
    const dataUrl = ensureDataUrl(outputImage)
    const a = document.createElement('a')
    a.href = dataUrl
    a.download = `tuneai-result-${requestId.slice(0, 8)}.png`
    a.click()
  }, [outputImage, requestId])

  const downloadJson = useCallback(() => {
    const blob = new Blob([JSON.stringify(scoreJson, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tuneai-score-${requestId.slice(0, 8)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [scoreJson, requestId])

  const copyDebugInfo = useCallback(() => {
    const text = [
      `request_id: ${requestId}`,
      processingTimeMs != null ? `processing_time_ms: ${processingTimeMs}` : '',
    ]
      .filter(Boolean)
      .join('\n')
    void navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }, [requestId, processingTimeMs])

  return (
    <div className="rounded-2xl border border-indigo-500/20 bg-slate-900/40 p-5 backdrop-blur-xl">
      <p className="mb-4 flex items-center gap-2 text-sm font-semibold text-indigo-300">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        下载与调试
      </p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={downloadImage}
          className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-500/25 transition-all hover:shadow-indigo-500/40 hover:scale-[1.02] active:scale-[0.98]"
        >
          <svg className="h-4 w-4 transition-transform group-hover:-translate-y-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          下载结果图
        </button>
        <button
          type="button"
          onClick={downloadJson}
          className="group inline-flex items-center gap-2 rounded-xl border border-indigo-500/30 bg-slate-900/60 px-4 py-2.5 text-sm font-medium text-indigo-300 backdrop-blur-sm transition-all hover:border-indigo-400/50 hover:bg-indigo-500/10 hover:text-indigo-200"
        >
          <svg className="h-4 w-4 transition-transform group-hover:-translate-y-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          下载解析 JSON
        </button>
        <button
          type="button"
          onClick={copyDebugInfo}
          className="group inline-flex items-center gap-2 rounded-xl border border-slate-600/50 bg-slate-900/40 px-4 py-2.5 text-sm font-medium text-slate-400 backdrop-blur-sm transition-all hover:border-slate-500 hover:bg-slate-800/60 hover:text-slate-300"
          title="复制 request_id 便于与后端日志关联"
        >
          {copied ? (
            <>
              <svg className="h-4 w-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-green-400">已复制</span>
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              复制调试信息
            </>
          )}
        </button>
      </div>
      <div className="mt-4 flex items-center gap-2 rounded-lg bg-slate-950/50 px-3 py-2">
        <span className="text-xs text-slate-500">request_id:</span>
        <code className="font-mono text-xs text-indigo-400">{requestId}</code>
      </div>
    </div>
  )
}
