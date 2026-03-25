import type { Warning, ScoreJson } from '../types/api'
import DownloadPanel from './DownloadPanel'

interface ResultSectionProps {
  processingTimeMs: number
  warnings: Warning[]
  outputImage: string
  scoreJson: ScoreJson
  requestId: string
  onContinue: () => void
}

export default function ResultSection({
  processingTimeMs,
  warnings,
  outputImage,
  scoreJson,
  requestId,
  onContinue,
}: ResultSectionProps) {
  return (
    <section className="relative mt-8 w-full space-y-4 overflow-hidden rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-slate-950/80 via-indigo-950/40 to-slate-950/80 p-4 backdrop-blur-xl shadow-2xl shadow-cyan-500/5 sm:p-5 lg:p-6">
      {/* 装饰层 */}
      <div className="pointer-events-none absolute inset-0">
        {/* 网格背景 */}
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage: `
              linear-gradient(rgba(6, 182, 212, 0.05) 1px, transparent 1px),
              linear-gradient(90deg, rgba(6, 182, 212, 0.05) 1px, transparent 1px)
            `,
            backgroundSize: '32px 32px',
          }}
        />
        {/* 顶部渐变线 */}
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-400/50 to-transparent" />
        {/* 光晕 */}
        <div className="absolute -left-20 top-1/3 h-48 w-48 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="absolute -right-20 bottom-0 h-48 w-48 rounded-full bg-violet-500/10 blur-3xl" />
      </div>

      <div className="relative space-y-4">
        {/* 状态栏 */}
        <div className="flex flex-wrap items-center justify-center gap-3 text-sm">
          {/* 完成徽章 */}
          <div className="flex items-center gap-2 rounded-full border border-emerald-400/30 bg-gradient-to-r from-emerald-950/60 to-cyan-950/40 px-4 py-1.5 shadow-lg shadow-emerald-500/10">
            <div className="relative flex h-2 w-2 items-center justify-center">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </div>
            <span className="font-mono text-xs font-bold uppercase tracking-widest text-emerald-300">Complete</span>
          </div>

          <span className="text-slate-600">|</span>

          {/* 处理时间 */}
          <div className="flex items-center gap-2">
            <svg className="h-4 w-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-mono text-xs text-cyan-200">{processingTimeMs}ms</span>
          </div>
        </div>

        {/* 警告提示 */}
        {warnings.length > 0 && (
          <div className="rounded-xl border border-amber-400/30 bg-gradient-to-br from-amber-950/40 to-slate-950/40 p-4 shadow-lg shadow-amber-500/5 backdrop-blur">
            <p className="mb-2 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-amber-300">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Warnings
            </p>
            <ul className="list-inside list-disc space-y-1 text-sm text-amber-200/80">
              {warnings.map((w, i) => (
                <li key={i}>
                  {w.measure != null && `Measure ${w.measure}: `}
                  {w.message}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 下载面板 */}
        <DownloadPanel
          outputImage={outputImage}
          scoreJson={scoreJson}
          requestId={requestId}
          processingTimeMs={processingTimeMs}
        />

        {/* 继续上传按钮 */}
        <div className="text-center pt-2">
          <button
            type="button"
            onClick={onContinue}
            className="group inline-flex items-center gap-2 rounded-xl border border-cyan-500/30 bg-gradient-to-r from-slate-900/80 to-indigo-950/60 px-6 py-2.5 text-sm font-bold uppercase tracking-wider text-cyan-300 shadow-lg shadow-cyan-500/10 backdrop-blur-sm transition-all hover:border-cyan-400/50 hover:from-slate-900 hover:to-indigo-950 hover:text-cyan-200 hover:shadow-cyan-500/20"
          >
            <svg className="h-4 w-4 transition-transform group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Continue Upload
          </button>
        </div>
      </div>
    </section>
  )
}
