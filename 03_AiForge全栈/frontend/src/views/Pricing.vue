<template>
  <div class="p-6 h-full overflow-y-auto" style="background: var(--bg-canvas)">
    <div class="max-w-5xl mx-auto">
      <div class="text-center mb-10 animate-fade-in">
        <h1 class="font-display text-3xl font-bold mb-2" style="color: var(--text-primary)">充值中心</h1>
        <p class="text-sm" style="color: var(--text-muted)">选择适合你的积分套餐，释放创作力</p>
      </div>

      <div class="glass-card p-5 mb-8 flex items-center justify-between animate-fade-in">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center" style="background: var(--accent); box-shadow: 0 0 20px var(--accent-glow)">
            <svg class="w-6 h-6" style="color:var(--text-primary)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
          </div>
          <div>
            <div class="text-sm" style="color: var(--text-muted)">当前积分余额</div>
            <div class="font-display text-2xl font-bold" style="color: var(--text-primary)">{{ auth.userPoints.toLocaleString() }}</div>
          </div>
        </div>
        <div class="text-right">
          <div class="text-xs" style="color: var(--text-tertiary)">积分有效期</div>
          <div class="text-sm" style="color: var(--text-secondary)">自充值日起 30 天</div>
        </div>
      </div>

      <div class="glass-card p-6 mb-8 animate-fade-in">
        <h3 class="font-display text-lg font-semibold mb-4 flex items-center gap-2" style="color: var(--text-primary)">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: var(--accent)"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" /></svg>
          兑换码充值
        </h3>
        <div class="flex gap-3">
          <input
            v-model="redeemInput"
            type="text"
            placeholder="请输入兑换码（如 AFXXXXXXXXXXXX）"
            class="input-field flex-1 font-mono tracking-wider uppercase"
            @keyup.enter="handleRedeem"
          />
          <button
            @click="handleRedeem"
            :disabled="!redeemInput.trim() || redeeming"
            class="btn-primary whitespace-nowrap"
          >
            {{ redeeming ? '兑换中...' : '兑换' }}
          </button>
        </div>
        <p v-if="redeemMsg" :class="['text-sm mt-3', redeemOk ? '' : '']" :style="redeemOk ? 'color: var(--color-success)' : 'color: var(--color-error)'">
          {{ redeemMsg }}
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
        <div
          v-for="(plan, idx) in plans"
          :key="plan.id"
          :class="[
            'relative glass-card p-6 flex flex-col transition-all duration-300 animate-fade-in',
            plan.popular ? 'plan-popular scale-[1.02]' : 'plan-default'
          ]"
          :style="{ animationDelay: `${idx * 80}ms` }"
        >
          <div
            v-if="plan.popular"
            class="absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-semibold px-4 py-1 rounded-full"
            style="background: var(--accent); color: var(--text-primary); box-shadow: 0 0 20px var(--accent-glow)"
          >
            推荐
          </div>

          <div class="mb-4">
            <h3 class="font-display text-lg font-bold" style="color: var(--text-primary)">{{ plan.name }}</h3>
            <div class="text-xs mt-1" style="color: var(--text-muted)">有效期 {{ plan.days }} 天</div>
          </div>

          <div class="mb-4">
            <div class="flex items-baseline gap-1">
              <span class="text-sm" style="color: var(--text-muted)">¥</span>
              <span class="font-display text-4xl font-extrabold" style="color: var(--text-primary)">{{ formatPrice(plan.price) }}</span>
            </div>
            <div class="flex items-center gap-2 mt-2">
              <span class="font-semibold text-sm" style="color: var(--accent)">{{ plan.points.toLocaleString() }} 积分</span>
              <span class="text-xs" style="color: var(--text-tertiary)">|</span>
              <span class="text-xs" style="color: var(--text-muted)">¥{{ unitPrice(plan) }}/百积分</span>
            </div>
          </div>

          <div class="flex-1" />

          <button
            :class="[
              'w-full py-2.5 rounded-lg font-medium text-sm transition-all duration-200 active:scale-[0.97]',
              plan.popular ? 'btn-primary' : 'btn-secondary'
            ]"
            @click="handlePurchase(plan)"
          >
            立即购买
          </button>
        </div>
      </div>

      <div class="glass-card p-6 animate-fade-in">
        <h3 class="font-display text-lg font-semibold mb-5 flex items-center gap-2" style="color: var(--text-primary)">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: var(--accent)"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          积分使用说明
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <div class="text-sm font-medium mb-3 flex items-center gap-2" style="color: var(--text-secondary)">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: var(--accent)"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
              视频生成
            </div>
            <div class="space-y-2">
              <div class="flex items-center justify-between text-sm">
                <span style="color: var(--text-muted)">谷歌 10s 视频</span>
                <span class="font-medium" style="color: var(--accent)">80 积分/个</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span style="color: var(--text-muted)">5s 视频</span>
                <span class="font-medium" style="color: var(--accent)">48 积分</span>
              </div>
            </div>
          </div>
          <div>
            <div class="text-sm font-medium mb-3 flex items-center gap-2" style="color: var(--text-secondary)">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: var(--accent)"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
              图片生成
            </div>
            <div class="space-y-2">
              <div class="flex items-center justify-between text-sm">
                <span style="color: var(--text-muted)">4K 分辨率</span>
                <span class="font-medium" style="color: var(--accent)">20 积分</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span style="color: var(--text-muted)">2K 分辨率</span>
                <span class="font-medium" style="color: var(--accent)">10 积分</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span style="color: var(--text-muted)">1K 分辨率</span>
                <span class="font-medium" style="color: var(--accent)">5 积分</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Transition name="toast">
        <div
          v-if="toast.visible"
          :class="[
            'fixed top-6 left-1/2 -translate-x-1/2 z-50 glass-card px-6 py-3 flex items-center gap-3',
            toast.type === 'success' ? 'toast-success' : toast.type === 'error' ? 'toast-error' : 'toast-info'
          ]"
        >
          <svg v-if="toast.type === 'success'" class="w-5 h-5 flex-shrink-0" style="color: var(--color-success)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
          <svg v-else-if="toast.type === 'error'" class="w-5 h-5 flex-shrink-0" style="color: var(--color-error)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          <svg v-else class="w-5 h-5 flex-shrink-0" style="color: var(--accent)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <span
            :class="['text-sm font-medium', toast.type === 'success' ? '' : toast.type === 'error' ? '' : '']"
            :style="toast.type === 'success' ? 'color: var(--color-success)' : toast.type === 'error' ? 'color: var(--color-error)' : 'color: var(--accent)'"
          >{{ toast.message }}</span>
        </div>
      </Transition>

      <!-- 收钱吧扫码支付弹窗 -->
      <Transition name="toast">
        <div
          v-if="payModal.visible"
          class="fixed inset-0 z-40 flex items-center justify-center modal-overlay"
          @click.self="closePayModal"
        >
          <div class="glass-card p-8 max-w-sm w-full mx-4 text-center animate-fade-in">
            <h3 class="font-display text-xl font-bold mb-2" style="color: var(--text-primary)">扫码支付</h3>
            <p class="text-sm mb-4" style="color: var(--text-muted)">{{ payModal.planName }}</p>
            <div class="text-3xl font-bold mb-4" style="color: var(--accent)">¥{{ payModal.amount }}</div>
            <p class="text-xs mb-4" style="color: var(--color-warning)">请支付精确金额 ¥{{ payModal.amount }}，勿修改金额</p>
            <div v-if="payModal.qrUrl" class="mb-4">
              <img :src="payModal.qrUrl" alt="收款码" class="w-48 h-48 mx-auto rounded-lg bg-white p-2" />
            </div>
            <div v-if="payModal.polling" class="flex items-center justify-center gap-2 text-sm mb-4" style="color: var(--accent)">
              <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
              等待支付确认...
            </div>
            <div v-else-if="payModal.paid" class="text-sm mb-4 font-medium" style="color: var(--color-success)">支付成功！积分已到账</div>
            <button @click="closePayModal" class="btn-primary w-full mt-2">{{ payModal.paid ? '完成' : '取消' }}</button>
          </div>
        </div>
      </Transition>

      <!-- 联系客服弹窗 -->
      <Transition name="toast">
        <div
          v-if="contactModal.visible"
          class="fixed inset-0 z-40 flex items-center justify-center modal-overlay"
          @click.self="contactModal.visible = false"
        >
          <div class="glass-card p-8 max-w-sm w-full mx-4 text-center animate-fade-in">
            <h3 class="font-display text-xl font-bold mb-2" style="color: var(--text-primary)">联系客服充值</h3>
            <p class="text-sm mb-4" style="color: var(--text-muted)">{{ contactModal.planName }} · ¥{{ contactModal.amount }}</p>
            <div class="rounded-xl p-5 mb-5" style="background: var(--bg-surface-3)">
              <div class="text-xs mb-2" style="color: var(--text-muted)">添加微信客服</div>
              <div class="text-2xl font-bold font-mono tracking-wider select-all" style="color: var(--text-primary)">wx16657290113</div>
            </div>
            <p class="text-xs mb-4" style="color: var(--text-muted)">添加客服微信，发送套餐名称完成充值</p>
            <button @click="contactModal.visible = false" class="btn-primary w-full">知道了</button>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { post, get } from '@/api'

