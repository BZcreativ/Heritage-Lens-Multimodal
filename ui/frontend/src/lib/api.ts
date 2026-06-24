// Typed client for the Heritage Lens FastAPI layer.
// All calls are same-origin relative to /api — Vite proxies to :8000 in dev, and
// in prod the frontend is served behind the same host with /api reverse-proxied.

import type {
  AnswerMode,
  DeleteSourceResponse,
  SearchResult,
  SourcesResponse,
  StatusResponse,
  UploadResponse,
} from './types'

const BASE = '/api'

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export async function getStatus(signal?: AbortSignal): Promise<StatusResponse> {
  return asJson<StatusResponse>(await fetch(`${BASE}/status`, { signal }))
}

export async function getSources(signal?: AbortSignal): Promise<SourcesResponse> {
  return asJson<SourcesResponse>(await fetch(`${BASE}/sources`, { signal }))
}

export async function deleteSource(name: string): Promise<DeleteSourceResponse> {
  const res = await fetch(`${BASE}/sources/${encodeURIComponent(name)}`, { method: 'DELETE' })
  return asJson<DeleteSourceResponse>(res)
}

export async function search(
  query: string,
  mode: AnswerMode = 'Strict Corpus-Only',
  signal?: AbortSignal,
): Promise<SearchResult> {
  const res = await fetch(`${BASE}/search`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ query, mode }),
    signal,
  })
  return asJson<SearchResult>(res)
}

export async function uploadFiles(files: File[], signal?: AbortSignal): Promise<UploadResponse> {
  const form = new FormData()
  for (const f of files) form.append('files', f, f.name)
  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form, signal })
  return asJson<UploadResponse>(res)
}

// The image route returns a relative URL on each ImageItem already; this helper
// is for building one from a bare on-disk path when needed.
export function imageUrl(path: string): string {
  return `${BASE}/images?path=${encodeURIComponent(path)}`
}

// ---------------------------------------------------------------- ingest SSE ----

export type IngestEvent =
  | { event: 'progress'; data: string }
  | { event: 'done'; data: string }
  | { event: 'error'; data: string }

/**
 * Trigger POST /api/ingest and stream its SSE events.
 *
 * EventSource only supports GET, and /ingest is POST, so we read the response
 * body as a stream and parse the `event:`/`data:` frames ourselves. Returns an
 * abort function. `onEvent` receives every frame; `done`/`error` are terminal.
 */
export function streamIngest(
  onEvent: (e: IngestEvent) => void,
  onClose?: () => void,
): () => void {
  const controller = new AbortController()

  ;(async () => {
    try {
      const res = await fetch(`${BASE}/ingest`, {
        method: 'POST',
        headers: { accept: 'text/event-stream' },
        signal: controller.signal,
      })
      if (!res.ok || !res.body) {
        onEvent({ event: 'error', data: `ingest failed (${res.status})` })
        return
      }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        // SSE frames are separated by a blank line.
        let sep: number
        while ((sep = buffer.indexOf('\n\n')) !== -1) {
          const frame = buffer.slice(0, sep)
          buffer = buffer.slice(sep + 2)
          let evName = 'message'
          const dataLines: string[] = []
          for (const line of frame.split('\n')) {
            if (line.startsWith('event:')) evName = line.slice(6).trim()
            else if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
          }
          const data = dataLines.join('\n')
          if (evName === 'progress' || evName === 'done' || evName === 'error') {
            onEvent({ event: evName, data })
          }
        }
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        onEvent({ event: 'error', data: err instanceof Error ? err.message : String(err) })
      }
    } finally {
      onClose?.()
    }
  })()

  return () => controller.abort()
}

export { ApiError }
