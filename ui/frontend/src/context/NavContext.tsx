import { createContext, useContext, useState, type ReactNode } from 'react'

export type NavView = 'ask' | 'sources' | 'uploads' | 'sessions'

interface NavCtx {
  view: NavView
  setView: (v: NavView) => void
}

const Ctx = createContext<NavCtx | null>(null)

export function NavProvider({ children }: { children: ReactNode }) {
  const [view, setView] = useState<NavView>('ask')
  return <Ctx.Provider value={{ view, setView }}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useNav(): NavCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useNav must be used within NavProvider')
  return ctx
}
