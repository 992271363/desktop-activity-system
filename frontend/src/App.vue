<script setup lang="ts">
import { RouterView } from 'vue-router'
import TopBar from '@/components/TopBar.vue'
</script>
<template>
  <TopBar />
  <main class="main-content">
    <RouterView />
  </main>
</template>
<style>
.main-content {
  padding-top: 64px;
  width: 100%;
}
</style>