const auth = useAuthStore()

interface Plan {
  id: string
  name: string
  price: number
  points: number
  days: number
  popular?: boolean
}

const plans: Plan[] = [
  { id: 'trial', name: '体验版', price: 9.9, points: 900, days: 30 },
  { id: 'basic', name: '基础版', price: 29.9, points: 3000, days: 30 },
  { id: 'pro', name: '专业版', price: 99, points: 11000, days: 30, popular: true },
  { id: 'ultimate', name: '至尊版', price: 299, points: 38000, days: 30 },
]

const redeemInput = ref('')
const redeeming = ref(false)
const redeemMsg = ref('')
const redeemOk = ref(false)

const toast = reactive({ visible: false, message: '', type: 'info' as 'success' | 'error' | 'info' })
let toastTimer: ReturnType<typeof setTimeout> | null = null

const payModal = reactive({
  visible: false,
  orderId: 0,
  amount: 0,
  planName: '',
  qrUrl: '',
  polling: false,
  paid: false,
})

const contactModal = reactive({
  visible: false,
  planName: '',
  amount: 0,
})
let pollTimer: ReturnType<typeof setInterval> | null = null

function showToast(message: string, type: 'success' | 'error' | 'info' = 'info') {
  if (toastTimer) clearTimeout(toastTimer)
  toast.visible = true
  toast.message = message
  toast.type = type
  toastTimer = setTimeout(() => { toast.visible = false }, 3000)
}

