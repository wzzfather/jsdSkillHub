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
  <div class="auth-wrap">
    <div class="card-panel auth-card">
      <div class="title">{{ text("title") }}</div>
      <p class="muted subtitle">企业级 Skill 分发与扫描审批（MVP）。</p>
      <el-form label-position="top" @submit.prevent="onSubmit">
        <el-form-item :label="text('user')">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item :label="text('pass')">
          <el-input v-model="form.password" type="password" autocomplete="current-password" />
        </el-form-item>
        <el-button type="primary" class="full" native-type="submit" :loading="loading">{{ text("btn") }}</el-button>
        <div class="muted foot">
          {{ text("hint") }}
          <el-button link type="primary" @click="router.push({ name: 'register' })">注册</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.auth-wrap {
  display: flex;
  justify-content: center;
  padding-top: 48px;
}

.auth-card {
  width: min(440px, 100%);
}

.title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}

.subtitle {
  margin-top: 0;
  margin-bottom: 16px;
}

.full {
  width: 100%;
}

.foot {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
