import { ThemeProvider } from './context/ThemeContext'
import { ReadingProvider } from './context/ReadingContext'
import { StatusProvider } from './context/StatusContext'
import { NavProvider, useNav } from './context/NavContext'
import { SearchProvider } from './context/SearchContext'
import { UIProvider } from './context/UIContext'

import { Sidebar } from './components/Sidebar'
import { TopBar } from './components/TopBar'
import { Footer } from './components/Footer'
import { RightRail } from './components/RightRail'
import { Lightbox } from './components/Lightbox'
import { ReadingComfortPanel } from './components/ReadingComfortPanel'
import { Toast } from './components/Toast'

import { AskView } from './views/AskView'
import { SourcesView } from './views/SourcesView'
import { UploadsView } from './views/UploadsView'
import { SessionsView } from './views/SessionsView'

function CurrentView() {
  const { view } = useNav()
  switch (view) {
    case 'sources':
      return <SourcesView />
    case 'uploads':
      return <UploadsView />
    case 'sessions':
      return <SessionsView />
    default:
      return <AskView />
  }
}

function Shell() {
  return (
    <>
      <div className="app">
        <Sidebar />
        <main className="main">
          <TopBar />
          <div className="content">
            <CurrentView />
          </div>
        </main>
        <RightRail />
        <Footer />
      </div>
      <ReadingComfortPanel />
      <Lightbox />
      <Toast />
    </>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <ReadingProvider>
        <StatusProvider>
          <UIProvider>
            <NavProvider>
              <SearchProvider>
                <Shell />
              </SearchProvider>
            </NavProvider>
          </UIProvider>
        </StatusProvider>
      </ReadingProvider>
    </ThemeProvider>
  )
}
