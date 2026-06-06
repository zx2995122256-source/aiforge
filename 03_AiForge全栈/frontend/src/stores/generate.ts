import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { get, post, del, upload } from '@/api'

export interface ModelInfo {
  name: string
  ratios?: string[]
  resolutions?: string[]
  durations?: number[]
  cost?: number
  cost_duration_scale?: Record<string, number>
  ref_max?: number
  video_ref?: boolean
}

export interface ModelsData {
  image: Record<string, ModelInfo>
  video: Record<string, ModelInfo>
  video_min_points: number
}

export interface Task {
  id: string
  type: 'image' | 'video'
  prompt: string
  model: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'running' | 'timeout'
  result_url?: string
  video_url?: string
  cost: number
  created_at: string
  error?: string
  oiioii_task_id?: number
  reference_images?: string[]
  reference_video?: string
}

function _normalizeModels(raw: Record<string, any>): Record<string, ModelInfo> {
  const result: Record<string, ModelInfo> = {}
  for (const [key, val] of Object.entries(raw || {})) {
    if (val.agent_only) continue
    result[key] = {
      name: val.name || key,
      ratios: val.ratios || [],
      resolutions: val.resolutions || [],
      durations: val.durations || [],
      cost: val.cost_base || 10,
      cost_duration_scale: val.cost_duration_scale || {},
      ref_max: val.ref_max || 0,
      video_ref: val.video_ref || false,
    }
  }
  return result
}

// 自定义费用覆盖（不使用oiioii的cost_base，按运营定价）
const IMAGE_COST_OVERRIDES: Record<string, Record<string, number>> = {
  'GPT-Image2': { '1K': 4, '2K': 8, '4K': 12 },
  'Gpt 4o':     { '1K': 5, '2K': 10, '4K': 20 },
}
const DEFAULT_IMAGE_COST: Record<string, number> = { '1K': 5, '2K': 10, '4K': 20 }

// 视频定价：每10s/720p的人民币价格 × 100 = 积分
// 分辨率比例: 720p=1.0, 1080p=1.29, 4K=2.14 (由Gemini Omni定价推算)
// 时长: 线性缩放 (10s = 1.0)
const VIDEO_PRICE_10S_720P: Record<string, number> = {
  'Grok Imagine': 0.4,
  'Gemini Omni': 0.7,
  'Wan2.7': 0.6,
  'Wan2.6': 0.6,
  'Vidu Q2': 0.7,
  'Vidu Q3 Pro': 0.84,
  'Vidu Q3 Ref': 0.84,
  'Vidu Q3 Mix': 0.84,
  'Kling 2.6': 0.7,
  'Kling O1': 1.12,
  'Hailuo 2.3 Std': 0.7,
  'Hailuo 2.3 Pro': 1.12,
  'Seedance 1.5 Pro': 1.12,
}

function calcImageCost(model: string, resolution: string, _modelInfo?: ModelInfo): number {
  const override = IMAGE_COST_OVERRIDES[model]
  const pricing = override || DEFAULT_IMAGE_COST
  if (resolution === "4K" || resolution === "4k") return pricing['4K']
  if (resolution === "2K" || resolution === "1080p") return pricing['2K']
  return pricing['1K']
}

function calcVideoCost(model: string, duration: number, resolution: string, modelInfo?: ModelInfo): number {
  // Price per 10s at 720p in RMB, then * 100 = points
  let basePrice = VIDEO_PRICE_10S_720P[model]
  if (!basePrice) {
    // Fallback: proportional to oiioii cost_base (Gemini base=25 → 0.7 RMB)
    const costBase = modelInfo?.cost || 25
    basePrice = 0.7 * (costBase / 25)
  }

  // Duration: linear scale (10s = 1.0)
  const durationScale = duration / 10.0

  // Resolution scale: 720p=1.0, 1080p=1.29, 4K=2.14
  let resScale = 1.0
  if (resolution === '1080p' || resolution === '2K') resScale = 1.29
  else if (resolution === '4K' || resolution === '4k') resScale = 2.14

  // RMB → points (× 100)
  const costRmb = basePrice * durationScale * resScale
  return Math.max(1, Math.round(costRmb * 100))
}

