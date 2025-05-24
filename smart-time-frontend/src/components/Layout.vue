<script setup>
import Navigation from './Navigation.vue'
</script>

<template>
  <div class="min-h-screen bg-gray-100 flex flex-col">
    <Navigation />
    <main class="flex-1 py-6">
      <div class="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 h-full">
        <slot></slot>
      </div>
    </main>
  </div>
</template>

<style>
/* Add custom scrollbar for better desktop experience */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
