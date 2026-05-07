<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterView, useRoute, useRouter } from "vue-router";
import { ArrowDown, Moon, Sunny } from "@element-plus/icons-vue";
import { useAuthStore } from "@/stores/auth";

const THEME_STORAGE_KEY = "theme";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const isDark = ref(false);

const isAuthed = computed(() => !!auth.token);
const isAdmin = computed(() => auth.isAdmin);

const userInitial = computed(() => {
  const id = auth.userId?.trim() ?? "";
  const c = id.charAt(0);
  return c ? c.toUpperCase() : "?";
});

function logout() {
  auth.clear();
  router.push({ name: "explore" });
}

function navClass(name: string | string[]) {
  const names = Array.isArray(name) ? name : [name];
  const hit = names.includes(String(route.name));
  return ["nav-link", ...(hit ? ["is-active"] : [])];
}

function goBrand() {
  router.push(auth.token ? { name: "dashboard" } : { name: "explore" });
}

function applyTheme(dark: boolean) {
  const root = document.documentElement;
  if (dark) {
    root.classList.add("dark");
    localStorage.setItem(THEME_STORAGE_KEY, "dark");
  } else {
    root.classList.remove("dark");
    localStorage.setItem(THEME_STORAGE_KEY, "light");
  }
  isDark.value = dark;
}

function toggleTheme() {
  document.documentElement.classList.toggle("dark");
  const dark = document.documentElement.classList.contains("dark");
  localStorage.setItem(THEME_STORAGE_KEY, dark ? "dark" : "light");
  isDark.value = dark;
}

onMounted(() => {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "dark") {
    applyTheme(true);
  } else if (stored === "light") {
    applyTheme(false);
  } else {
    applyTheme(false);
  }
});
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="header-left">
        <div class="app-brand" role="button" tabindex="0" @click="goBrand" @keydown.enter.prevent="goBrand">
          <span class="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" width="28" height="28" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M16 4l11 6.5v13L16 30 5 23.5v-13L16 4z"
                stroke="currentColor"
                stroke-width="1.5"
                fill="currentColor"
                fill-opacity="0.06"
              />
              <path d="M16 9l7 4v10l-7 4-7-4V13l7-4z" fill="currentColor" fill-opacity="0.12" />
            </svg>
          </span>
          <span class="brand-title">Skill Store</span>
        </div>

        <nav class="app-nav primary-nav" aria-label="主导航">
          <button type="button" class="plain-nav" :class="navClass(['explore', 'skill-detail'])" @click="router.push({ name: 'explore' })">
            浏览
          </button>

          <template v-if="isAuthed">
            <button type="button" class="plain-nav" :class="navClass('submit')" @click="router.push({ name: 'submit' })">提交应用</button>
            <button type="button" class="plain-nav" :class="navClass('my-apps')" @click="router.push({ name: 'my-apps' })">我的应用</button>
            <button type="button" class="plain-nav" :class="navClass('dashboard')" @click="router.push({ name: 'dashboard' })">看板</button>
            <button v-if="isAdmin" type="button" class="plain-nav" :class="navClass('review')" @click="router.push({ name: 'review' })">
              审批工作台
            </button>
            <button v-if="isAdmin" type="button" class="plain-nav" :class="navClass('admin-apps')" @click="router.push({ name: 'admin-apps' })">
              应用管理
            </button>
          </template>
        </nav>
      </div>

      <div class="header-right">
        <button
          type="button"
          class="theme-toggle"
          :aria-label="isDark ? '切换为亮色主题' : '切换为暗色主题'"
          @click="toggleTheme"
        >
          <el-icon class="theme-toggle-ico" :size="18" aria-hidden="true">
            <Sunny v-if="isDark" />
            <Moon v-else />
          </el-icon>
        </button>
        <template v-if="!isAuthed">
          <button type="button" class="plain-nav" :class="navClass('login')" @click="router.push({ name: 'login' })">登录</button>
          <button type="button" class="plain-nav register-pill" :class="navClass('register')" @click="router.push({ name: 'register' })">
            注册
          </button>
        </template>
        <el-dropdown v-else trigger="click" @command="(c: string) => c === 'logout' && logout()">
          <span class="user-trigger">
            <span class="user-avatar" :title="auth.userId || '用户'">{{ userInitial }}</span>
            <el-icon class="user-chevron"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <main class="app-main">
      <RouterView v-slot="{ Component }">
        <transition name="fade-page" mode="out-in">
          <component :is="Component" />
        </transition>
      </RouterView>
    </main>

    <footer class="app-footer">© 2026 AI Agent Skill Store</footer>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--app-bg);
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--header-height);
  background: var(--app-header-bg);
  color: var(--app-header-text);
  box-shadow: var(--shadow-header);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--page-padding-x);
  box-sizing: border-box;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 28px;
  min-width: 0;
}

.app-brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  color: var(--app-primary);
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--app-primary);
}

.brand-title {
  font-weight: 700;
  font-size: 18px;
  letter-spacing: 0.02em;
  color: var(--app-primary);
  white-space: nowrap;
}

.app-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.plain-nav {
  border: none;
  background: transparent;
  color: var(--app-text);
  font-weight: 500;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.4;
  padding: 8px 12px;
  border-radius: var(--radius-control);
}

.plain-nav:hover {
  background: color-mix(in srgb, var(--app-text) 6%, transparent);
  color: var(--app-primary);
}

.plain-nav.is-active {
  background: color-mix(in srgb, var(--app-text) 10%, transparent);
  color: var(--app-primary);
  font-weight: 600;
}

.register-pill {
  border: 1px solid var(--app-border-strong);
  background: var(--app-surface);
}

.register-pill:hover {
  border-color: var(--app-primary-deep);
  background: var(--app-surface);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.theme-toggle {
  border: none;
  background: transparent;
  padding: 6px 10px;
  border-radius: var(--radius-control);
  cursor: pointer;
  font: inherit;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.theme-toggle:hover {
  background: color-mix(in srgb, var(--app-text) 6%, transparent);
}

.theme-toggle-ico {
  color: var(--app-muted);
  line-height: 1;
}

.theme-toggle:hover .theme-toggle-ico {
  color: var(--app-primary);
}

.user-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 6px 4px 4px;
  border-radius: 999px;
}

.user-trigger:hover {
  background: color-mix(in srgb, var(--app-text) 6%, transparent);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--app-primary) 0%, var(--app-primary-deep) 100%);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.user-chevron {
  font-size: 12px;
  color: var(--app-muted);
}

.app-main {
  flex: 1;
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: var(--page-padding-y) var(--page-padding-x);
  box-sizing: border-box;
}

.app-footer {
  padding: 16px;
  text-align: center;
  font-size: 12px;
  color: var(--app-muted);
  border-top: 1px solid var(--app-border);
  background: var(--app-bg);
}

@media (max-width: 520px) {
  .brand-title {
    font-size: 16px;
  }
}
</style>

<style>
.fade-page-enter-active,
.fade-page-leave-active {
  transition: opacity 0.2s ease;
}

.fade-page-enter-from,
.fade-page-leave-to {
  opacity: 0;
}
</style>
