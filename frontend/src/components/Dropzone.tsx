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
        group relative flex h-full min-h-0 flex-col items-center justify-center overflow-hidden rounded-xl border border-dashed p-8 text-center transition-all duration-300
        ${dragOver
          ? 'border-indigo-400 bg-indigo-500/10 shadow-lg shadow-indigo-500/30'
          : 'border-slate-700/50 bg-slate-950/30 hover:border-indigo-500/40 hover:bg-slate-900/40'}
        ${disabled ? 'pointer-events-none opacity-40' : 'cursor-pointer'}
      `}
    >
      {/* AI风格网格背景 */}
      <div
        className={`
          absolute inset-0 opacity-30 transition-opacity duration-300
          ${dragOver ? 'opacity-50' : 'opacity-30'}
        `}
        style={{
          backgroundImage: `
            linear-gradient(rgba(99, 102, 241, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99, 102, 241, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px',
        }}
      />

      {/* 扫描线效果 */}
      <div className={`
        absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent
        transition-opacity duration-300
        ${dragOver ? 'opacity-100' : 'opacity-0'}
        animate-[scan_2s_linear_infinite]
      `} />

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        onChange={onInputChange}
        className="absolute inset-0 cursor-pointer opacity-0"
        disabled={disabled}
        aria-hidden
      />

      {/* AI图标 */}
      <div className={`
        relative mb-4 rounded-xl border bg-slate-900/80 p-4 backdrop-blur-sm
        transition-all duration-300
        ${dragOver ? 'scale-110 border-indigo-400/50 bg-indigo-950/50 shadow-lg shadow-indigo-500/30' : 'border-slate-700/50 group-hover:border-indigo-500/30'}
      `}>
        <svg
          className={`
            h-10 w-10 transition-colors duration-300
            ${dragOver ? 'text-indigo-400' : 'text-slate-600 group-hover:text-indigo-500'}
          `}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        {/* 角落科技装饰 */}
        <div className="absolute -left-1 -top-1 h-2 w-2 border-l-2 border-t-2 border-indigo-500/50" />
        <div className="absolute -right-1 -top-1 h-2 w-2 border-r-2 border-t-2 border-indigo-500/50" />
        <div className="absolute -bottom-1 -left-1 h-2 w-2 border-b-2 border-l-2 border-indigo-500/50" />
        <div className="absolute -bottom-1 -right-1 h-2 w-2 border-b-2 border-r-2 border-indigo-500/50" />
      </div>

      <p className={`
        relative font-mono text-sm tracking-wide transition-colors duration-300
        ${dragOver ? 'text-indigo-300' : 'text-slate-400 group-hover:text-slate-300'}
      `}>
        &lt; DROP_SHEET_HERE /&gt;
      </p>
      <p className={`
        relative mt-2 font-mono text-[10px] transition-colors duration-300
        ${dragOver ? 'text-indigo-400/80' : 'text-slate-600 group-hover:text-slate-500'}
      `}>
        [ ACCEPT: PNG, JPG | MAX: 20MB ]
      </p>

      {/* 底部状态指示器 */}
      <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-1">
        <span className={`h-1 w-1 rounded-full transition-colors duration-300 ${dragOver ? 'bg-indigo-400' : 'bg-slate-700'}`} />
        <span className={`h-1 w-1 rounded-full transition-colors duration-300 ${dragOver ? 'bg-indigo-400' : 'bg-slate-700'} delay-75`} />
        <span className={`h-1 w-1 rounded-full transition-colors duration-300 ${dragOver ? 'bg-indigo-400' : 'bg-slate-700'} delay-150`} />
      </div>
    </div>
  )
}
