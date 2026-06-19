import { createContext, useContext, type CSSProperties, type ReactNode } from 'react'
import { usePersistedState } from '../lib/usePersistedState'

export type ReadingFont = 'inter' | 'atkinson' | 'opendyslexic'

export interface ReadingPrefs {
  font: ReadingFont
  ls: number // letter spacing (em)
  lh: number // line height
  width: number // column width (ch)
  cream: boolean // Solarized cream background
  ragged: boolean // left-align instead of justify
}

export const READING_DEFAULTS: ReadingPrefs = {
  font: 'inter',
  ls: 0,
  lh: 1.65,
  width: 68,
  cream: false,
  ragged: false,
}

const FONT_STACK: Record<ReadingFont, string> = {
  inter: '"Inter", system-ui, sans-serif',
  atkinson: '"Atkinson Hyperlegible", "Inter", sans-serif',
  opendyslexic: '"OpenDyslexic", "Inter", sans-serif',
}

interface ReadingCtx {
  reading: ReadingPrefs
  set: <K extends keyof ReadingPrefs>(key: K, value: ReadingPrefs[K]) => void
  reset: () => void
  /** CSS custom properties to spread onto the .answer-doc element (scoped). */
  docStyle: CSSProperties
}

const Ctx = createContext<ReadingCtx | null>(null)

export function ReadingProvider({ children }: { children: ReactNode }) {
  const [reading, setReading] = usePersistedState<ReadingPrefs>('hl_rc', READING_DEFAULTS)

  const set: ReadingCtx['set'] = (key, value) => setReading((prev) => ({ ...prev, [key]: value }))
  const reset = () => setReading(READING_DEFAULTS)

  const docStyle = {
    '--rc-font': FONT_STACK[reading.font],
    '--rc-ls': `${reading.ls}em`,
    '--rc-lh': String(reading.lh),
    '--rc-width': `${reading.width}ch`,
    '--rc-align': reading.ragged ? 'left' : 'justify',
    '--rc-bg': reading.cream ? '#FDF6E3' : 'transparent',
    '--rc-ink': reading.cream ? '#3a3128' : 'var(--text)',
    '--rc-pad': reading.cream ? '18px 20px' : '0px',
  } as CSSProperties

  return <Ctx.Provider value={{ reading, set, reset, docStyle }}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useReading(): ReadingCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useReading must be used within ReadingProvider')
  return ctx
}
