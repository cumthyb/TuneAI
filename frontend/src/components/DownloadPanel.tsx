import { useCallback } from 'react'
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
    void navigator.clipboard.writeText(text)
  }, [requestId, processingTimeMs])

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p className="mb-3 text-sm font-medium text-slate-700">下载与调试</p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={downloadImage}
          className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700"
        >
          下载结果图
        </button>
        <button
          type="button"
          onClick={downloadJson}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          下载解析 JSON
        </button>
        <button
          type="button"
          onClick={copyDebugInfo}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          title="复制 request_id 便于与后端日志关联"
        >
          复制调试信息
        </button>
      </div>
      <p className="mt-3 font-mono text-xs text-slate-500">
        request_id: {requestId}
      </p>
    </div>
  )
}
