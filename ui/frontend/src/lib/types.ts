// TypeScript mirrors of the Pydantic models in api/models.py.
// Keep these in sync with that file — it is the contract.

export type SourceType = 'pdf' | 'img' | 'vid'
export type VideoModality = 'audio_transcript' | 'visual_caption' | 'ocr_text'
export type ConfidenceLevel = 'low' | 'moderate' | 'high'

export interface SourceItem {
  n: number
  title: string
  subtitle: string
  type: SourceType
  meta: Record<string, string>
}

export interface Confidence {
  level: ConfidenceLevel
  segments: number
  note: string
}

export interface Epistemic {
  source_bias: string
  absences: string
  interpretive_limits: string
  confidence: Confidence
  raw: string
}

export interface VideoChunk {
  modality: VideoModality
  timestamp: string
  start: number | null
  end: number | null
  caption: string
  source_name: string
  video_url: string | null  // playable: external http(s) or /api/media?path=...
  poster_url: string | null // thumbnail keyframe via /api/images?path=...
}

export interface ImageItem {
  url: string // already a relative /api/images?path=... URL
  caption: string
  alt: string
  source_name: string
  page_number: string
}

export interface SearchMeta {
  source_count: number
  video_count: number
  image_count: number
  elapsed_seconds: number
  image_keyword: string | null
  mode: string | null
}

export interface SearchResult {
  query: string
  answer: string
  answer_sources_raw: string
  grounded: boolean
  sources: SourceItem[]
  epistemic: Epistemic
  video_chunks: VideoChunk[]
  images: ImageItem[]
  meta: SearchMeta
}

export interface StatusResponse {
  text_chunks: number
  image_count: number
  video_chunks: number
  corpus_pdfs: number
  source_count: number
  qdrant_ok: boolean
}

export interface CorpusSource {
  source_name: string
  author: string
  source_type: string
  institution: string
  cultural_perspective: string
  language_of_origin: string
  modality: string
  chunk_count: number
}

export interface SourcesResponse {
  sources: CorpusSource[]
  total: number
}

export interface UploadResponse {
  saved: string[]
  skipped: string[]
}

export interface DeleteSourceResponse {
  source_name: string
  text_points_deleted: number
  image_points_deleted: number
  cache_images_deleted: number
  file_removed: boolean
}

// The three Answer Mode options shown in the sidebar select.
export type AnswerMode = 'Strict Corpus-Only' | 'Corpus + Background' | 'Exploratory'
