import { PanelLeft, PanelRight, Sun, Moon, ALargeSmall } from 'lucide-react'
import { useUI } from '../context/UIContext'
import { useTheme } from '../context/ThemeContext'
import { useStatus } from '../context/StatusContext'
import { useNav } from '../context/NavContext'

const TITLES: Record<string, string> = {
  ask: 'Ask',
  sources: 'Sources',
  uploads: 'Uploads',
  sessions: 'Sessions',
}

export function TopBar() {
  const { toggleNav, toggleRail, setReadingOpen } = useUI()
  const { dark, toggle } = useTheme()
  const { status } = useStatus()
  const { view } = useNav()

  const ok = status?.qdrant_ok
  const sourceCount = status?.source_count ?? 0

  return (
    <div className="topbar">
      <button className="icon-btn" onClick={toggleNav} title="Toggle sidebar" aria-label="Toggle sidebar">
        <PanelLeft />
      </button>
      <span className="ttl">{TITLES[view]}</span>
      <span className="grow" />
      <span className="status-mini">
        <span className={`status-dot${ok ? '' : ' off'}`} />
        <span className="status-label">
          {ok ? `Corpus ready · ${sourceCount} sources` : 'Corpus offline'}
        </span>
      </span>
      <button className="icon-btn" onClick={toggle} title="Toggle dark mode" aria-label="Toggle dark mode">
        {dark ? <Moon /> : <Sun />}
      </button>
      <button
        className="icon-btn"
        onClick={() => setReadingOpen(true)}
        title="Reading comfort"
        aria-label="Reading comfort"
      >
        <ALargeSmall />
      </button>
      <span className="divline" />
      <button className="icon-btn" onClick={toggleRail} title="Toggle session panel" aria-label="Toggle session panel">
        <PanelRight />
      </button>
    </div>
  )
}
