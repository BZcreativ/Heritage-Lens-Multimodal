// Placeholder shell — replaced in the next build step with the real layout
// (Sidebar / TopBar / views). For now it proves Tailwind 4 + design tokens load.
function App() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-bg text-text">
      <div
        className="rounded-r border border-border bg-surface p-8 text-center"
        style={{ boxShadow: 'var(--shadow)' }}
      >
        <div
          className="mx-auto mb-4 h-10 w-10 rounded-lg"
          style={{ background: 'linear-gradient(135deg, var(--answer), var(--sources))' }}
        />
        <h1 className="text-lg font-semibold tracking-tight">Heritage Lens</h1>
        <p className="mt-1 text-sm text-soft">
          Frontend scaffold ready — Tailwind 4 + design tokens loaded.
        </p>
      </div>
    </div>
  )
}

export default App
