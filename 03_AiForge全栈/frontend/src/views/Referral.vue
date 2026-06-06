<template>
  <div class="p-6 h-full overflow-y-auto" style="background: var(--bg-canvas)">
    <div class="max-w-4xl mx-auto">
      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <svg class="w-8 h-8 animate-spin" style="color: var(--accent)" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>

      <!-- Not an agent -->
      <div v-else-if="notAgent" class="glass-card p-10 text-center animate-fade-in">
        <div class="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-5" style="background: var(--accent-subtle)">
          <svg class="w-8 h-8" style="color: var(--accent)" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
          </svg>
        </div>
        <h2 class="font-display text-xl font-bold mb-2" style="color: var(--text-primary)">您还不是代理</h2>
        <p class="text-sm" style="color: var(--text-muted)">如需成为代理，请联系管理员</p>
      </div>

      <!-- Agent dashboard -->
      <template v-else-if="agent">
        <!-- Header -->
        <div class="text-center mb-8 animate-fade-in">
          <h1 class="font-display text-3xl font-bold mb-2" style="color: var(--text-primary)">我的邀请</h1>
          <p class="text-sm" style="color: var(--text-muted)">分享邀请链接，邀请好友注册即可获得佣金</p>
        </div>

        <!-- Invite link card -->
        <div class="glass-card p-5 mb-6 animate-fade-in">
          <h3 class="font-display text-lg font-semibold mb-4 flex items-center gap-2" style="color: var(--text-primary)">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: var(--accent)">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            邀请链接
          </h3>
          <div class="flex gap-3 items-center">
            <div class="flex-1 rounded-xl px-4 py-3 text-sm font-mono tracking-wide truncate" style="background: var(--bg-surface-2); color: var(--text-primary)">
              {{ inviteLink }}
            </div>
            <button @click="copyLink" class="btn-primary whitespace-nowrap text-sm">
              {{ copied ? '已复制' : '复制链接' }}
            </button>
          </div>
          <div class="mt-3 flex items-center gap-2">
            <span class="text-xs" style="color: var(--text-muted)">邀请码：</span>
            <span class="text-sm font-mono font-semibold tracking-wider" style="color: var(--accent)">{{ agent.ref_code }}</span>
          </div>
        </div>

        <!-- Stats grid -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6 animate-fade-in">
          <div class="glass-card p-4 text-center">
            <div class="text-xs mb-1" style="color: var(--text-muted)">佣金比例</div>
            <div class="font-display text-2xl font-bold" style="color: var(--accent)">{{ (agent.commission_rate * 100).toFixed(0) }}%</div>
          </div>
          <div class="glass-card p-4 text-center">
            <div class="text-xs mb-1" style="color: var(--text-muted)">邀请人数</div>
            <div class="font-display text-2xl font-bold" style="color: var(--text-primary)">{{ agent.total_referrals }}</div>
          </div>
          <div class="glass-card p-4 text-center">
            <div class="text-xs mb-1" style="color: var(--text-muted)">总佣金</div>
            <div class="font-display text-2xl font-bold" style="color: var(--text-primary)">¥{{ agent.total_commission.toFixed(2) }}</div>
          </div>
          <div class="glass-card p-4 text-center">
            <div class="text-xs mb-1" style="color: var(--text-muted)">已结算 / 未结算</div>
            <div class="font-display text-lg font-bold" style="color: var(--text-primary)">¥{{ agent.settled_commission.toFixed(2) }} <span style="color: var(--text-muted)">/</span> ¥{{ agent.pending_commission.toFixed(2) }}</div>
          </div>
        </div>

        <!-- Referrals list -->
        <div class="glass-card p-5 mb-6 animate-fade-in">
          <h3 class="font-display text-lg font-semibold mb-4 flex items-center gap-2" style="color: var(--text-primary)">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: var(--accent)">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            邀请人列表
          </h3>
          <div v-if="referrals.length === 0" class="text-center py-8">
            <p class="text-sm" style="color: var(--text-muted)">暂无邀请记录</p>
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr style="border-bottom: 1px solid var(--border-hairline)">
                  <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted)">用户</th>
                  <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted)">注册时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in referrals" :key="r.id" style="border-bottom: 1px solid var(--border-hairline)">
                  <td class="py-2.5 px-3" style="color: var(--text-primary)">{{ r.nickname || r.email }}</td>
                  <td class="py-2.5 px-3" style="color: var(--text-muted)">{{ formatDate(r.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Commission orders -->
        <div class="glass-card p-5 animate-fade-in">
          <h3 class="font-display text-lg font-semibold mb-4 flex items-center gap-2" style="color: var(--text-primary)">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: var(--accent)">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            佣金订单
          </h3>
          <div v-if="orders.length === 0" class="text-center py-8">
            <p class="text-sm" style="color: var(--text-muted)">暂无佣金记录</p>
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr style="border-bottom: 1px solid var(--border-hairline)">
                  <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted)">用户</th>
                  <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted)">订单金额</th>
                  <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted)">佣金</th>
                  <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted)">状态</th>
                  <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted)">时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="o in orders" :key="o.id" style="border-bottom: 1px solid var(--border-hairline)">
                  <td class="py-2.5 px-3" style="color: var(--text-primary)">{{ o.user_nickname || o.user_email }}</td>
                  <td class="py-2.5 px-3" style="color: var(--text-primary)">¥{{ o.order_amount.toFixed(2) }}</td>
                  <td class="py-2.5 px-3 font-medium" style="color: var(--accent)">¥{{ o.commission.toFixed(2) }}</td>
                  <td class="py-2.5 px-3">
                    <span
                      class="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
                      :style="o.status === 'settled'
                        ? 'background: color-mix(in srgb, var(--color-success) 15%, transparent); color: var(--color-success)'
                        : 'background: color-mix(in srgb, var(--accent) 15%, transparent); color: var(--accent)'"
                    >{{ o.status === 'settled' ? '已结算' : '未结算' }}</span>
                  </td>
                  <td class="py-2.5 px-3" style="color: var(--text-muted)">{{ formatDate(o.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { get } from '@/api'

interface AgentInfo {
  ref_code: string
  commission_rate: number
  total_referrals: number
  total_commission: number
  settled_commission: number
  pending_commission: number
}

interface ReferralUser {
  id: number
  email: string
  nickname: string
  created_at: string
}

interface CommissionOrder {
  id: number
  user_email: string
  user_nickname: string
  order_amount: number
  commission: number
  status: 'pending' | 'settled'
  created_at: string
}

const loading = ref(true)
const notAgent = ref(false)
const agent = ref<AgentInfo | null>(null)
const referrals = ref<ReferralUser[]>([])
const orders = ref<CommissionOrder[]>([])
const copied = ref(false)

const inviteLink = computed(() => {
  if (!agent.value) return ''
  return `${window.location.origin}/login?ref=${agent.value.ref_code}`
})

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(inviteLink.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // fallback
    const input = document.createElement('input')
    input.value = inviteLink.value
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}

onMounted(async () => {
  try {
    const data = await get<AgentInfo>('/admin/api/my-agent')
    agent.value = data
    // Load referrals and orders in parallel
    const [refData, orderData] = await Promise.all([
      get<ReferralUser[]>('/admin/api/my-agent/referrals'),
      get<CommissionOrder[]>('/admin/api/my-agent/orders'),
    ])
    referrals.value = refData
    orders.value = orderData
  } catch (err: any) {
    if (err.status === 403 || err.status === 404) {
      notAgent.value = true
    }
  } finally {
    loading.value = false
  }
})
</script>
