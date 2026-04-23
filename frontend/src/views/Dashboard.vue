<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getCurrentUser } from '../services/auth'
import { getRecommended, refreshRecommended, type JobMatch } from '../services/api'
import AppLayout from '../components/AppLayout.vue'
import JobCard from '../components/JobCard.vue'
import Loader from '../components/Loader.vue'

const router = useRouter()
const user = ref<any>(null)
const matches = ref<JobMatch[]>([])
const loading = ref(true)
const refreshing = ref(false)
const error = ref('')
const lastUpdated = ref<string | null>(null)
const isStale = ref(true)

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 18) return 'Good afternoon'
  return 'Good evening'
})

const displayJobs = computed(() =>
  matches.value.slice(0, 6).map((m) => m.job)
)

const matchMap = computed(() => {
  const m: Record<string, number> = {}
  matches.value.forEach((match) => (m[match.job.id] = match.match_score))
  return m
})

const reasonMap = computed(() => {
  const m: Record<string, string> = {}
  matches.value.forEach((match) => (m[match.job.id] = match.reason))
  return m
})

const updatedAgo = computed(() => {
  if (!lastUpdated.value) return null
  const diff = Date.now() - new Date(lastUpdated.value).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
})

onMounted(async () => {
  try {
    const [userData, matchData] = await Promise.all([
      getCurrentUser(),
      getRecommended().catch(() => ({ results: [], last_updated: null, is_stale: true })),
    ])
    user.value = userData
    matches.value = matchData.results
    lastUpdated.value = matchData.last_updated
    isStale.value = matchData.is_stale
  } catch {
    error.value = 'Failed to load dashboard data.'
  } finally {
    loading.value = false
  }
})

async function doRefresh() {
  refreshing.value = true
  error.value = ''
  try {
    const data = await refreshRecommended()
    matches.value = data.results
    lastUpdated.value = data.last_updated
    isStale.value = false
  } catch {
    error.value = 'Matching service temporarily unavailable. Please try again.'
  } finally {
    refreshing.value = false
  }
}

function goToJob(id: string) {
  router.push(`/jobs/${id}`)
}
</script>

