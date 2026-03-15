interface LoadingStateProps {
  message?: string
  error?: string
  errorCode?: string
  requestId?: string
  onRetry?: () => void
}

export default function LoadingState({
  message = '正在识别与移调，请稍候…',
  error,
  errorCode,
  requestId,
  onRetry,
}: LoadingStateProps) {
  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
        <p className="font-medium text-red-800">{error}</p>
        {errorCode && <p className="mt-1 text-sm text-red-600">错误码：{errorCode}</p>}
        {requestId && (
          <p className="mt-1 font-mono text-xs text-slate-500">request_id: {requestId}</p>
        )}
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            重新上传
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-slate-200 bg-slate-50/80 py-12">
      <div
        className="h-10 w-10 animate-spin rounded-full border-2 border-amber-500 border-t-transparent"
        aria-hidden
      />
      <p className="mt-4 text-slate-600">{message}</p>
      <p className="mt-1 text-xs text-slate-400">通常需要 5–15 秒</p>
    </div>
  )
}
