import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { useUI } from '../context/UIContext'

export function Lightbox() {
  const { lightbox, closeLightbox } = useUI()
  const [videoErr, setVideoErr] = useState(false)

  useEffect(() => {
    if (!lightbox) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeLightbox()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [lightbox, closeLightbox])

  // Reset error state whenever a new entry opens.
  useEffect(() => { setVideoErr(false) }, [lightbox])

  // Seek-then-play once metadata is ready. Doing this explicitly (instead of an
  // autoplay + #t= fragment) avoids a Chromium race where some videos stall on a
  // black/poster frame: we set currentTime first, then start playback.
  const startVideo = (el: HTMLVideoElement, start: number | null) => {
    if (start != null && Number.isFinite(el.duration) && start < el.duration) {
      try { el.currentTime = start } catch { /* ignore */ }
    }
    el.play().catch(() => { /* user can press play; controls are shown */ })
  }

  if (!lightbox) return null

  return (
    <div className="lightbox" onClick={(e) => { if (e.target === e.currentTarget) closeLightbox() }}>
      <button className="lb-close" onClick={closeLightbox} aria-label="Close">
        <X />
      </button>
      {lightbox.kind === 'image' ? (
        <>
          <img className="lb-img" src={lightbox.item.url} alt={lightbox.item.alt} />
          <div className="lb-cap">
            {lightbox.item.source_name && <b>{lightbox.item.source_name}</b>}
            {lightbox.item.caption}
          </div>
        </>
      ) : (
        <>
          {videoErr ? (
            <div className="lb-video lb-video-err">
              <p>This video can’t be played inline in your browser.</p>
            </div>
          ) : (
            <video
              className="lb-video"
              src={lightbox.item.video_url ?? undefined}
              poster={lightbox.item.poster_url ?? undefined}
              controls
              playsInline
              onLoadedMetadata={(e) => startVideo(e.currentTarget, lightbox.item.start)}
              onError={() => setVideoErr(true)}
            />
          )}
          <div className="lb-cap">
            {lightbox.item.source_name && <b>{lightbox.item.source_name}</b>}
            {lightbox.item.caption}
            {lightbox.item.video_url && (
              <a
                className="lb-open"
                href={lightbox.item.start != null ? `${lightbox.item.video_url}#t=${Math.floor(lightbox.item.start)}` : lightbox.item.video_url}
                target="_blank"
                rel="noreferrer"
              >
                Open video in new tab ↗
              </a>
            )}
          </div>
        </>
      )}
    </div>
  )
}
