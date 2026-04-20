<script setup lang="ts">
defineProps<{
  label?: string
  id?: string
  type?: string
  placeholder?: string
  error?: string
  autocomplete?: string
}>()

const model = defineModel<string>()
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="id" class="text-sm font-medium text-slate-700">
      {{ label }}
    </label>
    <input
      :id="id"
      :type="type ?? 'text'"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      v-model="model"
      :class="[
        'w-full px-3.5 py-2.5 text-sm text-slate-800 bg-white border rounded-lg transition-all duration-150',
        'placeholder:text-slate-400',
        'focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
        error
          ? 'border-red-400 focus:ring-red-400'
          : 'border-slate-200 hover:border-slate-300',
      ]"
    />
    <p v-if="error" class="text-xs text-red-500 flex items-center gap-1">
      <svg class="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
      </svg>
      {{ error }}
    </p>
  </div>
</template>
