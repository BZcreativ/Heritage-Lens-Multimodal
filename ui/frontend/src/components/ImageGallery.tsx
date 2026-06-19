import { Image as ImageIcon } from 'lucide-react'
import { useUI } from '../context/UIContext'
import type { ImageItem } from '../lib/types'

export function ImageGallery({ images }: { images: ImageItem[] }) {
  const { openLightbox } = useUI()
  if (images.length === 0) return null
  return (
    <div className="gallery">
      <h3>
        <ImageIcon />
        Visual Evidence <span className="cnt">{images.length} images</span>
      </h3>
      <div className="img-grid">
        {images.map((img, i) => (
          <button className="img-thumb" key={i} onClick={() => openLightbox(img)} aria-label={`Open ${img.alt}`}>
            <img src={img.url} alt={img.alt} loading="lazy" />
          </button>
        ))}
      </div>
    </div>
  )
}
