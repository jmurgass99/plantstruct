'use client'

import React, { useState } from 'react'
import { BucklingViewer } from '@/components/BucklingShell'

export default function BucklingPage() {
  const [nCirc, setNCirc] = useState(6)
  const [nLong, setNLong] = useState(2)
  const [amp, setAmp] = useState(0.18)

  return (
    <main className="min-h-screen p-8 bg-slate-950 text-slate-100">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Visor 3D — modo de pandeo</h1>
        <p className="text-slate-400 mb-6">
          Cilindro R3F con deformación paramétrica
          Δr(θ, z) = A · cos(n<sub>circ</sub> · θ) · sin(n<sub>long</sub> · π · z / H).
          Útil para visualizar modos clásicos de shell buckling (API 650 § 5.10 / EN 1993-1-6).
        </p>

        <BucklingViewer n_circ={nCirc} n_long={nLong} amplitude={amp} />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="bg-slate-900/50 rounded p-3">
            <label className="block text-xs text-slate-400 mb-1">
              n_circ (ondas circunferenciales) = {nCirc}
            </label>
            <input type="range" min={1} max={20} step={1}
              value={nCirc} onChange={(e) => setNCirc(Number(e.target.value))}
              className="w-full" />
          </div>
          <div className="bg-slate-900/50 rounded p-3">
            <label className="block text-xs text-slate-400 mb-1">
              n_long (medias-ondas longitudinales) = {nLong}
            </label>
            <input type="range" min={1} max={10} step={1}
              value={nLong} onChange={(e) => setNLong(Number(e.target.value))}
              className="w-full" />
          </div>
          <div className="bg-slate-900/50 rounded p-3">
            <label className="block text-xs text-slate-400 mb-1">
              Amplitud A = {amp.toFixed(3)}
            </label>
            <input type="range" min={0.02} max={0.5} step={0.01}
              value={amp} onChange={(e) => setAmp(Number(e.target.value))}
              className="w-full" />
          </div>
        </div>
      </div>
    </main>
  )
}
