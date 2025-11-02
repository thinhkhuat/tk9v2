<script setup lang="ts">
import { ref, onMounted } from 'vue'
import mammoth from 'mammoth'

const props = defineProps<{
  content: Uint8Array  // DOCX binary data
  filename?: string
}>()

const htmlContent = ref<string>('')
const isLoading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    // Convert Uint8Array to ArrayBuffer for mammoth
    // mammoth expects { arrayBuffer: ArrayBuffer }
    const arrayBuffer = props.content.buffer.slice(
      props.content.byteOffset,
      props.content.byteOffset + props.content.byteLength
    )

    // Convert DOCX to HTML using mammoth
    const result = await mammoth.convertToHtml({ arrayBuffer })
    htmlContent.value = result.value

    if (result.messages && result.messages.length > 0) {
      console.warn('Mammoth conversion warnings:', result.messages)
    }
  } catch (err: any) {
    console.error('Failed to convert DOCX:', err)
    error.value = err.message || 'Failed to convert DOCX file'
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="relative h-full flex flex-col bg-gray-50">
    <!-- Toolbar -->
    <div class="px-4 py-2 bg-white border-b border-gray-200">
      <div class="flex items-center justify-between">
        <span class="text-sm font-medium text-gray-700">Word Document Preview</span>
        <span class="text-sm text-gray-500 font-mono">{{ filename }}</span>
      </div>
    </div>

    <!-- Content Area -->
    <div class="flex-1 overflow-auto">
      <!-- Loading State -->
      <div v-if="isLoading" class="flex items-center justify-center h-full">
        <div class="text-center">
          <svg class="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-gray-600">Converting document...</p>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="flex items-center justify-center h-full">
        <div class="text-center max-w-md">
          <svg class="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">Conversion Failed</h3>
          <p class="text-gray-600">{{ error }}</p>
        </div>
      </div>

      <!-- Converted HTML Content -->
      <div v-else class="max-w-4xl mx-auto bg-white shadow-lg my-8">
        <div class="p-12 docx-content" v-html="htmlContent"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* DOCX content styling */
.docx-content {
  font-family: 'Calibri', 'Arial', sans-serif;
  font-size: 11pt;
  line-height: 1.5;
  color: #000;
}

.docx-content :deep(h1) {
  font-size: 24pt;
  font-weight: bold;
  margin-top: 12pt;
  margin-bottom: 12pt;
}

.docx-content :deep(h2) {
  font-size: 18pt;
  font-weight: bold;
  margin-top: 10pt;
  margin-bottom: 10pt;
}

.docx-content :deep(h3) {
  font-size: 14pt;
  font-weight: bold;
  margin-top: 8pt;
  margin-bottom: 8pt;
}

.docx-content :deep(p) {
  margin-top: 0;
  margin-bottom: 10pt;
}

.docx-content :deep(ul),
.docx-content :deep(ol) {
  margin: 10pt 0;
  padding-left: 40pt;
}

.docx-content :deep(li) {
  margin-bottom: 5pt;
}

.docx-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 10pt 0;
}

.docx-content :deep(table td),
.docx-content :deep(table th) {
  border: 1px solid #000;
  padding: 5pt;
}

.docx-content :deep(table th) {
  background-color: #f0f0f0;
  font-weight: bold;
}

.docx-content :deep(strong),
.docx-content :deep(b) {
  font-weight: bold;
}

.docx-content :deep(em),
.docx-content :deep(i) {
  font-style: italic;
}

.docx-content :deep(u) {
  text-decoration: underline;
}
</style>
