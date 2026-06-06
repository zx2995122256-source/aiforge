<template>
  <div class="workspace-root">
    <!-- Mobile sidebar toggle -->
    <button
      v-if="!sidebarOpen"
      class="mobile-toggle"
      @click="sidebarOpen = true"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
    </button>

    <!-- Mobile overlay -->
    <Transition name="overlay">
      <div
        v-if="sidebarOpen"
        class="mobile-overlay"
        @click="sidebarOpen = false"
      />
    </Transition>

    <!-- Left sidebar: params panel -->
    <aside
      :class="[
        'sidebar-panel',
        sidebarOpen ? 'sidebar-open' : 'sidebar-closed'
      ]"
    >
      <div class="sidebar-header">
        <h2 class="sidebar-title">参数设置</h2>
        <button class="sidebar-close" @click="sidebarOpen = false">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>

      <!-- Tab switcher: pill shape -->
      <div class="param-group">
        <label class="label-text">创作类型</label>
        <div class="tab-switcher">
          <button
            @click="genStore.currentTab = 'image'"
            :class="['tab-btn', genStore.currentTab === 'image' ? 'tab-active' : 'tab-inactive']"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            图片
          </button>
          <button
            @click="genStore.currentTab = 'video'"
            :class="['tab-btn', genStore.currentTab === 'video' ? 'tab-active' : 'tab-inactive']"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            视频
          </button>
        </div>
      </div>

      <div class="param-group">
        <label class="label-text">模型</label>
        <select v-model="selectedModel" class="select-field">
          <option value="" disabled>选择模型</option>
          <option v-for="(info, key) in currentModels" :key="key" :value="key">
            {{ info.name || key }}
          </option>
        </select>
      </div>

      <div v-if="selectedModelInfo" class="param-group">
        <label class="label-text">比例</label>
        <select v-model="params.ratio" class="select-field">
          <option v-for="r in selectedModelInfo.ratios" :key="r" :value="r">{{ r }}</option>
        </select>
      </div>

      <div v-if="selectedModelInfo" class="param-group">
        <label class="label-text">分辨率</label>
        <select v-model="params.resolution" class="select-field">
          <option v-for="r in selectedModelInfo.resolutions" :key="r" :value="r">{{ r }}</option>
        </select>
      </div>

      <div v-if="genStore.currentTab === 'video' && selectedModelInfo" class="param-group">
        <label class="label-text">时长</label>
        <select v-model.number="params.duration" class="select-field">
          <option v-for="d in selectedModelInfo.durations" :key="d" :value="d">{{ d }}s</option>
        </select>
      </div>

      <div v-if="genStore.currentTab === 'video'" class="param-group">
        <label class="label-text">运镜</label>
        <select v-model="params.camera_movement" class="select-field">
          <option value="">默认</option>
          <option value="zoom_in">推入 Zoom In</option>
          <option value="zoom_out">拉远 Zoom Out</option>
          <option value="pan_left">左摇 Pan Left</option>
          <option value="pan_right">右摇 Pan Right</option>
          <option value="tilt_up">上仰 Tilt Up</option>
          <option value="tilt_down">下俯 Tilt Down</option>
          <option value="orbit_left">左环绕 Orbit Left</option>
          <option value="orbit_right">右环绕 Orbit Right</option>
          <option value="dolly_in">跟推 Dolly In</option>
          <option value="dolly_out">跟拉 Dolly Out</option>
          <option value="crane_up">升 Crane Up</option>
          <option value="crane_down">降 Crane Down</option>
          <option value="tracking">跟踪 Tracking</option>
          <option value="static">静止 Static</option>
        </select>
      </div>

      <!-- Cost info pinned to bottom -->
      <div v-if="selectedModelInfo" class="sidebar-footer">
        <div class="cost-card">
          <span class="cost-label">单条消耗</span>
          <span class="cost-value">{{ estimatedCost }} 积分</span>
        </div>
        <div class="balance-row">
          <span class="balance-label">当前积分</span>
          <span :class="auth.userPoints < estimatedCost ? 'balance-low' : 'balance-value'">{{ auth.userPoints }}</span>
        </div>
      </div>
    </aside>

    <!-- Middle: input area -->
    <div class="input-panel">
      <div class="input-header">
        <div class="input-header-left">
          <h3 class="section-title">输入卡片</h3>
        </div>
        <div class="input-header-actions">
          <button @click="addCard" class="add-btn" title="添加卡片">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
          </button>
          <button @click="submitAllCards" :disabled="!canSubmitAll" class="btn-primary submit-all-btn">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            全部提交
          </button>
        </div>
      </div>
      <p class="input-hint">输入 @ 引用参考图 · Ctrl+Enter 提交当前卡片</p>

      <div class="cards-scroll">
        <div
          v-for="(card, idx) in cards"
          :key="card.id"
          :class="['input-card', card.submitting ? 'card-submitting' : '']"
        >
          <div class="card-header">
            <span class="card-index">卡片 {{ idx + 1 }}</span>
            <div class="card-header-right">
              <span class="card-cost">{{ cardCost(card) }} 积分</span>
              <button
                v-if="cards.length > 1"
                @click="removeCard(card.id)"
                class="card-remove-btn"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
          </div>

          <div class="card-textarea-wrap">
            <textarea
              :ref="el => setCardRef(card.id, el)"
              v-model="card.prompt"
              placeholder="描述你想要生成的内容..."
              class="input-field card-textarea"
              :rows="card.promptExpanded ? 14 : 3"
              @keydown.ctrl.enter="submitCard(card)"
              @keydown.meta.enter="submitCard(card)"
              @input="onPromptInput(card, $event)"
              @keydown="onPromptKeydown(card, $event)"
            ></textarea>
            <button
              @click.stop="card.promptExpanded = !card.promptExpanded"
              class="expand-btn"
              :title="card.promptExpanded ? '收起' : '展开全部'"
            >
              <svg v-if="!card.promptExpanded" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
              <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
            </button>

            <Teleport to="body">
              <Transition name="mention-pop">
                <div
                  v-if="card.mentionOpen && card.refImages.length > 0"
                  class="mention-popup"
                  :style="{ left: mentionPos.x + 'px', bottom: mentionPos.bottom + 'px' }"
                >
                  <div class="mention-popup-header">选择参考图引用</div>
                  <div class="mention-popup-list">
                    <button
                      v-for="(img, imgIdx) in card.refImages"
                      :key="imgIdx"
                      @click="insertMention(card, imgIdx)"
                      class="mention-item"
                    >
                      <img :src="img.url" class="mention-thumb" />
                      <span class="mention-label">图片{{ imgIdx + 1 }}</span>
                    </button>
                  </div>
                </div>
              </Transition>
            </Teleport>
          </div>

          <!-- Mention tags -->
          <div v-if="card.mentionTags.length > 0" class="mention-tags">
            <span v-for="(tag, ti) in card.mentionTags" :key="ti" class="mention-tag">
              {{ tag }}
              <button @click="removeMentionTag(card, ti)" class="mention-tag-remove">×</button>
            </span>
          </div>

          <!-- Ref images -->
          <div
            v-if="selectedModelInfo && (selectedModelInfo.ref_max > 0 || (genStore.currentTab === 'video' && selectedModelInfo.video_ref))"
            class="ref-section"
          >
            <div class="ref-header">
              <span class="ref-label">
                参考图{{ selectedModelInfo.ref_max > 0 ? ` (${card.refImages.length}/${selectedModelInfo.ref_max})` : '' }}
              </span>
            </div>
            <div class="ref-grid">
              <div v-for="(img, imgIdx) in card.refImages" :key="imgIdx" class="ref-thumb-wrap">
                <img :src="img.url" class="ref-thumb" />
                <button @click="removeRefImage(card, imgIdx)" class="ref-thumb-delete">×</button>
              </div>
              <div
                v-if="selectedModelInfo.ref_max > 0 && card.refImages.length < selectedModelInfo.ref_max"
                :class="['ref-upload', card.dragOverImage ? 'ref-upload-active' : '']"
                @dragover.prevent="card.dragOverImage = true"
                @dragleave.prevent="card.dragOverImage = false"
                @drop.prevent="e => handleCardDropImage(card, e)"
                @click="(e: MouseEvent) => ((e.currentTarget as HTMLElement)?.querySelector('input[type=file]') as HTMLInputElement)?.click()"
              >
                <input type="file" accept="image/*" class="hidden" @change="e => handleCardFileSelect(card, e)" />
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
              </div>
            </div>
          </div>

          <!-- Ref video -->
          <div
            v-if="genStore.currentTab === 'video' && selectedModelInfo && selectedModelInfo.video_ref"
            class="ref-section"
          >
            <div class="ref-header">
              <span class="ref-label">参考视频</span>
              <button v-if="card.refVideo" @click="card.refVideo = null" class="ref-video-remove">移除</button>
            </div>
            <div v-if="card.refVideo" class="ref-video-item">
              <svg class="w-4 h-4 flex-shrink-0" style="color: var(--accent)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
              <span class="ref-video-name">{{ card.refVideo.filename }}</span>
            </div>
            <div
              v-else
              :class="['ref-video-upload', card.dragOverVideo ? 'ref-upload-active' : '']"
              @dragover.prevent="card.dragOverVideo = true"
              @dragleave.prevent="card.dragOverVideo = false"
              @drop.prevent="e => handleCardDropVideo(card, e)"
              @click="(e: MouseEvent) => ((e.currentTarget as HTMLElement)?.querySelector('input[type=file]') as HTMLInputElement)?.click()"
            >
              <input type="file" accept="video/*" class="hidden" @change="e => handleCardVideoSelect(card, e)" />
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
              <span>拖拽或点击上传视频</span>
            </div>
          </div>

          <!-- Submit button -->
          <div class="card-submit-wrap">
            <button
              @click="submitCard(card)"
              :disabled="!canSubmitCard(card)"
              class="btn-primary card-submit-btn"
            >
              <template v-if="card.submitting">
                <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                提交中...
              </template>
              <template v-else>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                生成
              </template>
            </button>
          </div>
        </div>

        <!-- Add card button -->
        <button @click="addCard" class="add-card-btn">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
          添加卡片
        </button>
      </div>
    </div>

    <!-- Right: results area -->
    <div class="results-panel">
      <div class="results-header">
        <div class="results-header-left">
          <h3 class="section-title">生成结果</h3>
          <span class="results-count">{{ genStore.tasks.length }} 个任务</span>
        </div>
        <div class="filter-group">
          <button
            v-for="f in statusFilters"
            :key="f.value"
            @click="activeFilter = f.value"
            :class="['filter-btn', activeFilter === f.value ? 'filter-active' : '']"
          >
            {{ f.label }}
          </button>
        </div>
      </div>

      <div class="results-scroll">
        <!-- Empty state -->
        <div v-if="filteredTasks.length === 0" class="empty-state">
          <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p class="empty-title">输入 Prompt 开始创作</p>
          <p class="empty-sub">支持多卡片并行提交</p>
        </div>

        <!-- Task grid -->
        <div v-else ref="taskGrid" class="task-grid">
          <div
            v-for="task in filteredTasks"
            :key="task.id"
            class="task-card"
            @click="previewTask(task)"
          >
            <!-- Thumbnail area with aspect-ratio -->
            <div class="task-thumb">
              <!-- Image result -->
              <img
                v-if="task.type === 'image' && task.result_url"
                :src="task.result_url"
                alt=""
                loading="lazy"
              />
              <!-- Video result -->
              <video
                v-else-if="task.type === 'video' && task.video_url"
                :src="task.video_url"
                muted
                preload="metadata"
              />
              <!-- Loading state -->
              <div v-else-if="isTaskActive(task.status)" class="task-loading">
                <div class="spinner"></div>
              </div>
              <!-- Error/failed state - show error directly on card -->
              <div v-else class="task-error-state">
                <span class="task-error-text">{{ taskErrorHint(task) || '失败' }}</span>
                <button @click.stop="retryTask(task)" class="task-error-retry">重试</button>
              </div>

              <!-- Status badge (top-right, small pill) -->
              <div class="task-status-pill" :class="'status-'+task.status">
                {{ statusText(task.status) }}
              </div>

              <!-- Video play icon overlay -->
              <div v-if="task.type === 'video' && task.result_url" class="video-play-icon">▶</div>

              <!-- Hover actions overlay -->
              <div class="task-hover-actions">
                <button @click.stop="handleDelete(task.id, task.status)" title="删除">✕</button>
                <button v-if="task.status==='completed'" @click.stop="downloadTask(task)" title="下载">↓</button>
                <button v-if="task.type==='image'&&task.status==='completed'" @click.stop="describeImage(task)" title="反推">🔍</button>
                <button v-if="!isTaskActive(task.status)" @click.stop="retryTask(task)" title="重试">↻</button>
              </div>
            </div>

            <!-- Bottom info bar -->
            <div class="task-bottom-bar">
              <span class="task-prompt-text" :title="task.prompt">{{ task.prompt }}</span>
              <span class="task-model-tag">{{ task.model }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Lightbox -->
    <Teleport to="body">
      <Transition name="lightbox">
        <div
          v-if="previewing"
          class="lightbox-overlay"
          @click.self="previewing = null"
        >
          <div class="lightbox-content">
            <img
              v-if="previewing.type === 'image' && previewing.result_url"
              :src="previewing.result_url"
              class="lightbox-img"
              alt=""
            />
            <video
              v-else-if="previewing.type === 'video' && previewing.video_url"
              :src="previewing.video_url"
              controls
              autoplay
              class="lightbox-video"
            />
            <div class="lightbox-info">
              <p class="lightbox-prompt">{{ previewing.prompt }}</p>
              <div class="lightbox-meta">
                <span class="lightbox-model">{{ previewing.model }}</span>
                <span class="lightbox-dot">·</span>
                <span class="lightbox-cost">-{{ previewing.cost }} 积分</span>
              </div>
            </div>
          </div>
          <button @click="previewing = null" class="lightbox-close">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useGenerateStore } from '@/stores/generate'
