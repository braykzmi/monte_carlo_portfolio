import React from 'react'

export default function Controls({ days, setDays, nSims, setNSims, driftMode, setDriftMode, useStudentT, setUseStudentT, dof, setDof, onRun, busy }: any) {
  return (
    <div>
      <h3 className="font-medium mb-2">Simulation Controls</h3>
      <div className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <label className="flex items-center justify-between">Days
            <input type="number" min={1} max={252} className="w-28" value={days} onChange={e => setDays(Number(e.target.value))} />
          </label>
          <label className="flex items-center justify-between">nSims
            <input type="number" min={100} step={100} className="w-28" value={nSims} onChange={e => setNSims(Number(e.target.value))} />
          </label>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <label className="flex items-center gap-2">
            <input type="radio" checked={driftMode==='flat'} onChange={() => setDriftMode('flat')} /> Flat drift (0%)
          </label>
          <label className="flex items-center gap-2">
            <input type="radio" checked={driftMode==='useMu'} onChange={() => setDriftMode('useMu')} /> Use μ
          </label>
        </div>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={useStudentT} onChange={e => setUseStudentT(e.target.checked)} /> Heavy tails (Student‑t)
        </label>
        {useStudentT && (
          <label className="flex items-center justify-between">ν (dof)
            <input type="number" min={3} max={50} className="w-28" value={dof} onChange={e => setDof(Number(e.target.value))} />
          </label>
        )}
        <button className="bg-green-600 text-white w-full" disabled={busy} onClick={onRun}>{busy ? 'Running…' : 'Run Simulation'}</button>
      </div>
    </div>
  )
}