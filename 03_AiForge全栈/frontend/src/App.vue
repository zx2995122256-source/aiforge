<template>
  <div v-if="isLoginPage">
    <router-view />
  </div>

  <div v-else class="app-shell">
    <!-- ─── Sidebar ─── -->
    <aside ref="sidebarRef" class="sidebar">
      <!-- Logo -->
      <div class="sidebar-logo">
        <svg ref="logoIconRef" class="sidebar-logo-icon" viewBox="0 0 32 32" fill="none" :style="{ color: 'var(--accent)' }">
          <path d="M16 4L6 13l4 4-4 4 10 9 10-9-4-4 4-4-10-9z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
          <circle cx="16" cy="16" r="2.5" fill="currentColor" opacity="0.6"/>
        </svg>
        <h1 ref="logoTextRef" class="sidebar-logo-text" :style="{ color: 'var(--accent)' }">锻造</h1>
        <h1 class="sidebar-logo-letter" :style="{ color: 'var(--accent)' }">F</h1>
      </div>

      <!-- Navigation -->
      <nav ref="navRef" class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="[
            'nav-item',
            isActive(item.to) ? 'nav-item--active' : ''
          ]"
          @mouseenter="onNavEnter($event, item.to)"
          @mouseleave="onNavLeave($event, item.to)"
        >
          <component :is="item.icon" class="nav-item-icon" />
          <span class="nav-item-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- User section -->
      <div class="sidebar-user" ref="userSectionRef">
        <div class="sidebar-user-info">
          <div class="sidebar-avatar" :style="{ background: 'var(--accent)' }">
            {{ userInitial }}
          </div>
          <div class="sidebar-user-detail">
            <p class="sidebar-user-name">{{ auth.user?.nickname || '用户' }}</p>
            <p class="sidebar-user-points">{{ auth.userPoints }} 积分</p>
          </div>
        </div>

        <button
          @click="showContact = true"
          class="sidebar-action-btn"
          :style="{ color: 'var(--text-tertiary)' }"
          @mouseenter="onBtnHover($event.currentTarget as HTMLElement, 'var(--accent)')"
          @mouseleave="onBtnHover($event.currentTarget as HTMLElement, 'var(--text-tertiary)')"
        >
          <svg class="sidebar-action-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <span class="sidebar-action-label">联系客服</span>
        </button>

        <button
          @click="handleLogout"
          class="sidebar-action-btn"
          :style="{ color: 'var(--text-tertiary)' }"
          @mouseenter="onBtnHover($event.currentTarget as HTMLElement, '#ef4444')"
          @mouseleave="onBtnHover($event.currentTarget as HTMLElement, 'var(--text-tertiary)')"
        >
          <svg class="sidebar-action-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span class="sidebar-action-label">退出登录</span>
        </button>
      </div>
    </aside>

    <!-- ─── Contact Modal ─── -->
    <Transition name="modal">
      <div v-if="showContact" class="modal-overlay" @click.self="showContact = false">
        <div class="modal-backdrop"></div>
        <div class="modal-content">
          <div class="modal-icon-wrap">
            <svg class="modal-icon" :style="{ color: 'var(--accent)' }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h3 class="modal-title">联系客服</h3>
          <p class="modal-desc">添加客服微信，获取帮助</p>
          <div class="modal-wechat-bar">
            <svg class="modal-wechat-icon" style="color: #22c55e" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 00.167-.054l1.903-1.114a.864.864 0 01.717-.098 10.16 10.16 0 002.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 01-1.162 1.178A1.17 1.17 0 014.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 01-1.162 1.178 1.17 1.17 0 01-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.82 0 1.623-.107 2.388-.31a.728.728 0 01.603.082l1.6.936a.274.274 0 00.141.046c.136 0 .244-.113.244-.25 0-.06-.024-.12-.04-.178l-.328-1.244a.496.496 0 01.18-.56C23.157 18.404 24 16.82 24 15.042c0-3.21-2.546-5.873-6.062-6.184zM14.25 15.07c.539 0 .976.444.976.992a.984.984 0 01-.976.991.984.984 0 01-.976-.991c0-.548.437-.992.976-.992zm4.88 0c.539 0 .976.444.976.992a.984.984 0 01-.976.991.984.984 0 01-.976-.991c0-.548.437-.992.976-.992z"/>
            </svg>
            <span class="modal-wechat-id">{{ wechatId }}</span>
            <button @click="copyWechat" class="modal-copy-btn">复制</button>
          </div>
          <p class="modal-hours">工作时间: 9:00 - 22:00</p>
          <button @click="showContact = false" class="modal-close-btn">关闭</button>
        </div>
      </div>
    </Transition>

    <!-- ─── Main Area ─── -->
    <main ref="mainRef" class="main-area">
      <!-- Header -->
      <header class="header">
        <h2 class="header-title">{{ pageTitle }}</h2>
        <div class="header-actions">
          <!-- Theme Selector -->
          <div class="theme-selector" ref="themeSelectorRef">
            <button
              @click="themeOpen = !themeOpen"
              class="theme-selector-btn"
            >
              <span class="theme-selector-dot" :style="{ background: 'var(--accent)' }"></span>
              <span class="theme-selector-label">{{ themeStore.currentTheme.label }}</span>
              <svg class="theme-selector-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
            </button>
            <Transition name="dropdown">
              <div v-if="themeOpen" class="theme-dropdown">
                <button
                  v-for="t in themes"
                  :key="t.id"
                  @click="selectTheme(t.id)"
                  :class="['theme-dropdown-item', t.id === themeStore.current ? 'theme-dropdown-item--active' : '']"
                >
                  {{ t.label }}
                </button>
              </div>
            </Transition>
          </div>

          <!-- Points -->
          <span class="header-points">
            积分: <span class="header-points-value">{{ auth.userPoints }}</span>
          </span>
        </div>
      </header>

      <!-- Content -->
      <div class="main-content">
        <router-view v-slot="{ Component }">
          <component :is="Component" :key="$route.path" />
        </router-view>
      </div>
    </main>

    <!-- ─── Toast Notifications ─── -->
    <TransitionGroup name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="['toast', `toast--${toast.type}`]"
        :style="{ top: `${16 + toasts.indexOf(toast) * 56}px` }"
      >
        <span class="toast-message">{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, h, onMounted, watch, nextTick, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore, THEMES, type ThemeId } from '@/stores/theme'
