<template>
  <div class="min-h-screen" style="background: var(--bg-canvas); color: var(--text-primary)">
    <header class="h-14 px-5 flex items-center justify-between shrink-0" style="background: var(--bg-surface-1)">
      <div class="flex items-center gap-3">
        <button @click="$router.push('/workspace')" class="back-btn">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <h1 class="text-sm font-semibold tracking-wide">设置</h1>
      </div>
    </header>

    <div class="max-w-2xl mx-auto p-6 space-y-6">
      <!-- LLM 推理 API 配置 -->
      <section class="section-card rounded-xl p-5 space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-sm font-semibold">LLM 推理 API</h2>
            <p class="text-[11px] mt-0.5" style="color: var(--text-tertiary)">配置你的 AI 推理接口，所有 LLM 调用（拆段、Agent对话、视觉分解）都会使用此配置。留空则使用系统默认。</p>
          </div>
          <span v-if="saved" class="text-[10px]" style="color: var(--color-success)">已保存</span>
        </div>

        <!-- 预设模板 -->
        <div>
          <label class="lbl">快速预设</label>
          <div class="flex flex-wrap gap-1.5">
            <button v-for="(tpl, key) in presets" :key="key" @click="applyPreset(key)"
              class="preset-btn px-2.5 py-1 rounded-lg text-[11px] transition">
              {{ tpl.label }}
            </button>
          </div>
        </div>

        <!-- API URL -->
        <div>
          <label class="lbl">API 地址 <span class="text-faint">(base_url/chat/completions)</span></label>
          <input v-model="form.api_url" class="inp" placeholder="https://api.openai.com/v1/chat/completions" />
        </div>

        <!-- API Key -->
        <div>
          <label class="lbl">API Key</label>
          <div class="relative">
            <input v-model="form.api_key" :type="showKey ? 'text' : 'password'" class="inp pr-16" placeholder="sk-..." />
            <button @click="showKey=!showKey" class="toggle-key-btn absolute right-2 top-1/2 -translate-y-1/2 text-[10px]">{{ showKey ? '隐藏' : '显示' }}</button>
          </div>
        </div>

        <!-- Model -->
        <div>
          <label class="lbl">模型名称</label>
          <input v-model="form.model" class="inp" placeholder="deepseek-v4-flash / gpt-4o / glm-4-flash" />
        </div>

        <!-- Temperature & Max Tokens -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="lbl">Temperature <span class="text-faint">({{ form.temperature }})</span></label>
            <input v-model.number="form.temperature" type="range" min="0" max="2" step="0.1" class="w-full" style="accent-color: var(--accent)" />
          </div>
          <div>
            <label class="lbl">Max Tokens</label>
            <input v-model.number="form.max_tokens" type="number" class="inp" min="256" max="32768" step="256" />
          </div>
        </div>

        <!-- 保存按钮 -->
        <div class="flex items-center gap-3 pt-1">
          <button @click="saveSettings" :disabled="saving" class="btn-accent px-5 py-2 rounded-lg text-xs font-medium transition disabled:opacity-50">
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
          <button @click="testConnection" :disabled="testing" class="btn-surface px-5 py-2 rounded-lg text-xs transition disabled:opacity-50">
            {{ testing ? '测试中...' : '测试连接' }}
          </button>
          <button @click="resetSettings" class="reset-btn px-5 py-2 text-xs transition">重置为默认</button>
        </div>

        <!-- 测试结果 -->
        <div v-if="testResult" class="px-3 py-2 rounded-lg text-[11px] border" :style="testResult.ok ? 'background: color-mix(in srgb, var(--color-success) 10%, transparent); border-color: color-mix(in srgb, var(--color-success) 20%, transparent); color: var(--color-success)' : 'background: color-mix(in srgb, var(--color-error) 10%, transparent); border-color: color-mix(in srgb, var(--color-error) 20%, transparent); color: var(--color-error)'">
          {{ testResult.msg }}
        </div>
      </section>

      <!-- 当前配置预览 -->
      <section class="section-card rounded-xl p-5 space-y-3">
        <h2 class="text-sm font-semibold">当前生效配置</h2>
        <div class="grid grid-cols-2 gap-2 text-[11px]">
          <div style="color: var(--text-tertiary)">API 地址</div>
          <div class="truncate" style="color: var(--text-muted)">{{ form.api_url || '系统默认 (sensenova)' }}</div>
          <div style="color: var(--text-tertiary)">API Key</div>
          <div style="color: var(--text-muted)">{{ form.api_key ? form.api_key.slice(0, 8) + '...' : '系统默认' }}</div>
          <div style="color: var(--text-tertiary)">模型</div>
          <div style="color: var(--text-muted)">{{ form.model || '系统默认 (deepseek-v4-flash)' }}</div>
          <div style="color: var(--text-tertiary)">Temperature</div>
          <div style="color: var(--text-muted)">{{ form.temperature || 0.7 }}</div>
          <div style="color: var(--text-tertiary)">Max Tokens</div>
          <div style="color: var(--text-muted)">{{ form.max_tokens || 8192 }}</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { get, put } from '@/api'

