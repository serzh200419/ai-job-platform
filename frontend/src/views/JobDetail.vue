<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getJobById, createCoverLetter, formatSalary, timeAgo, type Job } from '../services/api'
import AppLayout from '../components/AppLayout.vue'
import Button from '../components/Button.vue'
import Loader from '../components/Loader.vue'

const route = useRoute()
const router = useRouter()
const job = ref<Job | null>(null)
const loading = ref(true)
const applying = ref(false)
const applied = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    job.value = await getJobById(route.params.id as string)
  } catch {
    error.value = 'Job not found.'
  } finally {
    loading.value = false
  }
})

async function handleApply() {
  if (!job.value) return
  applying.value = true
  try {
    await createCoverLetter(job.value.id)
    applied.value = true
  } catch {
    // cover letter generation is optional — mark as applied anyway
    applied.value = true
  } finally {
    applying.value = false
  }
}

const jobTypeColors: Record<string, string> = {
  remote: 'bg-emerald-50 text-emerald-600',
  onsite: 'bg-blue-50 text-blue-600',
  hybrid: 'bg-purple-50 text-purple-600',
}
</script>

<template>
  <AppLayout>
    <template #title>Job Details</template>

    <Loader v-if="loading" :center="true" size="lg" />

    <div v-else-if="error" class="text-center py-20">
      <p class="text-slate-500">{{ error }}</p>
      <button @click="router.back()" class="mt-3 text-sm text-indigo-600 hover:underline">← Go back</button>
    </div>

    <div v-else-if="job" class="max-w-3xl flex flex-col gap-5">
      <!-- Back -->
      <button @click="router.back()" class="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors w-fit">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Back to jobs
      </button>

      <!-- Header card -->
      <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <div class="flex items-start justify-between gap-4">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-100 to-indigo-50 flex items-center justify-center text-indigo-600 font-bold text-2xl shrink-0">
              {{ job.company.name.charAt(0) }}
            </div>
            <div>
              <h1 class="text-xl font-bold text-slate-800">{{ job.title }}</h1>
              <p class="text-slate-500 mt-0.5">{{ job.company.name }}</p>
              <p v-if="job.company.industry" class="text-xs text-slate-400 mt-0.5">{{ job.company.industry }}</p>
            </div>
          </div>
          <span :class="['text-xs font-semibold px-3 py-1.5 rounded-full capitalize shrink-0', jobTypeColors[job.job_type] ?? 'bg-slate-100 text-slate-600']">
            {{ job.job_type }}
          </span>
        </div>

        <!-- Meta row -->
        <div class="flex flex-wrap gap-4 mt-5 pt-5 border-t border-slate-100 text-sm text-slate-600">
          <span v-if="job.location" class="flex items-center gap-1.5">
            <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {{ job.location }}
          </span>
          <span class="flex items-center gap-1.5">
            <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ formatSalary(job.salary) }}
          </span>
          <span class="flex items-center gap-1.5 text-slate-400">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Posted {{ timeAgo(job.created_at) }}
          </span>
        </div>

        <!-- CTA -->
        <div class="mt-5 flex gap-3">
          <Button
            v-if="!applied"
            @click="handleApply"
            :loading="applying"
            size="lg"
          >
            Apply Now
          </Button>
          <div v-else class="flex items-center gap-2 text-emerald-600 font-semibold">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            Application submitted!
          </div>
          <router-link to="/ai">
            <Button variant="secondary" size="lg">Ask AI for tips</Button>
          </router-link>
        </div>
      </div>

      <!-- Skills -->
      <div v-if="job.skills?.length" class="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <h2 class="font-semibold text-slate-800 mb-3">Required Skills</h2>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="skill in job.skills"
            :key="skill.id"
            class="px-3 py-1.5 text-sm bg-indigo-50 text-indigo-700 rounded-lg font-medium"
          >
            {{ skill.skill_name }}
          </span>
        </div>
      </div>

      <!-- Description -->
      <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <h2 class="font-semibold text-slate-800 mb-3">About this role</h2>
        <p class="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">{{ job.description }}</p>
      </div>

      <!-- Requirements -->
      <div v-if="job.requirements" class="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <h2 class="font-semibold text-slate-800 mb-3">Requirements</h2>
        <p class="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">{{ job.requirements }}</p>
      </div>
    </div>
  </AppLayout>
</template>
