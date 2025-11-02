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
 * SINGLE SOURCE OF TRUTH for file type detection in frontend
 *
 * Extracts file extension with proper fallback handling.
 * This replaces all scattered file type detection logic.
 *
 * @param file_type - File type from backend (primary source)
 * @param filename - Filename for fallback extraction
 * @returns Normalized file extension (lowercase, without dot)
 */
export function detectFileExtension(file_type?: string | null, filename?: string | null): string | null {
  // Primary: Use backend-provided file_type
  let ext = file_type?.toLowerCase()

  // Fallback: Extract extension from filename if file_type is missing/undefined
  if (!ext && filename) {
    const match = filename.match(/\.([^.]+)$/)
    ext = match ? match[1].toLowerCase() : null
  }

  if (!ext) return null

  // Remove leading dot if present (.md → md)
  ext = ext.replace(/^\./, '')

  return ext
}

/**
 * Viewer type classification for file preview
 *
 * @param extension - File extension from detectFileExtension()
 * @returns Viewer type: 'text' | 'code' | 'docx' | 'pdf' | 'image' | null
 */
export function getViewerType(extension: string | null): 'text' | 'code' | 'docx' | 'pdf' | 'image' | null {
  if (!extension) return null

  // Text files (markdown, plain text, JSON)
  if (['md', 'markdown', 'txt', 'json'].includes(extension)) {
    return 'text'
  }

  // Code files
  if (['py', 'js', 'ts', 'jsx', 'tsx', 'vue', 'yaml', 'yml', 'html', 'css', 'scss', 'sh', 'bash'].includes(extension)) {
    return 'code'
  }

  // DOCX
  if (extension === 'docx' || extension === 'doc') {
    return 'docx'
  }

  // Images
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp'].includes(extension)) {
    return 'image'
  }

  // PDF
  if (extension === 'pdf') {
    return 'pdf'
  }

  return null
}

/**
 * Get normalized file type for display
 *
 * @param file_type - File type from backend
 * @param filename - Filename for fallback
 * @returns Display-friendly file type (e.g., 'pdf', 'docx', 'md')
 */
export function getNormalizedFileType(file_type?: string | null, filename?: string | null): string {
  const ext = detectFileExtension(file_type, filename)
  return ext || 'unknown'
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

/**
 * Extract filesystem path from download URL for API requests
 *
 * Converts download URL to the format expected by backend file content API.
 * Backend expects: {session_id}/{filename}
 * Frontend receives: /download/{session_id}/{filename}
 *
 * @param downloadPath - Download URL path (e.g., "/download/abc123/file.pdf")
 * @param fallbackFilename - Fallback filename if path parsing fails
 * @returns Filesystem path for backend API (e.g., "abc123/file.pdf")
 *
 * @example
 * extractFilePathFromDownloadUrl("/download/abc123/file.pdf", "file.pdf")
 * // Returns: "abc123/file.pdf"
 */
export function extractFilePathFromDownloadUrl(
  downloadPath: string | null | undefined,
  fallbackFilename: string
): string {
  if (!downloadPath) {
    return fallbackFilename
  }

  // Remove /download/ prefix to get session_id/filename
  const pathMatch = downloadPath.match(/^\/download\/(.+)$/)
  if (pathMatch) {
    return pathMatch[1] // Returns: {session_id}/{filename}
  }

  // Fallback to filename if pattern doesn't match
  return fallbackFilename
}
