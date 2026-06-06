import { defineStore } from 'pinia'
import { ref } from 'vue'
import { get } from '@/api'
import type { Task } from './generate'

export const useGalleryStore = defineStore('gallery', () => {
  const tasks = ref<Task[]>([])
  const loading = ref(false)

  async function fetchTasks() {
    loading.value = true
    try {
      const data = await get<any[]>('/gen/tasks')
      tasks.value = data.map(raw => ({
        id: String(raw.id),
        type: raw.task_type === 'image' ? 'image' as const : 'video' as const,
        prompt: raw.prompt || '',
        model: raw.model || '',
        status: (raw.status === 'running' ? 'processing' : raw.status) as Task['status'],
        cost: raw.points_cost || 0,
        created_at: raw.created_at ? new Date(raw.created_at * 1000).toISOString() : '',
        result_url: raw.result_url || undefined,
        video_url: raw.result_url || undefined,
      }))
    } finally {
      loading.value = false
    }
  }

  return {
    tasks,
    loading,
    fetchTasks,
  }
})
