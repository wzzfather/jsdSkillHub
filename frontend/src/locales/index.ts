import { reactive, toRef } from "vue";
import zh from "./zh";
import en from "./en";

export type LocaleCode = "zh" | "en";

const STORAGE_KEY = "locale";

/** 中英文完整词典（由各语言文件导出） */
const dictionaries: Record<LocaleCode, Record<string, string>> = {
  zh,
  en,
};

function normalizeLocale(raw: unknown): LocaleCode {
  if (raw === "en") return "en";
  return "zh";
}

function readStoredLocale(): LocaleCode {
  try {
    return normalizeLocale(localStorage.getItem(STORAGE_KEY));
  } catch {
    return "zh";
  }
}

const state = reactive({
  locale: readStoredLocale(),
});

/**
 * 按 flat key 取值，与 `useLocale().t` 共享 `state.locale`。
 * 用于 vue-router `beforeEach` 等非组件上下文（不可调用 composable）。
 */
export function translate(key: string): string {
  const bundle = dictionaries[state.locale];
  const fallback = dictionaries.zh;
  if (Object.prototype.hasOwnProperty.call(bundle, key) && bundle[key] !== "") {
    return bundle[key];
  }
  if (Object.prototype.hasOwnProperty.call(fallback, key)) {
    return fallback[key];
  }
  return key;
}

export function useLocale() {
  const setLocale = (lang: string) => {
    const next = normalizeLocale(lang);
    state.locale = next;
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* ignore quota / privacy mode */
    }
  };

  /**
   * 按 flat key 取值（如 login.title）。读取当前语言的 `dictionaries[state.locale]`，
   * 再从 reactive `state.locale` 取词，Vue 渲染时会建立依赖，切换语言会自动刷新。
   */
  const t = (key: string): string => translate(key);

  return {
    locale: toRef(state, "locale"),
    setLocale,
    t,
  };
}
