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
    <section className="relative mt-8 w-full space-y-4 overflow-hidden rounded-2xl border border-indigo-500/20 bg-slate-950/45 p-4 backdrop-blur-xl sm:p-5 lg:p-6">
      {/* AI 科技感装饰层 */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(99,102,241,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(99,102,241,0.05)_1px,transparent_1px)] bg-[size:34px_34px] opacity-50" />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-400/60 to-transparent" />
        <div className="absolute -left-20 top-1/3 h-40 w-40 rounded-full bg-indigo-500/15 blur-3xl" />
        <div className="absolute -right-20 bottom-0 h-40 w-40 rounded-full bg-violet-500/15 blur-3xl" />
      </div>

      <div className="relative space-y-4">
      {/* 处理时间 */}
      <div className="flex flex-wrap items-center justify-center gap-3 text-sm">
        <div className="flex items-center gap-1.5 rounded-full border border-emerald-400/40 bg-emerald-950/40 px-3 py-1.5 shadow-[0_0_22px_rgba(16,185,129,0.15)]">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-mono text-xs tracking-wide text-emerald-300">COMPLETE</span>
        </div>
        <span className="text-slate-600">|</span>
        <div className="flex items-center gap-2 text-slate-300">
          <svg className="h-4 w-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="font-mono text-indigo-200">{processingTimeMs}ms</span>
        </div>
      </div>

      {/* 警告提示 */}
      {warnings.length > 0 && (
        <div className="rounded-xl border border-amber-400/30 bg-amber-950/30 p-4 shadow-[0_0_20px_rgba(251,191,36,0.08)] backdrop-blur">
          <p className="mb-2 flex items-center gap-2 text-sm font-medium tracking-wide text-amber-300">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            提示与复核建议
          </p>
          <ul className="list-inside list-disc space-y-1 text-sm text-amber-200/80">
            {warnings.map((w, i) => (
              <li key={i}>
                {w.measure != null && `小节 ${w.measure}：`}
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
      <div className="text-center">
        <button
          type="button"
          onClick={onContinue}
          className="group inline-flex items-center gap-2 rounded-full border border-indigo-400/30 bg-slate-900/70 px-5 py-2 text-sm text-indigo-200 shadow-[0_0_25px_rgba(99,102,241,0.12)] backdrop-blur-sm transition-all hover:border-indigo-300/60 hover:bg-indigo-500/10 hover:text-indigo-100"
        >
          <svg className="h-4 w-4 transition-transform group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          继续上传另一张简谱
        </button>
      </div>
      </div>
    </section>
  )
}
