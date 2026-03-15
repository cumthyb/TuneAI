import { useCallback, useEffect, useState } from 'react'
import { TARGET_KEYS, type TargetKey } from '../types/api'
import FullscreenImage from './FullscreenImage'

const ACCEPT = 'image/png,image/jpeg,image/jpg'
const MAX_SIZE_MB = 20

export interface UploadProps {
  onSubmit: (file: File, targetKey: string) => void
  disabled?: boolean
  /** 左右布局：左侧预览/拖拽区，右侧目标调与提交 */
  splitLayout?: boolean
}

export default function Upload({ onSubmit, disabled, splitLayout }: UploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [objectUrl, setObjectUrl] = useState<string | null>(null)
  const [targetKey, setTargetKey] = useState<TargetKey>('C')
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!file) {
      setObjectUrl(null)
      return
    }
    const url = URL.createObjectURL(file)
    setObjectUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const validateFile = useCallback((f: File) => {
    const okType = ACCEPT.split(',').some((t) => t.trim().startsWith(f.type))
    if (!okType) return '请上传 PNG 或 JPG 图片'
    if (f.size > MAX_SIZE_MB * 1024 * 1024) return `图片大小不超过 ${MAX_SIZE_MB}MB`
    return null
  }, [])

  const handleFile = useCallback(
    (f: File | null) => {
      setError(null)
      if (!f) {
        setFile(null)
        return
      }
      const err = validateFile(f)
      if (err) {
        setError(err)
        setFile(null)
        return
      }
      setFile(f)
    },
    [validateFile]
  )

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      const f = e.dataTransfer.files[0]
      if (f) handleFile(f)
    },
    [handleFile]
  )

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }, [])

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }, [])

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0]
      handleFile(f ?? null)
      e.target.value = ''
    },
    [handleFile]
  )

  const handleSubmit = useCallback(() => {
    if (!file) {
      setError('请先选择一张简谱图片')
      return
    }
    onSubmit(file, targetKey)
  }, [file, targetKey, onSubmit])

  const dropzone = (
    <div
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      className={`
        relative flex min-h-[280px] flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-colors
        ${dragOver ? 'border-amber-500 bg-amber-50/50' : 'border-slate-300 bg-slate-50/80'}
        ${disabled ? 'pointer-events-none opacity-60' : 'cursor-pointer hover:border-slate-400'}
      `}
    >
      <input
        type="file"
        accept={ACCEPT}
        onChange={onInputChange}
        className="absolute inset-0 cursor-pointer opacity-0"
        disabled={disabled}
      />
      <p className="text-slate-600">
        拖拽简谱图片到此处，或 <span className="text-amber-600 font-medium">点击选择</span>
      </p>
      <p className="mt-1 text-xs text-slate-400">支持 PNG、JPG，单张图片</p>
    </div>
  )

  const imagePreview = objectUrl && (
    <div className="flex h-full min-h-[280px] flex-col overflow-hidden rounded-xl border border-slate-200 bg-slate-100">
      <p className="border-b border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-600">
        预览 · {file?.name}
      </p>
      <FullscreenImage src={objectUrl} alt="简谱预览" className="p-4" />
    </div>
  )

  const controls = (
    <div className="flex h-full min-h-[280px] flex-col justify-center space-y-6">
      <div>
        <label className="mb-2 block text-sm font-medium text-slate-700">目标调</label>
        <select
          value={targetKey}
          onChange={(e) => setTargetKey(e.target.value as TargetKey)}
          disabled={disabled}
          className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-slate-800 shadow-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
        >
          {TARGET_KEYS.map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
      </div>
      {error && (
        <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={disabled || !file}
        className="w-full rounded-xl bg-amber-600 px-4 py-3 font-medium text-white shadow-md transition hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        开始移调
      </button>
    </div>
  )

  if (splitLayout) {
    return (
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 lg:gap-6">
        <div className="flex flex-col lg:min-h-[60vh]">
          {imagePreview ?? dropzone}
        </div>
        <div className="flex flex-col rounded-xl border border-slate-200 bg-white p-6 lg:min-h-[60vh]">
          {controls}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col">{imagePreview ?? dropzone}</div>
      {controls}
    </div>
  )
}
