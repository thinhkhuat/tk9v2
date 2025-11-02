<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import hljs from 'highlight.js/lib/core'
import { useToast } from 'vue-toastification'

// Import only the languages we need
import python from 'highlight.js/lib/languages/python'
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import json from 'highlight.js/lib/languages/json'
import yaml from 'highlight.js/lib/languages/yaml'
import xml from 'highlight.js/lib/languages/xml' // for HTML
import css from 'highlight.js/lib/languages/css'
import scss from 'highlight.js/lib/languages/scss'
import bash from 'highlight.js/lib/languages/bash'
import sql from 'highlight.js/lib/languages/sql'
import markdown from 'highlight.js/lib/languages/markdown'

// Register languages
hljs.registerLanguage('python', python)
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('json', json)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('css', css)
hljs.registerLanguage('scss', scss)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('md', markdown)

// Vue files - treat as HTML
hljs.registerLanguage('vue', xml)

const props = defineProps<{
  content: string
  language?: string
  filename?: string
}>()

const toast = useToast()
const isCopied = ref(false)
const codeElement = ref<HTMLElement | null>(null)

// Map file extensions to highlight.js language names
const languageMap: Record<string, string> = {
  py: 'python',
  js: 'javascript',
  jsx: 'javascript',
  ts: 'typescript',
  tsx: 'typescript',
  json: 'json',
  yaml: 'yaml',
  yml: 'yaml',
  html: 'html',
  htm: 'html',
  xml: 'xml',
  css: 'css',
  scss: 'scss',
  sass: 'scss',
  sh: 'bash',
  bash: 'bash',
  sql: 'sql',
  md: 'markdown',
  vue: 'vue'
}

// Get the correct language for highlighting
const highlightLanguage = computed(() => {
  if (!props.language) return 'plaintext'
  const lang = props.language.toLowerCase()
  return languageMap[lang] || lang
})

// Highlighted code HTML
const highlightedCode = computed(() => {
  try {
    const language = highlightLanguage.value
    if (hljs.getLanguage(language)) {
      return hljs.highlight(props.content, {
        language,
        ignoreIllegals: true
      }).value
    } else {
      // Fallback to auto-detection
      return hljs.highlightAuto(props.content).value
    }
  } catch (e) {
    console.error('Syntax highlighting failed:', e)
    // Return escaped HTML if highlighting fails
    return props.content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
  }
})

// Line numbers
const lines = computed(() => {
  return props.content.split('\n')
})

// Language display name
const languageDisplayName = computed(() => {
  const lang = highlightLanguage.value
  const displayNames: Record<string, string> = {
    python: 'Python',
    javascript: 'JavaScript',
    typescript: 'TypeScript',
    json: 'JSON',
    yaml: 'YAML',
    html: 'HTML',
    xml: 'XML',
    css: 'CSS',
    scss: 'SCSS',
    bash: 'Bash',
    sh: 'Shell',
    sql: 'SQL',
    markdown: 'Markdown',
    vue: 'Vue'
  }
  return displayNames[lang] || lang.toUpperCase()
})

// Copy to clipboard
async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(props.content)
    isCopied.value = true
    toast.success('Code copied to clipboard!')

    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
    toast.error('Failed to copy to clipboard')
  }
}
</script>

<template>
  <div class="relative h-full flex flex-col bg-gray-900">
    <!-- Toolbar -->
    <div class="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
      <div class="flex items-center gap-2">
        <span class="px-2 py-1 text-xs font-medium bg-blue-600 text-white rounded">
          {{ languageDisplayName }}
        </span>
        <span v-if="filename" class="text-xs text-gray-400 font-mono">{{ filename }}</span>
      </div>

      <button
        @click="copyToClipboard"
        class="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-gray-700 text-gray-200 rounded-md hover:bg-gray-600 transition-colors"
        :class="{ 'bg-green-600 hover:bg-green-500': isCopied }"
      >
        <svg v-if="!isCopied" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        <span>{{ isCopied ? 'Copied!' : 'Copy' }}</span>
      </button>
    </div>

    <!-- Code Area -->
    <div class="flex-1 overflow-auto flex">
      <!-- Line Numbers -->
      <div class="flex-shrink-0 px-4 py-4 bg-gray-800 border-r border-gray-700 select-none">
        <div class="font-mono text-xs text-gray-500 leading-6 text-right">
          <div v-for="(_, index) in lines" :key="index">
            {{ index + 1 }}
          </div>
        </div>
      </div>

      <!-- Code Content -->
      <div class="flex-1 overflow-auto">
        <pre class="p-4 m-0"><code
          ref="codeElement"
          class="hljs language-{{ highlightLanguage }} text-sm leading-6"
          v-html="highlightedCode"
        /></pre>
      </div>
    </div>
  </div>
</template>

<style>
/* Import VS Code Dark+ theme for highlight.js */
@import 'highlight.js/styles/vs2015.css';

/* Override some styles for better appearance */
.hljs {
  background: #1e1e1e !important;
  color: #d4d4d4 !important;
  padding: 0 !important;
  overflow: visible !important;
}

/* Ensure code block styling */
pre {
  background: #1e1e1e;
  margin: 0;
  padding: 0;
}

pre code {
  display: block;
  overflow-x: auto;
  padding: 0;
}

/* Custom syntax highlighting colors (VS Code Dark+ inspired) */
.hljs-keyword {
  color: #569cd6;
}

.hljs-string {
  color: #ce9178;
}

.hljs-number {
  color: #b5cea8;
}

.hljs-comment {
  color: #6a9955;
  font-style: italic;
}

.hljs-function {
  color: #dcdcaa;
}

.hljs-class {
  color: #4ec9b0;
}

.hljs-variable {
  color: #9cdcfe;
}

.hljs-built_in {
  color: #4ec9b0;
}

.hljs-literal {
  color: #569cd6;
}

.hljs-attr {
  color: #9cdcfe;
}

.hljs-tag {
  color: #569cd6;
}

.hljs-name {
  color: #4ec9b0;
}

.hljs-attribute {
  color: #9cdcfe;
}

.hljs-regexp {
  color: #d16969;
}

.hljs-meta {
  color: #dcdcaa;
}

.hljs-selector-tag,
.hljs-selector-id,
.hljs-selector-class {
  color: #d7ba7d;
}
</style>
