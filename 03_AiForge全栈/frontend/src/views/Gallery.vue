<template>
  <div class="gallery-page h-full overflow-y-auto">
    <div class="px-6 pt-6 pb-2">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="w-1 h-8 rounded-full bg-gradient-accent"></div>
          <div>
            <h1 class="font-display text-2xl font-bold tracking-wide" style="color: var(--text-primary)">创作画廊</h1>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ completedTasks.length }} 件作品</p>
          </div>
        </div>
        <button @click="genStore.fetchTasks()" class="btn-secondary text-sm px-4 py-2 flex items-center gap-2">
          <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          刷新
        </button>
      </div>

      <div class="filter-bar">
        <button
          v-for="f in filters"
          :key="f.value"
          @click="activeFilter = f.value"
          :class="[
            'filter-btn',
            activeFilter === f.value ? 'filter-btn-active' : ''
          ]"
        >
          {{ f.label }}
          <span v-if="f.value !== 'all'" class="ml-1 text-xs opacity-60">{{ getFilterCount(f.value) }}</span>
        </button>
      </div>
    </div>

    <div v-if="completedTasks.length === 0" class="flex-1 flex items-center justify-center py-32">
      <div class="text-center animate-fade-in">
        <div class="empty-icon-wrap">
          <svg class="w-12 h-12" style="color: var(--text-tertiary)" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        <h3 class="font-display text-lg font-semibold mb-2" style="color: var(--text-secondary)">还没有作品</h3>
        <p class="text-sm mb-6 max-w-xs mx-auto" style="color: var(--text-muted)">前往创作空间，用 AI 生成你的第一张图片或视频</p>
        <router-link to="/workspace" class="btn-primary text-sm px-6 py-2.5 inline-flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          开始创作
        </router-link>
      </div>
    </div>

    <div v-else class="px-6 pb-6 pt-4">
      <div class="gallery-grid">
        <div
          v-for="(task, index) in filteredTasks"
          :key="task.id"
          class="gallery-card overflow-hidden cursor-pointer group relative animate-fade-in"
          :style="{ animationDelay: `${index * 40}ms` }"
          @click="openLightbox(task)"
        >
          <div class="aspect-[4/3] relative overflow-hidden" style="background: var(--bg-surface-1)">
            <img
              v-if="task.type === 'image' && task.result_url"
              :src="task.result_url"
              class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500 ease-out"
              alt=""
              loading="lazy"
            />
            <video
              v-else-if="task.type === 'video' && task.video_url"
              :src="task.video_url"
              class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500 ease-out"
              muted
              preload="metadata"
              :poster="task.result_url || undefined"
              @mouseenter="($event.target as HTMLVideoElement).play()"
              @mouseleave="($event.target as HTMLVideoElement).pause()"
              @loadeddata="($event.target as HTMLVideoElement).currentTime = 0.5"
            />
            <div v-else class="w-full h-full flex items-center justify-center" style="background: var(--bg-surface-1)">
              <svg class="w-10 h-10" style="color: var(--text-tertiary)" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>

            <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

            <div v-if="task.type === 'video'" class="absolute top-2.5 left-2.5">
              <span class="type-badge">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                VIDEO
              </span>
            </div>

            <div v-if="task.type === 'image'" class="absolute top-2.5 left-2.5">
              <span class="type-badge">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                IMG
              </span>
            </div>

            <button
              @click.stop="handleDelete(task.id)"
              class="absolute top-2.5 right-2.5 w-7 h-7 group-hover:rounded-lg flex items-center justify-center text-sm opacity-0 group-hover:opacity-100 transition-all duration-300 delete-btn"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>

            <button
              @click.stop="handleDownload(task)"
              class="download-btn absolute top-2.5 right-11 w-7 h-7 rounded-lg flex items-center justify-center text-sm opacity-0 group-hover:opacity-100 transition-all duration-300"
              title="下载"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>

            <div class="absolute bottom-0 left-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <p class="text-xs line-clamp-2 leading-relaxed" style="color: var(--text-secondary)">{{ task.prompt }}</p>
            </div>
          </div>

          <div class="p-3 space-y-2">
            <p class="text-sm truncate leading-snug" style="color: var(--text-secondary)">{{ task.prompt }}</p>
            <div class="flex items-center justify-between">
              <span class="model-badge">{{ task.model }}</span>
              <span class="text-[10px]" style="color: var(--text-tertiary)">{{ formatTime(task.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <Transition name="lightbox">
        <div
          v-if="lightboxTask"
          class="fixed inset-0 z-50 flex items-center justify-center"
          @keydown.escape="closeLightbox"
        >
          <div class="absolute inset-0 lightbox-overlay" @click="closeLightbox"></div>

          <div class="relative z-10 max-w-5xl w-full mx-8 animate-fade-in">
            <div class="flex items-start justify-between mb-4">
              <div class="flex-1 min-w-0 mr-4">
                <p class="text-sm leading-relaxed line-clamp-3" style="color: var(--text-primary)">{{ lightboxTask.prompt }}</p>
                <div class="flex items-center gap-3 mt-2">
                  <span class="model-badge">{{ lightboxTask.model }}</span>
                  <span class="text-xs" style="color: var(--text-muted)">{{ formatTime(lightboxTask.created_at) }}</span>
                  <span v-if="lightboxTask.cost" class="text-xs" style="color: var(--accent)">-{{ lightboxTask.cost }} 积分</span>
                </div>
              </div>
              <button
                @click="closeLightbox"
                class="lightbox-btn flex-shrink-0"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <button
                @click="handleDownload(lightboxTask!)"
                class="lightbox-btn flex-shrink-0"
                title="下载"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </button>
            </div>

            <div class="flex items-center justify-center">
              <img
                v-if="lightboxTask.type === 'image' && lightboxTask.result_url"
                :src="lightboxTask.result_url"
                class="max-w-full max-h-[72vh] object-contain rounded-2xl"
                alt=""
              />
              <video
                v-else-if="lightboxTask.type === 'video' && lightboxTask.video_url"
                :src="lightboxTask.video_url"
                controls
                autoplay
                class="max-w-full max-h-[72vh] rounded-2xl"
              />
            </div>
          </div>

          <button
            v-if="lightboxIndex > 0"
            @click="navigateLightbox(-1)"
            class="lightbox-nav absolute left-4 top-1/2 -translate-y-1/2 z-20"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button
            v-if="lightboxIndex < filteredTasks.length - 1"
            @click="navigateLightbox(1)"
            class="lightbox-nav absolute right-4 top-1/2 -translate-y-1/2 z-20"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useGenerateStore } from '@/stores/generate'
import type { Task } from '@/stores/generate'

const genStore = useGenerateStore()
const activeFilter = ref<'all' | 'image' | 'video'>('all')
const lightboxTask = ref<Task | null>(null)
const loading = ref(false)

const filters = [
  { label: '全部', value: 'all' as const },
  { label: '图片', value: 'image' as const },
  { label: '视频', value: 'video' as const },
]

const completedTasks = computed(() =>
  genStore.tasks.filter(t => t.status === 'completed' && (t.result_url || t.video_url))
)

const filteredTasks = computed(() => {
  if (activeFilter.value === 'all') return completedTasks.value
  return completedTasks.value.filter(t => t.type === activeFilter.value)
})

const lightboxIndex = computed(() => {
  if (!lightboxTask.value) return -1
  return filteredTasks.value.findIndex(t => t.id === lightboxTask.value!.id)
})

function getFilterCount(type: 'image' | 'video'): number {
  return completedTasks.value.filter(t => t.type === type).length
}

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins}分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function openLightbox(task: Task) {
  lightboxTask.value = task
  document.body.style.overflow = 'hidden'
}

function closeLightbox() {
  lightboxTask.value = null
  document.body.style.overflow = ''
}

function navigateLightbox(delta: number) {
  const idx = lightboxIndex.value + delta
  if (idx >= 0 && idx < filteredTasks.value.length) {
    lightboxTask.value = filteredTasks.value[idx]
  }
}

async function handleDelete(taskId: string) {
  if (!confirm('确定删除此作品？')) return
  try {
    await genStore.deleteTask(taskId)
    if (lightboxTask.value?.id === taskId) closeLightbox()
  } catch (err: any) {
    alert(err.message || '删除失败')
  }
}

function handleDownload(task: Task) {
  const url = task.type === 'video' ? task.video_url : task.result_url
  if (!url) return
  const token = localStorage.getItem('aiforge_token')
  const separator = url.includes('?') ? '&' : '?'
  const fullUrl = token ? `${url}${separator}token=${token}` : url
  const ext = task.type === 'video' ? 'mp4' : 'png'
  const filename = `aiforge_${task.model.replace(/\s+/g, '_')}_${task.id}.${ext}`
  const a = document.createElement('a')
  a.href = fullUrl
  a.download = filename
  a.target = '_blank'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

function handleKeydown(e: KeyboardEvent) {
  if (!lightboxTask.value) return
  if (e.key === 'Escape') closeLightbox()
  if (e.key === 'ArrowLeft') navigateLightbox(-1)
  if (e.key === 'ArrowRight') navigateLightbox(1)
}

async function refreshTasks() {
  loading.value = true
  try {
    await genStore.fetchTasks()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (genStore.tasks.length === 0) {
    refreshTasks()
  }
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.gallery-page {
  display: flex;
  flex-direction: column;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
}

@media (min-width: 1280px) {
  .gallery-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

/* Filter bar — surface ladder, no border */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  background: var(--bg-surface-1);
  border-radius: 12px;
  width: fit-content;
}

.filter-btn {
  padding: 6px 16px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--text-muted);
  background: transparent;
}

.filter-btn:hover {
  color: var(--text-secondary);
}

.filter-btn-active {
  background: var(--accent);
  color: var(--text-primary);
}

.filter-btn-active:hover {
  background: var(--accent-hover);
  color: var(--text-primary);
}

/* Gallery card — surface ladder, no border, subtle hover */
.gallery-card {
  border-radius: 1rem;
  background: var(--bg-surface-2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.gallery-card:hover {
  transform: translateY(-2px);
  background: var(--bg-surface-3);
}

/* Type badge on card image */
.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--bg-canvas) 60%, transparent);
  color: var(--text-secondary);
  font-weight: 500;
}

/* Download button on card */
.download-btn {
  background: transparent;
}

.download-btn:hover {
  background: var(--accent) !important;
}

/* Delete button */
.delete-btn {
  background: transparent;
  color: var(--text-primary);
}
.group:hover .delete-btn,
.gallery-card:hover .delete-btn {
  background: var(--color-error);
}
.delete-btn:hover {
  background: var(--color-error) !important;
}

/* Model badge — accent subtle, no border */
.model-badge {
  display: inline-flex;
  align-items: center;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--accent-subtle);
  color: var(--accent);
  font-weight: 500;
}

/* Empty state icon */
.empty-icon-wrap {
  width: 96px;
  height: 96px;
  margin: 0 auto 1.5rem;
  border-radius: 1rem;
  background: var(--bg-surface-1);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Lightbox overlay — canvas bg with opacity, no blur */
.lightbox-overlay {
  background: color-mix(in srgb, var(--bg-canvas) 92%, transparent);
}

/* Lightbox control buttons — surface ladder, no border */
.lightbox-btn {
  width: 36px;
  height: 36px;
  background: var(--bg-surface-2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  transition: all 0.2s ease;
}

.lightbox-btn:hover {
  color: var(--text-primary);
  background: var(--bg-surface-3);
}

/* Lightbox navigation buttons */
.lightbox-nav {
  width: 40px;
  height: 40px;
  background: var(--bg-surface-2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  transition: all 0.2s ease;
}

.lightbox-nav:hover {
  color: var(--text-primary);
  background: var(--bg-surface-3);
}

/* Transitions */
.lightbox-enter-active,
.lightbox-leave-active {
  transition: opacity 0.3s ease;
}

.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
