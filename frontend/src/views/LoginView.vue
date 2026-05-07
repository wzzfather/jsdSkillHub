<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/stores/auth";
import { useLocale } from "@/locales";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const { t } = useLocale();

const loginMode = ref<"username" | "email">("username");

const form = reactive({
  username: "",
  email: "",
  password: "",
});

const loading = ref(false);

async function onSubmit() {
  loading.value = true;
  try {
    if (loginMode.value === "username") {
      const u = form.username.trim();
      if (!u) {
        ElMessage.warning(t("login.warnUser"));
        loading.value = false;
        return;
      }
      await auth.login({ username: u, password: form.password });
    } else {
      const em = form.email.trim();
      if (!em) {
        ElMessage.warning(t("login.warnEmail"));
        loading.value = false;
        return;
      }
      await auth.login({ email: em, password: form.password });
    }
    ElMessage.success(t("login.ok"));
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "";
    await router.replace(redirect && redirect.startsWith("/") ? redirect : "/explore");
  } catch {
    ElMessage.error(t("login.fail"));
  } finally {
    loading.value = false;
  }
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
              fill="currentColor"
              fill-opacity="0.06"
            />
            <path d="M16 9l7 4v10l-7 4-7-4V13l7-4z" fill="currentColor" fill-opacity="0.12" />
          </svg>
        </span>
        <div class="brand-name">Skill Store</div>
        <div class="brand-sub">{{ t("common.brandSub") }}</div>
      </div>

      <h1 class="title">{{ t("login.title") }}</h1>

      <el-radio-group v-model="loginMode" class="mode-switch" size="large">
        <el-radio-button label="username">{{ t("login.modeUser") }}</el-radio-button>
        <el-radio-button label="email">{{ t("login.modeEmail") }}</el-radio-button>
      </el-radio-group>

      <el-form label-position="top" class="auth-form" @submit.prevent="onSubmit">
        <template v-if="loginMode === 'username'">
          <el-form-item :label="t('login.fieldUser')">
            <el-input v-model="form.username" class="auth-input" autocomplete="username" />
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item :label="t('login.fieldEmail')">
            <el-input v-model="form.email" class="auth-input" type="email" autocomplete="email" />
          </el-form-item>
        </template>
        <el-form-item :label="t('login.fieldPass')">
          <el-input v-model="form.password" class="auth-input" type="password" autocomplete="current-password" />
        </el-form-item>
        <el-button type="primary" class="auth-submit" native-type="submit" :loading="loading">{{ t("login.submit") }}</el-button>
        <div class="foot muted">
          {{ t("login.hintPrefix") }}
          <el-button link type="primary" class="link-btn" @click="router.push({ name: 'register' })">{{ t("login.linkRegister") }}</el-button>
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

.mode-switch {
  display: flex;
  width: 100%;
  margin-bottom: 16px;
  justify-content: center;
}

.mode-switch :deep(.el-radio-button__inner) {
  border-radius: var(--radius-control);
  font-weight: 600;
  color: var(--app-text);
  border-color: var(--app-border-strong);
  background: var(--app-surface);
  box-shadow: none;
}

.mode-switch :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: var(--radius-control) 0 0 var(--radius-control);
}

.mode-switch :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 var(--radius-control) var(--radius-control) 0;
}

.mode-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--app-primary);
  border-color: var(--app-primary);
  color: #fff;
  box-shadow: none;
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
