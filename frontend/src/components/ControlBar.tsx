import { TARGET_KEYS, type TargetKey } from '../types/api'

export interface ControlBarProps {
  file: File | null
  targetKey: TargetKey
  onTargetKeyChange: (key: TargetKey) => void
  onSubmit: () => void
  disabled?: boolean
  error?: string | null
}

export default function ControlBar({
  file,
  targetKey,
  onTargetKeyChange,
  onSubmit,
  disabled,
  error,
}: ControlBarProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <label htmlFor="target-key" className="text-sm font-medium text-slate-700">
            目标调
          </label>
          <select
            id="target-key"
            value={targetKey}
            onChange={(e) => onTargetKeyChange(e.target.value as TargetKey)}
            disabled={disabled}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
          >
            {TARGET_KEYS.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          onClick={onSubmit}
          disabled={disabled || !file}
          className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          开始移调
        </button>
      </div>
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
