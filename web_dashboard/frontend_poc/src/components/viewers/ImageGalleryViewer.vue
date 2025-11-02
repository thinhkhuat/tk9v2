<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FileGeneratedPayload } from '@/types/events'

const props = defineProps<{
  file: FileGeneratedPayload
}>()

const zoom = ref(1)
const position = ref({ x: 0, y: 0 })
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const imageElement = ref<HTMLImageElement | null>(null)
const naturalDimensions = ref({ width: 0, height: 0 })

// Image URL (using the path from file payload)
const imageUrl = computed(() => props.file.path || '')

// Handle image load to get natural dimensions
function handleImageLoad(event: Event) {
  const img = event.target as HTMLImageElement
  naturalDimensions.value = {
    width: img.naturalWidth,
    height: img.naturalHeight
  }
}

// Zoom controls
function zoomIn() {
  zoom.value = Math.min(zoom.value + 0.25, 5)
}

function zoomOut() {
  zoom.value = Math.max(zoom.value - 0.25, 0.5)
}

function resetZoom() {
  zoom.value = 1
  position.value = { x: 0, y: 0 }
}

// Pan controls (drag to move when zoomed)
function startDrag(event: MouseEvent) {
  if (zoom.value <= 1) return // Only allow dragging when zoomed in

  isDragging.value = true
  dragStart.value = {
    x: event.clientX - position.value.x,
    y: event.clientY - position.value.y
  }
}

function onDrag(event: MouseEvent) {
  if (!isDragging.value) return

  position.value = {
    x: event.clientX - dragStart.value.x,
    y: event.clientY - dragStart.value.y
  }
}

function endDrag() {
  isDragging.value = false
}

// Mouse wheel zoom
function handleWheel(event: WheelEvent) {
  event.preventDefault()

  if (event.deltaY < 0) {
    zoomIn()
  } else {
    zoomOut()
  }
}

// Format file size
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
</script>

<template>
  <div class="relative h-full flex flex-col bg-gray-900">
    <!-- Toolbar -->
    <div class="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
      <div class="flex items-center gap-4">
        <!-- Zoom Controls -->
        <div class="flex items-center gap-2">
          <button
            @click="zoomOut"
            class="p-2 text-gray-300 hover:bg-gray-700 rounded"
            title="Zoom Out"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
            </svg>
          </button>

          <span class="text-sm text-gray-300 font-medium min-w-[60px] text-center">
            {{ Math.round(zoom * 100) }}%
          </span>

          <button
            @click="zoomIn"
            class="p-2 text-gray-300 hover:bg-gray-700 rounded"
            title="Zoom In"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
            </svg>
          </button>

          <button
            @click="resetZoom"
            class="px-3 py-1.5 text-sm text-gray-300 hover:bg-gray-700 rounded"
            title="Reset View"
          >
            Reset
          </button>
        </div>

        <!-- Image Info -->
        <div class="text-sm text-gray-400 border-l border-gray-700 pl-4">
          <span v-if="naturalDimensions.width">
            {{ naturalDimensions.width }} × {{ naturalDimensions.height }}
          </span>
          <span class="mx-2">•</span>
          <span>{{ formatBytes(file.size_bytes) }}</span>
        </div>
      </div>

      <div class="text-sm text-gray-400 font-mono">
        {{ file.filename }}
      </div>
    </div>

    <!-- Image Viewer -->
    <div
      class="flex-1 overflow-hidden flex items-center justify-center"
      :class="{ 'cursor-grab': zoom > 1 && !isDragging, 'cursor-grabbing': isDragging }"
      @mousedown="startDrag"
      @mousemove="onDrag"
      @mouseup="endDrag"
      @mouseleave="endDrag"
      @wheel="handleWheel"
    >
      <div
        class="transition-transform duration-200"
        :style="{
          transform: `scale(${zoom}) translate(${position.x / zoom}px, ${position.y / zoom}px)`,
          transformOrigin: 'center center'
        }"
      >
        <img
          ref="imageElement"
          :src="imageUrl"
          :alt="file.filename"
          class="max-w-full max-h-[calc(100vh-200px)] object-contain select-none"
          draggable="false"
          @load="handleImageLoad"
        />
      </div>
    </div>

    <!-- Help Text -->
    <div class="px-4 py-2 bg-gray-800 border-t border-gray-700">
      <p class="text-xs text-gray-400 text-center">
        Use mouse wheel to zoom • Drag to pan when zoomed • Click Reset to restore
      </p>
    </div>
  </div>
</template>

<style scoped>
/* Prevent text selection while dragging */
.cursor-grabbing * {
  user-select: none;
}
</style>
