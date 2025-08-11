import React from 'react'

export default function CalibrationPanel({ onCalibrate }: { onCalibrate: (args: any) => void }) {
  const [start, setStart] = React.useState('2023-01-01')
  const [end, setEnd] = React.useState(new Date().toISOString().slice(0,10))
  const [useTR, setUseTR] = React.useState(false)

  return (
    <div>
      <h3 className="font-medium mb-2">Calibrate</h3>
      <div className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-sm">Start</label>
            <input type="date" className="w-full" value={start} onChange={e => setStart(e.target.value)} />
          </div>
          <div>
            <label className="text-sm">End</label>
            <input type="date" className="w-full" value={end} onChange={e => setEnd(e.target.value)} />
          </div>
        </div>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={useTR} onChange={e => setUseTR(e.target.checked)} />
          Use total return field
        </label>
        <button className="bg-blue-600 text-white" onClick={() => onCalibrate({ start, end, periodicity: 'DAILY', adjustSplits: true, adjustDividends: true, useTotalReturnField: useTR })}>Calibrate</button>
      </div>
    </div>
  )
}