import { MessageSquare, BookOpen, Upload, Activity, Search, Sun } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNav, type NavView } from '../context/NavContext'
import { useSearch } from '../context/SearchContext'
import { useStatus } from '../context/StatusContext'
import { useTheme } from '../context/ThemeContext'
import { useUI } from '../context/UIContext'
import type { AnswerMode } from '../lib/types'

const NAV: { id: NavView; icon: typeof MessageSquare }[] = [
  { id: 'ask', icon: MessageSquare },
  { id: 'sources', icon: BookOpen },
  { id: 'uploads', icon: Upload },
  { id: 'sessions', icon: Activity },
]

// AnswerMode values are sent to the backend verbatim; only the display label is localised.
const MODES: AnswerMode[] = ['Strict Corpus-Only', 'Corpus + Background', 'Exploratory']
const MODE_KEY: Record<AnswerMode, string> = {
  'Strict Corpus-Only': 'sidebar.modeStrict',
  'Corpus + Background': 'sidebar.modeBackground',
  Exploratory: 'sidebar.modeExploratory',
}

export function Sidebar() {
  const { t } = useTranslation()
  const { view, setView } = useNav()
  const { mode, setMode } = useSearch()
  const { status } = useStatus()
  const { dark, toggle } = useTheme()
  // "Show all layers" toggles the transparency layers (sources + epistemic) in
  // the results view; persisted, on by default to match the design.
  const { showLayers, toggleLayers, navCollapsed, toggleNav } = useUI()

  // On phones the sidebar is an overlay drawer; close it after picking a view
  // so the user isn't stranded behind it.
  const selectView = (id: NavView) => {
    setView(id)
    if (window.innerWidth <= 820 && !navCollapsed) toggleNav()
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="logo">
          <Search />
        </div>
        <div>
          <h1>Heritage Lens</h1>
          <div className="sub">{t('sidebar.brandSub')}</div>
        </div>
      </div>

      <nav className="side-sec">
        <div className="side-label">{t('sidebar.explore')}</div>
        {NAV.map(({ id, icon: Icon }) => (
          <button
            key={id}
            className={`nav-item${view === id ? ' active' : ''}`}
            onClick={() => selectView(id)}
            aria-current={view === id ? 'page' : undefined}
          >
            <Icon />
            {t(`nav.${id}`)}
            {id === 'sources' && status && (
              <span className="count">{status.source_count}</span>
            )}
          </button>
        ))}
      </nav>

      <div className="side-sec">
        <div className="side-label">{t('sidebar.answerSettings')}</div>
        <div className="field-label">{t('sidebar.answerMode')}</div>
        <select
          className="select"
          aria-label={t('sidebar.answerMode')}
          value={mode}
          onChange={(e) => setMode(e.target.value as AnswerMode)}
        >
          {MODES.map((m) => (
            <option key={m} value={m}>
              {t(MODE_KEY[m])}
            </option>
          ))}
        </select>
        <div className="switch-row" style={{ marginTop: 6 }}>
          <button className="sw" role="switch" aria-checked={showLayers} aria-label={t('sidebar.showAllLayers')} onClick={toggleLayers} />
          {t('sidebar.showAllLayers')}
        </div>
        <div className="side-note">
          {t('sidebar.sideNote')}
        </div>
      </div>

      <div className="side-sec">
        <div className="side-label">{t('sidebar.about')}</div>
        <p className="about-p">
          {t('sidebar.aboutText')}
        </p>
      </div>

      <div className="side-spacer" />
      <div className="side-sec" style={{ borderTop: '1px solid var(--border)' }}>
        <div className="switch-row" style={{ justifyContent: 'space-between' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
            <Sun size={16} style={{ color: 'var(--text-soft)' }} />
            {t('sidebar.darkMode')}
          </span>
          <button className="sw" role="switch" aria-checked={dark} aria-label={t('topbar.toggleDarkMode')} onClick={toggle} />
        </div>
      </div>
    </aside>
  )
}
