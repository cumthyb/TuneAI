import type { ScoreJson } from '../types/api'

interface ScoreViewProps {
  scoreJson: ScoreJson
  className: string
}

export default function ScoreView({ scoreJson, className }: ScoreViewProps) {
  return (
    <div className={`h-full overflow-auto bg-slate-950/60 p-4 font-mono text-xs ${className}`}>
      {/* JSON 查看器 */}
      <div className="rounded-xl border border-cyan-500/20 bg-gradient-to-br from-slate-900/80 to-indigo-950/40 p-4">
        <div className="mb-3 flex items-center gap-2 border-b border-cyan-500/20 pb-2">
          <svg className="h-4 w-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
          <span className="text-[10px] font-bold uppercase tracking-widest text-cyan-400/80">Raw JSON Data</span>
        </div>
        <pre className="overflow-x-auto whitespace-pre-wrap break-all text-slate-300/90">
          {JSON.stringify(scoreJson, null, 2)}
        </pre>
      </div>

      {/* 统计信息 */}
      {Array.isArray(scoreJson.events) && (
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-cyan-500/20 bg-gradient-to-br from-slate-900/60 to-cyan-950/40 p-3">
            <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-500/60">Events</div>
            <div className="text-2xl font-bold text-cyan-400">{scoreJson.events.length}</div>
          </div>
          <div className="rounded-xl border border-violet-500/20 bg-gradient-to-br from-slate-900/60 to-violet-950/40 p-3">
            <div className="text-[10px] font-bold uppercase tracking-wider text-violet-500/60">Source Key</div>
            <div className="text-2xl font-bold text-violet-400">
              {scoreJson.source_key.label}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
