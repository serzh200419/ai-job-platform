import api from '../api/axios'

// ── Shared types ──────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ApiUser {
  id: string
  email: string
  full_name: string
  phone: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Profile {
  id: string
  user: ApiUser
  profession: string
  summary: string
  years_experience: number
  desired_salary: string | null
  location: string
  created_at: string
}

export interface Skill {
  id: string
  skill_name: string
  skill_level: 'beginner' | 'intermediate' | 'advanced'
}

export interface Education {
  id: string
  institution: string
  degree: string
  field_of_study: string
  start_date: string
  end_date: string | null
}

export interface Experience {
  id: string
  company: string
  position: string
  description: string
  start_date: string
  end_date: string | null
}

export interface Company {
  id: string
  name: string
  industry: string
  description?: string
  location?: string
  website?: string
}

export interface JobSkill {
  id: string
  skill_name: string
}

export interface Salary {
  min: string | null
  max: string | null
}

export interface Job {
  id: string
  title: string
  company: Company
  description?: string
  requirements?: string
  salary: Salary
  location: string
  job_type: 'remote' | 'onsite' | 'hybrid'
  skills?: JobSkill[]
  created_at: string
}

export interface JobMatch {
  id: string
  job: Job
  match_score: number
  reason: string
  calculated_at: string
}

export interface ChatMessage {
  id: string
  sender: 'user' | 'ai'
  message: string
  created_at: string
}

export interface ChatSession {
  id: string
  started_at: string
  messages: ChatMessage[]
}

export interface CoverLetter {
  id: string
  job: string
  job_title: string
  company_name: string
  generated_text: string
  created_at: string
}

// ── Helpers ───────────────────────────────────────────────────────────────────

export function formatSalary(salary: Salary): string {
  const fmt = (n: string) => {
    const num = parseFloat(n)
    return `$${(num / 1000).toFixed(0)}k`
  }
  if (!salary.min && !salary.max) return 'Salary not listed'
  if (salary.min && salary.max) return `${fmt(salary.min)} – ${fmt(salary.max)}`
  if (salary.min) return `From ${fmt(salary.min)}`
  return `Up to ${fmt(salary.max!)}`
}

export function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const days = Math.floor(diff / 86_400_000)
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days} days ago`
  if (days < 30) return `${Math.floor(days / 7)}w ago`
  return `${Math.floor(days / 30)}mo ago`
}

// ── Profile ───────────────────────────────────────────────────────────────────

export const getProfile = () => api.get<Profile>('/auth/profile/')
export const updateProfile = (data: Partial<Omit<Profile, 'id' | 'user' | 'created_at'>>) =>
  api.put<Profile>('/auth/profile/', data)

// ── Skills ────────────────────────────────────────────────────────────────────

export const getSkills = () =>
  api.get<PaginatedResponse<Skill>>('/auth/skills/').then((r) => r.data.results)
export const createSkill = (data: Omit<Skill, 'id'>) =>
  api.post<Skill>('/auth/skills/', data).then((r) => r.data)
export const deleteSkill = (id: string) => api.delete(`/auth/skills/${id}/`)
export const updateSkill = (id: string, data: Pick<Skill, 'skill_level'>) =>
  api.patch<Skill>(`/auth/skills/${id}/`, data).then((r) => r.data)

// ── Education ─────────────────────────────────────────────────────────────────

export const getEducation = () =>
  api.get<PaginatedResponse<Education>>('/auth/education/').then((r) => r.data.results)
export const createEducation = (data: Omit<Education, 'id'>) =>
  api.post<Education>('/auth/education/', data).then((r) => r.data)
export const deleteEducation = (id: string) => api.delete(`/auth/education/${id}/`)

// ── Experience ────────────────────────────────────────────────────────────────

export const getExperience = () =>
  api.get<PaginatedResponse<Experience>>('/auth/experience/').then((r) => r.data.results)
export const createExperience = (data: Omit<Experience, 'id'>) =>
  api.post<Experience>('/auth/experience/', data).then((r) => r.data)
export const deleteExperience = (id: string) => api.delete(`/auth/experience/${id}/`)

// ── Jobs ──────────────────────────────────────────────────────────────────────

export const getJobs = (params?: Record<string, string>) =>
  api.get<PaginatedResponse<Job>>('/jobs/', { params }).then((r) => r.data)
export const getJobById = (id: string) => api.get<Job>(`/jobs/${id}/`).then((r) => r.data)
export const getCompanies = () =>
  api.get<PaginatedResponse<Company>>('/companies/').then((r) => r.data.results)

// ── Matching ──────────────────────────────────────────────────────────────────

export interface MatchesResponse {
  results: JobMatch[]
  last_updated: string | null
  is_stale: boolean
}

export const getMatches = () =>
  api.get<MatchesResponse>('/matches/').then((r) => r.data)

export const refreshMatches = () =>
  api.post<MatchesResponse>('/matches/refresh/').then((r) => r.data)

// Cache-first recommended jobs (auto-triggers AI on cache miss)
export const getRecommended = () =>
  api.get<MatchesResponse>('/jobs/recommended/').then((r) => r.data)

export const refreshRecommended = () =>
  api.post<MatchesResponse>('/jobs/recommended/refresh/').then((r) => r.data)

// ── Chat ──────────────────────────────────────────────────────────────────────

export const createChatSession = () =>
  api.post<ChatSession>('/chat/session/').then((r) => r.data)
export const getChatSessions = () =>
  api.get<ChatSession[]>('/chat/session/').then((r) => r.data)
export const getChatSession = (sessionId: string) =>
  api.get<ChatSession>(`/chat/${sessionId}/`).then((r) => r.data)
export const sendChatMessage = (sessionId: string, message: string) =>
  api
    .post<{ user_message: ChatMessage; ai_message: ChatMessage }>('/chat/message/', {
      session_id: sessionId,
      message,
    })
    .then((r) => r.data)

// ── Documents ─────────────────────────────────────────────────────────────────

export const createCoverLetter = (jobId: string) =>
  api.post<CoverLetter>('/cover-letter/', { job: jobId }).then((r) => r.data)
export const getCoverLetters = () =>
  api.get<PaginatedResponse<CoverLetter>>('/cover-letter/').then((r) => r.data.results)
