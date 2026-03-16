import type { ScoreJson } from '../types/api'

interface ScoreViewProps {
  scoreJson: ScoreJson
  className: string
}

export default function ScoreView({ scoreJson, className }: ScoreViewProps) {
  return (
    <div className={`h-full overflow-auto bg-slate-950/80 p-4 font-mono text-xs ${className}`}>
      <div className="rounded-lg border border-cyan-500/20 bg-slate-900/50 p-3">
        <div className="mb-2 flex items-center gap-2 text-cyan-400/80">
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
          <span className="text-[10px] uppercase tracking-wider">Raw JSON Data</span>
        </div>
        <pre className="overflow-x-auto whitespace-pre-wrap break-all text-slate-300/90">
          {JSON.stringify(scoreJson, null, 2)}
        </pre>
      </div>
      
      {/* 统计信息 */}
      {Array.isArray(scoreJson.events) && (
        <div className="mt-3 grid grid-cols-2 gap-2">
          <div className="rounded border border-slate-700/50 bg-slate-900/30 p-2">
            <div className="text-[10px] uppercase text-slate-500">Events</div>
            <div className="text-sm text-cyan-400">{scoreJson.events.length}</div>
          </div>
          <div className="rounded border border-slate-700/50 bg-slate-900/30 p-2">
            <div className="text-[10px] uppercase text-slate-500">Source Key</div>
            <div className="text-sm text-purple-400">
              {scoreJson.source_key.label}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
