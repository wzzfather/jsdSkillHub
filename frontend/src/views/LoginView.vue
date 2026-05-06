<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const form = reactive({
  username: "",
  password: "",
});

const loading = ref(false);

async function onSubmit() {
  loading.value = true;
  try {
    await auth.login(form.username.trim(), form.password);
    ElMessage.success("登录成功");
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "";
    await router.replace(redirect && redirect.startsWith("/") ? redirect : "/explore");
  } catch {
    ElMessage.error("登录失败，请检查账号密码");
  } finally {
    loading.value = false;
  }
}

function text(key: string) {
  const map: Record<string, string> = {
    title: "登录",
    user: "用户名",
    pass: "密码",
    btn: "登录",
    hint: "没有账号？去注册",
  };
  return map[key] ?? key;
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="brand">
        <span class="brand-icon" aria-hidden="true">
          <svg viewBox="0 0 32 32" width="40" height="40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M16 4l11 6.5v13L16 30 5 23.5v-13L16 4z"
              stroke="currentColor"
              stroke-width="1.5"
              fill="rgba(26,26,46,0.06)"
            />
            <path d="M16 9l7 4v10l-7 4-7-4V13l7-4z" fill="currentColor" fill-opacity="0.12" />
          </svg>
        </span>
        <div class="brand-name">Skill Store</div>
        <div class="brand-sub">企业级 AI Agent 应用商店</div>
      </div>

      <h1 class="title">{{ text("title") }}</h1>

      <el-form label-position="top" class="auth-form" @submit.prevent="onSubmit">
        <el-form-item :label="text('user')">
          <el-input v-model="form.username" class="auth-input" autocomplete="username" />
        </el-form-item>
        <el-form-item :label="text('pass')">
          <el-input v-model="form.password" class="auth-input" type="password" autocomplete="current-password" />
        </el-form-item>
        <el-button type="primary" class="auth-submit" native-type="submit" :loading="loading">{{ text("btn") }}</el-button>
        <div class="foot muted">
          {{ text("hint") }}
          <el-button link type="primary" class="link-btn" @click="router.push({ name: 'register' })">注册</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: calc(100vh - var(--header-height) - 80px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px 48px;
  background: var(--app-bg);
}

.auth-card {
  width: 100%;
  max-width: 420px;
  background: var(--app-surface);
  border-radius: 16px;
  box-shadow: var(--shadow-auth-card);
  padding: 40px;
  box-sizing: border-box;
  border: 1px solid var(--app-border);
}

.brand {
  text-align: center;
  margin-bottom: 8px;
}

.brand-icon {
  display: inline-flex;
  color: var(--app-primary);
}

.brand-name {
  margin-top: 10px;
  font-size: 22px;
  font-weight: 800;
  color: var(--app-text);
  letter-spacing: 0.02em;
}

.brand-sub {
  margin-top: 6px;
  font-size: 13px;
  color: var(--app-muted);
}

.title {
  margin: 20px 0 8px;
  font-size: 18px;
  font-weight: 700;
  text-align: center;
  color: var(--app-text);
}

.auth-form {
  margin-top: 8px;
}

.auth-form :deep(.el-form-item__label) {
  color: var(--app-muted);
  font-weight: 500;
  font-size: 13px;
}

.auth-input :deep(.el-input__wrapper) {
  min-height: 44px;
  border-radius: var(--radius-control);
  box-shadow: 0 0 0 1px var(--app-border) inset;
}

.auth-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: var(--focus-ring), 0 0 0 1px var(--app-primary-deep) inset;
}

.auth-submit {
  width: 100%;
  margin-top: 8px;
  height: 44px;
  border-radius: var(--radius-control);
  font-weight: 600;
  background: var(--app-primary) !important;
  border-color: var(--app-primary) !important;
}

.foot {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 13px;
}

.link-btn {
  font-weight: 600;
}
</style>
