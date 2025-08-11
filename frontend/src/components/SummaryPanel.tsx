import React from 'react'

export default function SummaryPanel({ pv0, summary, error }: any) {
  return (
    <div>
      <h3 className="font-medium mb-2">Summary</h3>
      {error && <div className="text-red-600 text-sm mb-2">{error}</div>}
      {!summary ? (
        <div className="text-sm opacity-60">Nothing yet</div>
      ) : (
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="opacity-60">PV₀</div><div>{pv0?.toFixed(2)}</div>
          <div className="opacity-60">Mean</div><div>{summary.mean.toFixed(2)}</div>
          <div className="opacity-60">Stdev</div><div>{summary.stdev.toFixed(2)}</div>
          <div className="opacity-60">VaR 95%</div><div>{summary.VaR95.toFixed(2)}</div>
          <div className="opacity-60">ES 95%</div><div>{summary.ES95.toFixed(2)}</div>
          <div className="opacity-60">Prob(Loss)</div><div>{(summary.probLoss * 100).toFixed(1)}%</div>
        </div>
      )}
    </div>
  )
}