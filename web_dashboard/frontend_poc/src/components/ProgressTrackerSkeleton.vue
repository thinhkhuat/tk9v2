<template>
  <div class="bg-white p-6 rounded-lg shadow-md animate-pulse">
    <!-- Title skeleton -->
    <div class="h-6 bg-gray-200 rounded-md w-1/3 mb-6"></div>

    <!-- Progress bar skeleton -->
    <div class="h-4 bg-gray-200 rounded-full w-full mb-6"></div>

    <!-- Agent list skeletons -->
    <div class="space-y-4">
      <div v-for="i in 8" :key="i" class="flex items-center space-x-3">
        <!-- Agent icon/status -->
        <div class="h-8 w-8 bg-gray-200 rounded-full flex-shrink-0"></div>
        <!-- Agent name -->
        <div class="h-4 w-32 bg-gray-200 rounded-md"></div>
        <!-- Agent progress bar -->
        <div class="flex-1 h-3 bg-gray-200 rounded-full"></div>
        <!-- Percentage -->
        <div class="h-4 w-12 bg-gray-200 rounded-md"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Skeleton loader for ProgressTracker component
// Phase 3: Enhanced UX with loading states
</script>
