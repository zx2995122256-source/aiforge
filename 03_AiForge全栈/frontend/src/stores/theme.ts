import { defineStore } from 'pinia'
import { ref, watch, computed } from 'vue'

export type ThemeId = 'silver' | 'deepspace' | 'warmlight' | 'polarnight' | 'twilight'

export interface ThemeConfig {
  id: ThemeId
  label: string
  loginBg: string
  workspaceBg: string
}

export const THEMES: ThemeConfig[] = [
  { id: 'silver',     label: '银白',  loginBg: '/api/gen/file/276', workspaceBg: '/api/gen/file/277' },
  { id: 'deepspace',  label: '深空',  loginBg: '/api/gen/file/278', workspaceBg: '/api/gen/file/279' },
  { id: 'warmlight',  label: '暖阳',  loginBg: '/api/gen/file/280', workspaceBg: '/api/gen/file/281' },
  { id: 'polarnight', label: '极夜',  loginBg: '/api/gen/file/282', workspaceBg: '/api/gen/file/282' },
  { id: 'twilight',   label: '暮色',  loginBg: '/api/gen/file/283', workspaceBg: '/api/gen/file/283' },
]

export const useThemeStore = defineStore('theme', () => {
  const saved = localStorage.getItem('aiforge_theme_id') as ThemeId | null
  const current = ref<ThemeId>(saved || 'deepspace')

  const currentTheme = computed(() => THEMES.find(t => t.id === current.value) || THEMES[1])

  watch(current, (val) => {
    localStorage.setItem('aiforge_theme_id', val)
    document.documentElement.setAttribute('data-theme', val)
  }, { immediate: true })

  function setTheme(id: ThemeId) {
    current.value = id
  }

  return { current, currentTheme, setTheme }
})