import gsap from 'gsap'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const themeStore = useThemeStore()

const themes = THEMES
const themeOpen = ref(false)
const themeSelectorRef = ref<HTMLElement | null>(null)

function selectTheme(id: ThemeId) {
  themeStore.setTheme(id)
  themeOpen.value = false
}

function onClickOutside(e: MouseEvent) {
  if (themeSelectorRef.value && !themeSelectorRef.value.contains(e.target as Node)) {
    themeOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
  if (!isLoginPage.value) {
    runEntranceAnimations()
  }
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
})

const sidebarRef = ref<HTMLElement | null>(null)
const navRef = ref<HTMLElement | null>(null)
const mainRef = ref<HTMLElement | null>(null)
const logoIconRef = ref<HTMLElement | null>(null)
const logoTextRef = ref<HTMLElement | null>(null)
const userSectionRef = ref<HTMLElement | null>(null)

const isLoginPage = computed(() => route.name === 'login')

function runEntranceAnimations() {
  nextTick(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power2.out', duration: 0.4 } })

    tl.fromTo(sidebarRef.value, { opacity: 0 }, { opacity: 1 })
      .fromTo(logoIconRef.value, { opacity: 0, y: 6 }, { opacity: 1, y: 0 }, '-=0.15')
      .fromTo(logoTextRef.value, { opacity: 0, y: 6 }, { opacity: 1, y: 0 }, '-=0.1')

    if (navRef.value) {
      const links = navRef.value.querySelectorAll('a')
      tl.fromTo(links, { opacity: 0, y: 4 }, { opacity: 1, y: 0, stagger: 0.04 }, '-=0.05')
    }

    if (userSectionRef.value) {
      tl.fromTo(userSectionRef.value, { opacity: 0 }, { opacity: 1 }, '-=0.05')
    }
  })
}

watch(isLoginPage, (val) => {
  if (!val) {
    runEntranceAnimations()
  }
})

interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'info'
}

const toasts = ref<Toast[]>([])
let toastId = 0

const showContact = ref(false)
const wechatId = '16657290113'

function copyWechat() {
  navigator.clipboard.writeText(wechatId).then(() => {
    showToast('微信号已复制', 'success')
  }).catch(() => {
    showToast('复制失败，请手动添加: ' + wechatId, 'info')
  })
}

function showToast(message: string, type: Toast['type'] = 'info') {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 3000)
}

const userInitial = computed(() => {
  const name = auth.user?.nickname || 'U'
  return name.charAt(0).toUpperCase()
})