import { useAuthStore } from '@/stores/auth'
import type { ModelInfo, Task } from '@/stores/generate'
import gsap from 'gsap'

interface RefImageItem {
  url: string
  filename: string
}

interface RefVideoItem {
  uri: string
  filename: string
}

interface InputCard {
  id: number
  prompt: string
  refImages: RefImageItem[]
  refVideo: RefVideoItem | null
  mentionTags: string[]
  mentionOpen: boolean
  submitting: boolean
  uploadingImage: boolean
  uploadingVideo: boolean
  promptExpanded: boolean
  dragOverImage: boolean
  dragOverVideo: boolean
}

const genStore = useGenerateStore()
const auth = useAuthStore()

const selectedModel = ref('')
const sidebarOpen = ref(false)
const expandedPrompts = ref(new Set<string>())

function togglePromptExpand(taskId: string) {
  const s = new Set(expandedPrompts.value)
  if (s.has(taskId)) s.delete(taskId)
  else s.add(taskId)
  expandedPrompts.value = s
}
const activeFilter = ref('all')
const previewing = ref<Task | null>(null)
const taskGrid = ref<HTMLElement | null>(null)
const mentionPos = reactive({ x: 0, bottom: 0 })

let cardIdCounter = 0

function createCard(): InputCard {
  return {
    id: ++cardIdCounter,
    prompt: '',
    refImages: [],
    refVideo: null,
    mentionTags: [],
    mentionOpen: false,
    submitting: false,
    uploadingImage: false,
    uploadingVideo: false,
    promptExpanded: false,
    dragOverImage: false,
    dragOverVideo: false,
  }
}

