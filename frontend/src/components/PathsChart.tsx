import React from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function PathsChart({ paths }: { paths: number[][] }) {
  // Transform paths (M sims x T days) -> array of { d, p0, p1, ... }
  const T = paths?.[0]?.length || 0
  const M = paths.length
  const data = React.useMemo(() => {
    const arr = [] as any[]
    for (let d = 0; d < T; d++) {
      const row: any = { d }
      for (let m = 0; m < M; m++) row['p' + m] = paths[m][d]
      arr.push(row)
    }
    return arr
  }, [paths, T, M])

  if (!M) return <div className="text-sm opacity-60">Run a simulation to see path lines</div>

  return (
    <div>
      <h3 className="font-medium mb-2">Paths (all plotted, capped ≤500)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <XAxis dataKey="d" tick={false} />
          <YAxis width={60} />
          <Tooltip />
          {Array.from({ length: M }).map((_, i) => (
            <Line key={i} type="monotone" dataKey={'p' + i} dot={false} strokeWidth={1} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}