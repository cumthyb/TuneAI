import type { Warning } from '../types/api'
import FullscreenImage from './FullscreenImage'

export interface ResultViewerProps {
  /** 原图预览 URL（object URL 或 data URL） */
  originalPreview: string
  /** 结果图 base64（带 data:image/... 前缀或纯 base64） */
  outputImage: string
  /** 告警与低置信度提示 */
  warnings: Warning[]
  processingTimeMs?: number
}

function ensureDataUrl(base64: string): string {
  if (base64.startsWith('data:')) return base64
  return `data:image/png;base64,${base64}`
}

export default function ResultViewer({
  originalPreview,
  outputImage,
  warnings,
  processingTimeMs,
}: ResultViewerProps) {
  const resultSrc = ensureDataUrl(outputImage)

  const panelBase = 'flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-slate-100 lg:min-h-[65vh]'
  const labelBase = 'shrink-0 border-b border-slate-200 px-3 py-2 text-sm font-medium'
  const imgWrap = 'flex min-h-[200px] flex-1 items-center justify-center overflow-auto p-4'

  return (
    <div className="flex flex-col gap-6">
      {processingTimeMs != null && (
        <p className="text-center text-sm text-slate-500">
          处理耗时 <strong>{processingTimeMs}</strong> ms
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 lg:gap-6">
        <div className={panelBase}>
          <p className={`${labelBase} bg-slate-50 text-slate-600`}>原图</p>
          <FullscreenImage src={originalPreview} alt="上传的简谱原图" className={imgWrap} />
        </div>
        <div className={panelBase}>
          <p className={`${labelBase} bg-amber-50 text-amber-800`}>移调结果</p>
          <FullscreenImage src={resultSrc} alt="移调后的简谱" className={imgWrap} />
        </div>
      </div>

      {warnings.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/80 p-4">
          <p className="mb-2 text-sm font-medium text-amber-800">提示与复核建议</p>
          <ul className="list-inside list-disc space-y-1 text-sm text-amber-900">
            {warnings.map((w, i) => (
              <li key={i}>
                {w.measure != null && `小节 ${w.measure}：`}
                {w.message}
                {w.type && (
                  <span className="ml-1 text-amber-600">({w.type})</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
