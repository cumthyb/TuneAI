/**
 * AI 标识徽章组件
 */
interface AIBadgeProps {
  text?: string
  size?: 'sm' | 'md' | 'lg'
  animated?: boolean
}

export default function AIBadge({ 
  text = 'AI POWERED', 
  size = 'md',
  animated = true 
}: AIBadgeProps) {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-3 py-1 text-xs',
    lg: 'px-4 py-1.5 text-sm',
  }

  return (
    <span 
      className={`
        inline-flex items-center gap-1.5 rounded-full border border-cyan-500/30 
        bg-gradient-to-r from-cyan-950/80 to-blue-950/80 
        font-mono font-semibold tracking-wider text-cyan-400
        backdrop-blur-sm ${sizeClasses[size]}
        ${animated ? 'animate-pulse' : ''}
      `}
    >
      {/* 脉冲点 */}
      <span className="relative flex h-1.5 w-1.5">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75" />
        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-cyan-400" />
      </span>
      {text}
    </span>
  )
}
