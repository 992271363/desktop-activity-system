<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import TopBar from '@/components/TopBar.vue'

const route = useRoute()
</script>
<template>
  <TopBar v-if="!route.meta.hideTopBar" />
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
