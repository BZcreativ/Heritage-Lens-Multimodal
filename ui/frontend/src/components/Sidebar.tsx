import { MessageSquare, BookOpen, Upload, Activity, Search, Sun } from 'lucide-react'
import { useNav, type NavView } from '../context/NavContext'
import { useSearch } from '../context/SearchContext'
import { useStatus } from '../context/StatusContext'
import { useTheme } from '../context/ThemeContext'
import { useUI } from '../context/UIContext'
import type { AnswerMode } from '../lib/types'

const NAV: { id: NavView; label: string; icon: typeof MessageSquare }[] = [
  { id: 'ask', label: 'Ask', icon: MessageSquare },
  { id: 'sources', label: 'Sources', icon: BookOpen },
  { id: 'uploads', label: 'Uploads', icon: Upload },
  { id: 'sessions', label: 'Sessions', icon: Activity },
]

const MODES: AnswerMode[] = ['Strict Corpus-Only', 'Corpus + Background', 'Exploratory']

export function Sidebar() {
  const { view, setView } = useNav()
  const { mode, setMode } = useSearch()
  const { status } = useStatus()
  const { dark, toggle } = useTheme()
  // "Show all layers" toggles the transparency layers (sources + epistemic) in
  // the results view; persisted, on by default to match the design.
  const { showLayers, toggleLayers } = useUI()

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="logo">
          <Search />
        </div>
        <div>
          <h1>Heritage Lens</h1>
          <div className="sub">Multimodal RAG</div>
        </div>
      </div>

      <nav className="side-sec">
        <div className="side-label">Explore</div>
        {NAV.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`nav-item${view === id ? ' active' : ''}`}
            onClick={() => setView(id)}
            aria-current={view === id ? 'page' : undefined}
          >
            <Icon />
            {label}
            {id === 'sources' && status && (
              <span className="count">{status.source_count}</span>
            )}
          </button>
        ))}
      </nav>

      <div className="side-sec">
        <div className="side-label">Answer Settings</div>
        <div className="field-label">Answer Mode</div>
        <select
          className="select"
          aria-label="Answer mode"
          value={mode}
          onChange={(e) => setMode(e.target.value as AnswerMode)}
        >
          {MODES.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
        <div className="switch-row" style={{ marginTop: 6 }}>
          <button className="sw" role="switch" aria-checked={showLayers} aria-label="Show all transparency layers" onClick={toggleLayers} />
          Show all layers
        </div>
        <div className="side-note">
          Answers are grounded in your indexed corpus. Background knowledge is tagged,
          never silently mixed in.
        </div>
      </div>

      <div className="side-sec">
        <div className="side-label">About</div>
        <p className="about-p">
          Heritage Lens retrieves across text, images, and video, then attributes every
          claim and surfaces what it cannot know. Built for accountable specialised
          research.
        </p>
      </div>

      <div className="side-spacer" />
      <div className="side-sec" style={{ borderTop: '1px solid var(--border)' }}>
        <div className="switch-row" style={{ justifyContent: 'space-between' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
            <Sun size={16} style={{ color: 'var(--text-soft)' }} />
            Dark mode
          </span>
          <button className="sw" role="switch" aria-checked={dark} aria-label="Toggle dark mode" onClick={toggle} />
        </div>
      </div>
    </aside>
  )
}
