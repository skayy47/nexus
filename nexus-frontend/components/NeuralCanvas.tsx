'use client'

import { useEffect, useRef } from 'react'

interface Node {
  x: number
  y: number
  vx: number
  vy: number
  r: number
}

const LINK_DIST = 128
const PULL_RADIUS = 160

/**
 * Cursor-reactive neural-network canvas for the hero.
 * Nodes drift, connect when near, brighten + are gently pulled toward the cursor,
 * with a soft violet "core" glow at the top-center. Respects reduced-motion.
 */
export function NeuralCanvas() {
  const ref = useRef<HTMLCanvasElement>(null)
  const mouse = useRef({ x: -9999, y: -9999 })
  const raf = useRef<number>(0)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let dpr = 1
    let nodes: Node[] = []

    function size() {
      if (!canvas) return
      dpr = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = canvas.offsetWidth * dpr
      canvas.height = canvas.offsetHeight * dpr
    }

    function seed() {
      if (!canvas) return
      const n = Math.min(74, Math.floor(canvas.offsetWidth / 18))
      nodes = Array.from({ length: n }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.25 * dpr,
        vy: (Math.random() - 0.5) * 0.25 * dpr,
        r: (Math.random() * 1.6 + 0.8) * dpr,
      }))
    }

    size()
    seed()
    const ro = new ResizeObserver(() => {
      size()
      seed()
    })
    ro.observe(canvas)

    function onMove(e: MouseEvent) {
      const rect = canvas!.getBoundingClientRect()
      mouse.current = { x: (e.clientX - rect.left) * dpr, y: (e.clientY - rect.top) * dpr }
    }
    function onLeave() {
      mouse.current = { x: -9999, y: -9999 }
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseleave', onLeave)

    function tick() {
      if (!canvas || !ctx) return
      const w = canvas.width
      const h = canvas.height
      ctx.clearRect(0, 0, w, h)

      // core glow
      const cx = w / 2
      const cy = h * 0.42
      const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, 170 * dpr)
      core.addColorStop(0, 'rgba(124,92,255,0.16)')
      core.addColorStop(1, 'rgba(124,92,255,0)')
      ctx.fillStyle = core
      ctx.beginPath()
      ctx.arc(cx, cy, 170 * dpr, 0, Math.PI * 2)
      ctx.fill()

      const mx = mouse.current.x
      const my = mouse.current.y

      for (const nd of nodes) {
        nd.x += nd.vx
        nd.y += nd.vy
        if (nd.x < 0 || nd.x > w) nd.vx *= -1
        if (nd.y < 0 || nd.y > h) nd.vy *= -1
        const dx = mx - nd.x
        const dy = my - nd.y
        const d = Math.hypot(dx, dy)
        if (d < PULL_RADIUS * dpr && d > 0) {
          nd.x += (dx / d) * 0.6
          nd.y += (dy / d) * 0.6
        }
      }

      // links
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i]
          const b = nodes[j]
          const d = Math.hypot(a.x - b.x, a.y - b.y)
          if (d < LINK_DIST * dpr) {
            const o = (1 - d / (LINK_DIST * dpr)) * 0.4
            ctx.strokeStyle = `rgba(120,130,250,${o})`
            ctx.lineWidth = dpr * 0.6
            ctx.beginPath()
            ctx.moveTo(a.x, a.y)
            ctx.lineTo(b.x, b.y)
            ctx.stroke()
          }
        }
      }

      // nodes
      for (const nd of nodes) {
        const d = Math.hypot(mx - nd.x, my - nd.y)
        const near = d < PULL_RADIUS * dpr
        ctx.fillStyle = near ? 'rgba(167,139,250,0.95)' : 'rgba(129,140,248,0.7)'
        ctx.beginPath()
        ctx.arc(nd.x, nd.y, near ? nd.r * 1.6 : nd.r, 0, Math.PI * 2)
        ctx.fill()
      }

      raf.current = requestAnimationFrame(tick)
    }

    raf.current = requestAnimationFrame(tick)

    return () => {
      ro.disconnect()
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseleave', onLeave)
      cancelAnimationFrame(raf.current)
    }
  }, [])

  return <canvas ref={ref} className="absolute inset-0 w-full h-full" style={{ pointerEvents: 'none' }} />
}