const cards = ref<InputCard[]>([createCard()])

const cardTextareaRefs = new Map<number, HTMLTextAreaElement>()

function setCardRef(cardId: number, el: any) {
  if (el) {
    cardTextareaRefs.set(cardId, el as HTMLTextAreaElement)
  } else {
    cardTextareaRefs.delete(cardId)
  }
}

const params = reactive({
  ratio: '',
  resolution: '',
  duration: 5,
  camera_movement: '',
})

const statusFilters = [
  { label: '全部', value: 'all' },
  { label: '生成中', value: 'active' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
]

const currentModels = computed(() => {
  return genStore.currentTab === 'image' ? genStore.imageModels : genStore.videoModels
})

const selectedModelInfo = computed((): ModelInfo | null => {
  if (!selectedModel.value) return null
  return currentModels.value[selectedModel.value] || null
})

const estimatedCost = computed(() => {
  if (!selectedModelInfo.value || !selectedModel.value) return 0
  if (genStore.currentTab === 'image') {
    return genStore.calcImageCost(selectedModel.value, params.resolution, selectedModelInfo.value)
  } else {
    return genStore.calcVideoCost(selectedModel.value, params.duration, params.resolution, selectedModelInfo.value)
  }
})

function cardCost(card: InputCard): number {
  return estimatedCost.value
}

const filteredTasks = computed(() => {
  const tasks = genStore.tasks
  if (activeFilter.value === 'all') return tasks
  if (activeFilter.value === 'active') return tasks.filter(t => isTaskActive(t.status))
  if (activeFilter.value === 'completed') return tasks.filter(t => t.status === 'completed')
  if (activeFilter.value === 'failed') return tasks.filter(t => t.status === 'failed' || t.status === 'timeout')
  return tasks
})

function isTaskActive(status: string): boolean {
  return status === 'pending' || status === 'processing' || status === 'running'
}

function canSubmitCard(card: InputCard): boolean {
  return card.prompt.trim().length > 0 && !!selectedModel.value && !card.submitting && auth.userPoints >= cardCost(card)
}

const canSubmitAll = computed(() => {
  const submittable = cards.value.filter(c => c.prompt.trim().length > 0 && !c.submitting)
  if (submittable.length === 0) return false
  const totalCost = submittable.reduce((sum, c) => sum + cardCost(c), 0)
  return !!selectedModel.value && auth.userPoints >= totalCost
})

watch(() => genStore.currentTab, () => {
  selectedModel.value = ''
  resetParams()
  cards.value = [createCard()]
})

watch(selectedModel, () => {
  resetParams()
  if (selectedModelInfo.value) {
    if (selectedModelInfo.value.ratios?.length) params.ratio = selectedModelInfo.value.ratios[0]
    if (selectedModelInfo.value.resolutions?.length) params.resolution = selectedModelInfo.value.resolutions[0]
    if (selectedModelInfo.value.durations?.length) params.duration = selectedModelInfo.value.durations[0]
  }
  cards.value.forEach(card => {
    if (selectedModelInfo.value) {
      if (!selectedModelInfo.value.ref_max || selectedModelInfo.value.ref_max <= 0) {
        card.refImages = []
      } else if (card.refImages.length > selectedModelInfo.value.ref_max) {
        card.refImages = card.refImages.slice(0, selectedModelInfo.value.ref_max)
      }
      if (!selectedModelInfo.value.video_ref) {
        card.refVideo = null
      }
    }
    card.mentionTags = []
    card.mentionOpen = false
  })
})

function resetParams() {
  params.ratio = ''
  params.resolution = ''
  params.duration = 5
}

function statusText(status: string) {
  const map: Record<string, string> = {
    pending: '排队中',
    processing: '生成中',
    running: '生成中',
    completed: '已完成',
    failed: '失败',
    timeout: '超时',
  }
  return map[status] || status
}

function taskErrorHint(task: Task): string {
  if (task.status === 'failed' || task.status === 'timeout') {
    return task.error || (task.status === 'timeout' ? '任务超时，积分已退还' : '生成失败，积分已退还')
  }
  return ''
}

function addCard() {
  cards.value.push(createCard())
}

function removeCard(cardId: number) {
  if (cards.value.length <= 1) return
  const idx = cards.value.findIndex(c => c.id === cardId)
  if (idx >= 0) {
    cardTextareaRefs.delete(cardId)
    cards.value.splice(idx, 1)
  }
}

function onPromptInput(card: InputCard, e: Event) {
  const textarea = e.target as HTMLTextAreaElement
  const value = textarea.value
  const cursorPos = textarea.selectionStart

  const textBeforeCursor = value.substring(0, cursorPos)
  const atIdx = textBeforeCursor.lastIndexOf('@')
  if (atIdx !== -1) {
    const textAfterAt = textBeforeCursor.substring(atIdx + 1)
    if (!textAfterAt.includes(' ') && textAfterAt.length < 20) {
      if (card.refImages.length > 0) {
        card.mentionOpen = true
        const rect = textarea.getBoundingClientRect()
        mentionPos.x = rect.left
        mentionPos.bottom = window.innerHeight - rect.top + 8
      }
      return
    }
  }
  card.mentionOpen = false
}

function onPromptKeydown(card: InputCard, e: KeyboardEvent) {
  if (e.key === 'Escape') {
    card.mentionOpen = false
  }
}

function insertMention(card: InputCard, imgIdx: number) {
  const textarea = cardTextareaRefs.get(card.id)
  if (!textarea) return

  const tag = `@图片${imgIdx + 1}`
  const value = card.prompt
  const cursorPos = textarea.selectionStart

  const textBeforeCursor = value.substring(0, cursorPos)
  const atIdx = textBeforeCursor.lastIndexOf('@')

  if (atIdx !== -1) {
    const before = value.substring(0, atIdx)
    const after = value.substring(cursorPos)
    card.prompt = before + tag + ' ' + after

    if (!card.mentionTags.includes(tag)) {
      card.mentionTags.push(tag)
    }

    nextTick(() => {
      const newPos = atIdx + tag.length + 1
      textarea.selectionStart = newPos
      textarea.selectionEnd = newPos
      textarea.focus()
    })
  }

  card.mentionOpen = false
}

function removeMentionTag(card: InputCard, tagIdx: number) {
  const tag = card.mentionTags[tagIdx]
  card.mentionTags.splice(tagIdx, 1)
  card.prompt = card.prompt.replace(new RegExp(tag.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\s*', 'g'), '')
}

function buildRequestParams(card: InputCard) {
  const modelInfo = selectedModelInfo.value
  const refImgList = (modelInfo && modelInfo.ref_max && modelInfo.ref_max > 0 && card.refImages.length > 0)
    ? card.refImages.slice(0, modelInfo.ref_max).map(r => r.url)
    : undefined
  const refVideoUri = (genStore.currentTab === 'video' && modelInfo?.video_ref && card.refVideo)
    ? card.refVideo.uri
    : undefined

  const refMap: Record<string, string> = {}
  if (refImgList && refImgList.length > 0) {
    card.mentionTags.forEach(tag => {
      const match = tag.match(/@图片(\d+)/)
      if (match) {
        const idx = parseInt(match[1]) - 1
        if (idx >= 0 && idx < refImgList.length) {
          refMap[tag] = refImgList[idx]
        }
      }
    })
  }

  const commonParams: Record<string, any> = {
    prompt: card.prompt.trim(),
    model: selectedModel.value,
    ratio: params.ratio,
    resolution: params.resolution,
    reference_images: refImgList,
  }

  if (Object.keys(refMap).length > 0) {
    commonParams.reference_map = refMap
  }

  if (genStore.currentTab === 'image') {
    return commonParams
  }

  return {
    ...commonParams,
    duration: params.duration,
    reference_video: refVideoUri,
    camera_movement: params.camera_movement || undefined,
  }
}

async function submitCard(card: InputCard) {
  if (!canSubmitCard(card)) return

  if (auth.userPoints < cardCost(card)) {
    alert('积分不足，请先充值')
    return
  }

  card.submitting = true
  try {
    const p = buildRequestParams(card)
    if (genStore.currentTab === 'image') {
      await genStore.generateImage(p as any)
    } else {
      await genStore.generateVideo(p as any)
    }
    card.prompt = ''
    card.mentionTags = []
    card.mentionOpen = false
    await auth.fetchProfile()
  } catch (err: any) {
    alert(err.message || '生成失败')
  } finally {
    card.submitting = false
  }
}

async function submitAllCards() {
  if (!canSubmitAll.value) return

  const submittable = cards.value.filter(c => c.prompt.trim().length > 0 && !c.submitting)
  const totalCost = submittable.reduce((sum, c) => sum + cardCost(c), 0)

  if (auth.userPoints < totalCost) {
    alert('积分不足，请先充值')
    return
  }

  for (const card of submittable) {
    card.submitting = true
  }

  const promises = submittable.map(async (card) => {
    try {
      const p = buildRequestParams(card)
      if (genStore.currentTab === 'image') {
        await genStore.generateImage(p as any)
      } else {
        await genStore.generateVideo(p as any)
      }
      card.prompt = ''
      card.mentionTags = []
      card.mentionOpen = false
    } catch (err: any) {
      console.error('提交失败:', err.message)
    } finally {
      card.submitting = false
    }
  })

  await Promise.allSettled(promises)
  await auth.fetchProfile()
}

async function handleDelete(taskId: string, status: string) {
  if (isTaskActive(status)) return
  if (!confirm('确定删除此任务？')) return
  try {
    await genStore.deleteTask(taskId)
  } catch (err: any) {
    alert(err.message || '删除失败')
  }
}

async function retryTask(task: Task) {
  if (task.status !== 'failed' && task.status !== 'timeout') return
  try {
    await genStore.retryTask(task.id)
    await auth.fetchProfile()
  } catch (err: any) {
    alert(err.message || '重试失败')
  }
}

async function describeImage(task: Task) {
  if (task.type !== 'image' || !task.result_url) return
  try {
    await genStore.describeImage(task.result_url)
    await auth.fetchProfile()
  } catch (err: any) {
    alert(err.message || '反推提示词失败')
  }
}

function downloadTask(task: Task) {
  const url = task.type === 'video' ? task.video_url : task.result_url
  if (!url) return
  const token = localStorage.getItem('aiforge_token')
  const separator = url.includes('?') ? '&' : '?'
  const fullUrl = token ? `${url}${separator}token=${token}` : url
  window.open(fullUrl, '_blank')
}

function previewTask(task: Task) {
  if (task.status === 'completed' && (task.result_url || task.video_url)) {
    previewing.value = task
  }
}

async function handleCardFileSelect(card: InputCard, e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  const maxRef = selectedModelInfo.value?.ref_max || 0
  for (const file of Array.from(input.files)) {
    if (maxRef > 0 && card.refImages.length >= maxRef) {
      alert(`最多上传${maxRef}张参考图`)
      break
    }
    card.uploadingImage = true
    try {
      const result = await genStore.uploadRefImage(file)
      card.refImages.push({ url: result.url, filename: result.filename })
    } catch (err: any) {
      alert('上传失败: ' + err.message)
    } finally {
      card.uploadingImage = false
    }
  }
  input.value = ''
}

function handleCardDropImage(card: InputCard, e: DragEvent) {
  card.dragOverImage = false
  const files = e.dataTransfer?.files
  if (!files) return
  const input = { files } as unknown as HTMLInputElement
  handleCardFileSelect(card, { target: input } as unknown as Event)
}

function removeRefImage(card: InputCard, idx: number) {
  const removedTag = `@图片${idx + 1}`
  card.refImages.splice(idx, 1)
  card.mentionTags = card.mentionTags.filter(t => {
    const m = t.match(/@图片(\d+)/)
    if (!m) return true
    const n = parseInt(m[1])
    if (n === idx + 1) return false
    if (n > idx + 1) {
      const oldTag = t
      const newTag = `@图片${n - 1}`
      card.prompt = card.prompt.replace(oldTag, newTag)
    }
    return true
  })
}

function handleCardDropVideo(card: InputCard, e: DragEvent) {
  card.dragOverVideo = false
  const files = e.dataTransfer?.files
  if (!files?.[0]) return
  const input = { files } as unknown as HTMLInputElement
  handleCardVideoSelect(card, { target: input } as unknown as Event)
}

async function handleCardVideoSelect(card: InputCard, e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.[0]) return
  card.uploadingVideo = true
  try {
    const result = await genStore.uploadRefVideo(input.files[0])
    card.refVideo = { uri: result.uri, filename: result.filename }
  } catch (err: any) {
    alert('上传失败: ' + err.message)
  } finally {
    card.uploadingVideo = false
  }
  input.value = ''
}

onMounted(() => {
  genStore.fetchModels()
  genStore.fetchTasks()
})

watch(filteredTasks, (tasks) => {
  if (tasks.length > 0 && taskGrid.value) {
    nextTick(() => {
      const cards = taskGrid.value!.children
      gsap.fromTo(cards,
        { opacity: 0, y: 24, scale: 0.96 },
        { opacity: 1, y: 0, scale: 1, stagger: 0.05, duration: 0.45, ease: 'power2.out' }
      )
      Array.from(cards).forEach(el => {
        el.addEventListener('mouseenter', () => {
          gsap.to(el, { y: -4, scale: 1.015, duration: 0.2, ease: 'power2.out' })
        })
        el.addEventListener('mouseleave', () => {
          gsap.to(el, { y: 0, scale: 1, duration: 0.2, ease: 'power2.out' })
        })
      })
    })
  }
})

onUnmounted(() => {
  genStore.stopAllPolling()
})
</script>

<style scoped>
/* ══════════════════════════════════════
   Workspace — Apple-inspired layout
   Depth through shadow, not borders
   ══════════════════════════════════════ */

/* ─── Root ─── */
.workspace-root {
  display: flex;
  height: 100%;
  position: relative;
}

/* ─── Mobile toggle ─── */
.mobile-toggle {
  display: none;
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 40;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  align-items: center;
  justify-content: center;
  background: var(--bg-surface-2);
  color: var(--text-muted);
  border: none;
  cursor: pointer;
  transition: background 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.mobile-toggle:hover {
  background: var(--bg-surface-3);
}
@media (max-width: 1023px) {
  .mobile-toggle { display: flex; }
}

/* ─── Mobile overlay ─── */
.mobile-overlay {
  position: fixed;
  inset: 0;
  z-index: 30;
  background: color-mix(in srgb, var(--bg-canvas) 50%, transparent);
}

/* ─── Sidebar panel ─── */
.sidebar-panel {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  overflow-y: auto;
  background: var(--bg-surface-1);
  transition: transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@media (max-width: 1023px) {
  .sidebar-panel {
    position: fixed;
    inset-y: 0;
    left: 0;
    z-index: 40;
  }
  .sidebar-closed { transform: translateX(-100%); }
  .sidebar-open { transform: translateX(0); }
}
@media (min-width: 1024px) {
  .sidebar-panel {
    position: relative;
    z-index: auto;
    transform: translateX(0);
  }
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.sidebar-title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--text-primary);
}

.sidebar-close {
  display: none;
  color: var(--text-tertiary);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 8px;
  transition: color 0.2s, background 0.2s;
}
.sidebar-close:hover {
  color: var(--text-primary);
  background: var(--bg-surface-3);
}
@media (max-width: 1023px) {
  .sidebar-close { display: flex; }
}

/* ─── Param groups ─── */
.param-group {
  display: flex;
  flex-direction: column;
}

/* ─── Tab switcher: pill shape ─── */
.tab-switcher {
  display: flex;
  border-radius: 12px;
  padding: 3px;
  gap: 2px;
  background: var(--bg-surface-2);
}

.tab-btn {
  flex: 1;
  padding: 8px 0;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: none;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.tab-active {
  background: var(--accent);
  color: var(--text-primary);
  box-shadow: 0 1px 4px var(--accent-glow);
}

.tab-inactive {
  background: transparent;
  color: var(--text-muted);
}
.tab-inactive:hover {
  color: var(--text-secondary);
}

/* ─── Sidebar footer (cost) ─── */
.sidebar-footer {
  margin-top: auto;
  padding-top: 8px;
}

.cost-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 12px;
  background: var(--bg-surface-2);
}

.cost-label {
  font-size: 13px;
  color: var(--text-muted);
}

.cost-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent);
}

.balance-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
}

