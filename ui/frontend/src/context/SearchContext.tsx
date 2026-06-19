import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import * as api from '../lib/api'
import { usePersistedState } from '../lib/usePersistedState'
import type { AnswerMode, SearchResult } from '../lib/types'

export type SearchState = 'empty' | 'loading' | 'results'

interface SearchCtx {
  query: string
  setQuery: (q: string) => void
  state: SearchState
  result: SearchResult | null
  error: string | null
  history: string[]
  mode: AnswerMode
  setMode: (m: AnswerMode) => void
  runSearch: (q: string) => void
  reset: () => void
}

const Ctx = createContext<SearchCtx | null>(null)
const HISTORY_CAP = 8

export function SearchProvider({ children }: { children: ReactNode }) {
  const [query, setQuery] = useState('')
  const [state, setState] = useState<SearchState>('empty')
  const [result, setResult] = useState<SearchResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = usePersistedState<string[]>('hl_hist', [])
  const [mode, setMode] = usePersistedState<AnswerMode>('hl_mode', 'Strict Corpus-Only')

  const abortRef = useRef<AbortController | null>(null)
  const modeRef = useRef(mode)
  modeRef.current = mode

  const pushHistory = useCallback(
    (q: string) => setHistory((prev) => [q, ...prev.filter((h) => h !== q)].slice(0, HISTORY_CAP)),
    [setHistory],
  )

  const runSearch = useCallback(
    (raw: string) => {
      const q = raw.trim()
      if (!q) return
      abortRef.current?.abort()
      const ctrl = new AbortController()
      abortRef.current = ctrl

      setQuery(q)
      setState('loading')
      setError(null)
      pushHistory(q)

      api
        .search(q, modeRef.current, ctrl.signal)
        .then((res) => {
          if (ctrl.signal.aborted) return
          setResult(res)
          setState('results')
        })
        .catch((err: unknown) => {
          if (ctrl.signal.aborted) return
          setError(err instanceof Error ? err.message : String(err))
          setState('results')
        })
    },
    [pushHistory],
  )

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setResult(null)
    setError(null)
    setQuery('')
    setState('empty')
  }, [])

  // On first load, auto-run a query passed via the #q= share hash.
  useEffect(() => {
    const m = window.location.hash.match(/[#&]q=([^&]+)/)
    if (m) {
      try {
        runSearch(decodeURIComponent(m[1]))
      } catch {
        /* malformed hash — ignore */
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const value: SearchCtx = {
    query,
    setQuery,
    state,
    result,
    error,
    history,
    mode,
    setMode,
    runSearch,
    reset,
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useSearch(): SearchCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useSearch must be used within SearchProvider')
  return ctx
}
