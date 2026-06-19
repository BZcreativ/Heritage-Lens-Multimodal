import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import * as api from '../lib/api'
import type { StatusResponse } from '../lib/types'

interface StatusCtx {
  status: StatusResponse | null
  loading: boolean
  refresh: () => void
}

const Ctx = createContext<StatusCtx | null>(null)

export function StatusProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(() => {
    setLoading(true)
    api
      .getStatus()
      .then(setStatus)
      .catch(() => setStatus(null))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  return <Ctx.Provider value={{ status, loading, refresh }}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useStatus(): StatusCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useStatus must be used within StatusProvider')
  return ctx
}
