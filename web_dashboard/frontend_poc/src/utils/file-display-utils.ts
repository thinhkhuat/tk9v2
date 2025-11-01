/**
 * File Display Utilities
 *
 * PRESENTATION LAYER ONLY - consumes pre-parsed metadata from backend.
 * Backend (Python filename_utils.py) is the single source of truth for parsing.
 *
 * Phase 3: Frontend Migration to DRY principle
 * Gemini validated: session dc76fc08-66c7-4a0b-81b8-51914d09e66d
 */

/**
 * Parsed file metadata structure (matches backend WebSocket events)
 */
export interface ParsedFileData {
  filename: string          // Original UUID filename (e.g., "abc123def456_vi.pdf")
  file_type: string          // From backend enum: 'pdf' | 'docx' | 'md' | 'txt' | 'json' | 'xml' | 'html'
  language: string           // ISO language code: 'en' | 'vi' | 'es' | 'fr' | etc.
  friendly_name: string      // User-facing name (e.g., "research_report_vi.pdf")
  uuid: string              // Extracted UUID (32 hex chars)
  is_translated: boolean    // Has language suffix in filename
  size_bytes: number        // File size
}

/**
 * Get emoji icon for file type
 *
 * @param fileType - File type from backend enum
 * @returns Emoji icon string
 */
export function getFileTypeIcon(fileType: string | undefined | null): string {
  const icons: Record<string, string> = {
    pdf: '📄',
    docx: '📝',
    doc: '📝',
    md: '📋',
    txt: '📃',
    json: '{ }',
    xml: '</>',
    html: '🌐'
  }

  // Handle undefined, null, or empty fileType
  if (!fileType) return '📎'

  return icons[fileType.toLowerCase()] || '📎'
}

/**
 * Convert ISO language code to display name
 *
 * @param languageCode - ISO 639-1 language code (e.g., 'vi', 'en')
 * @returns Human-readable language name
 */
export function getDisplayLanguage(languageCode: string): string {
  const languageMap: Record<string, string> = {
    en: 'English',
    vi: 'Vietnamese',
    es: 'Spanish',
    fr: 'French',
    de: 'German',
    it: 'Italian',
    pt: 'Portuguese',
    ru: 'Russian',
    ja: 'Japanese',
    ko: 'Korean',
    zh: 'Chinese',
    ar: 'Arabic',
    hi: 'Hindi',
    th: 'Thai',
    id: 'Indonesian',
    nl: 'Dutch',
    pl: 'Polish',
    tr: 'Turkish',
    sv: 'Swedish',
    no: 'Norwegian',
    da: 'Danish',
    fi: 'Finnish',
    cs: 'Czech',
    ro: 'Romanian',
    hu: 'Hungarian',
    el: 'Greek',
    he: 'Hebrew',
    uk: 'Ukrainian',
    bg: 'Bulgarian',
    hr: 'Croatian',
    sk: 'Slovak',
    sr: 'Serbian',
    sl: 'Slovenian',
    lt: 'Lithuanian',
    lv: 'Latvian',
    et: 'Estonian',
    ms: 'Malay',
    fa: 'Persian',
    ur: 'Urdu',
    bn: 'Bengali',
    ta: 'Tamil',
    te: 'Telugu',
    mr: 'Marathi',
    gu: 'Gujarati',
    kn: 'Kannada',
    ml: 'Malayalam',
    pa: 'Punjabi',
    si: 'Sinhala',
    ne: 'Nepali',
    my: 'Burmese',
    km: 'Khmer',
    lo: 'Lao'
  }

  return languageMap[languageCode] || languageCode.toUpperCase()
}

/**
 * Sort comparator for files
 * Priority: original files first, then translated (by language)
 *
 * @param a - First file
 * @param b - Second file
 * @returns Sort order (-1, 0, 1)
 */
export function compareFiles(a: ParsedFileData, b: ParsedFileData): number {
  // Original files (no translation) come first
  const aPriority = a.is_translated ? 1 : 0
  const bPriority = b.is_translated ? 1 : 0

  if (aPriority !== bPriority) {
    return aPriority - bPriority
  }

  // Within same category, sort by language
  return a.language.localeCompare(b.language)
}

// NOTE: formatFileSize() and getLanguageColor() are in @/utils/formatters.ts
// Import from there to avoid duplication (DRY principle)

/**
 * PRE-UPLOAD ONLY: Guess file type from filename extension
 *
 * IMPORTANT: This is NOT authoritative parsing. It's only for:
 * - File upload previews (before backend processes the file)
 * - Client-side UI hints
 *
 * Backend filename_utils.py remains the single source of truth.
 *
 * @param filename - Filename with extension
 * @returns Guessed file type
 */
export function guessFileTypeFromFilename(filename: string): string {
  const extension = filename.split('.').pop()?.toLowerCase()

  switch (extension) {
    case 'pdf':
      return 'pdf'
    case 'docx':
    case 'doc':
      return 'docx'
    case 'md':
    case 'markdown':
      return 'md'
    case 'txt':
    case 'text':
      return 'txt'
    case 'json':
      return 'json'
    case 'xml':
      return 'xml'
    case 'html':
    case 'htm':
      return 'html'
    default:
      return 'unknown'
  }
}

/**
 * Check if file type is binary (requires special download handling)
 *
 * @param fileType - File type from backend
 * @returns true if binary format
 */
export function isBinaryFileType(fileType: string): boolean {
  const binaryTypes = ['pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp']
  return binaryTypes.includes(fileType.toLowerCase())
}

/**
 * Normalize file data from WebSocket event
 * Ensures all expected fields are present with defaults
 *
 * @param fileEvent - Raw file event from WebSocket
 * @returns Normalized ParsedFileData
 */
export function normalizeFileData(fileEvent: any): ParsedFileData {
  return {
    filename: fileEvent.filename || 'unknown.txt',
    file_type: fileEvent.file_type || 'unknown',
    language: fileEvent.language || 'en',
    friendly_name: fileEvent.filename || 'unknown.txt',  // Backend should provide this
    uuid: fileEvent.file_id || '',
    is_translated: (fileEvent.filename || '').includes('_'),
    size_bytes: fileEvent.size_bytes || 0
  }
}
