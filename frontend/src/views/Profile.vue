<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import InputField from '../components/InputField.vue'
import Button from '../components/Button.vue'
import Loader from '../components/Loader.vue'
import {
  getProfile, updateProfile, getSkills, createSkill, deleteSkill,
  getEducation, createEducation, deleteEducation,
  getExperience, createExperience, deleteExperience,
  type Profile, type Skill, type Education, type Experience,
} from '../services/api'
import { getCurrentUser } from '../services/auth'

// ── State ─────────────────────────────────────────────────────────────────────
const user = ref<any>(null)
const profile = ref<Profile | null>(null)
const skills = ref<Skill[]>([])
const education = ref<Education[]>([])
const experience = ref<Experience[]>([])
const loading = ref(true)
const saving = ref(false)
const saved = ref(false)
const error = ref('')

// Profile form
const form = reactive({
  profession: '',
  summary: '',
  years_experience: 0,
  desired_salary: '',
  location: '',
})

// Skill form
const skillForm = reactive({ skill_name: '', skill_level: 'intermediate' as Skill['skill_level'] })
const addingSkill = ref(false)
const showSkillForm = ref(false)

// Education form
const eduForm = reactive({ institution: '', degree: '', field_of_study: '', start_date: '', end_date: '' })
const addingEdu = ref(false)
const showEduForm = ref(false)

// Experience form
const expForm = reactive({ company: '', position: '', description: '', start_date: '', end_date: '' })
const addingExp = ref(false)
const showExpForm = ref(false)

// ── Load ──────────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const [userData, profileData, skillsData, eduData, expData] = await Promise.all([
      getCurrentUser(),
      getProfile().then((r) => r.data),
      getSkills(),
      getEducation(),
      getExperience(),
    ])
    user.value = userData
    profile.value = profileData
    skills.value = skillsData
    education.value = eduData
    experience.value = expData

    Object.assign(form, {
      profession: profileData.profession,
      summary: profileData.summary,
      years_experience: profileData.years_experience,
      desired_salary: profileData.desired_salary ?? '',
      location: profileData.location,
    })
  } catch {
    error.value = 'Failed to load profile data.'
  } finally {
    loading.value = false
  }
})

// ── Profile save ──────────────────────────────────────────────────────────────
async function saveProfile() {
  saving.value = true
  try {
    const data = await updateProfile({
      profession: form.profession,
      summary: form.summary,
      years_experience: Number(form.years_experience),
      desired_salary: form.desired_salary || null,
      location: form.location,
    } as any)
    profile.value = data.data
    saved.value = true
    setTimeout(() => (saved.value = false), 2500)
  } catch {
    error.value = 'Failed to save profile.'
  } finally {
    saving.value = false
  }
}

// ── Skills ────────────────────────────────────────────────────────────────────
async function addSkill() {
  if (!skillForm.skill_name.trim()) return
  addingSkill.value = true
  try {
    const s = await createSkill({ skill_name: skillForm.skill_name.trim(), skill_level: skillForm.skill_level })
    skills.value.push(s)
    skillForm.skill_name = ''
    skillForm.skill_level = 'intermediate'
    showSkillForm.value = false
  } finally {
    addingSkill.value = false
  }
}

async function removeSkill(id: string) {
  await deleteSkill(id)
  skills.value = skills.value.filter((s) => s.id !== id)
}

// ── Education ─────────────────────────────────────────────────────────────────
async function addEdu() {
  addingEdu.value = true
  try {
    const e = await createEducation({
      institution: eduForm.institution,
      degree: eduForm.degree,
      field_of_study: eduForm.field_of_study,
      start_date: eduForm.start_date,
      end_date: eduForm.end_date || null,
    })
    education.value.push(e)
    Object.assign(eduForm, { institution: '', degree: '', field_of_study: '', start_date: '', end_date: '' })
    showEduForm.value = false
  } finally {
    addingEdu.value = false
  }
}

async function removeEdu(id: string) {
  await deleteEducation(id)
  education.value = education.value.filter((e) => e.id !== id)
}

// ── Experience ────────────────────────────────────────────────────────────────
async function addExp() {
  addingExp.value = true
  try {
    const e = await createExperience({
      company: expForm.company,
      position: expForm.position,
      description: expForm.description,
      start_date: expForm.start_date,
      end_date: expForm.end_date || null,
    })
    experience.value.push(e)
    Object.assign(expForm, { company: '', position: '', description: '', start_date: '', end_date: '' })
    showExpForm.value = false
  } finally {
    addingExp.value = false
  }
}