const navItems = computed(() => {
  const items = [
    { to: '/workspace', label: '工作台', icon: createIcon('M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z') },
    { to: '/gallery', label: '画廊', icon: createIcon('M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z') },
    { to: '/project', label: '一键成片', icon: createIcon('M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z') },
    { to: '/pricing', label: '充值', icon: createIcon('M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z') },
    { to: '/referral', label: '我的邀请', icon: createIcon('M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1') },
    { to: '/settings', label: '设置', icon: createIcon('M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z') },
  ]
  if (auth.isAdmin) {
    items.push({
      to: '/admin',
      label: '管理后台',
      icon: createIcon('M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z'),
    })
  }
  return items
})

function createIcon(pathD: string) {
  return {
    render() {
      return h('svg', {
        fill: 'none',
        stroke: 'currentColor',
        viewBox: '0 0 24 24',
        innerHTML: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${pathD}" />`
      })
    }
  }
}

function isActive(path: string) {
  return route.path === path
}

function onNavEnter(e: MouseEvent, path: string) {
  if (!isActive(path)) {
    ;(e.currentTarget as HTMLElement).style.background = 'var(--bg-surface-2)'
  }
}

function onNavLeave(e: MouseEvent, path: string) {
  if (!isActive(path)) {
    ;(e.currentTarget as HTMLElement).style.background = 'transparent'
  }
}

function onBtnHover(el: HTMLElement, color: string) {
  el.style.color = color
}

const pageTitle = computed(() => {
  const map: Record<string, string> = {
    workspace: '工作台',
    gallery: '画廊',
    pricing: '充值中心',
    referral: '我的邀请',
    admin: '管理后台',
  }
  return map[route.name as string] || 'AiForge'
})

function handleLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<style scoped>
/* ══════════════════════════════════════
   App Shell — Apple-inspired Layout
   ══════════════════════════════════════ */

.app-shell {
  display: flex;
  height: 100vh;
  background-color: var(--bg-canvas);
  position: relative;
}

/* ─── Sidebar ─── */
.sidebar {
  width: 64px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 10;
  background: var(--sidebar-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-right: 0.5px solid var(--border-hairline);
}

@media (min-width: 1024px) {
  .sidebar {
    width: 208px;
  }
}

/* Logo */
.sidebar-logo {
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.sidebar-logo-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.sidebar-logo-text {
  font-family: 'Inter', 'Noto Sans SC', sans-serif;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.022em;
  display: none;
}

.sidebar-logo-letter {
  font-family: 'Inter', 'Noto Sans SC', sans-serif;
  font-size: 18px;
  font-weight: 700;
  display: block;
  text-align: center;
}

@media (min-width: 1024px) {
  .sidebar-logo-text {
    display: block;
  }
  .sidebar-logo-letter {
    display: none;
  }
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 400;
  color: var(--text-muted);
  text-decoration: none;
  transition: background 0.15s ease, color 0.15s ease;
  letter-spacing: -0.01em;
}

.nav-item:hover {
  text-decoration: none;
}

.nav-item--active {
  background: var(--accent);
  color: white;
  font-weight: 500;
}

.nav-item-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.nav-item-label {
  display: none;
}

@media (min-width: 1024px) {
  .nav-item-label {
    display: inline;
  }
}

/* User section */
.sidebar-user {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
}

.sidebar-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.sidebar-user-detail {
  display: none;
  flex: 1;
  min-width: 0;
}

@media (min-width: 1024px) {
  .sidebar-user-detail {
    display: block;
  }
}

.sidebar-user-name {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
  line-height: 1.4;
}

.sidebar-user-points {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.4;
}

.sidebar-action-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 13px;
  border: none;
  background: none;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
  letter-spacing: -0.01em;
}

.sidebar-action-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.sidebar-action-label {
  display: none;
}

@media (min-width: 1024px) {
  .sidebar-action-label {
    display: inline;
  }
}

/* ─── Contact Modal ─── */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.modal-content {
  position: relative;
  padding: 32px;
  border-radius: 16px;
  text-align: center;
  max-width: 380px;
  width: calc(100% - 32px);
  background: var(--bg-surface-1);
  box-shadow: var(--shadow-elevated);
}

.modal-icon-wrap {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-subtle);
}

.modal-icon {
  width: 28px;
  height: 28px;
}

.modal-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px;
  letter-spacing: -0.022em;
}

.modal-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0 0 16px;
}

