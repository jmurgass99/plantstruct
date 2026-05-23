'use client'

import React, { useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'

export interface BucklingShellProps {
  radius?: number
  height?: number
  n_circ: number
  n_long: number
  amplitude?: number
  segmentsCirc?: number
  segmentsLong?: number
}

/**
 * Cilindro deformado con un patrón de pandeo paramétrico:
 *   Δr(θ, z) = A · cos(n_circ · θ) · sin(n_long · π · z / H)
 */
export function BucklingShell({
  radius = 2,
  height = 6,
  n_circ,
  n_long,
  amplitude = 0.18,
  segmentsCirc = 96,
  segmentsLong = 64,
}: BucklingShellProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  const animTimeRef = useRef(0)

  const geometry = useMemo(() => {
    const geom = new THREE.CylinderGeometry(radius, radius, height, segmentsCirc, segmentsLong, true)
    return geom
  }, [radius, height, segmentsCirc, segmentsLong])

  const colors = useMemo(() => {
    const count = geometry.attributes.position.count
    return new Float32Array(count * 3)
  }, [geometry])

  useFrame((_, dt) => {
    if (!meshRef.current) return
    animTimeRef.current += dt
    const t = animTimeRef.current
    const wave = Math.sin(t * 2)
    const pos = geometry.attributes.position as THREE.BufferAttribute
    // Re-deform from base cylinder each frame using the original X/Z (we recompute from index)
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i)
      const y = pos.getY(i)
      const z = pos.getZ(i)
      const theta = Math.atan2(z, x)
      const zNorm = (y + height / 2) / height // 0..1
      const dr = amplitude * Math.cos(n_circ * theta) * Math.sin(n_long * Math.PI * zNorm) * wave
      const r0 = radius
      const r = r0 + dr
      const nx = Math.cos(theta) * r
      const nz = Math.sin(theta) * r
      pos.setX(i, nx)
      pos.setZ(i, nz)
      // Color por magnitud de deformación
      const c = new THREE.Color().setHSL(0.66 - 0.66 * Math.abs(dr) / amplitude, 1, 0.5)
      colors[i * 3] = c.r
      colors[i * 3 + 1] = c.g
      colors[i * 3 + 2] = c.b
    }
    pos.needsUpdate = true
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    geometry.computeVertexNormals()
  })

  return (
    <mesh ref={meshRef} geometry={geometry}>
      <meshStandardMaterial vertexColors side={THREE.DoubleSide} metalness={0.2} roughness={0.5} />
    </mesh>
  )
}

export function BucklingViewer({
  n_circ,
  n_long,
  amplitude,
}: {
  n_circ: number
  n_long: number
  amplitude: number
}) {
  return (
    <div className="relative w-full h-[520px] bg-slate-900 rounded-lg overflow-hidden">
      <Canvas camera={{ position: [8, 4, 8], fov: 50 }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[10, 10, 5]} intensity={0.8} />
        <directionalLight position={[-10, -5, -5]} intensity={0.3} />
        <BucklingShell n_circ={n_circ} n_long={n_long} amplitude={amplitude} />
        <gridHelper args={[20, 20, '#334155', '#475569']} position={[0, -3.05, 0]} />
        <OrbitControls enableDamping />
      </Canvas>
      <div className="absolute top-2 left-2 bg-slate-950/70 text-xs text-slate-300 px-3 py-2 rounded">
        Modo: n<sub>circ</sub>={n_circ}, n<sub>long</sub>={n_long}
      </div>
    </div>
  )
}
