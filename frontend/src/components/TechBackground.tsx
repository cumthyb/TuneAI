/**
 * 科技感背景组件 - 神经网络 + 音波 + 电路纹理
 */
import { useMemo, useEffect, useState } from 'react'

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  hue: number
  delay: number
}

interface WavePoint {
  x: number
  baseY: number
  amplitude: number
  frequency: number
  phase: number
  speed: number
}

export default function TechBackground() {
  const [time, setTime] = useState(0)

  // 神经网络风格的粒子系统
  const particles = useMemo<Particle[]>(
    () =>
      Array.from({ length: 45 }, (_, i) => ({
        x: (i * 7.3 + 3.1) % 100,
        y: (i * 13.7 + 5.9) % 100,
        vx: ((Math.random() - 0.5) * 0.02),
        vy: ((Math.random() - 0.5) * 0.02),
        size: Math.random() * 2 + 1,
        hue: 220 + Math.random() * 60, // indigo to violet range
        delay: (i * 0.2) % 4,
      })),
    []
  )

  // 音波线配置
  const wavePoints = useMemo<WavePoint[]>(
    () =>
      Array.from({ length: 5 }, (_, i) => ({
        x: 0,
        baseY: 15 + i * 18,
        amplitude: 3 + Math.random() * 5,
        frequency: 0.008 + Math.random() * 0.004,
        phase: i * 0.5,
        speed: 0.02 + Math.random() * 0.01,
      })),
    []
  )

  // 动画帧更新
  useEffect(() => {
    const interval = setInterval(() => {
      setTime(t => t + 1)
    }, 50)
    return () => clearInterval(interval)
  }, [])

  // 电路板连接线
  const circuitLines = useMemo(() => {
    const lines: { x1: number; y1: number; x2: number; y2: number; delay: number }[] = []
    for (let i = 0; i < 8; i++) {
      const startX = (i * 14 + 5) % 100
      const startY = (i * 23 + 10) % 100
      const length = 8 + (i % 3) * 6
      const horizontal = i % 2 === 0
      lines.push({
        x1: startX,
        y1: startY,
        x2: horizontal ? (startX + length) % 100 : startX,
        y2: horizontal ? startY : (startY + length) % 100,
        delay: i * 0.4,
      })
    }
    return lines
  }, [])

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      {/* 深空背景 */}
      <div
        className="absolute inset-0"
        style={{
          background: `
            radial-gradient(ellipse 80% 50% at 20% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
            radial-gradient(ellipse 60% 40% at 80% 80%, rgba(139, 92, 246, 0.12) 0%, transparent 50%),
            radial-gradient(ellipse 100% 80% at 50% 100%, rgba(6, 182, 212, 0.08) 0%, transparent 40%),
            linear-gradient(180deg, #030712 0%, #0a0f1e 50%, #030712 100%)
          `,
        }}
      />

      {/* 五线谱纹理 - 音乐感 */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.8) 1px, transparent 1px)
          `,
          backgroundSize: '100% 20px',
          backgroundPosition: '0 30%',
        }}
      />

      {/* 细密网格 */}
      <div
        className="absolute inset-0 opacity-[0.08]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(99, 102, 241, 0.3) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99, 102, 241, 0.3) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* 神经网络粒子层 */}
      <svg className="absolute inset-0 h-full w-full opacity-40">
        {/* 粒子间连接线 */}
        {particles.map((p, i) =>
          particles.slice(i + 1, Math.min(i + 4, particles.length)).map((p2, j) => (
            <line
              key={`${i}-${j}`}
              x1={`${p.x}%`}
              y1={`${p.y}%`}
              x2={`${p2.x}%`}
              y2={`${p2.y}%`}
              stroke={`hsla(${p.hue}, 70%, 60%, 0.1)`}
              strokeWidth="0.5"
            />
          ))
        )}
      </svg>

      {/* 浮动光点 - AI节点 */}
      <div className="absolute inset-0">
        {particles.map((p, i) => (
          <div
            key={i}
            className="absolute rounded-full animate-pulse"
            style={{
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: `${p.size}px`,
              height: `${p.size}px`,
              background: `hsla(${p.hue}, 80%, 65%, 0.6)`,
              boxShadow: `0 0 ${p.size * 3}px hsla(${p.hue}, 80%, 65%, 0.4)`,
              animationDuration: `${3 + (i % 3)}s`,
              animationDelay: `${p.delay}s`,
            }}
          />
        ))}
      </div>

      {/* 音波可视化 */}
      <svg className="absolute inset-x-0 bottom-0 h-32 w-full opacity-20">
        {wavePoints.map((wp, i) => {
          const points = Array.from({ length: 100 }, (_, j) => {
            const x = j
            const y = wp.baseY + Math.sin((j * wp.frequency * 50) + time * wp.speed + wp.phase) * wp.amplitude
            return `${x},${y}`
          }).join(' ')
          return (
            <polyline
              key={i}
              points={points}
              fill="none"
              stroke={`hsla(${200 + i * 15}, 80%, 60%, 0.5)`}
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          )
        })}
      </svg>

      {/* 电路板连接装饰 */}
      <svg className="absolute inset-0 h-full w-full opacity-[0.15]">
        {circuitLines.map((line, i) => (
          <g key={i}>
            <line
              x1={`${line.x1}%`}
              y1={`${line.y1}%`}
              x2={`${line.x2}%`}
              y2={`${line.y2}%`}
              stroke={`rgba(6, 182, 212, 0.4)`}
              strokeWidth="1"
              strokeDasharray="4 4"
              className="animate-[dataflow_3s_linear_infinite]"
              style={{ animationDelay: `${line.delay}s` }}
            />
            <circle
              cx={`${line.x1}%`}
              cy={`${line.y1}%`}
              r="2"
              fill="rgba(6, 182, 212, 0.6)"
            />
          </g>
        ))}
      </svg>

      {/* 扫描线效果 */}
      <div className="absolute inset-0 overflow-hidden">
        <div
          className="h-full w-full"
          style={{
            background: 'linear-gradient(180deg, transparent 0%, rgba(99, 102, 241, 0.04) 50%, transparent 100%)',
            animation: `scan ${6 + (time % 3)}s linear infinite`,
            animationDelay: `${(time * 0.5) % 6}s`,
          }}
        />
      </div>

      {/* 角落科技边框 - 增强 */}
      <div className="absolute left-0 top-0 h-32 w-px">
        <div className="h-full w-full bg-gradient-to-b from-cyan-400/60 via-indigo-500/40 to-transparent" />
        <div className="absolute top-0 h-px w-32 bg-gradient-to-r from-cyan-400/60 to-transparent" />
      </div>
      <div className="absolute right-0 top-0 h-32 w-px">
        <div className="h-full w-full bg-gradient-to-b from-violet-400/60 via-purple-500/40 to-transparent" />
        <div className="absolute top-0 right-0 h-px w-32 bg-gradient-to-l from-violet-400/60 to-transparent" />
      </div>
      <div className="absolute bottom-0 left-0 h-32 w-px">
        <div className="h-full w-full bg-gradient-to-t from-cyan-400/40 via-indigo-500/30 to-transparent" />
        <div className="absolute bottom-0 h-px w-32 bg-gradient-to-r from-cyan-400/40 to-transparent" />
      </div>
      <div className="absolute bottom-0 right-0 h-32 w-px">
        <div className="h-full w-full bg-gradient-to-t from-violet-400/40 via-purple-500/30 to-transparent" />
        <div className="absolute bottom-0 right-0 h-px w-32 bg-gradient-to-l from-violet-400/40 to-transparent" />
      </div>

      {/* 顶部发光条 */}
      <div className="absolute top-0 left-0 right-0 h-1 overflow-hidden">
        <div
          className="h-full w-full"
          style={{
            background: 'linear-gradient(90deg, transparent 0%, rgba(6, 182, 212, 0.5) 30%, rgba(99, 102, 241, 0.7) 50%, rgba(139, 92, 246, 0.5) 70%, transparent 100%)',
            animation: 'shimmer 3s ease-in-out infinite',
          }}
        />
      </div>

      {/* 全息光晕 */}
      <div className="absolute left-1/4 top-1/4 h-64 w-64 rounded-full bg-gradient-to-r from-indigo-500/10 to-cyan-500/10 blur-3xl animate-pulse" />
      <div className="absolute right-1/4 bottom-1/4 h-64 w-64 rounded-full bg-gradient-to-r from-violet-500/10 to-fuchsia-500/10 blur-3xl animate-pulse" style={{ animationDelay: '1.5s' }} />
    </div>
  )
}
