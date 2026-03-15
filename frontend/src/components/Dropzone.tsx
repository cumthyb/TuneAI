import { useCallback, useRef, useState } from 'react'

const ACCEPT = 'image/png,image/jpeg,image/jpg'

export interface DropzoneProps {
  onFileSelect: (file: File) => void
  disabled?: boolean
}

export default function Dropzone({ onFileSelect, disabled }: DropzoneProps) {
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      const f = e.dataTransfer.files[0]
      if (f) onFileSelect(f)
    },
    [onFileSelect]
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
      if (f) onFileSelect(f)
      e.target.value = ''
    },
    [onFileSelect]
  )

  return (
    <div
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      onClick={() => inputRef.current?.click()}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      className={`
        relative flex min-h-[320px] flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-colors
        ${dragOver ? 'border-amber-500 bg-amber-50/50' : 'border-slate-300 bg-slate-100/80'}
        ${disabled ? 'pointer-events-none opacity-60' : 'cursor-pointer hover:border-slate-400'}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        onChange={onInputChange}
        className="absolute inset-0 cursor-pointer opacity-0 w-full h-full"
        disabled={disabled}
        aria-hidden
      />
      <p className="text-slate-600">
        将简谱图片拖到此处，或点击选择文件
      </p>
      <p className="mt-1 text-xs text-slate-400">支持 PNG、JPG</p>
    </div>
  )
}
