import { useEffect, useRef } from 'react'
import { Search, ArrowRight } from 'lucide-react'
import { useSearch } from '../context/SearchContext'

export function SearchBar() {
  const { query, setQuery, runSearch, state } = useSearch()
  const inputRef = useRef<HTMLInputElement>(null)

  // "/" focuses the search field (unless already typing in a field).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      const typing = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT'
      if (e.key === '/' && !typing) {
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const submit = () => runSearch(query)

  return (
    <div className="searchwrap">
      <div className="searchbar">
        <Search className="s-ico" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          placeholder="Ask a research question…"
          autoComplete="off"
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            // Enter or ⌘/Ctrl+Enter submits.
            if (e.key === 'Enter') {
              e.preventDefault()
              submit()
            }
          }}
        />
        <span className="kbd">⌘ ⏎</span>
        <button className="search-btn" onClick={submit} disabled={state === 'loading' || !query.trim()}>
          <ArrowRight />
          Search
        </button>
      </div>
    </div>
  )
}
