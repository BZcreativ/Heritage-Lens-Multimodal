import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './en'
import it from './it'
import es from './es'
import fr from './fr'

// Supported UI languages. `label` is the endonym shown in the picker; `backend`
// is the language name sent to /api/search to force the answer language.
export const LOCALES = [
  { code: 'en', label: 'English', backend: 'English' },
  { code: 'it', label: 'Italiano', backend: 'Italian' },
  { code: 'es', label: 'Español', backend: 'Spanish' },
  { code: 'fr', label: 'Français', backend: 'French' },
] as const

export type LocaleCode = (typeof LOCALES)[number]['code']

const STORAGE_KEY = 'hl_lang'

function initialLang(): LocaleCode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && LOCALES.some((l) => l.code === stored)) return stored as LocaleCode
  } catch {
    /* storage unavailable (private mode) — fall through to default */
  }
  return 'en'
}

/** Backend language name for the current UI language (for POST /api/search). */
export function backendLanguage(code: string = i18n.language): string {
  return LOCALES.find((l) => l.code === code)?.backend ?? 'English'
}

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    it: { translation: it },
    es: { translation: es },
    fr: { translation: fr },
  },
  lng: initialLang(),
  fallbackLng: 'en',
  interpolation: { escapeValue: false }, // React already escapes
})

// Persist the choice across reloads, matching the app's hl_* localStorage prefix.
i18n.on('languageChanged', (lng) => {
  try {
    localStorage.setItem(STORAGE_KEY, lng)
  } catch {
    /* ignore quota/private-mode errors */
  }
  document.documentElement.lang = lng
})
document.documentElement.lang = i18n.language

export default i18n
