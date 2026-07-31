import type { Resources } from './en'

// Spanish UI strings.
const es: Resources = {
  nav: { ask: 'Preguntar', sources: 'Fuentes', uploads: 'Subidas', sessions: 'Sesiones' },

  topbar: {
    corpusReady_one: 'Corpus listo · {{count}} fuente',
    corpusReady_other: 'Corpus listo · {{count}} fuentes',
    corpusOffline: 'Corpus no disponible',
    toggleSidebar: 'Mostrar/ocultar barra lateral',
    toggleDarkMode: 'Activar/desactivar modo oscuro',
    readingComfort: 'Comodidad de lectura',
    toggleSessionPanel: 'Mostrar/ocultar panel de sesión',
    language: 'Idioma',
  },

  sidebar: {
    brandSub: 'RAG multimodal',
    explore: 'Explorar',
    answerSettings: 'Ajustes de respuesta',
    answerMode: 'Modo de respuesta',
    modeStrict: 'Solo corpus (estricto)',
    modeBackground: 'Corpus + conocimiento general',
    modeExploratory: 'Exploratorio',
    showAllLayers: 'Mostrar todas las capas',
    sideNote:
      'Las respuestas se basan en tu corpus indexado. El conocimiento general siempre se etiqueta, nunca se mezcla en silencio.',
    about: 'Acerca de',
    aboutText:
      'Heritage Lens recupera entre texto, imágenes y vídeo, luego atribuye cada afirmación y revela lo que no puede saber. Creado para una investigación especializada responsable.',
    darkMode: 'Modo oscuro',
  },

  footer: {
    howItWorks: 'Cómo funciona',
    stepYouAsk: 'Preguntas',
    stepRetrieve: 'Recuperar',
    stepInterpret: 'Interpretar',
    stepAttribute: 'Atribuir',
    stepEvaluate: 'Evaluar',
    trust: 'Respuestas en las que confiar',
    tagline: 'Heritage Lens Multimodal Agent — IA responsable para la investigación especializada',
  },

  search: { placeholder: 'Haz una pregunta de investigación…', button: 'Buscar' },

  empty: {
    heading:
      'Heritage Lens combina varias fuentes y perspectivas para darte respuestas transparentes y listas para investigar.',
    body: 'Pregunta sobre el corpus mesoamericano. Cada respuesta cita sus fuentes y te dice lo que no puede saber.',
  },

  loading: {
    stepRetrieve: 'Recuperar',
    stepInterpret: 'Interpretar',
    stepAttribute: 'Atribuir',
    stepEvaluate: 'Evaluar',
    stageRetrieving: 'Recuperando en el corpus…',
    stageInterpreting: 'Interpretando los pasajes recuperados…',
    stageAttributing: 'Atribuyendo cada afirmación a su fuente…',
    stageEvaluating: 'Evaluando lo que el sistema no puede saber…',
  },

  results: {
    sources_one: '{{count}} fuente',
    sources_other: '{{count}} fuentes',
    videos_one: '{{count}} fragmento de vídeo',
    videos_other: '{{count}} fragmentos de vídeo',
    images_one: '{{count}} imagen',
    images_other: '{{count}} imágenes',
    seconds: '{{seconds}} s',
    shareQuery: 'Compartir consulta',
    export: 'Exportar',
    exportMarkdown: 'Exportar como Markdown',
    exportJson: 'Exportar como JSON',
    shareCopied: 'Enlace para compartir copiado al portapapeles',
    copyFailed: 'Error al copiar',
    exportedMd: 'Respuesta + fuentes exportadas como Markdown',
    exportedJson: 'Resultado exportado como JSON',
    mdAnswer: 'Respuesta',
    mdSources: 'Fuentes',
    mdUnknown: 'Lo que el sistema no sabe',
  },

  answer: {
    title: 'La respuesta',
    grounded: 'Fundamentada',
    ungrounded: 'Sin fundamento',
    noAnswer: 'No se produjo ninguna respuesta.',
    bgNote: '= conocimiento general, claramente separado de las afirmaciones basadas en el corpus.',
  },

  sources: {
    title: 'Fuentes',
    cited: '{{count}} citadas',
    none: 'No se recuperaron fuentes para esta consulta.',
  },

  epistemic: {
    title: 'Lo que el sistema no sabe',
    tag: 'Epistémico',
    sourceBias: 'Sesgo de las fuentes',
    absences: 'Ausencias',
    interpretiveLimits: 'Límites interpretativos',
    confidence: 'Confianza',
    noBias: 'No hay notas específicas de sesgo de fuentes para esta consulta.',
    noAbsences: 'No se señalaron ausencias específicas para esta consulta.',
    noLimits: 'No se señalaron límites interpretativos específicos.',
    levelLow: 'Baja',
    levelModerate: 'Moderada',
    levelHigh: 'Alta',
  },

  rail: {
    sessionOverview: 'Resumen de la sesión',
    show: 'Mostrar',
    hide: 'Ocultar',
    started: 'Iniciada',
    mode: 'Modo',
    sourcesIndexed: 'Fuentes indexadas',
    exchanges: 'Intercambios',
    exportSession: 'Exportar sesión',
    exportSoon: 'Exportación de sesión próximamente',
    recentQueries: 'Consultas recientes',
    noQueries: 'Aún no hay consultas.',
  },

  video: {
    title: 'Pruebas en vídeo',
    chunks_one: '{{count}} fragmento',
    chunks_other: '{{count}} fragmentos',
    audio: 'Audio',
    visual: 'Visual',
    ocr: 'OCR',
    play: 'Reproducir {{name}} en {{time}}',
    playAt: 'Reproducir en {{time}}',
    seekTo: 'Ir a {{time}}',
    videoFallback: 'vídeo',
  },

  image: {
    title: 'Pruebas visuales',
    images_one: '{{count}} imagen',
    images_other: '{{count}} imágenes',
    open: 'Abrir {{alt}}',
  },

  lightbox: {
    close: 'Cerrar',
    videoErr: 'Este vídeo no se puede reproducir en tu navegador.',
    openNewTab: 'Abrir vídeo en una pestaña nueva ↗',
  },

  reading: {
    title: 'Comodidad de lectura',
    sub: 'La tipografía se aplica a toda la app · el espaciado a la respuesta',
    dialogAria: 'Ajustes de comodidad de lectura',
    close: 'Cerrar',
    typeface: 'Tipografía',
    fontDefault: 'Predeterminada',
    spacing: 'Espaciado',
    letterSpacing: 'Espaciado entre letras',
    lineHeight: 'Interlineado',
    columnWidth: 'Ancho de columna',
    presentation: 'Presentación',
    creamBg: 'Fondo crema',
    creamSub: 'Solarized base3 · #FDF6E3',
    ragged: 'Alineado a la izquierda',
    raggedSub: 'Desactivar la justificación',
    reset: 'Restablecer valores predeterminados',
  },

  sourcesView: {
    title: 'Fuentes del corpus',
    desc: 'Todos los documentos indexados en el corpus de investigación, con metadatos de atribución.',
    loading: 'Cargando fuentes…',
    none: 'Aún no hay fuentes indexadas.',
    chunks_one: '{{count}} fragmento',
    chunks_other: '{{count}} fragmentos',
    deleteSource: 'Eliminar fuente',
    deleteAria: 'Eliminar {{name}}',
    removed: 'Eliminada {{name}}',
    confirmTitle: 'Eliminar fuente',
    confirmMsg:
      '¿Eliminar permanentemente «{{name}}» ({{count}} fragmentos)? Esto elimina sus vectores y archivos y no se puede deshacer.',
  },

  uploadsView: {
    title: 'Añadir al corpus',
    desc: 'Sube PDF, imágenes o vídeo. Los archivos se guardan en el corpus y el índice se reconstruye.',
    working: 'Trabajando…',
    drop: 'Suelta los archivos aquí, o haz clic para elegir',
    fileTypes: 'PDF · Imágenes · Vídeo',
    uploading_one: 'Subiendo {{count}} archivo…',
    uploading_other: 'Subiendo {{count}} archivos…',
    saved: '✓ guardado {{name}}',
    skipped: '✗ omitido {{name}} (no compatible)',
    nothingToIndex: 'Nada que indexar.',
    reindexing: 'Reindexando el corpus (puede tardar minutos con vídeo)…',
    reindexed: 'Corpus reindexado',
    ingestFailed: 'Error en la ingesta',
  },

  sessionsView: {
    title: 'Sesiones',
    desc: 'Tus consultas recientes en este navegador. Haz clic en cualquiera para volver a ejecutarla.',
    none: 'Aún no hay consultas — pregunta algo para empezar.',
  },

  common: { cancel: 'Cancelar', working: 'Trabajando…', delete: 'Eliminar' },
}

export default es