.balance-label {
  color: var(--text-tertiary);
}

.balance-value {
  color: var(--text-muted);
}

.balance-low {
  color: var(--color-error);
  font-weight: 500;
}

/* ─── Input panel (middle) ─── */
.input-panel {
  width: 420px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-canvas);
}

.input-header {
  padding: 16px 20px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.input-header-left {
  display: flex;
  align-items: center;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0;
  color: var(--text-secondary);
}

.input-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.add-btn {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-subtle);
  color: var(--accent);
  border: none;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.add-btn:hover {
  background: var(--accent-subtle);
}

.submit-all-btn {
  font-size: 12px;
  padding: 6px 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.input-hint {
  padding: 0 20px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-tertiary);
}

/* ─── Cards scroll ─── */
.cards-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ─── Input card ─── */
.input-card {
  padding: 14px;
  border-radius: 16px;
  background: var(--bg-surface-1);
  box-shadow: var(--shadow-card);
  animation: fade-slide-up 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
  transition: box-shadow 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.card-submitting {
  box-shadow: var(--shadow-card), 0 0 0 1px var(--accent-glow);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.card-index {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-tertiary);
}

.card-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-cost {
  font-size: 12px;
  color: var(--accent);
}

.card-remove-btn {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}
.card-remove-btn:hover {
  color: var(--color-error);
  background: color-mix(in srgb, var(--color-error) 10%, transparent);
}

/* ─── Card textarea ─── */
.card-textarea-wrap {
  position: relative;
}

.card-textarea {
  resize: none;
  min-height: 70px;
  max-height: 420px;
  font-size: 13px;
  line-height: 1.6;
}

.expand-btn {
  position: absolute;
  bottom: 6px;
  right: 8px;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--bg-surface-3);
  color: var(--text-tertiary);
  border: none;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.expand-btn:hover {
  color: var(--text-secondary);
  background: var(--bg-surface-3);
}

/* ─── Mention popup ─── */
.mention-popup {
  position: fixed;
  z-index: 9999;
  min-width: 220px;
  border-radius: 14px;
  background: var(--bg-surface-2);
  box-shadow: var(--shadow-elevated);
  overflow: hidden;
  border: 1px solid var(--border-hairline);
}

.mention-popup-header {
  padding: 10px 14px;
  font-size: 12px;
  color: var(--text-tertiary);
  border-bottom: 1px solid var(--border-hairline);
}

.mention-popup-list {
  max-height: 160px;
  overflow-y: auto;
  padding: 6px;
}

.mention-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  color: var(--text-secondary);
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}
.mention-item:hover {
  background: var(--bg-surface-3);
}

.mention-thumb {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  object-fit: cover;
  flex-shrink: 0;
}

.mention-label {
  font-size: 13px;
}

/* ─── Mention tags ─── */
.mention-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.mention-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--accent-subtle);
  color: var(--accent);
}

