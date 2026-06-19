import { createContext, useContext, useEffect, type ReactNode } from 'react'
import { usePersistedState } from '../lib/usePersistedState'

type Theme = 'light' | 'dark'

interface ThemeCtx {
  theme: Theme
  dark: boolean
  toggle: () => void
  setDark: (v: boolean) => void
}

const Ctx = createContext<ThemeCtx | null>(null)

function systemPrefersDark(): boolean {
  return typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  // Default to the OS preference on first load (no stored value yet).
  const [dark, setDarkState] = usePersistedState<boolean>('hl_dark', systemPrefersDark())

  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle('dark', dark)
    document.body.classList.toggle('dark', dark)
  }, [dark])

  const value: ThemeCtx = {
    theme: dark ? 'dark' : 'light',
    dark,
    toggle: () => setDarkState((d) => !d),
    setDark: (v: boolean) => setDarkState(v),
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useTheme(): ThemeCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
