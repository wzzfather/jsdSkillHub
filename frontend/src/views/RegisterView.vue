<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { register } from "@/api/auth";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();

const form = reactive({
  username: "",
  email: "",
  password: "",
  confirm: "",
});

const loading = ref(false);

async function onSubmit() {
  if (!form.username.trim()) {
    ElMessage.warning("请填写用户名");
    return;
  }
  if (form.password !== form.confirm) {
    ElMessage.warning("两次密码不一致");
    return;
  }
  const emailTrim = form.email.trim();
  if (emailTrim && emailTrim.length < 5) {
    ElMessage.warning("邮箱长度过短");
    return;
  }
  loading.value = true;
  try {
    const { data } = await register({
      username: form.username.trim(),
      password: form.password,
      ...(emailTrim ? { email: emailTrim } : {}),
    });
    ElMessage.success("注册成功");
    if (data.email && !data.email_verified) {
      await router.replace({ name: "verify-email", query: { email: data.email } });
    } else {
      await auth.login(form.username.trim(), form.password);
      await router.replace("/explore");
    }
  } catch {
    ElMessage.error("注册失败，用户名或邮箱可能已被占用");
  } finally {
    loading.value = false;
  }
}

function text(key: string) {
  const map: Record<string, string> = {
    title: "注册",
    user: "用户名",
    email: "邮箱（可选，填写后需验证）",
    pass: "密码",
    confirm: "确认密码",
    btn: "注册",
    hint: "已有账号？去登录",
  };
  return map[key] ?? key;
}
</script>

<template>
  <div class="auth-wrap">
    <div class="card-panel auth-card">
      <div class="title">{{ text("title") }}</div>
      <p class="muted subtitle">注册后可提交 Skill 并在「我的应用」中跟踪状态。</p>
      <el-form label-position="top" @submit.prevent="onSubmit">
        <el-form-item :label="text('user')">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item :label="text('email')">
          <el-input v-model="form.email" type="email" autocomplete="email" placeholder="name@company.com" />
        </el-form-item>
        <el-form-item :label="text('pass')">
          <el-input v-model="form.password" type="password" autocomplete="new-password" />
        </el-form-item>
        <el-form-item :label="text('confirm')">
          <el-input v-model="form.confirm" type="password" autocomplete="new-password" />
        </el-form-item>
        <el-button type="primary" class="full" native-type="submit" :loading="loading">{{ text("btn") }}</el-button>
        <div class="muted foot">
          {{ text("hint") }}
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

.foot {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
