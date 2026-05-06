<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { sendCode, verifyEmail } from "@/api/auth";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const email = ref("");
const code = ref("");
const loadingSend = ref(false);
const loadingVerify = ref(false);

watch(
  () => route.query.email,
  (q) => {
    email.value = typeof q === "string" ? decodeURIComponent(q) : "";
  },
  { immediate: true },
);

async function requestCode() {
  if (!email.value.trim()) {
    ElMessage.warning("缺少邮箱参数，请从注册页进入");
    return;
  }
  loadingSend.value = true;
  try {
    const { data } = await sendCode(email.value.trim());
    // MVP：后端已在响应中返回验证码；生产接入 SMTP 后删除下行
    console.log("[MVP] 模拟收件箱：邮箱验证码 =", data.code, "（后续接 SMTP 后勿在控制台输出）");
    ElMessage.success("验证码已生成（MVP：请打开浏览器控制台查看模拟邮件）");
  } catch {
    ElMessage.error("发送验证码失败");
  } finally {
    loadingSend.value = false;
  }
}

async function onVerify() {
  const c = code.value.replace(/\D/g, "").slice(0, 6);
  if (c.length !== 6) {
    ElMessage.warning("请输入 6 位数字验证码");
    return;
  }
  loadingVerify.value = true;
  try {
    const { data } = await verifyEmail(email.value.trim(), c);
    auth.setToken(data.access_token);
    await auth.ensureAdmin();
    ElMessage.success("验证成功");
    await router.replace("/dashboard");
  } catch {
    ElMessage.error("验证失败，请检查验证码");
  } finally {
    loadingVerify.value = false;
  }
}

onMounted(() => {
  if (email.value.trim()) void requestCode();
});
</script>

<template>
  <div class="auth-wrap">
    <div class="card-panel auth-card">
      <div class="title">验证邮箱</div>
      <p class="muted subtitle">
        MVP 模式：验证码由接口直接返回并在浏览器控制台打印；后续将改为邮件发送。
      </p>
      <el-form label-position="top" @submit.prevent="onVerify">
        <el-form-item label="邮箱">
          <el-input v-model="email" type="email" autocomplete="email" />
        </el-form-item>
        <el-form-item label="6 位验证码">
          <el-input
            v-model="code"
            maxlength="6"
            inputmode="numeric"
            pattern="[0-9]*"
            placeholder="000000"
            autocomplete="one-time-code"
            @input="code = code.replace(/\D/g, '').slice(0, 6)"
          />
        </el-form-item>
        <el-button type="primary" class="full" native-type="submit" :loading="loadingVerify">验证并登录</el-button>
        <el-button class="full secondary" :loading="loadingSend" @click="requestCode">重新获取验证码</el-button>
        <div class="muted foot">
          返回
          <el-button link type="primary" @click="router.push({ name: 'login' })">登录</el-button>
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

.secondary {
  margin-top: 10px;
}

.foot {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
