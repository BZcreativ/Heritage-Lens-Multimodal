// English UI strings (reference set). Keep it.ts / es.ts / fr.ts in sync with these keys.
const en = {
  nav: { ask: 'Ask', sources: 'Sources', uploads: 'Uploads', sessions: 'Sessions' },

  topbar: {
    corpusReady_one: 'Corpus ready · {{count}} source',
    corpusReady_other: 'Corpus ready · {{count}} sources',
    corpusOffline: 'Corpus offline',
    toggleSidebar: 'Toggle sidebar',
    toggleDarkMode: 'Toggle dark mode',
    readingComfort: 'Reading comfort',
    toggleSessionPanel: 'Toggle session panel',
    language: 'Language',
  },

  sidebar: {
    brandSub: 'Multimodal RAG',
    explore: 'Explore',
    answerSettings: 'Answer Settings',
    answerMode: 'Answer Mode',
    modeStrict: 'Strict Corpus-Only',
    modeBackground: 'Corpus + Background',
    modeExploratory: 'Exploratory',
    showAllLayers: 'Show all layers',
    sideNote:
      'Answers are grounded in your indexed corpus. Background knowledge is tagged, never silently mixed in.',
    about: 'About',
    aboutText:
      'Heritage Lens retrieves across text, images, and video, then attributes every claim and surfaces what it cannot know. Built for accountable specialised research.',
    darkMode: 'Dark mode',
  },

  footer: {
    howItWorks: 'How it works',
    stepYouAsk: 'You ask',
    stepRetrieve: 'Retrieve',
    stepInterpret: 'Interpret',
    stepAttribute: 'Attribute',
    stepEvaluate: 'Evaluate',
    trust: 'Answers you can trust',
    tagline: 'Heritage Lens Multimodal Agent — Accountable AI for Specialised Research',
  },

  search: { placeholder: 'Ask a research question…', button: 'Search' },

  empty: {
    heading:
      'Heritage Lens combines multiple sources and perspectives to give you transparent, research-ready answers.',
    body: 'Ask about the Mesoamerican corpus. Every answer cites its sources and tells you what it can’t know.',
  },

  loading: {
    stepRetrieve: 'Retrieve',
    stepInterpret: 'Interpret',
    stepAttribute: 'Attribute',
    stepEvaluate: 'Evaluate',
    stageRetrieving: 'Retrieving across the corpus…',
    stageInterpreting: 'Interpreting the retrieved passages…',
    stageAttributing: 'Attributing every claim to its source…',
    stageEvaluating: 'Evaluating what the system cannot know…',
  },

  results: {
    sources_one: '{{count}} source',
    sources_other: '{{count}} sources',
    videos_one: '{{count}} video chunk',
    videos_other: '{{count}} video chunks',
    images_one: '{{count}} image',
    images_other: '{{count}} images',
    seconds: '{{seconds}}s',
    shareQuery: 'Share query',
    export: 'Export',
    exportMarkdown: 'Export as Markdown',
    exportJson: 'Export as JSON',
    shareCopied: 'Share link copied to clipboard',
    copyFailed: 'Copy failed',
    exportedMd: 'Exported answer + sources as Markdown',
    exportedJson: 'Exported result as JSON',
    mdAnswer: 'Answer',
    mdSources: 'Sources',
    mdUnknown: 'What the system does not know',
  },

  answer: {
    title: 'The Answer',
    grounded: 'Grounded',
    ungrounded: 'Ungrounded',
    noAnswer: 'No answer was produced.',
    bgNote: '= general knowledge, clearly separated from corpus-grounded claims.',
  },

  sources: {
    title: 'Sources',
    cited: '{{count}} cited',
    none: 'No sources were retrieved for this query.',
  },

  epistemic: {
    title: 'What the System Doesn’t Know',
    tag: 'Epistemic',
    sourceBias: 'Source Bias',
    absences: 'Absences',
    interpretiveLimits: 'Interpretive Limits',
    confidence: 'Confidence',
    noBias: 'No specific source-bias notes for this query.',
    noAbsences: 'No specific absences flagged for this query.',
    noLimits: 'No specific interpretive limits flagged.',
    levelLow: 'Low',
    levelModerate: 'Moderate',
    levelHigh: 'High',
  },

  rail: {
    sessionOverview: 'Session Overview',
    show: 'Show',
    hide: 'Hide',
    started: 'Started',
    mode: 'Mode',
    sourcesIndexed: 'Sources Indexed',
    exchanges: 'Exchanges',
    exportSession: 'Export Session',
    exportSoon: 'Session export coming soon',
    recentQueries: 'Recent queries',
    noQueries: 'No queries yet.',
  },

  video: {
    title: 'Video Evidence',
    chunks_one: '{{count}} chunk',
    chunks_other: '{{count}} chunks',
    audio: 'Audio',
    visual: 'Visual',
    ocr: 'OCR',
    play: 'Play {{name}} at {{time}}',
    playAt: 'Play at {{time}}',
    seekTo: 'Seek to {{time}}',
    videoFallback: 'video',
  },

  image: {
    title: 'Visual Evidence',
    images_one: '{{count}} image',
    images_other: '{{count}} images',
    open: 'Open {{alt}}',
  },

  lightbox: {
    close: 'Close',
    videoErr: 'This video can’t be played inline in your browser.',
    openNewTab: 'Open video in new tab ↗',
  },

  reading: {
    title: 'Reading Comfort',
    sub: 'Typeface applies app-wide · spacing to the answer',
    dialogAria: 'Reading comfort settings',
    close: 'Close',
    typeface: 'Typeface',
    fontDefault: 'Default',
    spacing: 'Spacing',
    letterSpacing: 'Letter spacing',
    lineHeight: 'Line height',
    columnWidth: 'Column width',
    presentation: 'Presentation',
    creamBg: 'Cream background',
    creamSub: 'Solarized base3 · #FDF6E3',
    ragged: 'Ragged-right',
    raggedSub: 'Disable justification',
    reset: 'Reset to defaults',
  },

  sourcesView: {
    title: 'Corpus Sources',
    desc: 'Every document indexed in the research corpus, with attribution metadata.',
    loading: 'Loading sources…',
    none: 'No sources indexed yet.',
    chunks_one: '{{count}} chunk',
    chunks_other: '{{count}} chunks',
    deleteSource: 'Delete source',
    deleteAria: 'Delete {{name}}',
    removed: 'Removed {{name}}',
    confirmTitle: 'Delete source',
    confirmMsg:
      'Permanently remove “{{name}}” ({{count}} chunks)? This deletes its vectors and files and cannot be undone.',
  },

  uploadsView: {
    title: 'Add to Corpus',
    desc: 'Upload PDFs, images, or video. Files are saved to the corpus and the index is rebuilt.',
    working: 'Working…',
    drop: 'Drop files here, or click to choose',
    fileTypes: 'PDF · Images · Video',
    uploading_one: 'Uploading {{count}} file…',
    uploading_other: 'Uploading {{count}} files…',
    saved: '✓ saved {{name}}',
    skipped: '✗ skipped {{name}} (unsupported)',
    nothingToIndex: 'Nothing to index.',
    reindexing: 'Reindexing corpus (this can take minutes for video)…',
    reindexed: 'Corpus reindexed',
    ingestFailed: 'Ingest failed',
  },

  sessionsView: {
    title: 'Sessions',
    desc: 'Your recent queries this browser. Click any to re-run it.',
    none: 'No queries yet — ask something to get started.',
  },

  common: { cancel: 'Cancel', working: 'Working…', delete: 'Delete' },
}

export default en
export type Resources = typeof en
