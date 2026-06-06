<template>
  <div class="p-6 h-full overflow-y-auto">
    <h1 class="font-display text-2xl font-bold mb-6" style="color:var(--text-primary)">管理后台</h1>

    <div class="space-y-6">
      <div class="glass-card p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-display text-lg font-semibold" style="color:var(--text-primary)">账号池</h2>
          <div class="flex gap-2">
            <button @click="refreshPool" :disabled="poolRefreshing" class="btn-secondary text-xs px-3 py-1.5">
              {{ poolRefreshing ? '刷新中...' : '刷新全部' }}
            </button>
          </div>
        </div>

        <!-- 批量注册区域 -->
        <div class="reg-area rounded-xl p-4 mb-4">
          <h3 class="reg-label text-sm mb-3">自动注册</h3>
          <div class="flex items-center gap-3 flex-wrap">
            <div class="flex items-center gap-2">
              <span class="reg-label text-xs">数量</span>
              <div class="flex gap-1">
                <button v-for="n in [1, 5, 10, 50, 100]" :key="n"
                  @click="regCount = n"
                  :class="regCount === n ? 'reg-btn-active' : 'reg-btn-inactive'"
                  class="px-2.5 py-1 rounded text-xs transition-colors">
                  {{ n }}
                </button>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="reg-label text-xs">并发</span>
              <div class="flex gap-1">
                <button v-for="c in [1, 2, 3, 5]" :key="c"
                  @click="regConcurrent = c"
                  :class="regConcurrent === c ? 'reg-btn-active' : 'reg-btn-inactive'"
                  class="px-2.5 py-1 rounded text-xs transition-colors">
                  {{ c }}
                </button>
              </div>
            </div>
            <button @click="registerAccount" :disabled="poolRegistering" class="btn-primary text-xs px-4 py-1.5">
              {{ poolRegistering ? '注册中...' : `注册 ${regCount} 个` }}
            </button>
          </div>

          <!-- 注册进度 -->
          <div v-if="regJobId" class="mt-3">
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="reg-label">{{ regProgressText }}</span>
              <span style="color: var(--text-tertiary)">{{ regProgress[0] }}/{{ regProgress[1] }}</span>
            </div>
            <div class="w-full rounded-full h-1.5" style="background: var(--bg-surface-2)">
              <div class="h-1.5 rounded-full transition-all duration-300" style="background: var(--accent)"
                :style="{ width: regProgress[1] > 0 ? (regProgress[0] / regProgress[1] * 100) + '%' : '0%' }"></div>
            </div>
            <div v-if="regResult" class="mt-2 text-xs space-y-0.5">
              <span style="color: var(--color-success)">成功: {{ regResult.registered }}</span>
              <span style="color: var(--text-tertiary)" class="mx-1">|</span>
              <span style="color: var(--color-error)">失败: {{ regResult.failed }}</span>
              <span v-if="regTotalPoints > 0" style="color: var(--text-tertiary)" class="mx-1">|</span>
              <span v-if="regTotalPoints > 0" class="accent-text">总积分: {{ regTotalPoints }}</span>
            </div>
          </div>
        </div>

        <div v-if="poolLoading" class="flex items-center justify-center py-10">
          <div class="w-8 h-8 border-3 rounded-full animate-spin spinner"></div>
        </div>

        <div v-else-if="poolError" class="text-sm py-4" style="color: var(--color-error)">{{ poolError }}</div>

        <div v-else>
          <div class="grid grid-cols-3 gap-4 mb-4">
            <div class="stat-card rounded-xl p-4 text-center">
              <p class="stat-label text-xs mb-1">总账号</p>
              <p class="font-display text-2xl font-bold" style="color:var(--text-primary)">{{ poolStatus.total_accounts || 0 }}</p>
            </div>
            <div class="stat-card rounded-xl p-4 text-center">
              <p class="stat-label text-xs mb-1">活跃账号</p>
              <p class="font-display text-2xl font-bold" style="color: var(--color-success)">{{ poolStatus.active_accounts || 0 }}</p>
            </div>
            <div class="stat-card rounded-xl p-4 text-center">
              <p class="stat-label text-xs mb-1">总积分</p>
              <p class="accent-text font-display text-2xl font-bold">{{ poolStatus.total_points || 0 }}</p>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="table-header">
                  <th class="text-left py-2 px-3">ID</th>
                  <th class="text-left py-2 px-3">邮箱</th>
                  <th class="text-left py-2 px-3">积分</th>
                  <th class="text-left py-2 px-3">状态</th>
                  <th class="text-left py-2 px-3">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(a, idx) in (poolStatus.accounts || [])" :key="a.id" class="table-row">
                  <td class="py-2 px-3" style="color: var(--text-muted)">{{ a.id }}</td>
                  <td class="py-2 px-3" style="color: var(--text-secondary)">{{ a.email }}</td>
                  <td class="py-2 px-3" :style="a.points_remaining < 60 ? 'color: var(--color-error)' : 'color: var(--accent)'">
                    {{ a.points_remaining }}
                    <span v-if="a.points_remaining < 60" class="text-xs ml-1" style="color: var(--color-error)">仅生图</span>
                  </td>
                  <td class="py-2 px-3">
                    <span :class="statusClass(a.status)">{{ statusLabel(a.status) }}</span>
                  </td>
                  <td class="py-2 px-3">
                    <button @click="removeAccount(a.id)" class="text-xs transition-colors" style="color: var(--color-error)">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="mt-6 pt-4">
            <h3 class="reg-label text-sm mb-3">手动添加账号</h3>
            <div class="flex gap-2">
              <input v-model="newEmail" type="text" placeholder="邮箱" class="input-field flex-1 text-sm" />
              <input v-model="newPassword" type="text" placeholder="密码" class="input-field flex-1 text-sm" />
              <button @click="addAccount" :disabled="!newEmail || !newPassword || addingAccount" class="btn-primary text-xs px-4">
                {{ addingAccount ? '添加中...' : '添加' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="glass-card p-6">
          <h2 class="font-display text-lg font-semibold mb-4" style="color:var(--text-primary)">用户管理</h2>

          <div v-if="usersLoading" class="flex items-center justify-center py-10">
            <div class="w-8 h-8 border-3 rounded-full animate-spin spinner"></div>
          </div>

          <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="table-header">
                  <th class="text-left py-2 px-3">ID</th>
                  <th class="text-left py-2 px-3">邮箱</th>
                  <th class="text-left py-2 px-3">昵称</th>
                  <th class="text-left py-2 px-3">积分</th>
                  <th class="text-left py-2 px-3">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(u, idx) in users" :key="u.id" class="table-row">
                  <td class="py-2 px-3" style="color: var(--text-muted)">{{ u.id }}</td>
                  <td class="py-2 px-3" style="color: var(--text-secondary)">{{ u.email }}</td>
                  <td class="py-2 px-3" style="color: var(--text-secondary)">{{ u.nickname }}</td>
                  <td class="py-2 px-3 accent-text">{{ u.points }}</td>
                  <td class="py-2 px-3">
                    <button @click="addPoints(u.id)" class="text-xs px-3 py-1 rounded-lg transition-colors accent-btn">
                      加积分
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="glass-card p-6">
          <h2 class="font-display text-lg font-semibold mb-4" style="color:var(--text-primary)">兑换码生成</h2>

          <div class="space-y-4">
            <div>
              <label class="label-text">积分数量</label>
              <input v-model.number="codePoints" type="number" min="1" placeholder="输入积分数量" class="input-field" />
            </div>
            <button @click="generateCode" :disabled="!codePoints || codeGenerating" class="btn-primary">
              {{ codeGenerating ? '生成中...' : '生成兑换码' }}
            </button>

            <div v-if="generatedCode" class="reg-area rounded-xl p-4 mt-4">
              <p class="reg-label text-sm mb-1">兑换码</p>
              <p class="accent-text font-mono text-lg font-bold">{{ generatedCode }}</p>
              <p style="color: var(--text-tertiary)" class="text-xs mt-1">积分: {{ generatedPoints }}</p>
              <button @click="copyCode" class="btn-secondary text-xs mt-3 px-3 py-1.5">
                {{ copied ? '已复制' : '复制' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { get, post, del } from '@/api'

interface AdminUser {
  id: number
  email: string
  nickname: string
  points: number
}

interface PoolAccount {
  id: number
  email: string
  points_remaining: number
  status: string
}

interface PoolStatus {
  total_accounts: number
  active_accounts: number
  total_points: number
  accounts: PoolAccount[]
}

const users = ref<AdminUser[]>([])
const usersLoading = ref(true)
const codePoints = ref<number | null>(null)
const codeGenerating = ref(false)
const generatedCode = ref('')
const generatedPoints = ref(0)
const copied = ref(false)

const poolStatus = ref<PoolStatus>({ total_accounts: 0, active_accounts: 0, total_points: 0, accounts: [] })
const poolLoading = ref(true)
const poolError = ref('')
const poolRefreshing = ref(false)
const poolRegistering = ref(false)
const newEmail = ref('')
const newPassword = ref('')
const addingAccount = ref(false)

const regCount = ref(1)
const regConcurrent = ref(1)
const regJobId = ref('')
const regProgress = ref<[number, number]>([0, 0])
const regResult = ref<{ registered: number; failed: number } | null>(null)
const regProgressText = ref('准备中...')
const regDetails = ref<any[]>([])
const regTotalPoints = ref(0)
let regPollTimer: ReturnType<typeof setInterval> | null = null

function statusClass(status: string): string {
  if (status === 'active') return 'status-active'
  if (status === 'exhausted') return 'status-exhausted'
  return 'status-error'
}

function statusLabel(status: string): string {
  if (status === 'active') return '活跃'
  if (status === 'exhausted') return '耗尽'
  return '异常'
}

async function fetchPoolStatus() {
  poolLoading.value = true
  poolError.value = ''
  try {
    const data = await get<PoolStatus>('/pool/status')
    if ((data as any).error) {
      poolError.value = (data as any).error
    } else {
      poolStatus.value = data
    }
  } catch (err: any) {
    poolError.value = '无法连接 OiioiiPool（请确认 7861 端口运行中）'
  } finally {
    poolLoading.value = false
  }
}

async function refreshPool() {
  poolRefreshing.value = true
  try {
    await post('/pool/refresh')
    await fetchPoolStatus()
  } catch (err: any) {
    alert('刷新失败: ' + err.message)
  } finally {
    poolRefreshing.value = false
  }
}

async function registerAccount() {
  poolRegistering.value = true
  regResult.value = null
  regProgress.value = [0, regCount.value]
  regProgressText.value = '提交任务中...'
  try {
    const data = await post<any>(`/pool/register?count=${regCount.value}&concurrent=${regConcurrent.value}`)
    if (data.job_id) {
      regJobId.value = data.job_id
      regProgressText.value = '注册中...'
      // 轮询进度
      regPollTimer = setInterval(async () => {
        try {
          const status = await get<any>(`/pool/register/${data.job_id}`)
          if (status.status === 'running') {
            regProgress.value = status.progress || [0, regCount.value]
            regProgressText.value = `注册中 ${regProgress.value[0]}/${regProgress.value[1]}`
          } else if (status.status === 'done') {
            regProgress.value = [regCount.value, regCount.value]
            regResult.value = { registered: status.registered, failed: status.failed }
            regDetails.value = status.details || []
            regTotalPoints.value = regDetails.value.reduce((sum: number, d: any) => sum + (d.success ? (d.points || 0) : 0), 0)
            regProgressText.value = `完成！成功 ${status.registered}，失败 ${status.failed}`
            if (regPollTimer) { clearInterval(regPollTimer); regPollTimer = null }
            poolRegistering.value = false
            await fetchPoolStatus()
          } else {
            regProgressText.value = '注册失败: ' + (status.error || '未知错误')
            if (regPollTimer) { clearInterval(regPollTimer); regPollTimer = null }
            poolRegistering.value = false
          }
        } catch {
          if (regPollTimer) { clearInterval(regPollTimer); regPollTimer = null }
          poolRegistering.value = false
        }
      }, 2000)
    } else {
      alert('注册结果: ' + JSON.stringify(data))
      poolRegistering.value = false
    }
  } catch (err: any) {
    alert('注册失败: ' + err.message)
    poolRegistering.value = false
  }
}

async function addAccount() {
  if (!newEmail.value || !newPassword.value) return
  addingAccount.value = true
  try {
    const data = await post<any>('/pool/add', { email: newEmail.value, password: newPassword.value })
    alert('添加成功! 积分: ' + (data.points || '未知'))
    newEmail.value = ''
    newPassword.value = ''
    await fetchPoolStatus()
  } catch (err: any) {
    alert('添加失败: ' + err.message)
  } finally {
    addingAccount.value = false
  }
}

async function removeAccount(accountId: number) {
  if (!confirm('确定删除账号 #' + accountId + '？')) return
  try {
    await del('/pool/' + accountId)
    await fetchPoolStatus()
  } catch (err: any) {
    alert('删除失败: ' + err.message)
  }
}

async function fetchUsers() {
  usersLoading.value = true
  try {
    users.value = await get<AdminUser[]>('/user/admin/users')
  } catch (err: any) {
    alert('加载用户列表失败: ' + err.message)
  } finally {
    usersLoading.value = false
  }
}

async function addPoints(uid: number) {
  const pointsStr = prompt('输入要增加的积分数量:')
  if (!pointsStr) return
  const points = parseInt(pointsStr)
  if (isNaN(points) || points <= 0) {
    alert('请输入有效的积分数量')
    return
  }
  try {
    await post(`/user/admin/add_points?uid=${uid}&points=${points}`)
    await fetchUsers()
    alert('积分添加成功')
  } catch (err: any) {
    alert('添加失败: ' + err.message)
  }
}

async function generateCode() {
  if (!codePoints.value) return
  codeGenerating.value = true
  try {
    const data = await post<{ code: string; points: number }>(`/user/admin/redeem?points=${codePoints.value}`)
    generatedCode.value = data.code
    generatedPoints.value = data.points
  } catch (err: any) {
    alert('生成失败: ' + err.message)
  } finally {
    codeGenerating.value = false
  }
}

async function copyCode() {
  try {
    await navigator.clipboard.writeText(generatedCode.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    const el = document.createElement('textarea')
    el.value = generatedCode.value
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}

onMounted(() => {
  fetchPoolStatus()
  fetchUsers()
})
</script>

<style scoped>
.reg-area {
  background: var(--bg-surface-1);
}
.reg-label {
  color: var(--text-muted);
}
.stat-card {
  background: var(--bg-surface-1);
}
.stat-label {
  color: var(--text-muted);
}
.accent-text {
  color: var(--accent);
}
.reg-btn-active {
  background: var(--accent);
  color: var(--text-primary);
}
.reg-btn-inactive {
  background: var(--bg-surface-2);
  color: var(--text-muted);
}
.reg-btn-inactive:hover {
  background: var(--bg-surface-3);
}
.accent-btn {
  background: var(--accent-subtle);
  color: var(--accent);
}
.accent-btn:hover {
  background: var(--accent-glow);
}
.spinner {
  border-color: var(--accent-glow);
  border-top-color: var(--accent);
}
.status-active {
  color: var(--color-success);
  background: color-mix(in srgb, var(--color-success) 10%, transparent);
  padding: 0 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}
.status-exhausted {
  color: var(--color-warning);
  background: color-mix(in srgb, var(--color-warning) 10%, transparent);
  padding: 0 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}
.status-error {
  color: var(--color-error);
  background: color-mix(in srgb, var(--color-error) 10%, transparent);
  padding: 0 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}
.table-header {
  background: var(--bg-surface-1);
  color: var(--text-muted);
}
.table-row:hover {
  background: var(--bg-surface-3);
}
.table-row:nth-child(odd) {
  background: var(--bg-surface-2);
}
.table-row:nth-child(even) {
  background: transparent;
}
</style>
