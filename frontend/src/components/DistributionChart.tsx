import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

function histogram(data: number[], bins = 50) {
  if (!data.length) return [] as any[]
  const min = Math.min(...data), max = Math.max(...data)
  const w = (max - min) / bins
  const counts = new Array(bins).fill(0)
  for (const x of data) {
    const k = Math.min(bins - 1, Math.max(0, Math.floor((x - min) / w)))
    counts[k]++
  }
  return counts.map((c, i) => ({ x: (min + i * w), y: c }))
}

export default function DistributionChart({ pnl }: { pnl: number[] }) {
  const data = React.useMemo(() => histogram(pnl, 40), [pnl])
  if (!pnl.length) return <div className="text-sm opacity-60">Run a simulation to see the distribution</div>
  return (
    <div>
      <h3 className="font-medium mb-2">Final PnL Distribution</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <XAxis dataKey="x" tickFormatter={(v) => v.toFixed(0)} />
          <YAxis />
          <Tooltip formatter={(v: any) => v.toFixed ? v.toFixed(0) : v} />
          <Bar dataKey="y" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}