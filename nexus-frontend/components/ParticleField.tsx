'use client'

import { useEffect, useRef } from 'react'

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  baseOpacity: number
}

const PARTICLE_COUNT    = 95
const CONNECTION_DIST   = 130   // px — max distance to draw a line
const REPEL_RADIUS      = 110   // px — mouse influence zone
const REPEL_FORCE       = 1.1   // acceleration when mouse is close
const FRICTION          = 0.97  // velocity damping per frame
const MAX_SPEED         = 2.2   // px/frame cap

export function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mouse     = useRef({ x: -9999, y: -9999 })
  const particles = useRef<Particle[]>([])
  const raf       = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // ── Resize ──────────────────────────────────────────────────────
    function resize() {
      if (!canvas) return
      canvas.width  = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(canvas)

    // ── Seed particles ──────────────────────────────────────────────
    particles.current = Array.from({ length: PARTICLE_COUNT }, () => ({
      x:           Math.random() * canvas.width,
      y:           Math.random() * canvas.height,
      vx:          (Math.random() - 0.5) * 0.5,
      vy:          (Math.random() - 0.5) * 0.5,
      size:        Math.random() * 1.6 + 0.4,
      baseOpacity: Math.random() * 0.45 + 0.15,
    }))

    // ── Mouse tracking (window-level so whole hero is covered) ──────
    function onMouseMove(e: MouseEvent) {
      const rect = canvas!.getBoundingClientRect()
      mouse.current = { x: e.clientX - rect.left, y: e.clientY - rect.top }
    }
    function onMouseLeave() {
      mouse.current = { x: -9999, y: -9999 }
    }
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseleave', onMouseLeave)

    // ── Render loop ─────────────────────────────────────────────────
    function tick() {
      if (!canvas || !ctx) return
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const mx = mouse.current.x
      const my = mouse.current.y

      // Update positions
      for (const p of particles.current) {
        const dx   = p.x - mx
        const dy   = p.y - my
        const dist = Math.sqrt(dx * dx + dy * dy)

        // Repel from mouse
        if (dist < REPEL_RADIUS && dist > 0) {
          const strength = (REPEL_RADIUS - dist) / REPEL_RADIUS
          p.vx += (dx / dist) * strength * REPEL_FORCE
          p.vy += (dy / dist) * strength * REPEL_FORCE
        }

        // Friction & speed cap
        p.vx *= FRICTION
        p.vy *= FRICTION
        const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy)
        if (speed > MAX_SPEED) {
          p.vx = (p.vx / speed) * MAX_SPEED
          p.vy = (p.vy / speed) * MAX_SPEED
        }

        p.x += p.vx
        p.y += p.vy

        // Wrap edges
        if (p.x < 0)             p.x = canvas.width
        if (p.x > canvas.width)  p.x = 0
        if (p.y < 0)             p.y = canvas.height
        if (p.y > canvas.height) p.y = 0
      }

      // Draw connection lines
      const pts = particles.current
      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const dx   = pts[i].x - pts[j].x
          const dy   = pts[i].y - pts[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist >= CONNECTION_DIST) continue

          const alpha = (1 - dist / CONNECTION_DIST) * 0.28
          ctx.beginPath()
          ctx.strokeStyle = `rgba(99,102,241,${alpha})`   // indigo-500
          ctx.lineWidth   = 0.6
          ctx.moveTo(pts[i].x, pts[i].y)
          ctx.lineTo(pts[j].x, pts[j].y)
          ctx.stroke()
        }
      }

      // Draw dots
      for (const p of pts) {
        // Dots near mouse glow brighter
        const dx    = p.x - mx
        const dy    = p.y - my
        const dist  = Math.sqrt(dx * dx + dy * dy)
        const boost = dist < REPEL_RADIUS
          ? (1 - dist / REPEL_RADIUS) * 0.6
          : 0

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(148,163,184,${Math.min(1, p.baseOpacity + boost)})`
        ctx.fill()
      }

      raf.current = requestAnimationFrame(tick)
    }

    raf.current = requestAnimationFrame(tick)

    return () => {
      ro.disconnect()
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseleave', onMouseLeave)
      cancelAnimationFrame(raf.current)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full"
      style={{ pointerEvents: 'none' }}
    />
  )
}
