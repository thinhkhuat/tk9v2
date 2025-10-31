<template>
  <div class="bg-white p-6 rounded-lg shadow-md animate-pulse">
    <!-- Title skeleton -->
    <div class="h-6 bg-gray-200 rounded-md w-1/4 mb-6"></div>

    <!-- File list skeletons -->
    <div class="space-y-3">
      <div v-for="i in 5" :key="i" class="flex items-center space-x-3 p-3 rounded-md bg-gray-50">
        <!-- File icon -->
        <div class="h-10 w-10 bg-gray-200 rounded-md flex-shrink-0"></div>
        <div class="flex-1">
          <!-- File name -->
          <div class="h-4 bg-gray-200 rounded-md w-3/4 mb-2"></div>
          <!-- File metadata -->
          <div class="h-3 bg-gray-200 rounded-md w-1/2"></div>
        </div>
        <!-- Download button -->
        <div class="h-8 w-20 bg-gray-200 rounded-md"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Skeleton loader for FileExplorer component
// Phase 3: Enhanced UX with loading states
</script>