.mention-tag-remove {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1;
  padding: 0 2px;
  transition: color 0.15s;
}
.mention-tag-remove:hover {
  color: var(--text-primary);
}

/* ─── Ref section ─── */
.ref-section {
  margin-top: 10px;
}

.ref-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.ref-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.ref-grid {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: thin;
  scrollbar-color: color-mix(in srgb, var(--text-primary) 10%, transparent) transparent;
}

.ref-thumb-wrap {
  position: relative;
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  border-radius: 10px;
  overflow: hidden;
}

.ref-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ref-thumb-delete {
  position: absolute;
  top: 0;
  right: 0;
  width: 16px;
  height: 16px;
  background: var(--color-error);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  font-size: 11px;
  border: none;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}
.ref-thumb-wrap:hover .ref-thumb-delete {
  opacity: 1;
}

.ref-upload {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  border: 2px dashed var(--border-hairline);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-tertiary);
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.ref-upload-active {
  border-color: var(--accent);
  background: var(--accent-subtle);
  color: var(--accent);
}

.ref-upload:hover {
  border-color: var(--text-muted);
}

/* ─── Ref video ─── */
.ref-video-remove {
  font-size: 12px;
  color: var(--color-error);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.15s;
}
.ref-video-remove:hover {
  color: var(--color-error);
}