const auth = useAuthStore()
const saved = ref(false)
const saving = ref(false)
const testing = ref(false)
const showKey = ref(false)
const testResult = ref<{ok: boolean; msg: string} | null>(null)

const form = reactive({
  api_url: '',
  api_key: '',
  model: '',
  temperature: 0.7,
  max_tokens: 8192
})

const presets: Record<string, {label: string; api_url: string; model: string}> = {
  deepseek: { label: 'DeepSeek', api_url: 'https://api.deepseek.com/v1/chat/completions', model: 'deepseek-chat' },
  sensenova: { label: '商汤日日新', api_url: 'https://token.sensenova.cn/v1/chat/completions', model: 'deepseek-v4-flash' },
  openai: { label: 'OpenAI', api_url: 'https://api.openai.com/v1/chat/completions', model: 'gpt-4o' },
  zhipu: { label: '智谱 GLM', api_url: 'https://open.bigmodel.cn/api/paas/v4/chat/completions', model: 'glm-4-flash' },
  moonshot: { label: 'Moonshot', api_url: 'https://api.moonshot.cn/v1/chat/completions', model: 'moonshot-v1-8k' },
  qwen: { label: '通义千问', api_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', model: 'qwen-plus' },
  siliconflow: { label: 'SiliconFlow', api_url: 'https://api.siliconflow.cn/v1/chat/completions', model: 'deepseek-ai/DeepSeek-V3' },
  custom: { label: '自定义', api_url: '', model: '' }
}

function applyPreset(key: string) {
  const tpl = presets[key]
  if (tpl) {
    form.api_url = tpl.api_url
    form.model = tpl.model
  }
}

async function loadSettings() {
  try {
    const data = await get<any>('/user/llm-settings')
    if (data.api_url) form.api_url = data.api_url
    if (data.api_key) form.api_key = data.api_key
    if (data.model) form.model = data.model
    if (data.temperature != null) form.temperature = data.temperature
    if (data.max_tokens != null) form.max_tokens = data.max_tokens
  } catch {}
}

async function saveSettings() {
  saving.value = true
  saved.value = false
  try {
    await put('/user/llm-settings', form)
    saved.value = true
    setTimeout(() => { saved.value = false }, 2000)
  } catch (e: any) {
    alert('保存失败: ' + (e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    const url = form.api_url || 'https://token.sensenova.cn/v1/chat/completions'
    const key = form.api_key || ''
    const model = form.model || 'deepseek-v4-flash'
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${key}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model,
        messages: [{ role: 'user', content: 'Hi, reply with just OK' }],
        max_tokens: 8
      })
    })
    if (res.ok) {
      const data = await res.json()
      const content = data.choices?.[0]?.message?.content || ''
      testResult.value = { ok: true, msg: `连接成功！模型回复: "${content.slice(0, 50)}"` }
    } else {
      const text = await res.text()
      testResult.value = { ok: false, msg: `HTTP ${res.status}: ${text.slice(0, 150)}` }
    }
  } catch (e: any) {
    testResult.value = { ok: false, msg: `连接失败: ${e.message}` }
  } finally {
    testing.value = false
  }
}

async function resetSettings() {
  form.api_url = ''
  form.api_key = ''
  form.model = ''
  form.temperature = 0.7
  form.max_tokens = 8192
  await saveSettings()
}

onMounted(loadSettings)
</script>

<style scoped>
.section-card {
  background: var(--bg-surface-2);
}
.lbl {
  display: block;
  font-size: 11px;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}
.text-faint {
  color: var(--text-tertiary);
  opacity: 0.5;
}
.inp {
  width: 100%;
  background: var(--bg-surface-2);
  border: 1px solid var(--border-hairline);
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
  outline: none;
  transition: border-color 0.2s;
}
.inp:focus {
  border-color: var(--accent);
}
.back-btn {
  color: var(--text-tertiary);
  transition: color 0.2s;
}
.back-btn:hover {
  color: var(--text-primary);
}
.preset-btn {
  background: var(--bg-surface-2);
  color: var(--text-tertiary);
}
.preset-btn:hover {
  color: var(--text-secondary);
  background: var(--bg-surface-3);
}
.toggle-key-btn {
  color: var(--text-tertiary);
}
.toggle-key-btn:hover {
  color: var(--text-muted);
}
.btn-accent {
  background: var(--accent);
  color: var(--text-primary);
}
.btn-accent:hover:not(:disabled) {
  background: var(--accent-hover);
}
.btn-surface {
  background: var(--bg-surface-2);
  color: var(--text-muted);
}
.btn-surface:hover:not(:disabled) {
  background: var(--bg-surface-3);
}
.reset-btn {
  color: var(--text-tertiary);
}
.reset-btn:hover {
  color: var(--color-error);
}
</style>
