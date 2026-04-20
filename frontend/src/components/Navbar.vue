<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { logout } from '../services/auth'

defineProps<{ user?: { email: string } | null }>()

const router = useRouter()
const dropdownOpen = ref(false)

function handleLogout() {
  logout()
  router.push('/login')
}

function getInitials(email: string) {
  return email.charAt(0).toUpperCase()
}
</script>

<template>
  <header class="h-16 bg-white border-b border-slate-100 flex items-center justify-between px-6 shrink-0">
    <!-- Page title slot -->
    <div class="text-sm font-semibold text-slate-700">
      <slot name="title">Dashboard</slot>
    </div>

    <!-- Right actions -->
    <div class="flex items-center gap-3">
      <!-- Notifications -->
      <button class="relative p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <span class="absolute top-1.5 right-1.5 w-2 h-2 bg-indigo-500 rounded-full" />
      </button>

      <!-- Profile dropdown -->
      <div class="relative" @click.outside="dropdownOpen = false">
        <button
          @click="dropdownOpen = !dropdownOpen"
          class="flex items-center gap-2.5 pl-1 pr-3 py-1 rounded-xl hover:bg-slate-100 transition-colors"
        >
          <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 text-sm font-bold">
            {{ user ? getInitials(user.email) : 'U' }}
          </div>
          <span class="text-sm font-medium text-slate-700 hidden sm:block">
            {{ user?.email?.split('@')[0] || 'User' }}
          </span>
          <svg
            class="w-4 h-4 text-slate-400 transition-transform duration-150"
            :class="dropdownOpen ? 'rotate-180' : ''"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Dropdown menu -->
        <Transition
          enter-active-class="transition ease-out duration-100"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition ease-in duration-75"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="dropdownOpen"
            class="absolute right-0 top-full mt-2 w-52 bg-white rounded-xl border border-slate-100 shadow-lg z-50 overflow-hidden"
          >
            <div class="px-4 py-3 border-b border-slate-100">
              <p class="text-xs font-semibold text-slate-800">{{ user?.email?.split('@')[0] }}</p>
              <p class="text-xs text-slate-400 mt-0.5 truncate">{{ user?.email }}</p>
            </div>
            <div class="p-1.5">
              <router-link
                to="/profile"
                @click="dropdownOpen = false"
                class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition-colors"
              >
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Profile
              </router-link>
              <button
                @click="handleLogout"
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 transition-colors"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Sign out
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </header>
</template>
