import React from 'react'
import TickerSearch from './components/TickerSearch'
import PositionsTable from './components/PositionsTable'
import CalibrationPanel from './components/CalibrationPanel'
import Controls from './components/Controls'
import PathsChart from './components/PathsChart'
import DistributionChart from './components/DistributionChart'
import SummaryPanel from './components/SummaryPanel'
import { calibrate, simulate, CalibParams } from './api'

export type Position = { ticker: string; qty: number }

export default function App() {
  const [positions, setPositions] = React.useState<Position[]>([])
  const [calib, setCalib] = React.useState<CalibParams | null>(null)
  const [days, setDays] = React.useState(20)
  const [nSims, setNSims] = React.useState(2000)
  const [driftMode, setDriftMode] = React.useState<'flat' | 'useMu'>('flat')
  const [useStudentT, setUseStudentT] = React.useState(true)
  const [dof, setDof] = React.useState(6)

  const [paths, setPaths] = React.useState<number[][]>([])
  const [pnl, setPnl] = React.useState<number[]>([])
  const [summary, setSummary] = React.useState<any>(null)
  const [pv0, setPv0] = React.useState<number | null>(null)
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  function addTicker(t: string) {
    if (!positions.find(p => p.ticker === t)) {
      setPositions([...positions, { ticker: t, qty: 0 }])
    }
  }

  async function onCalibrate(args: any) {
    setError(null)
    try {
      const data = await calibrate({ ...args, tickers: positions.map(p => p.ticker) })
      setCalib(data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message)
    }
  }

  async function onRun() {
    if (!calib) { setError('Please calibrate first.'); return }
    setBusy(true); setError(null)
    try {
      const body = {
        positions, days, nSims, driftMode, useStudentT, dof,
        calibration: calib
      }
      const out = await simulate(body)
      setPaths(out.pathsSample)
      setPnl(out.pnl)
      setSummary(out.summary)
      setPv0(out.pv0)
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message)
    } finally { setBusy(false) }
  }

  function updateQty(ticker: string, qty: number) {
    setPositions(positions.map(p => p.ticker === ticker ? { ...p, qty } : p))
  }

  function removeTicker(ticker: string) {
    setPositions(positions.filter(p => p.ticker !== ticker))
  }

  return (
    <div className="max-w-7xl mx-auto p-4 space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Portfolio Monte Carlo Simulator</h1>
        <span className="text-sm opacity-70">Backend: {import.meta.env.VITE_API_BASE_URL}</span>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          <div className="card">
            <TickerSearch onSelect={addTicker} />
            <PositionsTable positions={positions} onChangeQty={updateQty} onRemove={removeTicker} calib={calib} />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="card"><PathsChart paths={paths} /></div>
            <div className="card"><DistributionChart pnl={pnl} /></div>
          </div>
        </div>
        <div className="space-y-4">
          <div className="card"><CalibrationPanel onCalibrate={onCalibrate} /></div>
          <div className="card"><Controls days={days} setDays={setDays} nSims={nSims} setNSims={setNSims} driftMode={driftMode} setDriftMode={setDriftMode} useStudentT={useStudentT} setUseStudentT={setUseStudentT} dof={dof} setDof={setDof} onRun={onRun} busy={busy} /></div>
          <div className="card"><SummaryPanel pv0={pv0} summary={summary} error={error} /></div>
        </div>
      </div>
    </div>
  )
}