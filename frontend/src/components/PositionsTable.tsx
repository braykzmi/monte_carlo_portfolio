import React from 'react'
import type { Position } from '../App'
import type { CalibParams } from '../api'

export default function PositionsTable({ positions, onChangeQty, onRemove, calib }: {
  positions: Position[]
  onChangeQty: (ticker: string, qty: number) => void
  onRemove: (ticker: string) => void
  calib: CalibParams | null
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium">Positions</h3>
        <span className="text-sm opacity-60">Qty negative ⇒ short</span>
      </div>
      <table className="w-full text-sm">
        <thead className="text-left opacity-70">
          <tr>
            <th className="py-2">Ticker</th>
            <th>S₀</th>
            <th>μ</th>
            <th>σ</th>
            <th>Qty</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {positions.map((p) => {
            const pp = calib?.paramsPerTicker?.[p.ticker]
            return (
              <tr key={p.ticker} className="border-t">
                <td className="py-2">{p.ticker}</td>
                <td>{pp ? pp.S0.toFixed(2) : '—'}</td>
                <td>{pp ? (pp.mu * 100).toFixed(2) + '%' : '—'}</td>
                <td>{pp ? (pp.vol * 100).toFixed(2) + '%' : '—'}</td>
                <td>
                  <input type="number" className="w-28" value={p.qty}
                    onChange={e => onChangeQty(p.ticker, Number(e.target.value))} />
                </td>
                <td><button className="text-red-600" onClick={() => onRemove(p.ticker)}>Remove</button></td>
              </tr>
            )
          })}
          {positions.length === 0 && (
            <tr><td className="py-3 text-center opacity-60" colSpan={6}>Add tickers to begin</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}