<template>
  <AppLayout>
    <template #title>Dashboard</template>

    <div v-if="loading" class="flex items-center justify-center h-64">
      <Loader size="lg" />
    </div>

    <div v-else-if="error && !matches.length" class="flex items-center justify-center h-64">
      <div class="text-center">
        <p class="text-red-500 font-medium">{{ error }}</p>
        <button @click="$router.go(0)" class="mt-3 text-sm text-indigo-600 hover:underline">Retry</button>
      </div>
    </div>

    <div v-else class="flex flex-col gap-6 max-w-6xl">
      <!-- Welcome banner -->
      <div class="relative bg-gradient-to-r from-indigo-600 to-indigo-500 rounded-2xl p-6 overflow-hidden">
        <div class="relative z-10">
          <p class="text-indigo-200 text-sm font-medium">{{ greeting }} 👋</p>
          <h2 class="text-white text-xl font-bold mt-1">
            Welcome back, {{ user?.full_name || user?.email?.split('@')[0] }}
          </h2>
          <p class="text-indigo-200 text-sm mt-1">
            <template v-if="matches.length">
              AI found <span class="text-white font-semibold">{{ matches.length }} job{{ matches.length !== 1 ? 's' : '' }}</span> matching your profile
            </template>
            <template v-else>
              Complete your profile to get AI-powered job matches
            </template>
          </p>
          <div class="flex gap-3 mt-4">
            <router-link
              to="/jobs"
              class="inline-flex items-center gap-1.5 px-4 py-2 bg-white text-indigo-600 text-sm font-semibold rounded-lg hover:bg-indigo-50 transition-colors"
            >
              Browse Jobs
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </router-link>
            <router-link
              v-if="!matches.length"
              to="/profile"
              class="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-700 text-white text-sm font-semibold rounded-lg hover:bg-indigo-800 transition-colors"
            >
              Complete Profile
            </router-link>
          </div>
        </div>
        <div class="absolute right-6 top-4 w-24 h-24 bg-white/10 rounded-full blur-2xl" />
        <div class="absolute right-16 bottom-2 w-16 h-16 bg-white/10 rounded-full blur-xl" />
      </div>

      <!-- Stats row -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white rounded-xl border border-slate-100 p-4 shadow-sm">
          <p class="text-xs text-slate-500 font-medium">Job Matches</p>
          <p class="text-2xl font-bold text-slate-800 mt-1">{{ matches.length }}</p>
          <p class="text-xs mt-1 font-medium text-indigo-500">AI-powered</p>
        </div>
        <div class="bg-white rounded-xl border border-slate-100 p-4 shadow-sm">
          <p class="text-xs text-slate-500 font-medium">Top Match</p>
          <p class="text-2xl font-bold text-slate-800 mt-1">
            {{ matches.length ? Math.round(matches[0].match_score * 100) + '%' : '—' }}
          </p>
          <p class="text-xs mt-1 font-medium text-emerald-600">Best score</p>
        </div>
        <div class="bg-white rounded-xl border border-slate-100 p-4 shadow-sm">
          <router-link to="/profile" class="block">
            <p class="text-xs text-slate-500 font-medium">Profile</p>
            <p class="text-2xl font-bold text-slate-800 mt-1">→</p>
            <p class="text-xs mt-1 font-medium text-amber-500">Update skills</p>
          </router-link>
        </div>
        <div class="bg-white rounded-xl border border-slate-100 p-4 shadow-sm">
          <router-link to="/ai" class="block">
            <p class="text-xs text-slate-500 font-medium">AI Assistant</p>
            <p class="text-2xl font-bold text-slate-800 mt-1">→</p>
            <p class="text-xs mt-1 font-medium text-indigo-500">Ask anything</p>
          </router-link>
        </div>
      </div>

      <!-- Job cards -->
      <div>
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="font-semibold text-slate-800">
              {{ matches.length ? 'Matched for you' : 'Latest Jobs' }}
            </h3>
            <p class="text-sm text-slate-500 mt-0.5">
              <template v-if="matches.length">
                Sorted by AI match score
                <span v-if="updatedAgo" class="text-slate-400"> · Updated {{ updatedAgo }}</span>
                <span v-if="isStale" class="ml-1.5 text-amber-500 text-xs font-medium">· outdated</span>
              </template>
              <template v-else>Browse all available positions</template>
            </p>
          </div>

          <div class="flex items-center gap-3">
            <!-- Refresh button -->
            <button
              v-if="matches.length || isStale"
              @click="doRefresh"
              :disabled="refreshing"
              class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-60"
              :class="isStale
                ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
            >
              <svg
                class="w-4 h-4"
                :class="{ 'animate-spin': refreshing }"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {{ refreshing ? 'Refreshing…' : 'Refresh Matches' }}
            </button>

            <router-link to="/jobs" class="text-sm font-medium text-indigo-600 hover:text-indigo-700">
              View all →
            </router-link>
          </div>
        </div>

        <!-- Refresh error inline -->
        <p v-if="error && matches.length" class="text-sm text-red-500 mb-3">{{ error }}</p>

        <!-- Empty state -->
        <div v-if="!displayJobs.length && !refreshing" class="text-center py-16 bg-white rounded-2xl border border-slate-100">
          <svg class="w-12 h-12 mx-auto mb-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <p class="text-slate-500 font-medium">No jobs available yet</p>
          <p class="text-sm text-slate-400 mt-1">Jobs posted by companies will appear here</p>
        </div>

        <!-- Refreshing overlay -->
        <div v-else-if="refreshing" class="flex items-center justify-center py-16">
          <Loader size="lg" />
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <JobCard
            v-for="job in displayJobs"
            :key="job.id"
            :job="job"
            :match-score="matchMap[job.id]"
            :match-reason="reasonMap[job.id]"
            @view="goToJob"
            @apply="goToJob"
          />
        </div>
      </div>
    </div>
  </AppLayout>
</template>
