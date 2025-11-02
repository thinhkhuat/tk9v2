<!--
  FileIcon.vue - Generic File Type Icon Component

  Displays different file type icons based on the type prop
  Replaces emoji-based file icons with proper SVG components
-->

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  type: string | undefined | null
  size?: 'sm' | 'md' | 'lg'
}>(), {
  size: 'md',
  type: 'unknown'
})

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  }
  return sizes[props.size]
})

const fileType = computed(() => (props.type || 'unknown').toLowerCase())
</script>

<template>
  <!-- PDF Icon -->
  <svg
    v-if="fileType === 'pdf'"
    :class="sizeClasses"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    class="text-red-500"
  >
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 3h4" />
  </svg>

  <!-- DOCX/DOC Icon -->
  <svg
    v-else-if="fileType === 'docx' || fileType === 'doc'"
    :class="sizeClasses"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    class="text-blue-600"
  >
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>

  <!-- Markdown Icon -->
  <svg
    v-else-if="fileType === 'md' || fileType === 'markdown'"
    :class="sizeClasses"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    class="text-purple-600"
  >
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10l1.5 1.5L12 10" />
  </svg>

  <!-- Text Icon -->
  <svg
    v-else-if="fileType === 'txt'"
    :class="sizeClasses"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    class="text-gray-600"
  >
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>

  <!-- JSON Icon -->
  <svg
    v-else-if="fileType === 'json'"
    :class="sizeClasses"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    class="text-yellow-600"
  >
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
  </svg>

  <!-- XML/HTML Icon -->
  <svg
    v-else-if="fileType === 'xml' || fileType === 'html'"
    :class="sizeClasses"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    class="text-orange-600"
  >
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
  </svg>

  <!-- Default/Unknown File Icon -->
  <svg
    v-else
    :class="sizeClasses"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    class="text-gray-500"
  >
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
  </svg>
</template>