function closePayModal() {
  payModal.visible = false
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  payModal.polling = false
}

function startPolling(orderId: number) {
  payModal.polling = true
  payModal.paid = false
  pollTimer = setInterval(async () => {
    try {
      const data = await get<any>(`/pay/order/${orderId}`)
      if (data.status === 'paid') {
        payModal.polling = false
        payModal.paid = true
        if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
        await auth.fetchPoints()
      }
    } catch { /* ignore */ }
  }, 3000)
  // 5分钟超时
  setTimeout(() => {
    if (payModal.polling) {
      closePayModal()
      showToast('支付超时，请重新下单', 'error')
    }
  }, 300000)
}

function formatPrice(price: number) {
  return price % 1 === 0 ? price.toString() : price.toFixed(1)
}

function unitPrice(plan: Plan) {
  return ((plan.price / plan.points) * 100).toFixed(2)
}

async function handleRedeem() {
  const code = redeemInput.value.trim().toUpperCase()
  if (!code) return
  redeeming.value = true
  redeemMsg.value = ''
  redeemOk.value = false
  try {
    const data = await post<{ ok: boolean; points: number }>(`/user/redeem?code=${encodeURIComponent(code)}`)
    redeemOk.value = true
    redeemMsg.value = `兑换成功！+${data.points} 积分`
    redeemInput.value = ''
    await auth.fetchPoints()
  } catch (err: any) {
    redeemOk.value = false
    redeemMsg.value = err.message || '兑换失败'
  } finally {
    redeeming.value = false
  }
}

async function handlePurchase(plan: Plan) {
  contactModal.visible = true
  contactModal.planName = plan.name
  contactModal.amount = plan.price
}
</script>

<style scoped>
.modal-overlay {
  background: color-mix(in srgb, var(--bg-canvas) 60%, transparent);
}

.plan-popular {
  box-shadow: 0 0 20px var(--accent-glow);
}

.plan-default {
  transition: transform 0.3s ease, background 0.2s ease;
}

.plan-default:hover {
  transform: translateY(-4px);
  background: var(--bg-surface-3);
}

.toast-success {
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--color-success) 20%, transparent);
}

.toast-error {
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--color-error) 20%, transparent);
}

.toast-info {
  box-shadow: inset 0 0 0 1px var(--accent-glow);
}

.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translate(-50%, -20px);
}
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -10px);
}
</style>
