import type { Resources } from './en'

// Italian UI strings.
const it: Resources = {
  nav: { ask: 'Chiedi', sources: 'Fonti', uploads: 'Caricamenti', sessions: 'Sessioni' },

  topbar: {
    corpusReady_one: 'Corpus pronto · {{count}} fonte',
    corpusReady_other: 'Corpus pronto · {{count}} fonti',
    corpusOffline: 'Corpus non disponibile',
    toggleSidebar: 'Mostra/nascondi barra laterale',
    toggleDarkMode: 'Attiva/disattiva tema scuro',
    readingComfort: 'Comfort di lettura',
    toggleSessionPanel: 'Mostra/nascondi pannello sessione',
    language: 'Lingua',
  },

  sidebar: {
    brandSub: 'RAG multimodale',
    explore: 'Esplora',
    answerSettings: 'Impostazioni risposta',
    answerMode: 'Modalità risposta',
    modeStrict: 'Solo corpus (rigoroso)',
    modeBackground: 'Corpus + conoscenza generale',
    modeExploratory: 'Esplorativa',
    showAllLayers: 'Mostra tutti i livelli',
    sideNote:
      'Le risposte si basano sul corpus indicizzato. La conoscenza generale è sempre etichettata, mai mescolata in silenzio.',
    about: 'Informazioni',
    aboutText:
      'Heritage Lens recupera tra testo, immagini e video, poi attribuisce ogni affermazione e rivela ciò che non può sapere. Pensato per una ricerca specialistica responsabile.',
    darkMode: 'Tema scuro',
  },

  footer: {
    howItWorks: 'Come funziona',
    stepYouAsk: 'Chiedi',
    stepRetrieve: 'Recupera',
    stepInterpret: 'Interpreta',
    stepAttribute: 'Attribuisci',
    stepEvaluate: 'Valuta',
    trust: 'Risposte di cui fidarsi',
    tagline: 'Heritage Lens Multimodal Agent — IA responsabile per la ricerca specialistica',
  },

  search: { placeholder: 'Poni una domanda di ricerca…', button: 'Cerca' },

  empty: {
    heading:
      'Heritage Lens combina più fonti e prospettive per darti risposte trasparenti e pronte per la ricerca.',
    body: 'Chiedi del corpus mesoamericano. Ogni risposta cita le sue fonti e ti dice ciò che non può sapere.',
  },

  loading: {
    stepRetrieve: 'Recupera',
    stepInterpret: 'Interpreta',
    stepAttribute: 'Attribuisci',
    stepEvaluate: 'Valuta',
    stageRetrieving: 'Recupero nel corpus…',
    stageInterpreting: 'Interpretazione dei passaggi recuperati…',
    stageAttributing: 'Attribuzione di ogni affermazione alla sua fonte…',
    stageEvaluating: 'Valutazione di ciò che il sistema non può sapere…',
  },

  results: {
    sources_one: '{{count}} fonte',
    sources_other: '{{count}} fonti',
    videos_one: '{{count}} segmento video',
    videos_other: '{{count}} segmenti video',
    images_one: '{{count}} immagine',
    images_other: '{{count}} immagini',
    seconds: '{{seconds}} s',
    shareQuery: 'Condividi query',
    export: 'Esporta',
    exportMarkdown: 'Esporta come Markdown',
    exportJson: 'Esporta come JSON',
    shareCopied: 'Link di condivisione copiato negli appunti',
    copyFailed: 'Copia non riuscita',
    exportedMd: 'Risposta + fonti esportate come Markdown',
    exportedJson: 'Risultato esportato come JSON',
    mdAnswer: 'Risposta',
    mdSources: 'Fonti',
    mdUnknown: 'Ciò che il sistema non sa',
  },

  answer: {
    title: 'La risposta',
    grounded: 'Fondata',
    ungrounded: 'Non fondata',
    noAnswer: 'Nessuna risposta prodotta.',
    bgNote: '= conoscenza generale, chiaramente separata dalle affermazioni fondate sul corpus.',
  },

  sources: {
    title: 'Fonti',
    cited: '{{count}} citate',
    none: 'Nessuna fonte recuperata per questa query.',
  },

  epistemic: {
    title: 'Ciò che il sistema non sa',
    tag: 'Epistemico',
    sourceBias: 'Bias delle fonti',
    absences: 'Assenze',
    interpretiveLimits: 'Limiti interpretativi',
    confidence: 'Affidabilità',
    noBias: 'Nessuna nota specifica sul bias delle fonti per questa query.',
    noAbsences: 'Nessuna assenza specifica segnalata per questa query.',
    noLimits: 'Nessun limite interpretativo specifico segnalato.',
    levelLow: 'Bassa',
    levelModerate: 'Moderata',
    levelHigh: 'Alta',
  },

  rail: {
    sessionOverview: 'Panoramica sessione',
    show: 'Mostra',
    hide: 'Nascondi',
    started: 'Iniziata',
    mode: 'Modalità',
    sourcesIndexed: 'Fonti indicizzate',
    exchanges: 'Scambi',
    exportSession: 'Esporta sessione',
    exportSoon: 'Esportazione sessione in arrivo',
    recentQueries: 'Query recenti',
    noQueries: 'Ancora nessuna query.',
  },

  video: {
    title: 'Prove video',
    chunks_one: '{{count}} segmento',
    chunks_other: '{{count}} segmenti',
    audio: 'Audio',
    visual: 'Visivo',
    ocr: 'OCR',
    play: 'Riproduci {{name}} a {{time}}',
    playAt: 'Riproduci a {{time}}',
    seekTo: 'Vai a {{time}}',
    videoFallback: 'video',
  },

  image: {
    title: 'Prove visive',
    images_one: '{{count}} immagine',
    images_other: '{{count}} immagini',
    open: 'Apri {{alt}}',
  },

  lightbox: {
    close: 'Chiudi',
    videoErr: 'Questo video non può essere riprodotto nel tuo browser.',
    openNewTab: 'Apri il video in una nuova scheda ↗',
  },

  reading: {
    title: 'Comfort di lettura',
    sub: 'Il carattere si applica a tutta l’app · la spaziatura alla risposta',
    dialogAria: 'Impostazioni comfort di lettura',
    close: 'Chiudi',
    typeface: 'Carattere',
    fontDefault: 'Predefinito',
    spacing: 'Spaziatura',
    letterSpacing: 'Spaziatura tra lettere',
    lineHeight: 'Interlinea',
    columnWidth: 'Larghezza colonna',
    presentation: 'Presentazione',
    creamBg: 'Sfondo crema',
    creamSub: 'Solarized base3 · #FDF6E3',
    ragged: 'Allineato a sinistra',
    raggedSub: 'Disattiva la giustificazione',
    reset: 'Ripristina i valori predefiniti',
  },

  sourcesView: {
    title: 'Fonti del corpus',
    desc: 'Ogni documento indicizzato nel corpus di ricerca, con metadati di attribuzione.',
    loading: 'Caricamento delle fonti…',
    none: 'Nessuna fonte ancora indicizzata.',
    chunks_one: '{{count}} segmento',
    chunks_other: '{{count}} segmenti',
    deleteSource: 'Elimina fonte',
    deleteAria: 'Elimina {{name}}',
    removed: 'Rimossa {{name}}',
    confirmTitle: 'Elimina fonte',
    confirmMsg:
      'Rimuovere definitivamente “{{name}}” ({{count}} segmenti)? Questo elimina i suoi vettori e file e non può essere annullato.',
  },

  uploadsView: {
    title: 'Aggiungi al corpus',
    desc: 'Carica PDF, immagini o video. I file vengono salvati nel corpus e l’indice viene ricostruito.',
    working: 'In corso…',
    drop: 'Trascina i file qui, o clicca per scegliere',
    fileTypes: 'PDF · Immagini · Video',
    uploading_one: 'Caricamento di {{count}} file…',
    uploading_other: 'Caricamento di {{count}} file…',
    saved: '✓ salvato {{name}}',
    skipped: '✗ ignorato {{name}} (non supportato)',
    nothingToIndex: 'Niente da indicizzare.',
    reindexing: 'Reindicizzazione del corpus (può richiedere minuti per i video)…',
    reindexed: 'Corpus reindicizzato',
    ingestFailed: 'Ingestione non riuscita',
  },

  sessionsView: {
    title: 'Sessioni',
    desc: 'Le tue query recenti in questo browser. Clicca su una per rieseguirla.',
    none: 'Ancora nessuna query — chiedi qualcosa per iniziare.',
  },

  common: { cancel: 'Annulla', working: 'In corso…', delete: 'Elimina' },
}

export default it
