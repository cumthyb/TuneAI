/**
 * 科技感背景组件 - 网格 + 粒子 + 光效
 */
import { useMemo } from 'react'

export default function TechBackground() {
  // 预生成粒子位置，避免每次渲染重新随机导致视觉抖动
  const particles = useMemo(
    () =>
      Array.from({ length: 20 }, (_, i) => ({
        left: `${(i * 7.3 + 3.1) % 100}%`,
        top: `${(i * 13.7 + 5.9) % 100}%`,
        delay: `${(i * 0.3) % 3}s`,
      })),
    []
  )
  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      {/* 网格背景 */}
      <div 
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `
            linear-gradient(rgba(99, 102, 241, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99, 102, 241, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px',
        }}
      />
      
      {/* 动态网格 - 更细密的AI风格网格 */}
      <div 
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `
            linear-gradient(rgba(139, 92, 246, 0.15) 1px, transparent 1px),
            linear-gradient(90deg, rgba(139, 92, 246, 0.15) 1px, transparent 1px)
          `,
          backgroundSize: '10px 10px',
        }}
      />

      {/* 扫描线效果 */}
      <div className="absolute inset-0 overflow-hidden">
        <div 
          className="h-full w-full animate-[scan_8s_linear_infinite]"
          style={{
            background: 'linear-gradient(180deg, transparent 0%, rgba(99, 102, 241, 0.03) 50%, transparent 100%)',
          }}
        />
      </div>

      {/* 浮动光点 - AI节点 */}
      <div className="absolute inset-0">
        {particles.map((p, i) => (
          <div
            key={i}
            className="absolute h-1 w-1 rounded-full bg-cyan-400/30 animate-[pulse_3s_ease-in-out_infinite]"
            style={{
              left: p.left,
              top: p.top,
              animationDelay: p.delay,
            }}
          />
        ))}
      </div>

      {/* 角落装饰 - 科技边框 */}
      <div className="absolute left-4 top-20 h-20 w-px bg-gradient-to-b from-cyan-500/50 to-transparent" />
      <div className="absolute left-4 top-20 h-px w-20 bg-gradient-to-r from-cyan-500/50 to-transparent" />
      
      <div className="absolute bottom-20 right-4 h-20 w-px bg-gradient-to-t from-purple-500/50 to-transparent" />
      <div className="absolute bottom-20 right-4 h-px w-20 bg-gradient-to-l from-purple-500/50 to-transparent" />

      {/* 数据流装饰线 */}
      <div className="absolute left-1/4 top-0 h-full w-px overflow-hidden">
        <div className="h-20 w-full animate-[dataflow_4s_linear_infinite] bg-gradient-to-b from-transparent via-cyan-500/20 to-transparent" />
      </div>
      <div className="absolute right-1/3 top-0 h-full w-px overflow-hidden">
        <div 
          className="h-20 w-full animate-[dataflow_5s_linear_infinite] bg-gradient-to-b from-transparent via-purple-500/20 to-transparent"
          style={{ animationDelay: '2s' }}
        />
      </div>
    </div>
  )
}