.ref-video-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background: var(--bg-surface-3);
}

.ref-video-name {
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ref-video-upload {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 2px dashed var(--border-hairline);
  cursor: pointer;
  font-size: 12px;
  color: var(--text-tertiary);
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.ref-video-upload:hover {
  border-color: var(--text-muted);
}

/* ─── Card submit ─── */
.card-submit-wrap {
  margin-top: 10px;
}

.card-submit-btn {
  width: 100%;
  font-size: 13px;
  padding: 10px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

/* ─── Add card button ─── */
.add-card-btn {
  width: 100%;
  padding: 14px 0;
  border-radius: 16px;
  border: 2px dashed var(--border-hairline);
  background: none;
  color: var(--text-tertiary);
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.add-card-btn:hover {
  border-color: var(--text-muted);
  color: var(--text-secondary);
  background: var(--bg-surface-1);
}

/* ─── Results panel (right) ─── */
.results-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  background: var(--bg-canvas);
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  flex-shrink: 0;
}

.results-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.results-count {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* ─── Filter group ─── */
.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-btn {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 100px;
  color: var(--text-tertiary);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.filter-btn:hover {
  color: var(--text-secondary);
  background: var(--bg-surface-2);
}

.filter-active {
  background: var(--accent-subtle);
  color: var(--accent);
}
.filter-active:hover {
  background: var(--accent-subtle);
  color: var(--accent);
}

/* ─── Results scroll ─── */
.results-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px 20px;
}

/* ─── Empty state ─── */
.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  color: var(--text-tertiary);
}

.empty-title {
  font-size: 14px;
  color: var(--text-muted);
}

.empty-sub {
  font-size: 12px;
  margin-top: 4px;
  color: var(--text-tertiary);
}

/* ─── Task grid ─── */
.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

/* ─── Task card ─── */
.task-card {
  border-radius: 12px;
  overflow: hidden;
  background: var(--bg-surface-1);
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  animation: fade-slide-up 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
}
.task-card:hover {
  box-shadow: var(--shadow-elevated);
  transform: translateY(-1px);
}

/* ─── Task thumbnail ─── */
.task-thumb {
  aspect-ratio: 1/1;
  position: relative;
  overflow: hidden;
  background: var(--bg-surface-2);
}

.task-thumb img,
.task-thumb video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.task-card:hover .task-thumb img,
.task-card:hover .task-thumb video {
  transform: scale(1.05);
}

/* ─── Task loading ─── */
.task-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--accent-subtle);
  border-top-color: var(--accent);
  animation: spin 0.8s linear infinite;
}

/* ─── Task error state ─── */
.task-error-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: color-mix(in srgb, var(--color-error) 8%, var(--bg-surface-2));
}

