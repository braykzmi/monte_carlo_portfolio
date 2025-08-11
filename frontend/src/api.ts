import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
export const api = axios.create({ baseURL })

export type SearchItem = { security: string; description: string }

export async function searchTickers(query: string, yellowKey = 'Equity') {
  const { data } = await api.post<SearchItem[]>('/api/search', { query, yellowKey })
  return data
}

export type CalibParams = {
  tickers: string[]
  paramsPerTicker: Record<string, { S0: number; mu: number; vol: number }>
  corr: number[][]
}

export async function calibrate(body: any) {
  const { data } = await api.post<CalibParams>('/api/calibrate', body)
  return data
}

export type SimSummary = { mean: number; stdev: number; VaR95: number; ES95: number; probLoss: number }
export type SimOut = { pv0: number; pnl: number[]; pathsSample: number[][]; summary: SimSummary }

export async function simulate(body: any) {
  const { data } = await api.post<SimOut>('/api/simulate', body)
  return data
}