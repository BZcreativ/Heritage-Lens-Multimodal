import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { usePersistedState } from '../lib/usePersistedState'
import type { ImageItem } from '../lib/types'

interface UICtx {
  navCollapsed: boolean
  railCollapsed: boolean
  sessionMasked: boolean
  readingOpen: boolean
  lightbox: ImageItem | null
  toastMsg: string | null
  toggleNav: () => void
  toggleRail: () => void
  toggleSessionMask: () => void
  setReadingOpen: (v: boolean) => void
  openLightbox: (img: ImageItem) => void
  closeLightbox: () => void
  toast: (msg: string) => void
}

const Ctx = createContext<UICtx | null>(null)

export function UIProvider({ children }: { children: ReactNode }) {
  const [navCollapsed, setNav] = usePersistedState<boolean>('hl_col_nav', false)
  const [railCollapsed, setRail] = usePersistedState<boolean>('hl_col_rail', false)
  const [sessionMasked, setMasked] = usePersistedState<boolean>('hl_session_masked', false)
  const [readingOpen, setReadingOpen] = useState(false)
  const [lightbox, setLightbox] = useState<ImageItem | null>(null)
  const [toastMsg, setToastMsg] = useState<string | null>(null)
  const toastTimer = useRef<number | null>(null)

  // Reflect collapse state onto <body> so the prototype's grid CSS applies.
  useEffect(() => {
    document.body.classList.toggle('nav-collapsed', navCollapsed)
  }, [navCollapsed])
  useEffect(() => {
    document.body.classList.toggle('rail-collapsed', railCollapsed)
  }, [railCollapsed])

  const toast = useCallback((msg: string) => {
    setToastMsg(msg)
    if (toastTimer.current) window.clearTimeout(toastTimer.current)
    toastTimer.current = window.setTimeout(() => setToastMsg(null), 2400)
  }, [])

  const value: UICtx = {
    navCollapsed,
    railCollapsed,
    sessionMasked,
    readingOpen,
    lightbox,
    toastMsg,
    toggleNav: () => setNav((v) => !v),
    toggleRail: () => setRail((v) => !v),
    toggleSessionMask: () => setMasked((v) => !v),
    setReadingOpen,
    openLightbox: (img) => setLightbox(img),
    closeLightbox: () => setLightbox(null),
    toast,
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useUI(): UICtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useUI must be used within UIProvider')
  return ctx
}