.task-error-text {
  font-size: 11px;
  color: var(--color-error);
  text-align: center;
  padding: 0 8px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-error-retry {
  font-size: 10px;
  padding: 2px 10px;
  border-radius: 100px;
  background: var(--color-error);
  color: white;
  border: none;
  cursor: pointer;
  transition: opacity 0.2s;
}
.task-error-retry:hover {
  opacity: 0.85;
}

/* ─── Status pill ─── */
.task-status-pill {
  position: absolute;
  top: 6px;
  right: 6px;
  padding: 2px 8px;
  border-radius: 100px;
  font-size: 10px;
  font-weight: 500;
  z-index: 2;
}
.status-completed {
  background: color-mix(in srgb, var(--color-success) 15%, transparent);
  color: var(--color-success);
}
.status-running,
.status-pending,
.status-processing,
.status-submitted {
  background: color-mix(in srgb, var(--accent) 15%, transparent);
  color: var(--accent);
  animation: pulse-status 1.5s ease-in-out infinite;
}
.status-failed,
.status-timeout {
  background: color-mix(in srgb, var(--color-error) 15%, transparent);
  color: var(--color-error);
}

/* ─── Video play icon ─── */
.video-play-icon {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.25);
  color: white;
  font-size: 24px;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}
.task-card:hover .video-play-icon {
  opacity: 1;
}

