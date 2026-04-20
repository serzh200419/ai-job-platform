<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '../services/auth'
import InputField from '../components/InputField.vue'
import Button from '../components/Button.vue'

const router = useRouter()
const email = ref('')
const password = ref('')
const errors = ref<Record<string, string>>({})
const loading = ref(false)

async function handleSubmit() {
  errors.value = {}
  loading.value = true
  try {
    await register(email.value, password.value)
    router.push('/login')
  } catch (e: any) {
    const data = e.response?.data || {}
    if (data.email) errors.value.email = data.email[0]
    if (data.password) errors.value.password = data.password[0]
    if (data.detail) errors.value.global = data.detail
    if (!Object.keys(errors.value).length) errors.value.global = 'Registration failed.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="flex items-center justify-center gap-2.5 mb-8">
        <div class="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center shadow-md">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <span class="font-bold text-xl text-slate-800 tracking-tight">JobAI</span>
      </div>

      <!-- Card -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
        <div class="mb-6">
          <h1 class="text-xl font-bold text-slate-800">Create your account</h1>
          <p class="text-sm text-slate-500 mt-1">Start your AI-powered job search today</p>
        </div>

        <form @submit.prevent="handleSubmit" class="flex flex-col gap-4">
          <InputField
            id="email"
            label="Email address"
            type="email"
            placeholder="you@example.com"
            v-model="email"
            :error="errors.email"
          />
          <InputField
            id="password"
            label="Password"
            type="password"
            placeholder="Min. 8 characters"
            autocomplete="new-password"
            v-model="password"
            :error="errors.password"
          />

          <div
            v-if="errors.global"
            class="flex items-center gap-2 p-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-600"
          >
            <svg class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
            {{ errors.global }}
          </div>

          <Button type="submit" :loading="loading" :full="true" size="lg" class="mt-1">
            Create account
          </Button>
        </form>

        <p class="text-center text-sm text-slate-500 mt-5">
          Already have an account?
          <router-link to="/login" class="font-medium text-indigo-600 hover:text-indigo-700">
            Sign in
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>
