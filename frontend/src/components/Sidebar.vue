<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const links = [
  {
    label: 'Dashboard',
    to: '/dashboard',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />`,
  },
  {
    label: 'Jobs',
    to: '/jobs',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />`,
  },
  {
    label: 'AI Assistant',
    to: '/ai',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />`,
  },
  {
    label: 'Profile',
    to: '/profile',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />`,
  },
]

function isActive(to: string) {
  return route.path === to || route.path.startsWith(to + '/')
}
</script>

<template>
  <aside class="flex flex-col w-60 min-h-screen bg-white border-r border-slate-100 shrink-0">
    <!-- Logo -->
    <div class="flex items-center gap-2.5 px-5 h-16 border-b border-slate-100">
      <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
        <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </div>
      <span class="font-bold text-slate-800 text-base tracking-tight">JobAI</span>
    </div>

    <!-- Navigation -->
    <nav class="flex flex-col gap-1 p-3 flex-1">
      <p class="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">Menu</p>
      <router-link
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        :class="[
          'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150',
          isActive(link.to)
            ? 'bg-indigo-50 text-indigo-600'
            : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800',
        ]"
      >
        <svg
          class="w-5 h-5 shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          v-html="link.icon"
        />
        {{ link.label }}
        <span
          v-if="link.label === 'AI Assistant'"
          class="ml-auto text-xs bg-indigo-100 text-indigo-600 px-1.5 py-0.5 rounded-full font-semibold"
        >
          NEW
        </span>
      </router-link>
    </nav>

    <!-- Bottom -->
    <div class="p-3 border-t border-slate-100">
      <div class="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-indigo-50">
        <div class="w-7 h-7 rounded-full bg-indigo-200 flex items-center justify-center text-indigo-700 text-xs font-bold shrink-0">
          U
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-xs font-semibold text-slate-700 truncate">My Account</p>
          <p class="text-xs text-slate-400">Free Plan</p>
        </div>
      </div>
    </div>
  </aside>
</template>
