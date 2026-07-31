import { useEffect, useRef, useState } from 'react'
import { Globe, Check } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { LOCALES } from '../lib/i18n'

export function LanguageMenu() {
  const { t, i18n } = useTranslation()
  const [open, setOpen] = useState(false)
  const wrapRef = useRef<HTMLDivElement>(null)

  const current = LOCALES.find((l) => l.code === i18n.language) ?? LOCALES[0]

  // Close on outside click or Escape.
  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('mousedown', onDown)
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('mousedown', onDown)
      window.removeEventListener('keydown', onKey)
    }
  }, [open])

  const pick = (code: string) => {
    i18n.changeLanguage(code)
    setOpen(false)
  }

  return (
    <div className="lang-menu" ref={wrapRef}>
      <button
        className="icon-btn lang-trigger"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={t('topbar.language')}
        title={t('topbar.language')}
      >
        <Globe />
        <span className="lang-code">{current.code.toUpperCase()}</span>
      </button>
      {open && (
        <div className="lang-pop" role="menu" aria-label={t('topbar.language')}>
          {LOCALES.map((l) => (
            <button
              key={l.code}
              className={`lang-opt${l.code === current.code ? ' active' : ''}`}
              role="menuitemradio"
              aria-checked={l.code === current.code}
              onClick={() => pick(l.code)}
            >
              <span>{l.label}</span>
              {l.code === current.code && <Check />}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
