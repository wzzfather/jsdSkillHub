import { ref, watch, computed } from 'vue'

export type Lang = 'zh' | 'en'

const locale = ref<Lang>((localStorage.getItem('locale') as Lang) || 'zh')

watch(locale, (val) => {
  localStorage.setItem('locale', val)
})

let _messages: Record<string, string> = {}

export function setMessages(msgs: Record<string, string>) {
  _messages = msgs
}

export function updateMessages(msgs: Record<string, string>) {
  Object.assign(_messages, msgs)
}

export function t(key: string): string {
  return _messages[key] ?? key
}

export function setLocale(lang: Lang) {
  locale.value = lang
}

export function useLocale() {
  return {
    locale,
    t,
    setLocale,
    isZh: computed(() => locale.value === 'zh'),
    isEn: computed(() => locale.value === 'en'),
  }
}
