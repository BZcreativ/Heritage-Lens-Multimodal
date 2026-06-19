import { useEffect } from 'react'
import { ALargeSmall, X, RotateCcw } from 'lucide-react'
import { useReading, type ReadingFont } from '../context/ReadingContext'
import { useUI } from '../context/UIContext'

const FONTS: { id: ReadingFont; name: string; family: string; badge?: 'sci' | 'pref'; badgeText?: string; note?: string }[] = [
  { id: 'inter', name: 'Inter', family: "'Inter', sans-serif", note: 'Default' },
  { id: 'atkinson', name: 'Atkinson Hyperlegible', family: "'Atkinson Hyperlegible', sans-serif", badge: 'sci', badgeText: 'Sci ✓' },
  { id: 'opendyslexic', name: 'OpenDyslexic', family: "'OpenDyslexic', sans-serif", badge: 'pref', badgeText: 'Pref ⓘ' },
]

export function ReadingComfortPanel() {
  const { reading, set, reset } = useReading()
  const { readingOpen, setReadingOpen } = useUI()

  useEffect(() => {
    if (!readingOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setReadingOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [readingOpen, setReadingOpen])

  return (
    <>
      <div className={`scrim${readingOpen ? ' show' : ''}`} onClick={() => setReadingOpen(false)} />
      <aside className={`rc${readingOpen ? ' show' : ''}`} role="dialog" aria-label="Reading comfort settings">
        <div className="rc-head">
          <div className="rc-ico">
            <ALargeSmall />
          </div>
          <div>
            <h2>Reading Comfort</h2>
            <div className="rc-sub">Typeface applies app-wide · spacing to the answer</div>
          </div>
          <button className="x" onClick={() => setReadingOpen(false)} aria-label="Close">
            <X />
          </button>
        </div>

        <div className="rc-body">
          <div className="rc-sec">
            <div className="rc-l">Typeface</div>
            {FONTS.map((f) => (
              <button
                key={f.id}
                className="rc-fopt"
                role="radio"
                aria-checked={reading.font === f.id}
                onClick={() => set('font', f.id)}
              >
                <span className="rc-radio" />
                <span className="rc-fname" style={{ fontFamily: f.family }}>{f.name}</span>
                {f.badge ? (
                  <span className={`rc-badge ${f.badge}`}>{f.badgeText}</span>
                ) : (
                  <span style={{ fontSize: 11, color: 'var(--text-faint)' }}>{f.note}</span>
                )}
              </button>
            ))}
          </div>

          <div className="rc-sec">
            <div className="rc-l">Spacing</div>
            <div className="rc-slider">
              <div className="rc-srow">
                <span className="rc-sname">Letter spacing</span>
                <span className="rc-sval">{reading.ls.toFixed(2)}em</span>
              </div>
              <input type="range" min={0} max={0.15} step={0.01} value={reading.ls}
                onChange={(e) => set('ls', Number(e.target.value))} aria-label="Letter spacing" />
            </div>
            <div className="rc-slider">
              <div className="rc-srow">
                <span className="rc-sname">Line height</span>
                <span className="rc-sval">{reading.lh.toFixed(1)}</span>
              </div>
              <input type="range" min={1.2} max={2} step={0.1} value={reading.lh}
                onChange={(e) => set('lh', Number(e.target.value))} aria-label="Line height" />
            </div>
            <div className="rc-slider">
              <div className="rc-srow">
                <span className="rc-sname">Column width</span>
                <span className="rc-sval">{reading.width}ch</span>
              </div>
              <input type="range" min={50} max={100} step={2} value={reading.width}
                onChange={(e) => set('width', Number(e.target.value))} aria-label="Column width" />
            </div>
          </div>

          <div className="rc-sec">
            <div className="rc-l">Presentation</div>
            <button className="rc-toggle" role="switch" aria-checked={reading.cream} onClick={() => set('cream', !reading.cream)}>
              <span className="sw" aria-hidden="true" aria-checked={reading.cream} />
              <span>Cream background<span className="rc-tsub" style={{ display: 'block' }}>Solarized base3 · #FDF6E3</span></span>
            </button>
            <button className="rc-toggle" role="switch" aria-checked={reading.ragged} onClick={() => set('ragged', !reading.ragged)}>
              <span className="sw" aria-hidden="true" aria-checked={reading.ragged} />
              <span>Ragged-right<span className="rc-tsub" style={{ display: 'block' }}>Disable justification</span></span>
            </button>
          </div>
        </div>

        <button className="rc-reset" onClick={reset}>
          <RotateCcw />
          Reset to defaults
        </button>
      </aside>
    </>
  )
}
