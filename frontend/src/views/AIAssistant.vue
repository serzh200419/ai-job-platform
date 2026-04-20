<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import Button from '../components/Button.vue'
import Loader from '../components/Loader.vue'
import {
  createChatSession, getChatSessions, sendChatMessage,
  type ChatSession, type ChatMessage,
} from '../services/api'

// ── State ─────────────────────────────────────────────────────────────────────
const session = ref<ChatSession | null>(null)
const messages = ref<ChatMessage[]>([])
const input = ref('')
const sending = ref(false)
const initializing = ref(true)
const messagesEnd = ref<HTMLElement | null>(null)
const error = ref('')

const suggestions = [
  'Find remote frontend jobs',
  'Review my resume tips',
  'Help me write a cover letter',
  'Interview tips for tech roles',
]

// ── Init ──────────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    // Reuse last session or create new one
    const sessions = await getChatSessions().catch(() => [])
    if (Array.isArray(sessions) && sessions.length) {
      const last = sessions[0] as ChatSession
      session.value = last
      messages.value = last.messages ?? []
    } else {
      const newSession = await createChatSession()
      session.value = newSession
      messages.value = []
    }
  } catch {
    error.value = 'Failed to start chat session.'
  } finally {
    initializing.value = false
    await scrollDown()
  }
})

// ── Send ──────────────────────────────────────────────────────────────────────
async function send(text?: string) {
  const msg = (text || input.value).trim()
  if (!msg || !session.value || sending.value) return
  input.value = ''
  sending.value = true
  error.value = ''

  // Optimistic user message
  const tempId = `temp-${Date.now()}`
  messages.value.push({
    id: tempId,
    sender: 'user',
    message: msg,
    created_at: new Date().toISOString(),
  })
  await scrollDown()

  try {
    const { user_message, ai_message } = await sendChatMessage(session.value.id, msg)

    // Replace temp message with real one from server
    const idx = messages.value.findIndex((m) => m.id === tempId)
    if (idx !== -1) messages.value[idx] = user_message
    messages.value.push(ai_message)
  } catch {
    // Remove temp message on failure
    messages.value = messages.value.filter((m) => m.id !== tempId)
    error.value = 'Failed to send message. Please try again.'
  } finally {
    sending.value = false
    await scrollDown()
  }
}

async function newSession() {
  initializing.value = true
  try {
    const s = await createChatSession()
    session.value = s
    messages.value = []
  } finally {
    initializing.value = false
  }
}

async function scrollDown() {
  await nextTick()
  messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
}

function formatTime(dateStr: string) {
  return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <AppLayout>
    <template #title>AI Assistant</template>

    <div class="flex flex-col max-w-3xl mx-auto" style="height: calc(100vh - 112px)">

      <Loader v-if="initializing" :center="true" size="lg" />

      <div v-else class="flex-1 bg-white rounded-2xl border border-slate-100 shadow-sm flex flex-col overflow-hidden">
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-slate-100 shrink-0">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-sm">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <p class="text-sm font-semibold text-slate-800">JobAI Assistant</p>
              <p class="text-xs text-emerald-500 font-medium flex items-center gap-1">
                <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full inline-block" />
                Online
              </p>
            </div>
          </div>
          <button
            @click="newSession"
            class="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1.5 transition-colors"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            New chat
          </button>
        </div>

        <!-- Messages -->
        <div class="flex-1 overflow-y-auto p-5 flex flex-col gap-4 min-h-0">
          <!-- Welcome message when empty -->
          <div v-if="!messages.length" class="flex gap-3">
            <div class="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-bold text-indigo-600 shrink-0">AI</div>
            <div class="max-w-[80%]">
              <div class="px-4 py-3 bg-slate-50 border border-slate-100 rounded-2xl rounded-tl-sm text-sm text-slate-700 leading-relaxed">
                Hi! I'm your AI job assistant. I can help you find jobs, improve your resume, prepare for interviews, or answer career questions. What would you like to work on?
              </div>
            </div>
          </div>

          <TransitionGroup name="msg">
            <div
              v-for="msg in messages"
              :key="msg.id"
              :class="['flex gap-3', msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row']"
            >
              <div
                :class="[
                  'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5',
                  msg.sender === 'ai' ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-200 text-slate-600',
                ]"
              >
                {{ msg.sender === 'ai' ? 'AI' : 'U' }}
              </div>
              <div :class="['max-w-[80%] flex flex-col gap-1', msg.sender === 'user' ? 'items-end' : 'items-start']">
                <div
                  :class="[
                    'px-4 py-3 rounded-2xl text-sm leading-relaxed',
                    msg.sender === 'ai'
                      ? 'bg-slate-50 text-slate-700 rounded-tl-sm border border-slate-100'
                      : 'bg-indigo-600 text-white rounded-tr-sm',
                  ]"
                >
                  {{ msg.message }}
                </div>
                <p class="text-xs text-slate-400 px-1">{{ formatTime(msg.created_at) }}</p>
              </div>
            </div>
          </TransitionGroup>

          <!-- Typing indicator -->
          <div v-if="sending" class="flex gap-3">
            <div class="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-bold text-indigo-600 shrink-0">AI</div>
            <div class="px-4 py-3 bg-slate-50 border border-slate-100 rounded-2xl rounded-tl-sm">
              <span class="flex gap-1 items-center h-4">
                <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay:0ms" />
                <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay:150ms" />
                <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay:300ms" />
              </span>
            </div>
          </div>

          <div ref="messagesEnd" />
        </div>

        <!-- Suggestions (shown when empty) -->
        <div v-if="!messages.length" class="px-5 pb-3 flex flex-wrap gap-2 shrink-0">
          <button
            v-for="s in suggestions"
            :key="s"
            @click="send(s)"
            class="text-xs px-3 py-1.5 rounded-full border border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50 transition-all"
          >
            {{ s }}
          </button>
        </div>

        <!-- Error -->
        <div v-if="error" class="px-5 pb-2 shrink-0">
          <p class="text-xs text-red-500">{{ error }}</p>
        </div>

        <!-- Input bar -->
        <div class="border-t border-slate-100 p-4 flex gap-3 shrink-0">
          <input
            v-model="input"
            @keydown.enter.prevent="send()"
            :disabled="sending || !session"
            placeholder="Ask me anything about your job search…"
            class="flex-1 px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-slate-400 disabled:opacity-50"
          />
          <Button @click="send()" :disabled="!input.trim() || sending || !session" size="md">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </Button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.msg-enter-active { transition: all 0.2s ease; }
.msg-enter-from { opacity: 0; transform: translateY(8px); }
</style>