.modal-wechat-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 16px;
  background: var(--bg-surface-2);
}

.modal-wechat-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.modal-wechat-id {
  font-size: 14px;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-weight: 600;
  color: var(--text-primary);
  user-select: all;
}

.modal-copy-btn {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 9999px;
  border: none;
  background: var(--accent);
  color: white;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.15s ease;
  letter-spacing: -0.01em;
}

.modal-copy-btn:hover {
  background: var(--accent-hover);
}

.modal-hours {
  font-size: 11px;
  color: var(--text-tertiary);
  margin: 0;
}

.modal-close-btn {
  margin-top: 16px;
  font-size: 13px;
  color: var(--text-muted);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 16px;
  border-radius: 9999px;
  transition: background 0.15s ease, color 0.15s ease;
}

.modal-close-btn:hover {
  background: var(--bg-surface-2);
  color: var(--text-primary);
}

/* Modal transitions */
.modal-enter-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .modal-content {
  transition: transform 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94), opacity 0.2s ease;
}
.modal-leave-active {
  transition: opacity 0.15s ease;
}
.modal-leave-active .modal-content {
  transition: transform 0.15s ease, opacity 0.15s ease;
}
.modal-enter-from {
  opacity: 0;
}
.modal-enter-from .modal-content {
  transform: scale(0.96);
  opacity: 0;
}
.modal-leave-to {
  opacity: 0;
}
.modal-leave-to .modal-content {
  transform: scale(0.96);
  opacity: 0;
}

/* ─── Main Area ─── */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.header {
  height: 48px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  flex-shrink: 0;
  position: relative;
  z-index: 20;
  overflow: visible;
  background: var(--header-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 0.5px solid var(--border-hairline);
}

.header-title {
  font-family: 'Inter', 'Noto Sans SC', sans-serif;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.022em;
  margin: 0;
}

.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Theme Selector */
.theme-selector {
  position: relative;
}

.theme-selector-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 9999px;
  border: none;
  background: var(--bg-surface-2);
  color: var(--text-muted);
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
  letter-spacing: -0.01em;
}

.theme-selector-btn:hover {
  background: var(--bg-surface-3);
  color: var(--text-secondary);
}

.theme-selector-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.theme-selector-label {
  display: none;
}

@media (min-width: 640px) {
  .theme-selector-label {
    display: inline;
  }
}

.theme-selector-arrow {
  width: 12px;
  height: 12px;
}

.theme-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 4px);
  border-radius: 12px;
  padding: 4px;
  min-width: 128px;
  z-index: 100;
  background: var(--bg-surface-1);
  box-shadow: var(--shadow-elevated);
  border: 0.5px solid var(--border-hairline);
}

.theme-dropdown-item {
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  font-size: 12px;
  border-radius: 8px;
  border: none;
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: background 0.12s ease, color 0.12s ease;
  letter-spacing: -0.01em;
}

.theme-dropdown-item:hover {
  background: var(--bg-surface-2);
  color: var(--text-primary);
}

.theme-dropdown-item--active {
  font-weight: 500;
  color: var(--accent);
  background: var(--accent-subtle);
}

/* Dropdown transitions */
.dropdown-enter-active {
  transition: opacity 0.15s ease, transform 0.15s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.dropdown-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}

/* Points */
.header-points {
  font-size: 12px;
  color: var(--text-tertiary);
  letter-spacing: -0.01em;
}

.header-points-value {
  color: var(--accent);
  font-weight: 600;
}

/* Content */
.main-content {
  flex: 1;
  overflow: hidden;
}

/* ─── Toast Notifications ─── */
.toast {
  position: fixed;
  right: 16px;
  z-index: 50;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 12px;
  max-width: 360px;
  background: var(--bg-surface-1);
  box-shadow: var(--shadow-elevated);
}

.toast--success {
  border: 0.5px solid rgba(34, 197, 94, 0.25);
}

.toast--error {
  border: 0.5px solid rgba(239, 68, 68, 0.25);
}

.toast--info {
  border: 0.5px solid var(--border-hairline);
}

.toast-message {
  font-size: 13px;
  letter-spacing: -0.01em;
}

.toast--success .toast-message {
  color: #22c55e;
}

.toast--error .toast-message {
  color: #ef4444;
}

.toast--info .toast-message {
  color: var(--accent);
}

/* Toast transitions */
.toast-enter-active {
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(24px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(24px);
}
.toast-move {
  transition: transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
</style>