function _rawToTask(raw: any): Task {
  let refImages: string[] | undefined
  if (raw.reference_images) {
    try {
      refImages = typeof raw.reference_images === 'string' ? JSON.parse(raw.reference_images) : raw.reference_images
      if (!Array.isArray(refImages) || refImages.length === 0) refImages = undefined
    } catch { refImages = undefined }
  }
  return {
    id: String(raw.id),
    type: raw.task_type === 'image' ? 'image' : 'video',
    prompt: raw.prompt || '',
    model: raw.model || '',
    status: (raw.status === 'running' ? 'processing' : raw.status) as Task['status'],
    cost: raw.points_cost || 0,
    created_at: raw.created_at ? new Date(raw.created_at * 1000).toISOString() : '',
    result_url: raw.result_url || undefined,
    video_url: raw.result_url || undefined,
    oiioii_task_id: raw.oiioii_task_id || 0,
    error: raw.error || undefined,
    reference_images: refImages,
    reference_video: raw.reference_video || undefined,
  }
}

const STORAGE_KEY = 'aiforge_tasks_cache'
const CACHE_TIME_KEY = 'aiforge_tasks_cache_time'
const CACHE_MAX_AGE = 60000 // 1 minute

function loadTasksFromCache(): Task[] {
  try {
    const cacheTime = localStorage.getItem(CACHE_TIME_KEY)
    if (!cacheTime || Date.now() - parseInt(cacheTime) > CACHE_MAX_AGE) {
      return []
    }
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const tasks = JSON.parse(raw) as Task[]
    return tasks
  } catch {
    return []
  }
}

function saveTasksToCache(tasks: Task[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks))
    localStorage.setItem(CACHE_TIME_KEY, String(Date.now()))
  } catch {}
}

