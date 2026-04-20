<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getJobs, type Job } from '../services/api'
import AppLayout from '../components/AppLayout.vue'
import JobCard from '../components/JobCard.vue'
import InputField from '../components/InputField.vue'
import Loader from '../components/Loader.vue'

const router = useRouter()
const jobs = ref<Job[]>([])
const loading = ref(true)
const error = ref('')
const total = ref(0)

const search = ref('')
const selectedType = ref('all')
const types = [
  { label: 'All', value: 'all' },
  { label: 'Remote', value: 'remote' },
  { label: 'On-site', value: 'onsite' },
  { label: 'Hybrid', value: 'hybrid' },
]

// Debounced search
let searchTimer: ReturnType<typeof setTimeout>
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(fetchJobs, 350)
})

watch(selectedType, fetchJobs)

async function fetchJobs() {
  loading.value = true
  error.value = ''
  try {
    const params: Record<string, string> = {}
    if (search.value) params.search = search.value
    if (selectedType.value !== 'all') params.type = selectedType.value
    const data = await getJobs(params)
    jobs.value = data.results
    total.value = data.count
  } catch {
    error.value = 'Failed to load jobs. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchJobs)

function goToJob(id: string) {
  router.push(`/jobs/${id}`)
}
</script>

<template>
  <AppLayout>
    <template #title>Browse Jobs</template>

    <div class="flex flex-col gap-5 max-w-6xl">
      <!-- Search + filters -->
      <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-4 flex flex-col sm:flex-row gap-3">
        <div class="flex-1">
          <InputField placeholder="Search by title, company…" v-model="search" />
        </div>
        <div class="flex gap-2 flex-wrap">
          <button
            v-for="t in types"
            :key="t.value"
            @click="selectedType = t.value"
            :class="[
              'px-3.5 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap',
              selectedType === t.value
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200',
            ]"
          >
            {{ t.label }}
          </button>
        </div>
      </div>

      <!-- Status line -->
      <p v-if="!loading" class="text-sm text-slate-500 -mb-1">
        Showing <span class="font-semibold text-slate-700">{{ jobs.length }}</span>
        of <span class="font-semibold text-slate-700">{{ total }}</span> jobs
      </p>

      <!-- Loading -->
      <Loader v-if="loading" :center="true" size="lg" />

      <!-- Error -->
      <div v-else-if="error" class="text-center py-12 bg-white rounded-2xl border border-slate-100">
        <p class="text-red-500 font-medium">{{ error }}</p>
        <button @click="fetchJobs" class="mt-3 text-sm text-indigo-600 hover:underline">Retry</button>
      </div>

      <!-- Grid -->
      <div v-else-if="jobs.length" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <JobCard
          v-for="job in jobs"
          :key="job.id"
          :job="job"
          @view="goToJob"
          @apply="goToJob"
        />
      </div>

      <!-- Empty state -->
      <div v-else class="text-center py-16 bg-white rounded-2xl border border-slate-100">
        <svg class="w-12 h-12 mx-auto mb-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <p class="font-medium text-slate-500">No jobs found</p>
        <p class="text-sm text-slate-400 mt-1">Try a different search or filter</p>
        <button @click="search = ''; selectedType = 'all'" class="mt-3 text-sm text-indigo-600 hover:underline">
          Clear filters
        </button>
      </div>
    </div>
  </AppLayout>
</template>
