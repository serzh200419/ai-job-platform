<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Sidebar from './Sidebar.vue'
import Navbar from './Navbar.vue'
import { getCurrentUser } from '../services/auth'

const user = ref<{ email: string } | null>(null)

onMounted(async () => {
  try {
    user.value = await getCurrentUser()
  } catch {
    // token expired / not logged in — router guard handles redirect
  }
})
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-slate-50">
    <Sidebar />
    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <Navbar :user="user">
        <template #title>
          <slot name="title" />
        </template>
      </Navbar>
      <main class="flex-1 overflow-y-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>