export const useGenerateStore = defineStore('generate', () => {
  const models = ref<ModelsData | null>(null)
  const currentTab = ref<'image' | 'video'>('image')
  const tasks = ref<Task[]>(loadTasksFromCache())
  const imageModels = ref<Record<string, ModelInfo>>({})
  const videoModels = ref<Record<string, ModelInfo>>({})
  const _pollTimers = new Map<string, ReturnType<typeof setTimeout>>()
  const _pollDelays = new Map<string, number>()

  // Watch tasks and persist to cache
  watch(tasks, (newTasks) => {
    saveTasksToCache(newTasks)
  }, { deep: true })

  async function fetchModels() {
    try {
      const data = await get<any>('/gen/models')
      models.value = data
      imageModels.value = _normalizeModels(data.image)
      videoModels.value = _normalizeModels(data.video)
    } catch (e) {
      console.error('fetchModels error', e)
    }
  }

  async function fetchTasks() {
    try {
      const data = await get<any[]>('/gen/tasks')
      tasks.value = data.map(_rawToTask)
      data.forEach(raw => {
        const t = _rawToTask(raw)
        if (t.status === 'processing' || t.status === 'pending' || t.status === 'running') {
          _startPolling(t.id)
        }
      })
    } catch (e) {
      console.error('fetchTasks error', e)
    }
  }

  function _upsertTask(task: Task) {
    const idx = tasks.value.findIndex(t => t.id === task.id)
    if (idx >= 0) {
      tasks.value[idx] = task
    } else {
      tasks.value.unshift(task)
    }
  }

  async function generateImage(params: {
    prompt: string
    model: string
    ratio: string
    resolution: string
    reference_images?: string[]
  }) {
    const data = await post<{ task_id: number; cost: number }>('/gen/image', params)
    const task: Task = {
      id: String(data.task_id),
      type: 'image',
      prompt: params.prompt,
      model: params.model,
      status: 'pending',
      cost: data.cost,
      created_at: new Date().toISOString(),
    }
    _upsertTask(task)
    _startPolling(task.id)
    return data
  }

  async function generateVideo(params: {
    prompt: string
    model: string
    ratio: string
    resolution: string
    duration: number
    reference_images?: string[]
    reference_video?: string
    camera_movement?: string
  }) {
    const data = await post<{ task_id: number; cost: number }>('/gen/video', params)
    const task: Task = {
      id: String(data.task_id),
      type: 'video',
      prompt: params.prompt,
      model: params.model,
      status: 'pending',
      cost: data.cost,
      created_at: new Date().toISOString(),
    }
    _upsertTask(task)
    _startPolling(task.id)
    return data
  }

  async function pollTask(taskId: string): Promise<Task> {
    const raw = await get<any>(`/gen/task/${taskId}`)
    return _rawToTask(raw)
  }

  function _startPolling(taskId: string) {
    if (_pollTimers.has(taskId)) return
    _pollDelays.set(taskId, 3000)
    const poll = async () => {
      try {
        const task = await pollTask(taskId)
        _upsertTask(task)
        if (task.status === 'completed' || task.status === 'failed' || task.status === 'timeout') {
          _stopPolling(taskId)
          return
        }
      } catch {
        _stopPolling(taskId)
        return
      }
      // Exponential backoff: 3s → 6s → 12s → 30s (max)
      const prev = _pollDelays.get(taskId) || 3000
      const next = Math.min(prev * 2, 30000)
      _pollDelays.set(taskId, next)
      _pollTimers.set(taskId, setTimeout(poll, next))
    }
    _pollTimers.set(taskId, setTimeout(poll, 3000))
  }

  function _stopPolling(taskId: string) {
    const timer = _pollTimers.get(taskId)
    if (timer) {
      clearTimeout(timer)
      _pollTimers.delete(taskId)
    }
    _pollDelays.delete(taskId)
  }

  function stopAllPolling() {
    _pollTimers.forEach((timer) => clearTimeout(timer))
    _pollTimers.clear()
    _pollDelays.clear()
  }

  async function describeImage(imageUrl: string) {
    const data = await post<{ task_id: number; cost: number }>('/gen/describe', { image_url: imageUrl })
    const task: Task = {
      id: String(data.task_id),
      type: 'image',
      prompt: '反推提示词...',
      model: 'describe_image',
      status: 'pending',
      cost: data.cost,
      created_at: new Date().toISOString(),
    }
    _upsertTask(task)
    _startPolling(task.id)
    return data
  }

  async function retryTask(taskId: string): Promise<Task> {
    const raw = await post<any>(`/gen/task/${taskId}/retry`)
    const task = _rawToTask(raw)
    _upsertTask(task)
    _startPolling(task.id)
    return task
  }

  async function deleteTask(taskId: string) {
    await del(`/gen/task/${taskId}`)
    _stopPolling(taskId)
    tasks.value = tasks.value.filter(t => t.id !== taskId)
  }

  async function uploadRefImage(file: File): Promise<{ url: string; filename: string }> {
    const fd = new FormData()
    fd.append('file', file)
    return upload<{ url: string; filename: string }>('/gen/upload_ref', fd)
  }

  async function uploadRefVideo(file: File): Promise<{ uri: string; filename: string }> {
    const fd = new FormData()
    fd.append('file', file)
    return upload<{ uri: string; filename: string }>('/gen/upload_video_ref', fd)
  }

  const generating = ref(false)
  const currentTask = ref<Task | null>(null)

  return {
    models, currentTab, generating, currentTask, tasks,
    imageModels, videoModels,
    fetchModels, fetchTasks, generateImage, generateVideo, describeImage,
    pollTask, retryTask, deleteTask,
    stopAllPolling,
    uploadRefImage, uploadRefVideo,
    calcImageCost, calcVideoCost,
  }
})
