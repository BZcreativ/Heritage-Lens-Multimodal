import { SearchBar } from '../components/SearchBar'
import { EmptyState } from '../components/EmptyState'
import { LoadingState } from '../components/LoadingState'
import { Results } from '../components/Results'
import { useSearch } from '../context/SearchContext'

export function AskView() {
  const { state, result } = useSearch()
  return (
    <>
      <SearchBar />
      {state === 'empty' && <EmptyState />}
      {state === 'loading' && <LoadingState />}
      {state === 'results' && result && <Results result={result} />}
    </>
  )
}
