<script setup lang="ts">
import type { Job } from '../services/api'
import { formatSalary, timeAgo } from '../services/api'

defineProps<{ job: Job; matchScore?: number; matchReason?: string }>()
const emit = defineEmits<{ view: [id: string]; apply: [id: string] }>()
</script>

<template>
  <div
    class="group bg-white border border-slate-100 rounded-2xl p-5 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 flex flex-col gap-4 cursor-pointer"
    @click="emit('view', job.id)"
  >
    <!-- Header -->
    <div class="flex items-start justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-100 to-indigo-50 flex items-center justify-center text-indigo-600 font-bold text-lg shrink-0">
          {{ job.company.name.charAt(0) }}
        </div>
        <div>
          <h3 class="font-semibold text-slate-800 text-sm leading-tight group-hover:text-indigo-600 transition-colors">
            {{ job.title }}
          </h3>
          <p class="text-slate-500 text-xs mt-0.5">{{ job.company.name }}</p>
        </div>
      </div>
      <div class="flex flex-col items-end gap-1.5 shrink-0">
        <span class="text-xs font-medium px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-600 capitalize">
          {{ job.job_type }}
        </span>
        <span
          v-if="matchScore !== undefined"
          :class="[
            'text-xs font-semibold px-2 py-0.5 rounded-full',
            matchScore >= 0.8 ? 'bg-emerald-50 text-emerald-600' :
            matchScore >= 0.5 ? 'bg-amber-50 text-amber-600' :
            'bg-slate-100 text-slate-500'
          ]"
        >
          {{ Math.round(matchScore * 100) }}% match
        </span>
      </div>
    </div>

    <!-- Details -->
    <div class="flex flex-wrap gap-3 text-xs text-slate-500">
      <span v-if="job.location" class="flex items-center gap-1">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        {{ job.location }}
      </span>
      <span class="flex items-center gap-1">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {{ formatSalary(job.salary) }}
      </span>
    </div>

    <!-- AI reason -->
    <p v-if="matchReason" class="text-xs text-indigo-600 bg-indigo-50 rounded-lg px-3 py-1.5 leading-relaxed">
      {{ matchReason }}
    </p>

    <!-- Skills -->
    <div v-if="job.skills?.length" class="flex flex-wrap gap-1.5">
      <span
        v-for="skill in job.skills.slice(0, 4)"
        :key="skill.id"
        class="text-xs px-2 py-0.5 rounded-md bg-slate-100 text-slate-600"
      >
        {{ skill.skill_name }}
      </span>
      <span v-if="job.skills.length > 4" class="text-xs px-2 py-0.5 rounded-md bg-slate-100 text-slate-400">
        +{{ job.skills.length - 4 }}
      </span>
    </div>

    <!-- Footer -->
    <div class="flex items-center justify-between pt-1 border-t border-slate-50">
      <span class="text-xs text-slate-400">{{ timeAgo(job.created_at) }}</span>
      <button
        @click.stop="emit('apply', job.id)"
        class="text-xs font-medium px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors duration-150"
      >
        Apply Now
      </button>
    </div>
  </div>
</template>
