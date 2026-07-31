import { PanelLeft, PanelRight, Sun, Moon, ALargeSmall } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useUI } from '../context/UIContext'
import { useTheme } from '../context/ThemeContext'
import { useStatus } from '../context/StatusContext'
import { useNav } from '../context/NavContext'
import { LanguageMenu } from './LanguageMenu'

export function TopBar() {
  const { t } = useTranslation()
  const { toggleNav, toggleRail, setReadingOpen } = useUI()
  const { dark, toggle } = useTheme()
  const { status } = useStatus()
  const { view } = useNav()

  const ok = status?.qdrant_ok
  const sourceCount = status?.source_count ?? 0

  return (
    <div className="topbar">
      <button className="icon-btn" onClick={toggleNav} title={t('topbar.toggleSidebar')} aria-label={t('topbar.toggleSidebar')}>
        <PanelLeft />
      </button>
      <span className="ttl">{t(`nav.${view}`)}</span>
      <span className="grow" />
      <span className="status-mini">
        <span className={`status-dot${ok ? '' : ' off'}`} />
        <span className="status-label">
          {ok ? t('topbar.corpusReady', { count: sourceCount }) : t('topbar.corpusOffline')}
        </span>
      </span>
      <LanguageMenu />
      <button className="icon-btn" onClick={toggle} title={t('topbar.toggleDarkMode')} aria-label={t('topbar.toggleDarkMode')}>
        {dark ? <Moon /> : <Sun />}
      </button>
      <button
        className="icon-btn"
        onClick={() => setReadingOpen(true)}
        title={t('topbar.readingComfort')}
        aria-label={t('topbar.readingComfort')}
      >
        <ALargeSmall />
      </button>
      <span className="divline" />
      <button className="icon-btn" onClick={toggleRail} title={t('topbar.toggleSessionPanel')} aria-label={t('topbar.toggleSessionPanel')}>
        <PanelRight />
      </button>
    </div>
  )
}