async function removeExp(id: string) {
  await deleteExperience(id)
  experience.value = experience.value.filter((e) => e.id !== id)
}

const levelBadge: Record<string, string> = {
  beginner: 'bg-slate-100 text-slate-600',
  intermediate: 'bg-blue-50 text-blue-600',
  advanced: 'bg-indigo-50 text-indigo-600',
}
</script>

<template>
  <AppLayout>
    <template #title>Profile</template>

    <Loader v-if="loading" :center="true" size="lg" />

    <div v-else class="max-w-2xl flex flex-col gap-5">

      <!-- Error banner -->
      <div v-if="error" class="bg-red-50 border border-red-100 text-red-600 text-sm rounded-xl px-4 py-3">
        {{ error }}
      </div>

      <!-- Avatar card -->
      <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 flex items-center gap-5">
        <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center text-white text-2xl font-bold shadow-sm shrink-0">
          {{ user?.full_name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() }}
        </div>
        <div>
          <p class="font-semibold text-slate-800">{{ user?.full_name || user?.email?.split('@')[0] }}</p>
          <p class="text-sm text-slate-500 mt-0.5">{{ user?.email }}</p>
          <p v-if="profile?.profession" class="text-sm text-indigo-600 mt-0.5 font-medium">{{ profile.profession }}</p>
          <span class="inline-block mt-2 text-xs px-2.5 py-0.5 bg-emerald-50 text-emerald-600 border border-emerald-100 rounded-full font-medium">
            Active account
          </span>
        </div>
      </div>

      <!-- ── Profile form ── -->
      <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <h3 class="font-semibold text-slate-800 mb-4">Profile Details</h3>
        <div class="flex flex-col gap-4">
          <InputField label="Profession" placeholder="e.g. Senior Frontend Developer" v-model="form.profession" />
          <div>
            <label class="text-sm font-medium text-slate-700 block mb-1.5">Summary</label>
            <textarea
              v-model="form.summary"
              rows="3"
              placeholder="Brief description about yourself…"
              class="w-full px-3.5 py-2.5 text-sm text-slate-800 bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none placeholder:text-slate-400"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <InputField label="Years of experience" type="number" v-model="form.years_experience" />
            <InputField label="Desired salary (USD/yr)" type="number" placeholder="e.g. 120000" v-model="form.desired_salary" />
          </div>
          <InputField label="Location" placeholder="e.g. New York, NY" v-model="form.location" />
        </div>
        <div class="flex items-center gap-3 mt-5 pt-5 border-t border-slate-100">
          <Button :loading="saving" @click="saveProfile">
            {{ saving ? 'Saving…' : 'Save profile' }}
          </Button>
          <Transition name="fade">
            <span v-if="saved" class="text-sm text-emerald-600 font-medium flex items-center gap-1.5">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              Saved!
            </span>
          </Transition>
        </div>
      </div>

      <!-- ── Skills ── -->
      <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-slate-800">Skills</h3>
          <button
            @click="showSkillForm = !showSkillForm"
            class="text-xs font-medium text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Add skill
          </button>
        </div>

        <!-- Add skill form -->
        <Transition name="fade">
          <div v-if="showSkillForm" class="flex gap-2 mb-4 flex-wrap">
            <input
              v-model="skillForm.skill_name"
              placeholder="Skill name (e.g. Python)"
              @keydown.enter="addSkill"
              class="flex-1 min-w-[140px] px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <select
              v-model="skillForm.skill_level"
              class="px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
            <Button @click="addSkill" :loading="addingSkill" size="sm">Add</Button>
            <Button @click="showSkillForm = false" variant="ghost" size="sm">Cancel</Button>
          </div>
        </Transition>

        <!-- Skills list -->
        <div v-if="skills.length" class="flex flex-wrap gap-2">
          <div
            v-for="skill in skills"
            :key="skill.id"
            class="group flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-100"
          >
            <span class="text-sm text-slate-700 font-medium">{{ skill.skill_name }}</span>
            <span :class="['text-xs px-1.5 py-0.5 rounded-md font-medium', levelBadge[skill.skill_level]]">
              {{ skill.skill_level }}
            </span>
            <button
              @click="removeSkill(skill.id)"
              class="ml-1 text-slate-300 hover:text-red-400 transition-colors"
            >
              <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
        <p v-else class="text-sm text-slate-400">No skills added yet.</p>
      </div>

      <!-- ── Education ── -->
      <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-slate-800">Education</h3>
          <button @click="showEduForm = !showEduForm" class="text-xs font-medium text-indigo-600 hover:text-indigo-700 flex items-center gap-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Add
          </button>
        </div>

        <Transition name="fade">
          <div v-if="showEduForm" class="flex flex-col gap-3 mb-4 p-4 bg-slate-50 rounded-xl border border-slate-100">
            <div class="grid grid-cols-2 gap-3">
              <InputField label="Institution" placeholder="University name" v-model="eduForm.institution" />
              <InputField label="Degree" placeholder="e.g. Bachelor's" v-model="eduForm.degree" />
            </div>
            <InputField label="Field of study" placeholder="e.g. Computer Science" v-model="eduForm.field_of_study" />
            <div class="grid grid-cols-2 gap-3">
              <InputField label="Start date" type="date" v-model="eduForm.start_date" />
              <InputField label="End date (optional)" type="date" v-model="eduForm.end_date" />
            </div>
            <div class="flex gap-2">
              <Button @click="addEdu" :loading="addingEdu" size="sm">Save</Button>
              <Button @click="showEduForm = false" variant="ghost" size="sm">Cancel</Button>
            </div>
          </div>
        </Transition>

        <div v-if="education.length" class="flex flex-col gap-3">
          <div
            v-for="edu in education"
            :key="edu.id"
            class="flex items-start justify-between gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100"
          >
            <div>
              <p class="text-sm font-semibold text-slate-800">{{ edu.degree }} — {{ edu.institution }}</p>
              <p v-if="edu.field_of_study" class="text-xs text-slate-500 mt-0.5">{{ edu.field_of_study }}</p>
              <p class="text-xs text-slate-400 mt-1">{{ edu.start_date }} – {{ edu.end_date || 'Present' }}</p>
            </div>
            <button @click="removeEdu(edu.id)" class="text-slate-300 hover:text-red-400 transition-colors shrink-0">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
        <p v-else class="text-sm text-slate-400">No education added yet.</p>
      </div>

      <!-- ── Experience ── -->
      <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-slate-800">Work Experience</h3>
          <button @click="showExpForm = !showExpForm" class="text-xs font-medium text-indigo-600 hover:text-indigo-700 flex items-center gap-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Add
          </button>
        </div>

        <Transition name="fade">
          <div v-if="showExpForm" class="flex flex-col gap-3 mb-4 p-4 bg-slate-50 rounded-xl border border-slate-100">
            <div class="grid grid-cols-2 gap-3">
              <InputField label="Company" placeholder="Company name" v-model="expForm.company" />
              <InputField label="Position" placeholder="e.g. Software Engineer" v-model="expForm.position" />
            </div>
            <div>
              <label class="text-sm font-medium text-slate-700 block mb-1.5">Description (optional)</label>
              <textarea
                v-model="expForm.description"
                rows="2"
                placeholder="Describe your responsibilities…"
                class="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none placeholder:text-slate-400"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <InputField label="Start date" type="date" v-model="expForm.start_date" />
              <InputField label="End date (optional)" type="date" v-model="expForm.end_date" />
            </div>
            <div class="flex gap-2">
              <Button @click="addExp" :loading="addingExp" size="sm">Save</Button>
              <Button @click="showExpForm = false" variant="ghost" size="sm">Cancel</Button>
            </div>
          </div>
        </Transition>

        <div v-if="experience.length" class="flex flex-col gap-3">
          <div
            v-for="exp in experience"
            :key="exp.id"
            class="flex items-start justify-between gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100"
          >
            <div>
              <p class="text-sm font-semibold text-slate-800">{{ exp.position }}</p>
              <p class="text-xs text-slate-500 mt-0.5 font-medium">{{ exp.company }}</p>
              <p v-if="exp.description" class="text-xs text-slate-500 mt-1">{{ exp.description }}</p>
              <p class="text-xs text-slate-400 mt-1">{{ exp.start_date }} – {{ exp.end_date || 'Present' }}</p>
            </div>
            <button @click="removeExp(exp.id)" class="text-slate-300 hover:text-red-400 transition-colors shrink-0">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
        <p v-else class="text-sm text-slate-400">No experience added yet.</p>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