/* ─── Hover actions overlay ─── */
.task-hover-actions {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 6px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  background: linear-gradient(transparent, color-mix(in srgb, var(--bg-canvas) 80%, transparent));
  z-index: 3;
}
.task-card:hover .task-hover-actions {
  opacity: 1;
}
.task-hover-actions button {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  background: color-mix(in srgb, var(--bg-surface-1) 90%, transparent);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  transition: all 0.15s;
  backdrop-filter: blur(4px);
}
.task-hover-actions button:hover {
  background: var(--bg-surface-3);
  color: var(--text-primary);
}

/* ─── Bottom info bar ─── */
.task-bottom-bar {
  padding: 6px 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.task-prompt-text {
  flex: 1;
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-model-tag {
  font-size: 9px;
  padding: 1px 6px;
  border-radius: 100px;
  background: var(--bg-surface-3);
  color: var(--text-muted);
  white-space: nowrap;
  flex-shrink: 0;
}

/* ─── Lightbox ─── */
.lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  background: color-mix(in srgb, var(--bg-canvas) 92%, transparent);
}

.lightbox-content {
  max-width: 64rem;
  max-height: 100%;
  animation: scale-in 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
  position: relative;
}

.lightbox-img {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
  border-radius: 16px;
  box-shadow: var(--shadow-elevated);
}

.lightbox-video {
  max-width: 100%;
  max-height: 80vh;
  border-radius: 16px;
  box-shadow: var(--shadow-elevated);
}

.lightbox-info {
  margin-top: 16px;
  text-align: center;
}

.lightbox-prompt {
  font-size: 14px;
  line-height: 1.6;
  max-width: 36rem;
  margin: 0 auto;
  color: var(--text-secondary);
}

.lightbox-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 8px;
}

.lightbox-model {
  font-size: 12px;
  color: var(--text-tertiary);
}

.lightbox-dot {
  font-size: 12px;
  color: var(--text-tertiary);
}

.lightbox-cost {
  font-size: 12px;
  color: var(--accent);
}

.lightbox-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-surface-2);
  color: var(--text-muted);
  border: none;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.lightbox-close:hover {
  background: var(--bg-surface-3);
  color: var(--text-primary);
}

/* ─── Animations ─── */
@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse-status {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes fade-slide-up {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.lightbox-enter-active,
.lightbox-leave-active {
  transition: opacity 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}

.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}

.mention-pop-enter-active,
.mention-pop-leave-active {
  transition: all 0.15s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.mention-pop-enter-from,
.mention-pop-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
