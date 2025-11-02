<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'
import { useToast } from 'vue-toastification'

const props = defineProps<{
  content: string
  fileType: string // 'md', 'txt', 'json'
}>()

const toast = useToast()
const isCopied = ref(false)

// DEBUG: Log received props
console.log('[TextFileViewer] Received fileType:', props.fileType, 'Content length:', props.content.length)

// Configure marked for better rendering
marked.setOptions({
  breaks: true,
  gfm: true // GitHub Flavored Markdown
})

// Render content based on file type
const renderedContent = computed<string>(() => {
  console.log('[TextFileViewer] Computing renderedContent, fileType:', props.fileType)

  if (props.fileType === 'md') {
    // Render markdown to HTML (marked.parse is sync in v11+)
    const html = marked.parse(props.content) as string
    console.log('[TextFileViewer] Rendered markdown HTML length:', typeof html === 'string' ? html.length : 0)
    return html
  } else if (props.fileType === 'json') {
    // Pretty print JSON
    try {
      const parsed = JSON.parse(props.content)
      return JSON.stringify(parsed, null, 2)
    } catch (e) {
      // If JSON parsing fails, return as-is
      return props.content
    }
  } else {
    // Plain text - return as-is
    console.log('[TextFileViewer] Returning plain text')
    return props.content
  }
})

// Check if content is JSON
const isJson = computed(() => {
  const result = props.fileType === 'json'
  console.log('[TextFileViewer] isJson:', result)
  return result
})

const isMarkdown = computed(() => {
  const result = props.fileType === 'md'
  console.log('[TextFileViewer] isMarkdown:', result, 'fileType:', props.fileType)
  return result
})

// isPlainText removed - unused in template

// Line numbers for plain text and JSON
const lines = computed(() => {
  if (isMarkdown.value) return []
  return renderedContent.value.split('\n')
})

// Copy to clipboard
async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(props.content)
    isCopied.value = true
    toast.success('Copied to clipboard!')

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
  <div class="relative h-full flex flex-col">
    <!-- Toolbar -->
    <div class="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
      <div class="flex items-center gap-2">
        <span class="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
          {{ fileType.toUpperCase() }}
        </span>
        <span v-if="isMarkdown" class="text-xs text-gray-500">Markdown Preview</span>
        <span v-else-if="isJson" class="text-xs text-gray-500">Pretty Printed JSON</span>
        <span v-else class="text-xs text-gray-500">Plain Text</span>
      </div>

      <button
        @click="copyToClipboard"
        class="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        :class="{ 'bg-green-50 border-green-300 text-green-700': isCopied }"
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

    <!-- Content Area -->
    <div class="flex-1 overflow-auto">
      <!-- Markdown Rendered HTML -->
      <div
        v-if="isMarkdown"
        class="prose prose-sm max-w-none p-6 markdown-body"
        v-html="renderedContent"
      />

      <!-- JSON and Plain Text with Line Numbers -->
      <div v-else class="flex h-full">
        <!-- Line Numbers -->
        <div class="flex-shrink-0 px-4 py-4 bg-gray-50 border-r border-gray-200 select-none">
          <div class="font-mono text-xs text-gray-400 leading-6 text-right">
            <div v-for="(_, index) in lines" :key="index">
              {{ index + 1 }}
            </div>
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 px-4 py-4 overflow-auto">
          <pre
            class="font-mono text-sm leading-6 text-gray-800 whitespace-pre"
            :class="{ 'text-blue-900': isJson }"
          >{{ renderedContent }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Markdown styles */
.markdown-body {
  color: #24292e;
  line-height: 1.6;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body h1 {
  font-size: 2em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body h2 {
  font-size: 1.5em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body p {
  margin-top: 0;
  margin-bottom: 16px;
}

.markdown-body code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
}

.markdown-body pre {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 3px;
}

.markdown-body pre code {
  padding: 0;
  margin: 0;
  background-color: transparent;
  border-radius: 0;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 16px;
}

.markdown-body li {
  margin-bottom: 0.25em;
}

.markdown-body blockquote {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin-top: 0;
  margin-bottom: 16px;
}

.markdown-body table {
  border-spacing: 0;
  border-collapse: collapse;
  margin-top: 0;
  margin-bottom: 16px;
  width: 100%;
}

.markdown-body table th,
.markdown-body table td {
  padding: 6px 13px;
  border: 1px solid #dfe2e5;
}

.markdown-body table th {
  font-weight: 600;
  background-color: #f6f8fa;
}

.markdown-body table tr {
  background-color: #fff;
  border-top: 1px solid #c6cbd1;
}

.markdown-body table tr:nth-child(2n) {
  background-color: #f6f8fa;
}

.markdown-body a {
  color: #0366d6;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body img {
  max-width: 100%;
  box-sizing: content-box;
}

.markdown-body hr {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: #e1e4e8;
  border: 0;
}
</style>
