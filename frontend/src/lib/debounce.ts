export function debounce<T extends (...args: any[]) => any>(fn: T, delay = 250) {
  let t: any
  return (...args: Parameters<T>) => {
    clearTimeout(t)
    t = setTimeout(() => fn(...args), delay)
  }
}