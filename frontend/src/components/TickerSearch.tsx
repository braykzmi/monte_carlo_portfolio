import React from 'react'
import { searchTickers, SearchItem } from '../api'
import { debounce } from '../lib/debounce'

export default function TickerSearch({ onSelect }: { onSelect: (ticker: string) => void }) {
  const [q, setQ] = React.useState('')
  const [items, setItems] = React.useState<SearchItem[]>([])
  const [open, setOpen] = React.useState(false)

  const doSearch = React.useMemo(() => debounce(async (qq: string) => {
    if (!qq) { setItems([]); return }
    try {
      const res = await searchTickers(qq)
      setItems(res)
      setOpen(true)
    } catch (e) { /* noop */ }
  }, 250), [])

  return (
    <div>
      <label className="text-sm font-medium">Search tickers</label>
      <input
        value={q}
        onChange={(e) => { setQ(e.target.value); doSearch(e.target.value) }}
        placeholder="Type to search..."
        className="w-full mt-1"
      />
      {open && items.length > 0 && (
        <div className="mt-2 border rounded-xl divide-y bg-white dark:bg-neutral-800 max-h-64 overflow-auto">
          {items.map((it) => (
            <button key={it.security} className="w-full text-left px-3 py-2 hover:bg-gray-100 dark:hover:bg-neutral-700"
              onClick={() => { onSelect(it.security); setOpen(false); setQ('') }}>
              <div className="font-medium">{it.security}</div>
              <div className="text-sm opacity-70">{it.description}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}