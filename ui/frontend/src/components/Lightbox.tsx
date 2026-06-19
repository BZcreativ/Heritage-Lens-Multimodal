import { useEffect } from 'react'
import { X } from 'lucide-react'
import { useUI } from '../context/UIContext'

export function Lightbox() {
  const { lightbox, closeLightbox } = useUI()

  useEffect(() => {
    if (!lightbox) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeLightbox()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [lightbox, closeLightbox])

  if (!lightbox) return null

  return (
    <div className="lightbox" onClick={(e) => { if (e.target === e.currentTarget) closeLightbox() }}>
      <button className="lb-close" onClick={closeLightbox} aria-label="Close">
        <X />
      </button>
      <img className="lb-img" src={lightbox.url} alt={lightbox.alt} />
      <div className="lb-cap">
        {lightbox.source_name && <b>{lightbox.source_name}</b>}
        {lightbox.caption}
      </div>
    </div>
  )
}
