import type { Resources } from './en'

// French UI strings.
const fr: Resources = {
  nav: { ask: 'Demander', sources: 'Sources', uploads: 'Imports', sessions: 'Sessions' },

  topbar: {
    corpusReady_one: 'Corpus prêt · {{count}} source',
    corpusReady_other: 'Corpus prêt · {{count}} sources',
    corpusOffline: 'Corpus indisponible',
    toggleSidebar: 'Afficher/masquer la barre latérale',
    toggleDarkMode: 'Activer/désactiver le mode sombre',
    readingComfort: 'Confort de lecture',
    toggleSessionPanel: 'Afficher/masquer le panneau de session',
    language: 'Langue',
  },

  sidebar: {
    brandSub: 'RAG multimodal',
    explore: 'Explorer',
    answerSettings: 'Paramètres de réponse',
    answerMode: 'Mode de réponse',
    modeStrict: 'Corpus uniquement (strict)',
    modeBackground: 'Corpus + connaissances générales',
    modeExploratory: 'Exploratoire',
    showAllLayers: 'Afficher toutes les couches',
    sideNote:
      'Les réponses s’appuient sur votre corpus indexé. Les connaissances générales sont toujours signalées, jamais mêlées en silence.',
    about: 'À propos',
    aboutText:
      'Heritage Lens recherche à travers le texte, les images et la vidéo, puis attribue chaque affirmation et révèle ce qu’il ne peut pas savoir. Conçu pour une recherche spécialisée responsable.',
    darkMode: 'Mode sombre',
  },

  footer: {
    howItWorks: 'Comment ça marche',
    stepYouAsk: 'Vous demandez',
    stepRetrieve: 'Récupérer',
    stepInterpret: 'Interpréter',
    stepAttribute: 'Attribuer',
    stepEvaluate: 'Évaluer',
    trust: 'Des réponses dignes de confiance',
    tagline: 'Heritage Lens Multimodal Agent — IA responsable pour la recherche spécialisée',
  },

  search: { placeholder: 'Posez une question de recherche…', button: 'Rechercher' },

  empty: {
    heading:
      'Heritage Lens combine plusieurs sources et perspectives pour vous offrir des réponses transparentes et prêtes pour la recherche.',
    body: 'Posez une question sur le corpus mésoaméricain. Chaque réponse cite ses sources et indique ce qu’elle ne peut pas savoir.',
  },

  loading: {
    stepRetrieve: 'Récupérer',
    stepInterpret: 'Interpréter',
    stepAttribute: 'Attribuer',
    stepEvaluate: 'Évaluer',
    stageRetrieving: 'Recherche dans le corpus…',
    stageInterpreting: 'Interprétation des passages récupérés…',
    stageAttributing: 'Attribution de chaque affirmation à sa source…',
    stageEvaluating: 'Évaluation de ce que le système ne peut pas savoir…',
  },

  results: {
    sources_one: '{{count}} source',
    sources_other: '{{count}} sources',
    videos_one: '{{count}} segment vidéo',
    videos_other: '{{count}} segments vidéo',
    images_one: '{{count}} image',
    images_other: '{{count}} images',
    seconds: '{{seconds}} s',
    shareQuery: 'Partager la requête',
    export: 'Exporter',
    exportMarkdown: 'Exporter en Markdown',
    exportJson: 'Exporter en JSON',
    shareCopied: 'Lien de partage copié dans le presse-papiers',
    copyFailed: 'Échec de la copie',
    exportedMd: 'Réponse + sources exportées en Markdown',
    exportedJson: 'Résultat exporté en JSON',
    mdAnswer: 'Réponse',
    mdSources: 'Sources',
    mdUnknown: 'Ce que le système ne sait pas',
  },

  answer: {
    title: 'La réponse',
    grounded: 'Fondée',
    ungrounded: 'Non fondée',
    noAnswer: 'Aucune réponse produite.',
    bgNote: '= connaissances générales, clairement séparées des affirmations fondées sur le corpus.',
  },

  sources: {
    title: 'Sources',
    cited: '{{count}} citées',
    none: 'Aucune source récupérée pour cette requête.',
  },

  epistemic: {
    title: 'Ce que le système ne sait pas',
    tag: 'Épistémique',
    sourceBias: 'Biais des sources',
    absences: 'Absences',
    interpretiveLimits: 'Limites d’interprétation',
    confidence: 'Confiance',
    noBias: 'Aucune note spécifique sur le biais des sources pour cette requête.',
    noAbsences: 'Aucune absence spécifique signalée pour cette requête.',
    noLimits: 'Aucune limite d’interprétation spécifique signalée.',
    levelLow: 'Faible',
    levelModerate: 'Modérée',
    levelHigh: 'Élevée',
  },

  rail: {
    sessionOverview: 'Aperçu de la session',
    show: 'Afficher',
    hide: 'Masquer',
    started: 'Démarrée',
    mode: 'Mode',
    sourcesIndexed: 'Sources indexées',
    exchanges: 'Échanges',
    exportSession: 'Exporter la session',
    exportSoon: 'Export de session bientôt disponible',
    recentQueries: 'Requêtes récentes',
    noQueries: 'Aucune requête pour l’instant.',
  },

  video: {
    title: 'Preuves vidéo',
    chunks_one: '{{count}} segment',
    chunks_other: '{{count}} segments',
    audio: 'Audio',
    visual: 'Visuel',
    ocr: 'OCR',
    play: 'Lire {{name}} à {{time}}',
    playAt: 'Lire à {{time}}',
    seekTo: 'Aller à {{time}}',
    videoFallback: 'vidéo',
  },

  image: {
    title: 'Preuves visuelles',
    images_one: '{{count}} image',
    images_other: '{{count}} images',
    open: 'Ouvrir {{alt}}',
  },

  lightbox: {
    close: 'Fermer',
    videoErr: 'Cette vidéo ne peut pas être lue dans votre navigateur.',
    openNewTab: 'Ouvrir la vidéo dans un nouvel onglet ↗',
  },

  reading: {
    title: 'Confort de lecture',
    sub: 'La police s’applique à toute l’app · l’espacement à la réponse',
    dialogAria: 'Paramètres de confort de lecture',
    close: 'Fermer',
    typeface: 'Police',
    fontDefault: 'Par défaut',
    spacing: 'Espacement',
    letterSpacing: 'Interlettrage',
    lineHeight: 'Interligne',
    columnWidth: 'Largeur de colonne',
    presentation: 'Présentation',
    creamBg: 'Fond crème',
    creamSub: 'Solarized base3 · #FDF6E3',
    ragged: 'Aligné à gauche',
    raggedSub: 'Désactiver la justification',
    reset: 'Réinitialiser les valeurs par défaut',
  },

  sourcesView: {
    title: 'Sources du corpus',
    desc: 'Chaque document indexé dans le corpus de recherche, avec ses métadonnées d’attribution.',
    loading: 'Chargement des sources…',
    none: 'Aucune source indexée pour l’instant.',
    chunks_one: '{{count}} segment',
    chunks_other: '{{count}} segments',
    deleteSource: 'Supprimer la source',
    deleteAria: 'Supprimer {{name}}',
    removed: 'Supprimée {{name}}',
    confirmTitle: 'Supprimer la source',
    confirmMsg:
      'Supprimer définitivement « {{name}} » ({{count}} segments) ? Cela supprime ses vecteurs et fichiers et est irréversible.',
  },

  uploadsView: {
    title: 'Ajouter au corpus',
    desc: 'Importez des PDF, images ou vidéos. Les fichiers sont enregistrés dans le corpus et l’index est reconstruit.',
    working: 'En cours…',
    drop: 'Déposez les fichiers ici, ou cliquez pour choisir',
    fileTypes: 'PDF · Images · Vidéo',
    uploading_one: 'Import de {{count}} fichier…',
    uploading_other: 'Import de {{count}} fichiers…',
    saved: '✓ enregistré {{name}}',
    skipped: '✗ ignoré {{name}} (non pris en charge)',
    nothingToIndex: 'Rien à indexer.',
    reindexing: 'Réindexation du corpus (peut prendre quelques minutes pour la vidéo)…',
    reindexed: 'Corpus réindexé',
    ingestFailed: 'Échec de l’ingestion',
  },

  sessionsView: {
    title: 'Sessions',
    desc: 'Vos requêtes récentes dans ce navigateur. Cliquez sur l’une d’elles pour la relancer.',
    none: 'Aucune requête pour l’instant — posez une question pour commencer.',
  },

  common: { cancel: 'Annuler', working: 'En cours…', delete: 'Supprimer' },
}

export default fr
