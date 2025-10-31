<script setup lang="ts">
import ProgressTrackerSkeleton from './ProgressTrackerSkeleton.vue'
import FileExplorerSkeleton from './FileExplorerSkeleton.vue'
import LogViewerSkeleton from './LogViewerSkeleton.vue'
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Left Column - Progress and Files -->
    <div class="lg:col-span-2 space-y-6">
      <ProgressTrackerSkeleton />
      <FileExplorerSkeleton />
    </div>

    <!-- Right Column - Logs -->
    <div class="lg:col-span-1">
      <LogViewerSkeleton />
    </div>
  </div>
</template>

<!--
  AppSkeletonLoader - Composite skeleton for initial page load
  Phase 3: Provides smooth loading experience during session rehydration
-->
